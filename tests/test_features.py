import pandas as pd
import pytest
from basket_price_prediction.features import build_supervised

def monthly(prices, months=None, product='Arroz', supermarket='S1'):
    return pd.DataFrame({'supermarket':supermarket,'product':product,'brand':'A','quantity':1.,'month':pd.to_datetime(months or pd.date_range('2024-01-01',periods=len(prices),freq='MS')),'price_current':prices,'records':1})

@pytest.mark.parametrize('next_price,expected',[(101.99, 0), (102, 0), (102 + 1e-11, 0), (102.01, 1), (99, 0)])
def test_strict_target(next_price,expected):
    d,_=build_supervised(monthly([100,100,100,next_price]))
    assert len(d)==1 and d.iloc[0].target==expected

def test_missing_next_month_not_labelled():
    d,_=build_supervised(monthly([100,100,100,120],['2024-01-01','2024-02-01','2024-03-01','2024-05-01']))
    assert d.empty

def test_lags_rolling_and_no_future_leakage():
    base=monthly([10,20,30,40,50]); a,_=build_supervised(base); changed=base.copy(); changed.loc[3,'price_current']=400; b,_=build_supervised(changed)
    row=a.iloc[0]; assert (row.price_current,row.price_lag_1,row.price_lag_2)==(30,20,10)
    assert row.rolling_mean_3m==20 and row.rolling_min_3m==10 and row.rolling_max_3m==30
    assert a.iloc[0].rolling_std_3m==pytest.approx((200/3)**.5)
    cols=['price_current','price_lag_1','price_lag_2','rolling_mean_3m','rolling_std_3m','variation_1m']
    pd.testing.assert_series_equal(a.iloc[0][cols],b.iloc[0][cols])

def test_gaps_and_entities_separate():
    x=pd.concat([monthly([1,2,3,4]),monthly([100,200,300,400],product='Feijão'),monthly([5,6,7,8],supermarket='S2')])
    d,_=build_supervised(x)
    assert len(d)==3
    assert set(d.price_lag_1)=={2,200,6}
    gapped=monthly([1,2,3,4],['2024-01-01','2024-03-01','2024-04-01','2024-05-01'])
    assert build_supervised(gapped)[0].empty


def test_reports_loss_when_target_exists_but_history_has_gap():
    observations = monthly(
        [100, 101, 102, 105],
        ['2024-01-01', '2024-03-01', '2024-04-01', '2024-05-01'],
    )
    examples, report = build_supervised(observations)
    assert examples.empty
    assert report['with_target_without_history'] == 2
    assert report['without_next_calendar_month'] == 2
