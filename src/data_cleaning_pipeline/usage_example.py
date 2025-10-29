from pipeline_functions import AdjustTimestampColumn, RemoveDuplicatesAndNaN, TreatHighValues, \
     FixBatteryAndAlternatorValues, PivotDataframe, RemoveZeroColumns, CreateMinutesRunningColumn, \
     CreateVariationsColumns, GenericScaler, CreateHydraulicColumns, CreateMotorColumns, \
     load_and_concat_data_from_csv
from sklearn.pipeline import Pipeline

pipeline = Pipeline(steps=[
    ## Data Cleaning
    ("adjust_timestamp", AdjustTimestampColumn()),
    ("remove_duplicates_and_nan", RemoveDuplicatesAndNaN()),
    ("treat_high_values", TreatHighValues()),
    ("fix_battery_and_alternator_values", FixBatteryAndAlternatorValues()),
    ("pivot_dataframe", PivotDataframe(resample_seconds=12)),
    ("remove_zero_columns", RemoveZeroColumns()),
    ("generic_scaler", GenericScaler(exclude_columns=["timestamp", "motor_pump"])), ## Após essa etapa, os valores não vão ficar "estranhos"
    ## Feature Engineering
    ("create_minutes_running_column", CreateMinutesRunningColumn()),
    ("create_variation_columns", CreateVariationsColumns(columns = ["Bat_V", "Char_V", "Cool_T", "Eng_RPM", "Fuel_Con", "Fuel_L", "Oil_L", "Oil_P"])),
    ("create_hydraulic_columns", CreateHydraulicColumns()),
    ("create_motor_columns", CreateMotorColumns())
])

df_itu_693_csv_locations = ["../data/full_history_ITU-693_2025-05-01_a_2025-06-08.csv", "../data/full_history_ITU-693_2025-06-08_a_2025-07-22.csv"]
df_itu_415_csv_locations = ["../data/full_history_ITU-415_2025-06-01_a_2025-06-17.csv", "../data/full_history_ITU-415_2025-06-17_a_2025-06-29.csv",
                            "../data/full_history_ITU-415_2025-06-29_a_2025-06-31.csv", "../data/full_history_ITU-415_2025-07-01_a_2025-07-17.csv"]

df_itu_693_raw = load_and_concat_data_from_csv(df_itu_693_csv_locations)
df_itu_693_processed = pipeline.fit_transform(df_itu_693_raw)

df_itu_693_processed.to_csv("itu_693_processed.csv", index=False)
print("df_itu_693_processed salvo no caminho itu_693_processed.csv")

df_itu_415_raw = load_and_concat_data_from_csv(df_itu_415_csv_locations)
df_itu_415_processed = pipeline.fit_transform(df_itu_415_raw)

df_itu_415_processed.to_csv("itu_415_processed.csv", index=False)
print("df_itu_415_processed salvo no caminho itu_415_processed.csv")
