"""Limpeza explícita e mediana mensal por série de embalagem."""
import numpy as np
import pandas as pd
from .config import ENTITY

def prepare_monthly(raw: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
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
    monthly = df.groupby(ENTITY + ['month'], as_index=False, observed=True).agg(price_current=('price','median'), records=('price','size'))
    report.update(monthly_observations=len(monthly), monthly_series=int(monthly.groupby(ENTITY, observed=True).ngroups), aggregated_extra_records=int(len(df)-len(monthly)), missing_brand_label='(não informada)')
    return monthly.sort_values(ENTITY+['month']).reset_index(drop=True), report
