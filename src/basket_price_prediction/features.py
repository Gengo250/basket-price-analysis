"""Apenas preços de t, t-1 e t-2 consecutivos entram nos preditores."""
import numpy as np
import pandas as pd
from .config import ENTITY, FEATURES, INCREASE_THRESHOLD, INCREASE_TOLERANCE

def is_price_increase(change: pd.Series) -> pd.Series:
    """Identifica altas que excedem o limite fora da tolerância numérica."""
    return change.gt(INCREASE_THRESHOLD) & ~np.isclose(
        change, INCREASE_THRESHOLD, rtol=0, atol=INCREASE_TOLERANCE,
    )

def build_supervised(monthly: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    d = monthly.sort_values(ENTITY+['month']).copy()
    g = d.groupby(ENTITY, sort=False, observed=True)
    for lag in (1,2):
        prev_month = g['month'].shift(lag)
        continuous = (d['month'].dt.to_period('M').astype('int64') - prev_month.dt.to_period('M').astype('int64')) == lag
        d[f'price_lag_{lag}'] = g['price_current'].shift(lag).where(continuous)
    # Duas diferenças de calendário garantem t-1 e t-2, não observações anteriores arbitrárias.
    d['variation_1m'] = d.price_current / d.price_lag_1 - 1
    d['variation_2m'] = d.price_current / d.price_lag_2 - 1
    w = d[['price_current','price_lag_1','price_lag_2']]
    d['rolling_mean_3m'] = w.mean(axis=1, skipna=False)
    d['rolling_std_3m'] = w.std(axis=1, ddof=0, skipna=False)
    d['rolling_min_3m'] = w.min(axis=1, skipna=False)
    d['rolling_max_3m'] = w.max(axis=1, skipna=False)
    d['month_sin'] = np.sin(2*np.pi*d.month.dt.month/12)
    d['month_cos'] = np.cos(2*np.pi*d.month.dt.month/12)
    future_month = g['month'].shift(-1)
    consecutive = (future_month.dt.to_period('M').astype('int64') - d.month.dt.to_period('M').astype('int64')) == 1
    future_price = g['price_current'].shift(-1).where(consecutive)
    d['target_month'] = future_month.where(consecutive)
    d['actual_change'] = future_price/d.price_current-1
    # Comparação monetária tolerante ao erro de ponto flutuante: exatamente 2% é classe zero.
    d['target'] = pd.Series(pd.NA, index=d.index, dtype='Int64')
    valid = d.actual_change.notna()
    d.loc[valid,'target'] = is_price_increase(d.loc[valid, 'actual_change']).astype(int)
    history = d[['price_lag_1','price_lag_2']].notna().all(axis=1)
    report = {'monthly_observations':len(d), 'without_next_calendar_month':int((~valid).sum()), 'with_target':int(valid.sum()), 'with_target_without_history':int((valid & ~history).sum()), 'eligible':int((valid & history).sum())}
    out = d.loc[valid & history].copy()
    out['target'] = out.target.astype(int)
    out['quantity'] = out['quantity'].map(lambda x: f'{x:g}')
    assert out[FEATURES].notna().all().all()
    return out.reset_index(drop=True), report

def temporal_split(data: pd.DataFrame, boundaries: dict) -> dict[str, pd.DataFrame]:
    result = {}
    for name, (start, end) in boundaries.items():
        mask = data.target_month.between(pd.Timestamp(start), pd.Timestamp(end))
        result[name] = data.loc[mask].copy()
    sets = [set(x.target_month.unique()) for x in result.values()]
    if any(sets[i] & sets[j] for i in range(len(sets)) for j in range(i+1,len(sets))):
        raise ValueError('Períodos-alvo sobrepostos')
    if any(x.empty for x in result.values()):
        raise ValueError('Partição vazia: verifique cobertura temporal')
    if any(result[a].target_month.max() >= result[b].target_month.min() for a, b in zip(result, list(result)[1:])):
        raise ValueError('Partições não estão em ordem cronológica')
    return result
