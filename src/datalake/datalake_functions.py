#!/usr/bin/env python3
"""
CSV to Parquet Converter, MinIO Uploader and Dremio Iceberg Table Creator

Professional production-ready version with proper logging, error handling,
and modular architecture following SOLID principles.

Author: Data Engineering Team
Version: 2.0.0
"""

import os
import sys
import time
import logging
import datetime
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from abc import ABC, abstractmethod

import pandas as pd
import requests
from minio import Minio
from minio.error import S3Error


# ================================================================================
# CONFIGURATION CLASSES
# ================================================================================

@dataclass
class MinIOConfig:
    """Configuration for MinIO connection"""
    endpoint: str = "localhost:9000"
    access_key: str = "VSXTQD0QTFTL1MGIH5Z7"
    secret_key: str = "mcABEMcJHgHANeuGx305MoId1977HsvkBnyQVC8c"
    secure: bool = False
    bucket_name: str = "datalake"
    folder_name: str = "dados"


@dataclass
class DremioConfig:
    """Configuration for Dremio connection"""
    host: str = "localhost"
    port: int = 9047
    username: str = "caio.santos"
    password: str = "Inteli@123"
    timeout: int = 60


@dataclass
class PipelineConfig:
    """Configuration for pipeline execution"""
    compression: str = 'snappy'
    keep_parquet_local: bool = False
    clear_existing_data: bool = False
    debug: bool = True


# ================================================================================
# CONSTANTS
# ================================================================================

class Constants:
    """Application constants"""
    SUPPORTED_COMPRESSIONS = ['snappy', 'gzip', 'brotli', None]
    DREMIO_TOKEN_PREFIX = "_dremio"
    METADATA_REFRESH_DELAY = 2
    MAX_RETRIES = 3
    
    # SQL Templates
    ICEBERG_TABLE_CREATE_TEMPLATE = '''CREATE TABLE Iceberg.datalake.datalake."{table_name}" (
    "timestamp" VARCHAR,
    "ingestion_timestamp" VARCHAR,
    "timestamp_date" DATE,
    "motor_pump" VARCHAR,
    "resource" VARCHAR,
    "value" DOUBLE,
    "processed" BOOLEAN
)
PARTITION BY (MONTH("timestamp_date"))'''

    ICEBERG_INSERT_TEMPLATE = '''INSERT INTO Iceberg.datalake.datalake."{table_name}"
SELECT
    CAST("timestamp" AS VARCHAR) AS "timestamp",
    CAST("ingestion_timestamp" AS VARCHAR) AS "ingestion_timestamp",
    CAST(SUBSTR(CAST("timestamp" AS VARCHAR), 1, 10) AS DATE) AS "timestamp_date",
    "motor_pump",
    "resource",
    CAST("value" AS DOUBLE) AS "value",
    CAST("processed" AS BOOLEAN) AS "processed"
FROM datalake.datalake.dados."{machine_name}"."{filename}";'''


# ================================================================================
# LOGGING SETUP
# ================================================================================

class LoggerSetup:
    """Setup and manage logging configuration"""
    
    @staticmethod
    def setup_logger(name: str = __name__, debug: bool = False) -> logging.Logger:
        """
        Setup logger with appropriate level and formatting
        
        Args:
            name: Logger name
            debug: Enable debug logging
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger


# ================================================================================
# EXCEPTION CLASSES
# ================================================================================

class PipelineException(Exception):
    """Base exception for pipeline operations"""
    pass


class CSVProcessingException(PipelineException):
    """Exception raised during CSV processing"""
    pass


class MinIOOperationException(PipelineException):
    """Exception raised during MinIO operations"""
    pass


class DremioOperationException(PipelineException):
    """Exception raised during Dremio operations"""
    pass


# ================================================================================
# ABSTRACT INTERFACES
# ================================================================================

class DataProcessor(ABC):
    """Abstract interface for data processors"""
    
    @abstractmethod
    def process(self, input_path: str, **kwargs) -> str:
        """Process data from input path"""
        pass


class CloudStorage(ABC):
    """Abstract interface for cloud storage operations"""
    
    @abstractmethod
    def upload(self, local_path: str, remote_path: str) -> bool:
        """Upload file to cloud storage"""
        pass


class QueryEngine(ABC):
    """Abstract interface for query engines"""
    
    @abstractmethod
    def execute_query(self, sql: str) -> Optional[Dict[str, Any]]:
        """Execute SQL query"""
        pass


# ================================================================================
# CORE CLASSES
# ================================================================================

class CSVProcessor(DataProcessor):
    """Handle CSV to Parquet conversion operations"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
    
    def extract_machine_name(self, csv_file_path: str) -> str:
        """
        Extract machine name from motor_pump column in CSV file
        
        Args:
            csv_file_path: Path to CSV file
            
        Returns:
            Machine name
            
        Raises:
            CSVProcessingException: If extraction fails
        """
        try:
            if not os.path.exists(csv_file_path):
                raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
            
            self.logger.info(f"Extracting machine name from {csv_file_path}")
            
            # Read only the motor_pump column to optimize memory usage
            df = pd.read_csv(csv_file_path, usecols=['motor_pump'])
            
            if df.empty:
                raise CSVProcessingException("CSV file is empty or doesn't contain data")
            
            unique_machines = df['motor_pump'].unique()
            
            if len(unique_machines) == 0:
                raise CSVProcessingException("No machine names found in motor_pump column")
            elif len(unique_machines) > 1:
                raise CSVProcessingException(
                    f"Multiple machines found in the same file: {unique_machines}. "
                    "Each file should contain data from only one machine."
                )
            
            machine_name = unique_machines[0]
            self.logger.info(f"Machine name extracted: {machine_name}")
            
            return machine_name
            
        except Exception as e:
            self.logger.error(f"Error extracting machine name: {e}")
            raise CSVProcessingException(f"Failed to extract machine name: {e}") from e
    
    def process(self, csv_file_path: str, parquet_file_path: Optional[str] = None, 
                compression: str = 'snappy') -> str:
        """
        Convert CSV file to Parquet format
        
        Args:
            csv_file_path: Path to input CSV file
            parquet_file_path: Path for output Parquet file
            compression: Compression algorithm
            
        Returns:
            Path to created Parquet file
            
        Raises:
            CSVProcessingException: If conversion fails
        """
        try:
            if not os.path.exists(csv_file_path):
                raise FileNotFoundError(f"CSV file not found: {csv_file_path}")
            
            if compression not in Constants.SUPPORTED_COMPRESSIONS:
                raise ValueError(f"Unsupported compression: {compression}")
            
            if parquet_file_path is None:
                parquet_file_path = Path(csv_file_path).with_suffix('.parquet')
            
            self.logger.info(f"Converting {csv_file_path} to {parquet_file_path}")
            
            # Read CSV and add metadata columns
            df = pd.read_csv(csv_file_path)
            
            self.logger.debug(f"Data info: {len(df)} rows, {len(df.columns)} columns")
            
            # Add metadata columns
            df["ingestion_timestamp"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            df["processed"] = False
            
            self.logger.debug(f"Columns: {list(df.columns)}")
            
            # Convert to Parquet
            df.to_parquet(parquet_file_path, compression=compression, index=False, engine='pyarrow')
            
            # Log file size information
            csv_size = os.path.getsize(csv_file_path)
            parquet_size = os.path.getsize(parquet_file_path)
            compression_ratio = (1 - parquet_size / csv_size) * 100
            
            self.logger.info(f"Conversion successful - CSV: {csv_size:,} bytes, "
                           f"Parquet: {parquet_size:,} bytes, "
                           f"Compression: {compression_ratio:.1f}% reduction")
            
            return str(parquet_file_path)
            
        except Exception as e:
            self.logger.error(f"CSV to Parquet conversion failed: {e}")
            raise CSVProcessingException(f"Conversion failed: {e}") from e
    
    def generate_unique_filename(self, csv_file_path: str) -> str:
        """
        Generate unique parquet filename with timestamp
        
        Args:
            csv_file_path: Original CSV file path
            
        Returns:
            Unique filename with timestamp
        """
        base_filename = Path(csv_file_path).stem
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_filename = f"{base_filename}_{timestamp}.parquet"
        
        self.logger.debug(f"Generated unique filename: {unique_filename}")
        return unique_filename


class MinIOClient(CloudStorage):
    """Handle MinIO storage operations"""
    
    def __init__(self, config: MinIOConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.client = self._create_client()
    
    def _create_client(self) -> Minio:
        """Create MinIO client instance"""
        try:
            return Minio(
                self.config.endpoint,
                access_key=self.config.access_key,
                secret_key=self.config.secret_key,
                secure=self.config.secure
            )
        except Exception as e:
            self.logger.error(f"Failed to create MinIO client: {e}")
            raise MinIOOperationException(f"MinIO client creation failed: {e}") from e
    
    def upload(self, local_path: str, remote_path: str) -> bool:
        """
        Upload file to MinIO
        
        Args:
            local_path: Local file path
            remote_path: Remote object path
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")
            
            # Ensure bucket exists
            if not self.client.bucket_exists(self.config.bucket_name):
                self.logger.info(f"Creating bucket: {self.config.bucket_name}")
                self.client.make_bucket(self.config.bucket_name)
            
            self.logger.info(f"Uploading {local_path} to {remote_path}")
            
            self.client.fput_object(
                self.config.bucket_name,
                remote_path,
                local_path,
                content_type="application/octet-stream"
            )
            
            file_size = os.path.getsize(local_path)
            self.logger.info(f"Upload successful - Size: {file_size:,} bytes, "
                           f"Location: s3://{self.config.bucket_name}/{remote_path}")
            
            return True
            
        except S3Error as e:
            self.logger.error(f"MinIO S3 error during upload: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Upload error: {e}")
            return False
    
    def upload_parquet(self, parquet_file_path: str, unique_filename: str, 
                      machine_name: str) -> Optional[str]:
        """
        Upload parquet file with machine-specific folder structure
        
        Args:
            parquet_file_path: Local parquet file path
            unique_filename: Unique filename for the object
            machine_name: Machine name for folder isolation
            
        Returns:
            Object name if successful, None otherwise
        """
        try:
            # Generate object path with machine subfolder
            if self.config.folder_name:
                object_name = f"{self.config.folder_name}/{machine_name}/{unique_filename}"
            else:
                object_name = f"{machine_name}/{unique_filename}"
            
            if self.upload(parquet_file_path, object_name):
                return object_name
            return None
            
        except Exception as e:
            self.logger.error(f"Error uploading parquet file: {e}")
            return None


class DremioClient(QueryEngine):
    """Handle Dremio operations and queries"""
    
    def __init__(self, config: DremioConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.base_url = f"http://{config.host}:{config.port}"
        self.token: Optional[str] = None
    
    def authenticate(self) -> bool:
        """
        Authenticate with Dremio and obtain token
        
        Returns:
            True if successful, False otherwise
        """
        try:
            url = f"{self.base_url}/apiv2/login"
            payload = {
                "userName": self.config.username,
                "password": self.config.password
            }
            
            self.logger.info("Authenticating with Dremio")
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            self.token = response.json().get("token")
            if not self.token:
                raise DremioOperationException("No token received from Dremio")
            
            self.logger.info("Dremio authentication successful")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Dremio authentication failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during authentication: {e}")
            return False
    
    def execute_query(self, sql: str) -> Optional[Dict[str, Any]]:
        """
        Execute SQL query in Dremio
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Query result or None if failed
        """
        try:
            if not self.token:
                raise DremioOperationException("Not authenticated. Please login first.")
            
            # Submit query
            url = f"{self.base_url}/api/v3/sql"
            headers = {
                "Authorization": f"{Constants.DREMIO_TOKEN_PREFIX}{self.token}",
                "Content-Type": "application/json"
            }
            payload = {"sql": sql}
            
            self.logger.debug(f"Executing query: {sql}")
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            job_id = response.json().get("id")
            if not job_id:
                raise DremioOperationException("No job ID received from Dremio")
            
            return self._wait_for_job_completion(job_id)
            
        except requests.RequestException as e:
            self.logger.error(f"Error executing query: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during query execution: {e}")
            return None
    
    def _wait_for_job_completion(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Wait for job completion and return result
        
        Args:
            job_id: Dremio job ID
            
        Returns:
            Job result or None if failed
        """
        try:
            headers = {"Authorization": f"{Constants.DREMIO_TOKEN_PREFIX}{self.token}"}
            
            for attempt in range(self.config.timeout):
                status_url = f"{self.base_url}/api/v3/job/{job_id}"
                status_response = requests.get(status_url, headers=headers, timeout=30)
                status_response.raise_for_status()
                
                job_status = status_response.json().get("jobState")
                
                if job_status == "COMPLETED":
                    result_url = f"{self.base_url}/api/v3/job/{job_id}/results"
                    result_response = requests.get(result_url, headers=headers, timeout=30)
                    result_response.raise_for_status()
                    return result_response.json()
                    
                elif job_status in ["FAILED", "CANCELLED"]:
                    self.logger.error(f"Job failed with status: {job_status}")
                    return None
                
                time.sleep(1)
            
            self.logger.error(f"Timeout waiting for job completion: {job_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for job completion: {e}")
            return None


class IcebergTableManager:
    """Manage Iceberg table operations"""
    
    def __init__(self, dremio_client: DremioClient, logger: logging.Logger):
        self.dremio_client = dremio_client
        self.logger = logger
    
    def table_exists(self, table_name: str) -> bool:
        """
        Check if Iceberg table exists
        
        Args:
            table_name: Name of the table
            
        Returns:
            True if table exists, False otherwise
        """
        try:
            check_query = f'SELECT 1 FROM Iceberg.datalake.datalake."{table_name}" LIMIT 1'
            self.logger.debug(f"Checking if Iceberg table '{table_name}' exists")
            
            result = self.dremio_client.execute_query(check_query)
            exists = result is not None
            
            if exists:
                self.logger.info(f"Iceberg table '{table_name}' already exists")
            else:
                self.logger.info(f"Iceberg table '{table_name}' does not exist")
            
            return exists
            
        except Exception as e:
            self.logger.debug(f"Table existence check failed (table likely doesn't exist): {e}")
            return False
    
    def create_table(self, table_name: str) -> bool:
        """
        Create new Iceberg table
        
        Args:
            table_name: Name of the table to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            create_query = Constants.ICEBERG_TABLE_CREATE_TEMPLATE.format(table_name=table_name)
            
            self.logger.info(f"Creating Iceberg table '{table_name}'")
            result = self.dremio_client.execute_query(create_query)
            
            if result is not None:
                self.logger.info(f"Iceberg table '{table_name}' created successfully")
                return True
            else:
                self.logger.error(f"Failed to create Iceberg table '{table_name}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error creating Iceberg table: {e}")
            return False
    
    def refresh_metadata(self, machine_name: str, bucket_name: str = "datalake", 
                        folder_name: str = "dados") -> bool:
        """
        Refresh metadata for machine-specific datalake subfolder
        
        Args:
            machine_name: Machine name for subfolder
            bucket_name: MinIO bucket name
            folder_name: Folder within bucket
            
        Returns:
            True if successful, False otherwise
        """
        try:
            machine_folder_path = f"{folder_name}.{machine_name}"
            refresh_queries = [
                ## f'ALTER PDS REFRESH METADATA FOR TABLE {bucket_name}.{bucket_name}."{machine_folder_path}"',
                ## f'ALTER PDS REFRESH METADATA FOR TABLE {bucket_name}.{bucket_name}."{machine_folder_path}" FORCE UPDATE',
                f'ALTER TABLE {bucket_name}.{bucket_name}."{machine_folder_path}" REFRESH METADATA'
            ]
            
            self.logger.info(f"Refreshing metadata for machine subfolder: {machine_name}")
            
            for i, refresh_query in enumerate(refresh_queries, 1):
                try:
                    self.logger.debug(f"Attempting refresh method {i}/{len(refresh_queries)}")
                    result = self.dremio_client.execute_query(refresh_query)
                    
                    if result is not None:
                        self.logger.info(f"Metadata refresh successful using method {i}")
                        return True
                        
                except Exception as e:
                    self.logger.debug(f"Refresh method {i} failed: {e}")
                    continue
            
            self.logger.warning("All refresh methods failed, but continuing pipeline")
            return False
            
        except Exception as e:
            self.logger.warning(f"Error refreshing metadata: {e}")
            return False
    
    def insert_data(self, table_name: str, machine_name: str, unique_filename: str) -> bool:
        """
        Insert data from datalake parquet to Iceberg table
        
        Args:
            table_name: Target Iceberg table name
            machine_name: Machine name for source path
            unique_filename: Unique parquet filename
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Refresh metadata first
            self.logger.info("Refreshing datalake metadata before insert")
            self.refresh_metadata(machine_name)
            
            # Wait for metadata refresh to propagate
            time.sleep(Constants.METADATA_REFRESH_DELAY)
            
            # Verify source data
            self._verify_source_data(machine_name, unique_filename)
            
            # Execute insert
            insert_query = Constants.ICEBERG_INSERT_TEMPLATE.format(
                table_name=table_name,
                machine_name=machine_name,
                filename=unique_filename
            )
            
            self.logger.info(f"Inserting data into Iceberg table '{table_name}' from '{unique_filename}'")
            result = self.dremio_client.execute_query(insert_query)
            
            if result is not None:
                self.logger.info(f"Data inserted successfully into Iceberg table '{table_name}'")
                self._verify_insert_success(table_name)
                return True
            else:
                self.logger.error(f"Failed to insert data into Iceberg table '{table_name}'")
                return False
                
        except Exception as e:
            self.logger.error(f"Error inserting data to Iceberg table: {e}")
            return False
    
    def _verify_source_data(self, machine_name: str, unique_filename: str) -> None:
        """Verify source data before insert"""
        try:
            verify_query = (f'SELECT COUNT(*) as row_count, MIN("timestamp") as min_ts, '
                          f'MAX("timestamp") as max_ts FROM datalake.datalake.dados.'
                          f'"{machine_name}"."{unique_filename}"')
            
            result = self.dremio_client.execute_query(verify_query)
            
            if result and 'rows' in result and result['rows']:
                row_data = result['rows'][0]
                self.logger.info(f"Source data verification - Rows: {row_data.get('row_count', 'unknown')}, "
                               f"Time range: {row_data.get('min_ts', 'unknown')} to {row_data.get('max_ts', 'unknown')}")
        except Exception as e:
            self.logger.debug(f"Source data verification failed: {e}")
    
    def _verify_insert_success(self, table_name: str) -> None:
        """Verify insert was successful"""
        try:
            count_query = f'SELECT COUNT(*) as total_rows FROM Iceberg.datalake.datalake."{table_name}"'
            count_result = self.dremio_client.execute_query(count_query)
            
            if count_result and 'rows' in count_result and count_result['rows']:
                total_rows = count_result['rows'][0].get('total_rows', 'unknown')
                self.logger.info(f"Total rows in Iceberg table after insert: {total_rows}")
        except Exception as e:
            self.logger.debug(f"Insert verification failed: {e}")


class IcebergPipeline:
    """Main pipeline orchestrator"""
    
    def __init__(self, minio_config: MinIOConfig, dremio_config: DremioConfig, 
                 pipeline_config: PipelineConfig):
        self.minio_config = minio_config
        self.dremio_config = dremio_config
        self.pipeline_config = pipeline_config
        
        # Setup logger
        self.logger = LoggerSetup.setup_logger(__name__, pipeline_config.debug)
        
        # Initialize components
        self.csv_processor = CSVProcessor(self.logger)
        self.minio_client = MinIOClient(minio_config, self.logger)
        self.dremio_client = DremioClient(dremio_config, self.logger)
        self.iceberg_manager = IcebergTableManager(self.dremio_client, self.logger)
    
    def execute(self, csv_file_path: str) -> Dict[str, Any]:
        """
        Execute the complete CSV to Iceberg pipeline
        
        Args:
            csv_file_path: Path to CSV file to process
            
        Returns:
            Dictionary with execution results
        """
        results = {
            'success': False,
            'csv_file': csv_file_path,
            'machine_name': None,
            'parquet_file': None,
            'unique_filename': None,
            'uploaded_object': None,
            'iceberg_table': None,
            'data_inserted': False,
            'error': None
        }
        
        try:
            self.logger.info("Starting CSV to Iceberg Pipeline")
            
            # Step 1: Extract machine name
            self.logger.info("Step 1: Extracting machine name from CSV")
            machine_name = self.csv_processor.extract_machine_name(csv_file_path)
            results['machine_name'] = machine_name
            
            # Step 2: Generate unique filename
            self.logger.info("Step 2: Generating unique filename")
            unique_filename = self.csv_processor.generate_unique_filename(csv_file_path)
            results['unique_filename'] = unique_filename
            
            # Step 3: Convert CSV to Parquet
            self.logger.info("Step 3: Converting CSV to Parquet")
            parquet_file_path = self.csv_processor.process(
                csv_file_path, 
                compression=self.pipeline_config.compression
            )
            results['parquet_file'] = parquet_file_path
            
            # Step 4: Upload to MinIO
            self.logger.info("Step 4: Uploading to MinIO")
            uploaded_object = self.minio_client.upload_parquet(
                parquet_file_path, unique_filename, machine_name
            )
            
            if not uploaded_object:
                raise MinIOOperationException("Upload to MinIO failed")
            
            results['uploaded_object'] = uploaded_object
            
            # Step 5: Connect to Dremio
            self.logger.info("Step 5: Connecting to Dremio")
            if not self.dremio_client.authenticate():
                raise DremioOperationException("Dremio authentication failed")
            
            # Step 6: Verify datalake access
            self.logger.info("Step 6: Verifying datalake access")
            if not self._ping_datalake_table(machine_name, unique_filename):
                raise DremioOperationException("Datalake table not accessible")
            
            # Step 7: Ensure Iceberg table exists
            self.logger.info("Step 7: Ensuring Iceberg table exists")
            if not self.iceberg_manager.table_exists(machine_name):
                if not self.iceberg_manager.create_table(machine_name):
                    raise DremioOperationException("Failed to create Iceberg table")
            
            results['iceberg_table'] = machine_name
            
            # Step 8: Insert data to Iceberg
            self.logger.info("Step 8: Inserting data to Iceberg table")
            if not self.iceberg_manager.insert_data(machine_name, machine_name, unique_filename):
                raise DremioOperationException("Failed to insert data to Iceberg table")
            
            results['data_inserted'] = True
            
            # Step 9: Cleanup
            if not self.pipeline_config.keep_parquet_local:
                self.logger.info("Step 9: Cleaning up local files")
                os.remove(parquet_file_path)
                self.logger.info(f"Local file {parquet_file_path} removed")
            
            results['success'] = True
            self.logger.info("Pipeline completed successfully")
            
            return results
            
        except Exception as e:
            results['error'] = str(e)
            self.logger.error(f"Pipeline failed: {e}")
            return results
    
    def _ping_datalake_table(self, machine_name: str, unique_filename: str) -> bool:
        """Ping datalake table to verify accessibility"""
        try:
            ping_query = (f'SELECT * FROM datalake.datalake.dados."{machine_name}".'
                         f'"{unique_filename}" LIMIT 1')
            
            self.logger.debug("Pinging datalake table")
            result = self.dremio_client.execute_query(ping_query)
            
            if result is not None:
                self.logger.info("Datalake table ping successful")
                return True
            else:
                self.logger.error("Datalake table ping failed")
                return False
                
        except Exception as e:
            self.logger.error(f"Error pinging datalake table: {e}")
            return False


# ================================================================================
# PUBLIC API FUNCTIONS
# ================================================================================

def process_csv_to_iceberg_complete(csv_file_path: str,
                                   compression: str = 'snappy',
                                   bucket_name: str = "datalake",
                                   folder_name: str = "dados",
                                   minio_endpoint: str = "localhost:9000",
                                   access_key: str = "1RRRTXCQGD7SXKUFP7YB",
                                   secret_key: str = "1RRRTXCQGD7SXKUFP7YB",
                                   keep_parquet_local: bool = False,
                                   clear_existing_data: bool = False,
                                   dremio_host: str = "localhost",
                                   dremio_port: int = 9047,
                                   dremio_username: str = "caio.santos",
                                   dremio_password: str = "Inteli@123",
                                   debug: bool = False) -> Dict[str, Any]:
    """
    Complete pipeline: CSV -> Parquet -> Upload to MinIO -> Create Iceberg Table -> Insert Data
    
    This is the main public API function that maintains backward compatibility
    while using the new modular architecture internally.
    
    Args:
        csv_file_path: Path to input CSV file
        compression: Parquet compression algorithm
        bucket_name: MinIO bucket name
        folder_name: Folder within bucket
        minio_endpoint: MinIO server endpoint
        access_key: MinIO access key
        secret_key: MinIO secret key
        keep_parquet_local: Whether to keep local Parquet file after upload
        clear_existing_data: Whether to clear existing data (currently unused)
        dremio_host: Dremio server host
        dremio_port: Dremio server port
        dremio_username: Dremio username
        dremio_password: Dremio password
        debug: Enable debug logging
    
    Returns:
        Dictionary with execution results
    """
    # Create configuration objects
    minio_config = MinIOConfig(
        endpoint=minio_endpoint,
        access_key=access_key,
        secret_key=secret_key,
        bucket_name=bucket_name,
        folder_name=folder_name
    )
    
    dremio_config = DremioConfig(
        host=dremio_host,
        port=dremio_port,
        username=dremio_username,
        password=dremio_password
    )
    
    pipeline_config = PipelineConfig(
        compression=compression,
        keep_parquet_local=keep_parquet_local,
        clear_existing_data=clear_existing_data,
        debug=debug
    )
    
    # Create and execute pipeline
    pipeline = IcebergPipeline(minio_config, dremio_config, pipeline_config)
    return pipeline.execute(csv_file_path)


def main():
    """Main function for CLI usage"""
    # Default configuration
    csv_file_path = "test_data.csv"
    
    # MinIO configuration
    minio_config = {
        'minio_endpoint': "localhost:9000",
        'access_key': "VSXTQD0QTFTL1MGIH5Z7", ## Tudo bem subir porque é local
        'secret_key': "mcABEMcJHgHANeuGx305MoId1977HsvkBnyQVC8c" ## Tudo bem subir porque é local
    }
    
    # Dremio configuration
    dremio_config = {
        'dremio_host': "localhost",
        'dremio_port': 9047,
        'dremio_username': "caio.santos", ## Tudo bem subir porque é local
        'dremio_password': "Inteli@123" ## Tudo bem subir porque é local
    }
    
    # Validate input file
    if not os.path.exists(csv_file_path):
        print(f"Error: CSV file not found: {csv_file_path}")
        print("Please update the 'csv_file_path' variable with the correct path to your CSV file.")
        sys.exit(1)
    
    # Execute pipeline with debug enabled for CLI usage
    results = process_csv_to_iceberg_complete(
        csv_file_path=csv_file_path,
        debug=True,
        **minio_config,
        **dremio_config
    )
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()