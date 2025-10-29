# test_midrange.py
import numpy as np, pandas as pd
from model_inference_gru import GRUInference, EXPECTED_FEATURES, TIME_STEPS

mi = GRUInference()
sc = mi.scaler

mid = (sc.data_min_ + sc.data_max_) / 2.0
noise = 0.02 * (sc.data_max_ - sc.data_min_)

rows = TIME_STEPS
X = np.tile(mid, (rows, 1)) + np.random.randn(rows, len(mid)) * noise
df = pd.DataFrame(X, columns=EXPECTED_FEATURES)
df.insert(0, "timestamp", pd.date_range("2025-01-01", periods=rows, freq="min"))

print(mi.predict_health_indices(df))
