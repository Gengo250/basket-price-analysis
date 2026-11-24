"""Limpeza explícita e mediana mensal por série de embalagem."""
import numpy as np
import pandas as pd
from .config import ENTITY

def _clean_observations(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df = raw.rename(columns={'Mes_Ano_Data':'month', 'Data_Coleta':'collection_date', 'Estab':'supermarket', 'Produto':'product', 'Marca':'brand', 'Preco':'price', 'Quantidade':'quantity', 'PPK':'ppk'}).copy()
    report = {'initial_records':len(df), 'missing_by_column':raw.isna().sum().astype(int).to_dict(), 'exact_duplicates':int(df.duplicated().sum())}
    df = df.drop_duplicates()
    for col in ['month','collection_date']:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df['month'] = df['month'].dt.to_period('M').dt.to_timestamp()
    for col in ['price','quantity','ppk']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    for col in ['product','supermarket','brand']:
        df[col] = df[col].astype('string').str.strip().replace('', pd.NA)
    invalid_month = df['month'].isna()
    invalid_entity = df[['product','supermarket']].isna().any(axis=1)
    invalid_price = ~np.isfinite(df['price']) | (df['price'] <= 0)
    invalid_quantity = ~np.isfinite(df['quantity']) | (df['quantity'] <= 0)
    wrong_collection = df['collection_date'].notna() & (df['collection_date'].dt.to_period('M') != df['month'].dt.to_period('M'))
    report['invalid_reasons_overlapping'] = {'month':int(invalid_month.sum()), 'entity':int(invalid_entity.sum()), 'price':int(invalid_price.sum()), 'quantity':int(invalid_quantity.sum()), 'collection_outside_reference_month':int(wrong_collection.sum())}
    df = df.loc[~(invalid_month | invalid_entity | invalid_price | invalid_quantity | wrong_collection)].copy()
    df['brand'] = df['brand'].fillna('(não informada)')
    report['valid_records_after_deduplication'] = len(df)
    report['ppk_discrepancies_over_0_01'] = int(((df['ppk'] - df['price']/df['quantity']).abs() > 0.01).sum())
    return df, report

def _aggregate_monthly(observations: pd.DataFrame) -> pd.DataFrame:
    return observations.groupby(ENTITY + ['month'], as_index=False, observed=True).agg(
        price_current=('price', 'median'), records=('price', 'size'),
    ).sort_values(ENTITY + ['month']).reset_index(drop=True)

def prepare_monthly(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    df, report = _clean_observations(raw)
    monthly = _aggregate_monthly(df)
    report.update(monthly_observations=len(monthly), monthly_series=int(monthly.groupby(ENTITY, observed=True).ngroups), aggregated_extra_records=int(len(df)-len(monthly)), missing_brand_label='(não informada)')
    return monthly, report

def diagnose_suspicious_prices(raw: pd.DataFrame) -> pd.DataFrame:
    """Sinaliza preços válidos pelo contexto, sem afetar a agregação mensal."""
    observations, _ = _clean_observations(raw)
    monthly = _aggregate_monthly(observations)
    keys = ENTITY + ['month']
    context = monthly[keys].copy()
    for offset, label in [(1, 'previous_month_median'), (-1, 'next_month_median')]:
        neighbors = monthly[keys + ['price_current']].rename(columns={'price_current': label})
        neighbors['month'] += pd.DateOffset(months=offset)
        context = context.merge(neighbors, on=keys, how='left', validate='one_to_one')

    # Cada outro supermercado contribui com uma mediana, independentemente do
    # número de coletas. Marca ausente aproxima comparabilidade, sem comprová-la.
    peer_keys = ['product', 'brand', 'quantity', 'month']
    peers = monthly[keys + ['price_current']].merge(
        monthly[peer_keys + ['supermarket']], on=peer_keys, suffixes=('_peer', ''),
    )
    peers = peers.loc[peers.supermarket.ne(peers.supermarket_peer)]
    peer_stats = peers.groupby(keys, as_index=False, observed=True).price_current.agg(
        peer_median='median', peer_stores='size',
    )
    context = context.merge(peer_stats, on=keys, how='left', validate='one_to_one')
    candidates = observations.reset_index(names='source_index').merge(
        context, on=keys, how='left', validate='many_to_one',
    )
    neighbors = ['previous_month_median', 'next_month_median']
    candidates['neighbor_median'] = candidates[neighbors].median(axis=1)
    candidates['peer_stores'] = candidates.peer_stores.fillna(0).astype(int)
    candidates['peer_median'] = candidates.peer_median.where(candidates.peer_stores.ge(2))
    candidates['ratio_to_neighbors'] = candidates.price / candidates.neighbor_median
    candidates['ratio_to_peers'] = candidates.price / candidates.peer_median

    # Fator simétrico de três, para triagem exploratória.
    neighbor_ratio = candidates.ratio_to_neighbors
    peer_ratio = candidates.ratio_to_peers
    neighbor_flag = neighbor_ratio.ge(3) | neighbor_ratio.le(1/3)
    peer_flag = peer_ratio.ge(3) | peer_ratio.le(1/3)
    candidates['reason'] = np.select(
        [neighbor_flag & peer_flag, neighbor_flag, peer_flag],
        ['Meses vizinhos e outros mercados', 'Meses vizinhos', 'Outros mercados'],
        default='',
    )
    ratios = candidates[['ratio_to_neighbors', 'ratio_to_peers']]
    severity = ratios.combine(1 / ratios, np.maximum).max(axis=1)
    return candidates.loc[neighbor_flag | peer_flag].assign(
        factor=severity,
    ).sort_values('factor', ascending=False)[
        ['source_index', *keys, 'price', 'collection_date', *neighbors,
         'neighbor_median', 'peer_stores', 'peer_median', 'ratio_to_neighbors',
         'ratio_to_peers', 'factor', 'reason']
    ].reset_index(drop=True)
