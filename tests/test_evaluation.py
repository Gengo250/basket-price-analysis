import numpy as np
import pandas as pd
from basket_price_prediction.evaluation import bootstrap_intervals, collinearity_report, previous_increase_rule
from basket_price_prediction.config import NUMERIC

def predictions(series=60, months=6, seed=0):
    rng=np.random.default_rng(seed); rows=[]
    for s in range(series):
        for m in range(months):
            target=int(rng.random()<.3)
            rows.append({'supermarket':f'S{s%5}','product':f'P{s%7}','brand':f'B{s}','quantity':'1','target':target,'probability':rng.uniform(.4,.9) if target else rng.uniform(.1,.6),'variation_1m':rng.normal(0,.05)})
    return pd.DataFrame(rows)

def test_interval_contains_point_estimate_and_is_reproducible():
    data=predictions()
    a=bootstrap_intervals(data,.5,samples=200)
    b=bootstrap_intervals(data,.5,samples=200)
    assert a==b
    for name in ('precision','recall','f1'):
        low,high=a['intervals'][name]['low'],a['intervals'][name]['high']
        assert low<=a['intervals'][name]['median']<=high and 0<=low<=high<=1

def test_series_are_resampled_as_blocks_not_rows():
    data=predictions()
    result=bootstrap_intervals(data,.5,samples=50)
    assert result['series']==data.groupby(['supermarket','product','brand','quantity']).ngroups
    assert result['resampled_unit']==['supermarket','product','brand','quantity']

def test_exact_linear_combination_is_flagged():
    rng=np.random.default_rng(1); n=300
    frame=pd.DataFrame({c:rng.normal(size=n) for c in NUMERIC})
    frame['rolling_mean_3m']=(frame.price_current+frame.price_lag_1+frame.price_lag_2)/3
    report=collinearity_report(frame,NUMERIC).set_index('feature')
    assert report.loc['rolling_mean_3m','vif']>1e6
    assert report.loc['month_sin','vif']<5

def test_previous_increase_rule_is_strict_about_two_percent():
    data=pd.DataFrame({'variation_1m':[.0201,.02,.019,-.5]})
    assert previous_increase_rule(data).tolist()==[1.,0.,0.,0.]

def test_risk_by_variation_band_separates_unchanged_prices():
    from basket_price_prediction.evaluation import risk_by_variation_band
    data=pd.DataFrame({'variation_1m':[-.30,-.30,0.,0.,0.,.03],'target':[1,1,0,0,0,1]})
    table=risk_by_variation_band(data).set_index('band')
    assert table.loc['< -20%','n']==2 and table.loc['< -20%','risk']==1.
    # Preço exatamente inalterado é faixa própria, não absorvida por "-2 a 0%" nem "0 a 2%".
    assert table.loc['preço inalterado','n']==3 and table.loc['preço inalterado','risk']==0.
    assert table.loc['2 a 5%','n']==1
