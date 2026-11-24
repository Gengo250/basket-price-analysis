"""Configuração explícita e limites por mês-alvo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / 'data' / 'ICB_DADOS_2026.xlsx'
RESULTS = ROOT / 'runs' / 'results'
SEED = 42
INCREASE_THRESHOLD = 0.02
INCREASE_TOLERANCE = 1e-12
MIN_VALIDATION_PRECISION = 0.35
C_CANDIDATES = (0.1, 1.0, 10.0)
CLASS_WEIGHT_CANDIDATES = (None, 'balanced')
ALERT_THRESHOLD_CANDIDATES = tuple(percent / 100 for percent in range(10, 91, 5))
LOGISTIC_SOLVER = 'liblinear'
LOGISTIC_MAX_ITER = 2000
SPLITS = {'train': ('2022-09', '2024-12'), 'validation': ('2025-01', '2025-08'), 'test': ('2025-09', '2026-08')}
ENTITY = ['supermarket', 'product', 'brand', 'quantity']
NUMERIC = ['price_current', 'price_lag_1', 'price_lag_2', 'variation_1m', 'variation_2m', 'rolling_mean_3m', 'rolling_std_3m', 'rolling_min_3m', 'rolling_max_3m', 'month_sin', 'month_cos']
CATEGORICAL = ['supermarket', 'product', 'brand', 'quantity']
FEATURES = NUMERIC + CATEGORICAL
