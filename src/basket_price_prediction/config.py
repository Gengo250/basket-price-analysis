"""Configuração explícita e limites por mês-alvo."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATASET = ROOT / 'data' / 'ICB_DADOS_2026.xlsx'
RESULTS = ROOT / 'runs' / 'results'
SEED = 42
SPLITS = {'train': ('2022-09', '2024-12'), 'validation': ('2025-01', '2025-08'), 'test': ('2025-09', '2026-08')}
ENTITY = ['supermarket', 'product', 'brand', 'quantity']
NUMERIC = ['price_current', 'price_lag_1', 'price_lag_2', 'variation_1m', 'variation_2m', 'rolling_mean_3m', 'rolling_std_3m', 'rolling_min_3m', 'rolling_max_3m', 'month_sin', 'month_cos']
CATEGORICAL = ['supermarket', 'product', 'brand', 'quantity']
FEATURES = NUMERIC + CATEGORICAL
