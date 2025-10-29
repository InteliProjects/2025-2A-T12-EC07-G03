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
import re
from pathlib import Path
from variables import motor_pumps


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
    RAW_TABLE_NAME = 'raw_logs'
    
    # SQL Templates
    ICEBERG_TABLE_CREATE_PUMP_TEMPLATE = '''CREATE TABLE Iceberg.datalake.datalake."{table_name}" (
    "timestamp" VARCHAR,
    "ingestion_timestamp" VARCHAR,
    "timestamp_date" DATE,
    "motor_pump" VARCHAR,
    "resource" VARCHAR,
    "value" DOUBLE,
    "processed" BOOLEAN
)
PARTITION BY (MONTH("timestamp_date"))'''

    # raw logs contain timestamp, topic, payload; include timestamp_date for partitioning
    ICEBERG_TABLE_CREATE_RAW_LOG_TEMPLATE = '''CREATE TABLE Iceberg.datalake.datalake."{table_name}" (
    "timestamp" VARCHAR,
    "timestamp_date" DATE,
    "topic" VARCHAR,
    "payload" VARCHAR
)
PARTITION BY (MONTH("timestamp_date"))'''

    ICEBERG_INSERT_PUMP_TEMPLATE = '''INSERT INTO Iceberg.datalake.datalake."{table_name}"
SELECT
    CAST("timestamp" AS VARCHAR) AS "timestamp",
    CAST("ingestion_timestamp" AS VARCHAR) AS "ingestion_timestamp",
    CAST(SUBSTR(CAST("timestamp" AS VARCHAR), 1, 10) AS DATE) AS "timestamp_date",
    "motor_pump",
    "resource",
    CAST("value" AS DOUBLE) AS "value",
    CAST("processed" AS BOOLEAN) AS "processed"
FROM datalake.datalake.dados."{machine_name}"."{filename}";'''

    ICEBERG_INSERT_RAW_LOG_TEMPLATE = '''INSERT INTO Iceberg.datalake.datalake."{table_name}"
SELECT
    CAST("timestamp" as VARCHAR) AS "timestamp",
    CAST(SUBSTR(CAST("timestamp" as VARCHAR), 1, 10) AS DATE) AS "timestamp_date",
    CAST("topic" as VARCHAR) AS "topic",
    CAST("payload" as VARCHAR) AS "payload"
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

            # First attempt: read motor_pump column (expected for processed/pump files)
            try:
                df_mp = pd.read_csv(csv_file_path, usecols=['motor_pump'])
            except ValueError:
                # Column not present
                df_mp = None

            if df_mp is not None and not df_mp.empty:
                unique_machines = list(df_mp['motor_pump'].dropna().unique())
                if len(unique_machines) == 0:
                    # treat as missing and fall back
                    df_mp = None
                else:
                    # return list of machines found (may be single)
                    self.logger.info(f"Machine names extracted from 'motor_pump' column: {unique_machines}")
                    return unique_machines

            # Fallback: raw log files may not have motor_pump column. Try to extract from 'topic' column
            try:
                df_topic = pd.read_csv(csv_file_path, usecols=['topic'])
            except ValueError:
                df_topic = None

            if df_topic is None or df_topic.empty:
                raise CSVProcessingException("CSV file does not contain 'motor_pump' or 'topic' columns to determine machine name")

            # Search for known motor_pumps tokens in topic values first
            found = set()
            for t in df_topic['topic'].dropna().astype(str):
                # check explicit motor_pumps list
                for mp in motor_pumps:
                    if mp in t:
                        found.add(mp)
                # fallback regex: look for ITU-### style tokens
                match = re.search(r"(ITU-\d{2,6})", t)
                if match:
                    found.add(match.group(1))

            if len(found) == 0:
                raise CSVProcessingException(
                    "Could not determine machine name from 'topic' values. Ensure topics contain machine id or include motor_pump column."
                )

            machines = list(found)
            self.logger.info(f"Machine names extracted from 'topic' column: {machines}")
            return machines

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
                    # capture detailed job information to aid debugging
                    job_json = status_response.json()
                    # try to extract a useful message
                    failure_msg = None
                    if isinstance(job_json, dict):
                        # common fields that may contain failure info
                        failure_msg = job_json.get('failureInfo') or job_json.get('errorMessage') or job_json.get('message')
                    self.logger.error(f"Job failed with status: {job_status}; detail: {failure_msg}")
                    return {'status': job_status, 'job': job_json, 'message': str(failure_msg)}
                
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
    
    def create_table(self, table_name: str, is_raw: bool = False) -> bool:
        """
        Create new Iceberg table
        
        Args:
            table_name: Name of the table to create
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # choose template based on explicit flag first, fallback to name check
            if is_raw or re.search(r'raw', table_name, re.IGNORECASE):
                create_query = Constants.ICEBERG_TABLE_CREATE_RAW_LOG_TEMPLATE.format(table_name=table_name)
            else:
                create_query = Constants.ICEBERG_TABLE_CREATE_PUMP_TEMPLATE.format(table_name=table_name)

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
    
    def insert_data(self, table_name: str, machine_name: str, unique_filename: str, is_raw: bool = False) -> bool:
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
            # choose insert template based on explicit flag first, otherwise
            # check filename for 'raw' marker
            filename = unique_filename
            if is_raw or re.search(r'raw', filename, re.IGNORECASE):
                insert_query = Constants.ICEBERG_INSERT_RAW_LOG_TEMPLATE.format(
                    table_name=table_name,
                    machine_name=machine_name,
                    filename=filename
                )
            else:
                insert_query = Constants.ICEBERG_INSERT_PUMP_TEMPLATE.format(
                    table_name=table_name,
                    machine_name=machine_name,
                    filename=filename
                )
            
            self.logger.info(f"Inserting data into Iceberg table '{table_name}' from '{unique_filename}'")
            result = self.dremio_client.execute_query(insert_query)

            # If Dremio returned a structured failure (dict with status), propagate it
            if isinstance(result, dict) and result.get('status') in ['FAILED', 'CANCELLED']:
                self.logger.error(f"Dremio job failed for insert: {result.get('message')}")
                return result

            if result is not None:
                self.logger.info(f"Data inserted successfully into Iceberg table '{table_name}'")
                self._verify_insert_success(table_name)
                return True

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
    
    def execute(self, csv_file_path: str, is_raw: Optional[bool] = None) -> Dict[str, Any]:
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
            
            # Step 1: Extract machine name(s)
            self.logger.info("Step 1: Extracting machine name(s) from CSV")
            machines = self.csv_processor.extract_machine_name(csv_file_path)

            # Normalize machines into a list
            if isinstance(machines, (list, set, tuple)):
                machines_list = list(machines)
            else:
                machines_list = [machines]

            results['machine_name'] = machines_list if len(machines_list) > 1 else machines_list[0]

            # If multiple machines detected, create per-machine filtered CSVs and process each one
            import tempfile
            temp_dir = tempfile.mkdtemp(prefix='datalake_split_')
            per_machine_results = []

            # Pre-read original CSV once
            try:
                original_df = pd.read_csv(csv_file_path)
            except Exception:
                original_df = None

            # Determine file-type heuristics from original filename
            csv_basename = Path(csv_file_path).name
            if is_raw is None:
                if any(mp in csv_basename for mp in motor_pumps):
                    file_is_raw = False
                    self.logger.info(f"Detected pump file by machine id in filename: '{csv_basename}' -> using PUMP templates")
                elif re.search(r'raw', csv_basename, re.IGNORECASE):
                    file_is_raw = True
                    self.logger.info(f"Detected raw log by filename: '{csv_basename}' -> using RAW templates")
                else:
                    file_is_raw = False
                    self.logger.debug(f"Could not detect explicit type from filename '{csv_basename}'; defaulting to PUMP templates")
            else:
                file_is_raw = is_raw
                self.logger.info(f"is_raw explicitly provided={is_raw}; using that to choose templates")

            # Process each machine separately
            for machine in machines_list:
                self.logger.info(f"Processing machine: {machine}")

                # Create filtered CSV for this machine
                per_csv_name = f"{machine}_{Path(csv_file_path).name}"
                per_csv_path = os.path.join(temp_dir, per_csv_name)

                try:
                    if original_df is not None:
                        df = original_df.copy()
                        if 'motor_pump' in df.columns:
                            filtered = df[df['motor_pump'] == machine]
                        elif 'topic' in df.columns:
                            filtered = df[df['topic'].astype(str).str.contains(re.escape(machine))]
                        else:
                            # If we cannot filter rows, fallback to using the whole file for each machine
                            filtered = df

                        if filtered is None or filtered.empty:
                            self.logger.warning(f"No rows found for machine {machine} in {csv_file_path}; skipping")
                            per_machine_results.append({'machine': machine, 'success': False, 'error': 'no_rows_for_machine'})
                            continue

                        filtered.to_csv(per_csv_path, index=False)
                    else:
                        # If pandas couldn't read original, just copy the file for each machine
                        import shutil
                        shutil.copy(csv_file_path, per_csv_path)

                    # Generate unique filename (prefix with machine to avoid collisions)
                    unique_filename = f"{machine}_{self.csv_processor.generate_unique_filename(per_csv_path)}"

                    # Convert per-machine CSV to Parquet
                    parquet_file_path = self.csv_processor.process(per_csv_path, compression=self.pipeline_config.compression)

                    # Upload to MinIO under machine folder
                    uploaded_object = self.minio_client.upload_parquet(parquet_file_path, unique_filename, machine)

                    if not uploaded_object:
                        self.logger.error(f"Upload failed for machine {machine}")
                        per_machine_results.append({'machine': machine, 'success': False, 'error': 'upload_failed'})
                        # cleanup local parquet if exists
                        try:
                            if not self.pipeline_config.keep_parquet_local and os.path.exists(parquet_file_path):
                                os.remove(parquet_file_path)
                        except Exception:
                            pass
                        continue

                    per_machine_results.append({
                        'machine': machine,
                        'per_csv': per_csv_path,
                        'parquet_file': parquet_file_path,
                        'unique_filename': unique_filename,
                        'uploaded_object': uploaded_object,
                        'success': True
                    })

                except Exception as e:
                    self.logger.error(f"Error processing machine {machine}: {e}")
                    per_machine_results.append({'machine': machine, 'success': False, 'error': str(e)})

            # Save per-machine results
            results['per_machine'] = per_machine_results

            # Step 5: Connect to Dremio (only once)
            self.logger.info("Step 5: Connecting to Dremio")
            if not self.dremio_client.authenticate():
                raise DremioOperationException("Dremio authentication failed")

            # Ensure required Iceberg tables exist: global raw table and per-pump tables
            try:
                # helper: ensure a table exists, create if missing and poll until available
                def ensure_table(name: str, is_raw_flag: bool) -> bool:
                    if self.iceberg_manager.table_exists(name):
                        return True
                    self.logger.info(f"Table '{name}' missing; attempting to create")
                    created = self.iceberg_manager.create_table(name, is_raw=is_raw_flag)
                    if not created:
                        self.logger.warning(f"Create table returned False for '{name}'")

                    # Poll for existence
                    for attempt in range(Constants.MAX_RETRIES):
                        if self.iceberg_manager.table_exists(name):
                            self.logger.info(f"Table '{name}' is now available")
                            return True
                        self.logger.debug(f"Waiting for table '{name}' to become available (attempt {attempt+1}/{Constants.MAX_RETRIES})")
                        time.sleep(1)

                    self.logger.error(f"Table '{name}' did not become available after {Constants.MAX_RETRIES} attempts")
                    return False

                # Create global raw table if missing (single table for raw logs)
                ensure_table(Constants.RAW_TABLE_NAME, is_raw_flag=True)

                # Create per-machine pump tables if missing
                for m in machines_list:
                    ensure_table(m, is_raw_flag=False)

            except Exception as e:
                self.logger.warning(f"Error while ensuring tables exist: {e}")

            # For each successful per-machine upload, ensure table exists and insert
            for pm in per_machine_results:
                if not pm.get('success'):
                    continue

                machine = pm['machine']
                unique_filename = pm['unique_filename']
                is_raw_used = file_is_raw

                # Choose target Iceberg table: if raw, use a dedicated global raw table to avoid schema clash
                target_table = Constants.RAW_TABLE_NAME if is_raw_used else machine
                pm['target_table'] = target_table

                # Verify datalake access (ping)
                if not self._ping_datalake_table(machine, unique_filename):
                    pm['success'] = False
                    pm['error'] = 'datalake_ping_failed'
                    continue

                # Ensure Iceberg table exists (use target_table)
                if not self.iceberg_manager.table_exists(target_table):
                    if not self.iceberg_manager.create_table(target_table, is_raw=is_raw_used):
                        pm['success'] = False
                        pm['error'] = 'create_table_failed'
                        continue

                # Insert data into target_table; machine stays as source folder name
                insert_result = self.iceberg_manager.insert_data(target_table, machine, unique_filename, is_raw=is_raw_used)
                if not insert_result:
                    pm['success'] = False
                    pm['error'] = 'insert_failed'
                    # try to surface more details if available from dremio client
                    pm['dremio_last'] = getattr(self.dremio_client, 'last_job_result', None)
                    continue
                # if insert_result is a dict with status indicating failure, capture message
                if isinstance(insert_result, dict) and insert_result.get('status') in ['FAILED', 'CANCELLED']:
                    pm['success'] = False
                    pm['error'] = insert_result.get('message') or 'insert_failed'
                    pm['dremio_job'] = insert_result.get('job')
                    continue

                pm['data_inserted'] = True
                pm['iceberg_table'] = target_table

                # Cleanup local parquet if configured
                try:
                    if not self.pipeline_config.keep_parquet_local and os.path.exists(pm.get('parquet_file', '')):
                        os.remove(pm.get('parquet_file'))
                except Exception:
                    pass

            # Aggregate final success
            all_success = all(p.get('success') and p.get('data_inserted') for p in per_machine_results if 'success' in p)
            results['success'] = all_success
            results['iceberg_table'] = [p['machine'] for p in per_machine_results if p.get('success')]

            # Collect errors if any
            errors = [ { 'machine': p.get('machine'), 'error': p.get('error') } for p in per_machine_results if not p.get('success') ]
            results['errors_by_machine'] = errors

            if all_success:
                self.logger.info("Pipeline completed successfully for all machines")
            else:
                self.logger.warning("Pipeline completed with errors for some machines")
            
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
                                   access_key: str = "OMCMU0X7B3K3A12M0DIV",
                                   secret_key: str = "7dyRZI+yyWTvx5uEiMflv0eHqjH75EufeGCIDSyu",
                                   keep_parquet_local: bool = False,
                                   clear_existing_data: bool = False,
                                   dremio_host: str = "localhost",
                                   dremio_port: int = 9047,
                                   dremio_username: str = "caio.santos",
                                   dremio_password: str = "Inteli@123",
                                   debug: bool = False,
                                   is_raw: Optional[bool] = None) -> Dict[str, Any]:
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
    return pipeline.execute(csv_file_path, is_raw=is_raw)


def save_to_data_lake(csv_file_path: str):
    """Main function for CLI usage"""
    # Default configuration
    # csv_file_path = "test_data.csv"
    
    # MinIO configuration
    minio_config = {
        'minio_endpoint': "localhost:9000",
        'access_key': "OMCMU0X7B3K3A12M0DIV", ## Tudo bem subir porque é local
        'secret_key': "7dyRZI+yyWTvx5uEiMflv0eHqjH75EufeGCIDSyu" ## Tudo bem subir porque é local
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
    save_to_data_lake()