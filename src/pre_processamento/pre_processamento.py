"""
Data preprocessing service for telemetry data pipeline.

This module implements a comprehensive data preprocessing pipeline that:
1. Extracts unprocessed data from Iceberg tables via Dremio
2. Applies ML preprocessing transformations
3. Stores processed data in PostgreSQL
4. Updates processing flags in the source tables

The service is designed with security, error handling, and observability in mind.
"""

import sys
import time
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
from contextlib import contextmanager

import pandas as pd
import requests
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sklearn.pipeline import Pipeline

from pipeline_functions import (
    AdjustTimestampColumn, RemoveDuplicatesAndNaN, TreatHighValues,
    FixBatteryAndAlternatorValues, PivotDataframe, RemoveZeroColumns,
    CreateMinutesRunningColumn, CreateVariationsColumns, GenericScaler,
    CreateHydraulicColumns, CreateMotorColumns
)

class PipelineException(Exception):
    """Base exception for pipeline operations."""
    pass


class AuthenticationError(PipelineException):
    """Exception raised when authentication fails."""
    pass


class DataProcessingError(PipelineException):
    """Exception raised during data processing operations."""
    pass


class DatabaseError(PipelineException):
    """Exception raised during database operations."""
    pass

@dataclass
class DremioConfig:
    """Configuration for Dremio connection.
    
    Attributes:
        host: Dremio server host
        port: Dremio server port
        username: Authentication username
        password: Authentication password
        timeout: Query timeout in seconds
    """
    host: str = "localhost"
    port: int = 9047
    username: str = "caio.santos"
    password: str = "Inteli@123"
    timeout: int = 3600

@dataclass
class DatabaseConfig:
    """Configuration for PostgreSQL database connection.
    
    Attributes:
        host: Database host
        port: Database port
        username: Database username
        password: Database password
        database: Database name
    """
    host: str = "localhost"
    port: int = 5435
    username: str = "admin"
    password: str = "admin123"
    database: str = "SyncTelemetry"

    def get_connection_string(self) -> str:
        """Generate SQLAlchemy connection string.
        
        Returns:
            Database connection string
        """
        return f"postgresql+psycopg2://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"

class Constants:
    """Application constants."""
    
    DREMIO_TOKEN_PREFIX = "_dremio"
    REQUEST_TIMEOUT = 30
    PAGINATION_LIMIT = 500

class LoggerSetup:
    """Setup and manage logging configuration."""
    
    @staticmethod
    def setup_logger(name: str = __name__, debug: bool = False) -> logging.Logger:
        """Setup logger with appropriate level and formatting.
        
        Args:
            name: Logger name
            debug: Enable debug logging
            
        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)
        
        if logger.handlers:
            return logger
            
        logger.setLevel(logging.DEBUG if debug else logging.INFO)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        return logger

class QueryEngine(ABC):
    """Abstract interface for query engines."""
    
    @abstractmethod
    def execute_query(self, sql: str) -> Optional[Dict[str, Any]]:
        """Execute SQL query.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Query result or None if failed
        """
        pass

class DatabaseManager:
    """Manages PostgreSQL database operations."""
    
    def __init__(self, config: DatabaseConfig, logger: logging.Logger):
        """Initialize database manager.
        
        Args:
            config: Database configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self._engine = None

    @property
    def engine(self):
        """Get database engine, creating if necessary.
        
        Returns:
            SQLAlchemy engine instance
        """
        if self._engine is None:
            try:
                self._engine = create_engine(
                    self.config.get_connection_string(),
                    pool_pre_ping=True,
                    pool_recycle=3600
                )
                self.logger.info("Database engine created successfully")
            except Exception as e:
                self.logger.error(f"Failed to create database engine: {e}")
                raise DatabaseError(f"Database engine creation failed: {e}") from e
        return self._engine

    @contextmanager
    def get_connection(self):
        """Get database connection context manager.
        
        Yields:
            Database connection
            
        Raises:
            DatabaseError: If connection fails
        """
        conn = None
        try:
            conn = self.engine.connect()
            yield conn
        except SQLAlchemyError as e:
            self.logger.error(f"Database connection error: {e}")
            raise DatabaseError(f"Database connection failed: {e}") from e
        finally:
            if conn:
                conn.close()

    def insert_processed_data(self, df: pd.DataFrame, table_name: str = 'processed_data') -> bool:
        """Insert processed data into PostgreSQL table.
        
        Args:
            df: DataFrame to insert
            table_name: Target table name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with self.get_connection() as conn:
                df.to_sql(
                    table_name,
                    conn,
                    if_exists='append',
                    index=False,
                    method='multi'
                )
                
            self.logger.info(f"Successfully inserted {len(df)} records into {table_name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error inserting data into {table_name}: {e}")
            return False

class DremioClient(QueryEngine):
    """Handle Dremio operations and queries."""
    
    def __init__(self, config: DremioConfig, logger: logging.Logger):
        """Initialize Dremio client.
        
        Args:
            config: Dremio configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger
        self.base_url = f"http://{config.host}:{config.port}"
        self.token: Optional[str] = None

    def authenticate(self) -> bool:
        """Authenticate with Dremio and obtain token.
        
        Returns:
            True if successful, False otherwise
            
        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            url = f"{self.base_url}/apiv2/login"
            payload = {
                "userName": self.config.username,
                "password": self.config.password
            }
            
            self.logger.info("Authenticating with Dremio")
            response = requests.post(
                url, 
                json=payload, 
                timeout=Constants.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            self.token = response.json().get("token")
            if not self.token:
                raise AuthenticationError("No token received from Dremio")
            
            self.logger.info("Dremio authentication successful")
            return True
            
        except requests.RequestException as e:
            self.logger.error(f"Dremio authentication failed: {e}")
            raise AuthenticationError(f"Authentication failed: {e}") from e

    def execute_query(self, sql: str) -> Optional[Dict[str, Any]]:
        """Execute SQL query in Dremio.
        
        Args:
            sql: SQL query to execute
            
        Returns:
            Query result or None if failed
        """
        try:
            if not self.token:
                raise AuthenticationError("Not authenticated. Please login first.")
            
            url = f"{self.base_url}/api/v3/sql"
            headers = {
                "Authorization": f"{Constants.DREMIO_TOKEN_PREFIX}{self.token}",
                "Content-Type": "application/json"
            }
            payload = {"sql": sql}
            
            self.logger.debug(f"Executing query: {sql[:100]}...")
            response = requests.post(
                url, 
                headers=headers, 
                json=payload, 
                timeout=Constants.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            job_id = response.json().get("id")
            if not job_id:
                raise DataProcessingError("No job ID received from Dremio")
            
            return self._wait_for_job_completion(job_id)
            
        except requests.RequestException as e:
            self.logger.error(f"Error executing query: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error during query execution: {e}")
            return None

    def _wait_for_job_completion(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Wait for job completion and return result.
        
        Args:
            job_id: Dremio job ID
            
        Returns:
            Job result or None if failed
        """
        try:
            headers = {"Authorization": f"{Constants.DREMIO_TOKEN_PREFIX}{self.token}"}
            
            for attempt in range(self.config.timeout):
                status_url = f"{self.base_url}/api/v3/job/{job_id}"
                status_response = requests.get(
                    status_url, 
                    headers=headers, 
                    timeout=Constants.REQUEST_TIMEOUT
                )
                status_response.raise_for_status()
                
                job_status = status_response.json().get("jobState")
                
                if job_status == "COMPLETED":
                    return self._get_all_results(job_id, headers)
                elif job_status in ["FAILED", "CANCELLED"]:
                    self.logger.error(f"Job failed with status: {job_status}")
                    return None
                
                time.sleep(1)
            
            self.logger.error(f"Timeout waiting for job completion: {job_id}")
            return None
            
        except Exception as e:
            self.logger.error(f"Error waiting for job completion: {e}")
            return None

    def _get_all_results(self, job_id: str, headers: dict) -> Optional[Dict[str, Any]]:
        """Get all results from a job with pagination.
        
        Args:
            job_id: Dremio job ID
            headers: Request headers with authorization
            
        Returns:
            Complete job result or None if failed
        """
        try:
            all_rows = []
            offset = 0
            columns = None
            
            while True:
                result_url = f"{self.base_url}/api/v3/job/{job_id}/results"
                params = {
                    "offset": offset,
                    "limit": Constants.PAGINATION_LIMIT
                }
                
                result_response = requests.get(
                    result_url, 
                    headers=headers, 
                    params=params, 
                    timeout=Constants.REQUEST_TIMEOUT
                )
                result_response.raise_for_status()
                result_data = result_response.json()
                
                if columns is None and 'columns' in result_data:
                    columns = result_data['columns']
                
                if 'rows' in result_data and result_data['rows']:
                    all_rows.extend(result_data['rows'])
                    offset += len(result_data['rows'])
                    
                    if len(result_data['rows']) < Constants.PAGINATION_LIMIT:
                        break
                else:
                    break
            
            final_result = {
                'rows': all_rows,
                'columns': columns if columns else []
            }
            
            self.logger.debug(f"Retrieved {len(all_rows)} total rows for job {job_id}")
            return final_result
            
        except Exception as e:
            self.logger.error(f"Error getting all results for job {job_id}: {e}")
            return None


class IcebergTableManager:
    """Manage Iceberg table operations."""
    
    def __init__(self, dremio_client: DremioClient, logger: logging.Logger):
        """Initialize Iceberg table manager.
        
        Args:
            dremio_client: Dremio client instance
            logger: Logger instance
        """
        self.dremio_client = dremio_client
        self.logger = logger

    def list_iceberg_tables(self) -> List[str]:
        """List all existing Iceberg tables in the datalake.
        
        Returns:
            List of table names
        """
        try:
            list_tables_query = "SHOW TABLES IN Iceberg.datalake.datalake"
            
            self.logger.info("Listing Iceberg tables in datalake")
            result = self.dremio_client.execute_query(list_tables_query)
            
            if result and 'rows' in result and result['rows']:
                table_names = []
                for row in result['rows']:
                    if 'TABLE_NAME' in row:
                        table_names.append(row['TABLE_NAME'])
                    elif 'table_name' in row:
                        table_names.append(row['table_name'])
                    elif isinstance(row, dict) and len(row) > 0:
                        table_names.append(list(row.values())[0])
                
                self.logger.info(f"Found {len(table_names)} Iceberg tables: {table_names}")
                return table_names
            else:
                self.logger.info("No Iceberg tables found or query failed")
                return []
                
        except Exception as e:
            self.logger.error(f"Error listing Iceberg tables: {e}")
            return []

    def get_unprocessed_data(self, table_name: str) -> Tuple[Optional[pd.DataFrame], Optional[str], Optional[str]]:
        """Fetch unprocessed data from a specific table.
        
        Args:
            table_name: Name of the Iceberg table
            
        Returns:
            Tuple of (dataframe, first_timestamp, last_timestamp)
        """
        try:
            self.logger.info(f"Fetching unprocessed data from table {table_name}")
            
            query = f"""
            SELECT * 
            FROM Iceberg.datalake.datalake."{table_name}" 
            WHERE "processed" = false
            ORDER BY "timestamp"
            """
            
            result = self.dremio_client.execute_query(query)

            if result and 'rows' in result and result['rows']:
                self.logger.debug(f"Result keys: {result.keys()}")
                self.logger.debug(f"Number of rows: {len(result['rows'])}")
                
                if 'columns' in result:
                    columns = [col['name'] for col in result['columns']]
                    self.logger.debug(f"Columns from metadata: {columns}")
                else:
                    columns = list(result['rows'][0].keys()) if result['rows'] else []
                    self.logger.debug(f"Columns from first row: {columns}")
                
                if result['rows']:
                    self.logger.debug(f"First row: {result['rows'][0]}")
                
                df = pd.DataFrame(result['rows'])
                self.logger.debug(f"DataFrame shape: {df.shape}")
                self.logger.debug(f"DataFrame columns: {list(df.columns)}")
                
                if df.empty:
                    self.logger.warning(f"DataFrame is empty for table {table_name}")
                    return None, None, None

                if 'timestamp' in df.columns:
                    first_timestamp = df['timestamp'].min()
                    last_timestamp = df['timestamp'].max()
                else:
                    self.logger.debug(f"Available columns: {list(df.columns)}")
                    first_timestamp = None
                    last_timestamp = None
                
                self.logger.info(f"Found {len(df)} unprocessed records in table {table_name}")
                self.logger.info(f"Time range: {first_timestamp} to {last_timestamp}")
                
                return df, first_timestamp, last_timestamp
            else:
                self.logger.info(f"No unprocessed data found in table {table_name}")
                return None, None, None
                
        except Exception as e:
            self.logger.error(f"Error fetching data from table {table_name}: {e}")
            return None, None, None

    def mark_data_as_processed(self, table_name: str, first_timestamp: str, last_timestamp: str) -> bool:
        """Mark data as processed in the Iceberg table.
        
        Args:
            table_name: Name of the table
            first_timestamp: Start timestamp
            last_timestamp: End timestamp
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.logger.info(f"Updating Iceberg table {table_name} to mark data as processed")
            
            update_query = f"""
            UPDATE Iceberg.datalake.datalake."{table_name}"
            SET "processed" = true
            WHERE "timestamp" >= '{first_timestamp}' 
            AND "timestamp" <= '{last_timestamp}'
            AND "processed" = false
            """
            
            result = self.dremio_client.execute_query(update_query)
            
            if result is not None:
                self.logger.info(f"Iceberg table {table_name} updated successfully")
                return True
            else:
                self.logger.error(f"Failed to update Iceberg table {table_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error updating Iceberg table {table_name}: {e}")
            return False


class DataPipelineProcessor:
    """Main data processing pipeline."""
    
    def __init__(self):
        """Initialize the data pipeline processor."""
        self.logger = LoggerSetup.setup_logger(__name__, debug=True)
        self.pipeline = self._create_preprocessing_pipeline()

    def _create_preprocessing_pipeline(self) -> Pipeline:
        """Create the preprocessing pipeline.
        
        Returns:
            Configured sklearn Pipeline
        """
        return Pipeline(steps=[
            ("adjust_timestamp", AdjustTimestampColumn()),
            ("remove_duplicates_and_nan", RemoveDuplicatesAndNaN()),
            ("treat_high_values", TreatHighValues()),
            ("fix_battery_and_alternator_values", FixBatteryAndAlternatorValues()),
            ("pivot_dataframe", PivotDataframe(resample_seconds=12)),
            ("remove_zero_columns", RemoveZeroColumns()),
            ("generic_scaler", GenericScaler(exclude_columns=["timestamp", "motor_pump"])),
            ("create_minutes_running_column", CreateMinutesRunningColumn()),
            ("create_variation_columns", CreateVariationsColumns(
                columns=["Bat_V", "Char_V", "Cool_T", "Eng_RPM", "Fuel_Con", "Fuel_L", "Oil_L", "Oil_P"]
            )),
            ("create_hydraulic_columns", CreateHydraulicColumns()),
            ("create_motor_columns", CreateMotorColumns())
        ])

    def process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process raw data through the pipeline.
        
        Args:
            df: Raw data DataFrame
            
        Returns:
            Processed DataFrame
            
        Raises:
            DataProcessingError: If processing fails
        """
        try:
            self.logger.info(f"Processing {len(df)} records through pipeline")
            processed_df = self.pipeline.fit_transform(df)
            self.logger.info(f"Processing completed, output has {len(processed_df)} records")
            return processed_df
            
        except Exception as e:
            self.logger.error(f"Error during data processing: {e}")
            raise DataProcessingError(f"Data processing failed: {e}") from e

    def run_processing_pipeline(self) -> List[str]:
        """Run the complete processing pipeline.
        
        Returns:
            List of processed table names
        """
        try:
            dremio_config = DremioConfig()
            database_config = DatabaseConfig()
            
            self.logger.info("Connecting to Dremio...")
            dremio_client = DremioClient(dremio_config, self.logger)
            
            if not dremio_client.authenticate():
                raise AuthenticationError("Failed to authenticate with Dremio")
            
            iceberg_manager = IcebergTableManager(dremio_client, self.logger)
            database_manager = DatabaseManager(database_config, self.logger)
            
            self.logger.info("Listing Iceberg tables...")
            table_names = iceberg_manager.list_iceberg_tables()
            
            processed_tables = []
            
            if table_names:
                self.logger.info(f"Found {len(table_names)} Iceberg tables to process")
                
                for table_name in table_names:
                    self.logger.info(f"Processing table: {table_name}")
                    
                    if self._process_table(table_name, iceberg_manager, database_manager):
                        processed_tables.append(table_name)
                        self.logger.info(f"Successfully processed table: {table_name}")
                    else:
                        self.logger.warning(f"Failed to process table: {table_name}")
            else:
                self.logger.info("No Iceberg tables found")
            
            self.logger.info(f"Processing completed. Processed {len(processed_tables)} tables successfully")
            return processed_tables
            
        except Exception as e:
            self.logger.error(f"Error in processing pipeline: {e}")
            return []

    def _process_table(self, table_name: str, iceberg_manager: IcebergTableManager, 
                      database_manager: DatabaseManager) -> bool:
        """Process a single table.
        
        Args:
            table_name: Name of the table to process
            iceberg_manager: Iceberg table manager
            database_manager: Database manager
            
        Returns:
            True if successful, False otherwise
        """
        try:
            df, first_timestamp, last_timestamp = iceberg_manager.get_unprocessed_data(table_name)
            
            if df is None or df.empty:
                self.logger.info(f"No unprocessed data found for table {table_name}")
                return True
            
            self.logger.info(f"Found {len(df)} records to process")
            self.logger.info(f"Time range: {first_timestamp} to {last_timestamp}")
            
            df_cleaned = df.drop(
                columns=['ingestion_timestamp', 'timestamp_date', 'processed'], 
                errors='ignore'
            )
            
            processed_df = self.process_data(df_cleaned)
            
            if database_manager.insert_processed_data(processed_df):
                self.logger.info(f"Data inserted successfully to PostgreSQL for table {table_name}")
                
                if iceberg_manager.mark_data_as_processed(table_name, first_timestamp, last_timestamp):
                    self.logger.info(f"Successfully marked data as processed for table {table_name}")
                    return True
                else:
                    self.logger.error(f"Failed to mark data as processed for table {table_name}")
                    return False
            else:
                self.logger.error(f"Failed to insert data to PostgreSQL for table {table_name}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error processing table {table_name}: {e}")
            return False


def main():
    """Main function to run the data preprocessing service."""
    processor = DataPipelineProcessor()
    
    try:
        processed_tables = processor.run_processing_pipeline()
        processor.logger.info(f"Pipeline execution completed. Processed tables: {processed_tables}")
        
    except Exception as e:
        processor.logger.error(f"Pipeline execution failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()