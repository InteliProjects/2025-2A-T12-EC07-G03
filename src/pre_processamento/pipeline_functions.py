import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.preprocessing import StandardScaler

def load_and_concat_data_from_csv(data: list) -> pd.DataFrame:
    """Load multiple CSV files, remove unnecessary rows, and concatenate them into a single DataFrame.

    This function reads multiple CSV files into pandas DataFrames, removes rows where
    the column "resource" has the value "lon", converts the "value" column to numeric,
    and then concatenates all the DataFrames into a single one.

    Args:
        data (list): A list of file paths (str) pointing to CSV files.

    Returns:
        pd.DataFrame: A concatenated DataFrame containing the cleaned data from all input files.

    Raises:
        FileNotFoundError: If any of the specified CSV files cannot be found.
        pd.errors.EmptyDataError: If a CSV file is empty.
        KeyError: If the column "resource" is not present in one of the CSV files."""
    dataframes = []
    for file in data:
        df = pd.read_csv(file)

        ## Esses dados "lon" são inuteis e não deveriam estar no dataset
        df = df[df["resource"] != "lon"]

        ## Converte a coluna value para numérica
        df["value"] = pd.to_numeric(df["value"], errors="coerce")

        dataframes.append(df)
    
    return pd.concat(dataframes)

class AdjustTimestampColumn(BaseEstimator, TransformerMixin):
    """Transformer that converts the 'timestamp' column to datetime format.

    This transformer is compatible with scikit-learn pipelines. It ensures that the
    'timestamp' column in the input DataFrame is converted to a pandas datetime object
    using the ISO8601 format.

    Methods:
        fit(X, y=None):
            Does nothing and returns self. Required for compatibility with
            scikit-learn pipelines.
        transform(X):
            Returns a copy of the DataFrame with the 'timestamp' column converted
            to datetime."""
    def fit(self, X: pd.DataFrame, y=None):
        return self
    
    def transform(self, X: pd.DataFrame):
        df = X.copy()
        df["timestamp"] = pd.to_datetime(df["timestamp"], format="ISO8601")
        return df

class RemoveDuplicatesAndNaN(BaseEstimator, TransformerMixin):
    """Transformer that fills missing values and removes duplicate rows.

    This transformer is designed to be used within scikit-learn pipelines.
    It fills missing values in each column with the column's mode (most frequent value)
    and then removes any duplicate rows from the DataFrame.

    Methods:
        fit(X, y=None):
            Returns self. Included for compatibility with scikit-learn pipelines.
        transform(X):
            Returns a cleaned DataFrame with missing values filled and duplicates removed."""
    def fit(self, X: pd.DataFrame, y=None):
        return self
    
    def transform(self, X: pd.DataFrame):
        df = X.copy()
        df_filled = df.apply(lambda col: col.fillna(col.mode().iloc[0]) if col.isnull().any() else col)
        df_cleaned = df_filled.drop_duplicates()
        return df_cleaned
    
class TreatHighValues(BaseEstimator, TransformerMixin):
    """Transformer that caps high values and creates a running status flag.

    This transformer is intended for use in scikit-learn pipelines. It checks the
    column value in the input DataFrame and applies the following rules:
    
    - If value exceeds max_limit, it is replaced with 0.
    - A new column running is created, set to 1 when value is within the limit
      and 0 otherwise.

    Args:
        max_limit (int, optional): Maximum allowed value for the value column.
            Values above this threshold are set to 0. Defaults to 20000.

    Methods:
        fit(X, y=None):
            Returns self. Required for scikit-learn pipeline compatibility.
        transform(X):
            Returns a DataFrame with capped values and a new running column."""
    def __init__(self, max_limit: int = 20000):
        self.max_limit = max_limit

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X:pd.DataFrame):
        df = X.copy()
        df['running'] = np.where(df['value'] > self.max_limit, 0, 1)
        df['value'] = np.where(df['value'] > self.max_limit, 0, df['value'])
        return df
    
class FixBatteryAndAlternatorValues(BaseEstimator, TransformerMixin):
    """Transformer that adjusts battery and alternator voltage values.

    This transformer is compatible with scikit-learn pipelines. It modifies the
    `value` column for specific resources:
    
    - For rows where `resource` is `"Bat_V"`, the `value` is divided by 10.
    - For rows where `resource` is `"Char_V"`, the `value` is divided by 10.

    Methods:
        fit(X, y=None):
            Returns self. Included for compatibility with scikit-learn pipelines.
        transform(X):
            Returns a DataFrame with adjusted values for `"Bat_V"` and `"Char_V"`."""
    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X:pd.DataFrame):
        df = X.copy()

        if "Bat_V" not in df.columns or "Char_V" not in df.columns:
            return df

        df.loc[df["resource"] == "Bat_V", "value"] = df.loc[df["resource"] == "Bat_V", "value"] / 10
        df.loc[df["resource"] == "Char_V", "value"] = df.loc[df["resource"] == "Char_V", "value"] / 10
        return df
    
class PivotDataframe(BaseEstimator, TransformerMixin):
    """Transformer that pivots, resamples, and cleans time-series data for each motor pump.

    This transformer is designed for use in scikit-learn pipelines. It performs the following steps:
    
    1. Checks that required columns ("timestamp", "motor_pump", "resource", "value", "running") are present.
    2. Pivots the DataFrame from long to wide format using "resource" as columns and "value" as values.
    3. Merges the "running" column back into the wide DataFrame.
    4. Sets "timestamp" as the index.
    5. Resamples the data for each "motor_pump" at a fixed interval (`resample_seconds`), filling missing values with forward fill.
    6. Rounds the "running" column to integer and ensures proper sorting and deduplication.

    Args:
        resample_seconds (int, optional): The interval in seconds for resampling the time-series data. Defaults to 60.

    Methods:
        fit(X, y=None):
            Returns self. Required for compatibility with scikit-learn pipelines.
        transform(X):
            Returns a cleaned, pivoted, and resampled DataFrame.
            
    Raises:
        ValueError: If any of the required columns are missing from the input DataFrame."""
    def __init__(self, resample_seconds: int = 60,  target_variable_name: str = "target"):
        self.resample_seconds = resample_seconds
        self.target_variable_name = target_variable_name

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X:pd.DataFrame):
        df = X.copy()

        required_cols = {"timestamp", "motor_pump", "resource", "value", "running"}
        missing = required_cols - set(df.columns)
        if missing:
            raise ValueError(f"PivotDataframe: missing columns: {missing}")


        df_wide = (
        df.pivot_table(
            index=["timestamp", "motor_pump"],
            columns="resource",
            values="value",
            aggfunc="mean"
        )
        .reset_index()
        )

        df_running = df[["timestamp", "motor_pump", "running", self.target_variable_name]] if self.target_variable_name in df.columns else df[["timestamp", "motor_pump", "running"]]
        df_wide = df_wide.merge(df_running, on=["timestamp", "motor_pump"], how="left")
        df_wide = df_wide.set_index("timestamp")

        resampled = []
        for pump_id, group in df_wide.groupby("motor_pump"):
            g = (
                group
                .resample(f"{self.resample_seconds}s")
                .mean(numeric_only=True)
                .ffill()
            )
            g["running"] = g["running"].round().astype(int)
            g["motor_pump"] = pump_id
            resampled.append(g)

        df_wide = pd.concat(resampled).reset_index()
        df_wide = df_wide.sort_values(["motor_pump", "timestamp"]).reset_index(drop=True)
        return df_wide.drop_duplicates().fillna(0)
        
class RemoveZeroColumns(BaseEstimator, TransformerMixin):
    """Transformer that removes columns containing only zeros.

    This transformer is designed to be used in scikit-learn pipelines. It identifies
    columns where all values are zero during fitting and removes them during transformation.

    Methods:
        fit(X, y=None):
            Identifies columns that contain only zeros and stores the ones to keep.
        transform(X):
            Returns a DataFrame with zero-only columns removed."""
    def __init__(self, target_variable_name: str = "target"):
        self.target_variable_name = target_variable_name

    def fit(self, X: pd.DataFrame, y=None):
        zero_columns = (X == 0).all()
        self.columns_to_keep = zero_columns[~zero_columns].index.tolist()
        if self.target_variable_name not in self.columns_to_keep and self.target_variable_name in X.columns:
            self.columns_to_keep.append(self.target_variable_name)
        return self

    def transform(self, X: pd.DataFrame):
        return X[self.columns_to_keep]
    
## Engenharia de Features

class CreateMinutesRunningColumn(BaseEstimator, TransformerMixin):
    """Transformer that creates a new feature representing the number of minutes 
    a motor pump has been running.

    This transformer calculates the time difference in minutes between consecutive 
    timestamps for each motor pump and assigns it to a new column `minutes_running` 
    whenever the motor pump is in a running state (`running == 1`). Otherwise, the 
    value is set to 0. Missing values are filled with 0.

    Attributes:
        None

    Methods:
        fit(X, y=None):
            Fits the transformer (no-op in this case).
        transform(X):
            Transforms the input DataFrame by adding the `minutes_running` column."""

    def fit(self, X: pd.DataFrame, y=None):
        return self

    def transform(self, X: pd.DataFrame):
        df_processed = X.copy()

        df_processed['time_diff_minutes'] = df_processed.groupby('motor_pump')['timestamp'].diff().dt.total_seconds() / 60
        df_processed['minutes_running'] = np.where(
            df_processed['running'] == 1, 
            df_processed['time_diff_minutes'], 
            0
        )
        df_processed['minutes_running'] = df_processed['minutes_running'].fillna(0)
        df_processed = df_processed.drop('time_diff_minutes', axis=1)

        return df_processed

class CreateVariationsColumns(BaseEstimator, TransformerMixin):
    """Transformer that creates variation columns (absolute and percentage) 
    for a list of numeric features.

    This transformer calculates:
      - Absolute variation between consecutive rows using the `.diff()` method.
      - Percentage variation between consecutive rows using the `.pct_change()` method.

    For each original column, two new columns are created:
      - `<col>_variation`: absolute difference between the current and previous value.
      - `<col>_variation_percentage`: percentage change from the previous value, 
        rounded to 3 decimal places.

    Missing values resulting from the first row (which has no previous value) 
    are filled with 0.

    Attributes:
        columns (list): List of column names to compute variations for.

    Methods:
        fit(X, y=None):
            Fits the transformer (no-op in this case).
        transform(X):
            Transforms the input DataFrame by adding variation columns."""
    
    def __init__(self, columns: list):
        self.columns = columns

    def fit(self, X: pd.DataFrame, y=None):
        return self
    
    def transform(self, X: pd.DataFrame):
        df = X.copy()

        ## Coluna de variação em unidade
        for col in self.columns:
            if col not in df.columns:
                continue
            new_col_name = f"{col}_variation"
            df[new_col_name] = df[col].diff()
            df[new_col_name] = df[new_col_name].fillna(0)
        
        ## Coluna de variação em porcentagem
        for col in self.columns:
            if col not in df.columns:
                continue
            new_col_name = f"{col}_variation_percentage"
            df[new_col_name] = round((df[col].pct_change() * 100), 3)
            df[new_col_name] = df[new_col_name].fillna(0)

        return df
    
class CreateHydraulicColumns(BaseEstimator, TransformerMixin):
    """Transformer that creates hydraulic performance-related features for pump systems.

    This transformer generates new columns based on suction (`Succao`) and 
    discharge (`Recalque`) pressures, along with engine RPM and running time:

      - `Hydraulic_Head`: The hydraulic head of the pump, calculated as 
        the difference between discharge and suction pressures.
      - `Head_per_RPM`: The hydraulic head normalized by engine RPM.
      - `Head_trend_per_minutes`: The change in hydraulic head over time, 
        calculated as the difference in hydraulic head divided by 
        `minutes_running`.

    Infinite values and missing values are replaced with 0.

    If either `Succao` or `Recalque` columns are missing, the DataFrame is 
    returned unchanged.

    Attributes:
        None

    Methods:
        fit(X, y=None):
            Fits the transformer (no-op in this case).
        transform(X):
            Transforms the input DataFrame by adding hydraulic-related columns."""
    
    def fit(self, X: pd.DataFrame, y=None):
        return self
    
    def transform(self, X: pd.DataFrame):
        df = X.copy()

        ## Succao = entrada da bomba
        ## Recalque = saida da bomba
        
        if "Recalque" not in df.columns or "Succao" not in df.columns:
            return df

        df["Hydraulic_Head"] = df["Recalque"] - df["Succao"] ## Carga hidraulica da bomba
        df["Head_per_RPM"] = df["Hydraulic_Head"] / df["Eng_RPM"]
        df["Head_trend_per_minutes"] = df["Hydraulic_Head"].diff() / df["minutes_running"]

        df = df.replace([float('inf'), float('-inf')], 0).fillna(0)

        return df
    
class CreateMotorColumns(BaseEstimator, TransformerMixin):
    """Transformer that creates motor performance-related features.

    This transformer generates new columns that relate engine behavior 
    (oil pressure, coolant temperature, fuel consumption) to RPM and 
    pump performance:

      - `OilP_per_RPM`: Oil pressure normalized by engine RPM, 
        indicating if oil pressure is consistent with engine speed.
      - `CoolT_per_RPM`: Coolant temperature normalized by engine RPM, 
        used as an indicator of thermal overload.
      - `Fuel_rate`: Fuel consumption rate, calculated as fuel consumed 
        per minute of operation.
      - `Fuel_efficiency`: Pump efficiency, calculated as hydraulic head 
        per fuel consumption rate (only created if `Hydraulic_Head` is available).

    Infinite values and missing values are replaced with 0.

    Attributes:
        None

    Methods:
        fit(X, y=None):
            Fits the transformer (no-op in this case).
        transform(X):
            Transforms the input DataFrame by adding motor-related columns."""
    
    def fit(self, X: pd.DataFrame, y=None):
        return self
    
    def transform(self, X: pd.DataFrame):
        df = X.copy()
        
        if "Oil_P" not in df.columns or "Cool_T" not in df.columns or "Fuel_Con" not in df.columns:
            return df
        
        df["OilP_per_RPM"] = df["Oil_P"] / df["Eng_RPM"] ## indica se pressão de óleo está compatível com a rotação
        df["CoolT_per_RPM"] = df["Cool_T"] / df["Eng_RPM"] ## indicador de sobrecarga térmica
        df["Fuel_rate"] = df["Fuel_Con"] / df["minutes_running"] ## taxa de consumo de combustível

        if "Hydraulic_Head" not in df.columns:
            return df

        df["Fuel_efficiency"] = df["Hydraulic_Head"] / df["Fuel_rate"] ## eficiência do conjunto  

        df = df.replace([float('inf'), float('-inf')], 0).fillna(0)

        return df
    
class GenericScaler(BaseEstimator, TransformerMixin):
    """Transformer that scales numeric features using StandardScaler, 
    excluding specified columns.

    This transformer applies standard scaling (z-score normalization) 
    to all numeric columns in the input DataFrame, except for those 
    explicitly listed in `exclude_columns`. The mean and standard 
    deviation are computed during `fit` and applied in `transform`.

    Attributes:
        exclude_columns (list): List of column names to exclude from scaling.
        scaler (StandardScaler): The internal scaler used for transformation.
        cols_to_scale (list): List of columns that will be scaled.

    Methods:
        fit(X, y=None):
            Fits the scaler to the numeric columns of the DataFrame 
            (excluding specified columns).
        transform(X):
            Transforms the DataFrame by scaling the selected columns."""
    
    def __init__(self, exclude_columns=None):
        self.exclude_columns = exclude_columns if exclude_columns is not None else []
        self.scaler = None
        self.cols_to_scale = None

    def fit(self, X, y=None):
        self.cols_to_scale = [c for c in X.columns if c not in self.exclude_columns]
        self.scaler = StandardScaler()
        self.scaler.fit(X[self.cols_to_scale])
        return self

    def transform(self, X):
        df = X.copy()
        df[self.cols_to_scale] = self.scaler.transform(df[self.cols_to_scale])
        return df

class CreateTargetVariable(BaseEstimator, TransformerMixin):
    def __init__(self, target_variable_name: str = "target"):
        self.target_variable_name = target_variable_name

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        df = X.copy()
        df[self.target_variable_name] = 1 if "type" in df.columns else 0
        return df
    
class RemoveInfValues(BaseEstimator, TransformerMixin):
    def fit(self, X, y=None):
        return self
    
    def transform(self, X):
        df = X.copy()
        df = df.replace([float('inf'), float('-inf')], 0)
        return df