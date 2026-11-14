import pandas as pd
from basket_price_prediction.preprocessing import prepare_monthly

def test_cleaning_and_median():
    raw=pd.DataFrame({'Mes_Ano_Data':['2024-01-01']*5,'Data_Coleta':[None]*5,'Estab':['S']*5,'Produto':['P']*5,'Marca':[None]*5,'Preco':[10.,10.,20.,30.,-1.],'Quantidade':[1.]*5,'PPK':[10.,10.,20.,30.,-1.]})
    monthly,report=prepare_monthly(raw)
    assert report['exact_duplicates']==1 and report['invalid_reasons_overlapping']['price']==1
    assert report['valid_records_after_deduplication']==3
    assert monthly.iloc[0].price_current==20 and monthly.iloc[0].records==3
    assert monthly.iloc[0].brand=='(não informada)'
