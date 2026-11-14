import numpy as np
import pandas as pd
import pytest
from basket_price_prediction.features import temporal_split
from basket_price_prediction.training import make_pipeline, select_model
from basket_price_prediction.config import FEATURES, NUMERIC, CATEGORICAL

def frame(month, n=8):
    x=pd.DataFrame({k:np.arange(n,dtype=float) for k in NUMERIC})
    for k in CATEGORICAL: x[k]='known'
    x['target']=[0,1]*(n//2); x['target_month']=pd.Timestamp(month); x['month']=x.target_month-pd.offsets.MonthBegin(1); x['actual_change']=0.1
    return x

def test_splits_target_boundaries_and_overlap():
    d=pd.concat([frame('2024-12'),frame('2025-01'),frame('2025-09')])
    parts=temporal_split(d,{'train':('2024-12','2024-12'),'validation':('2025-01','2025-08'),'test':('2025-09','2026-08')})
    assert [len(x) for x in parts.values()]==[8,8,8]
    with pytest.raises(ValueError): temporal_split(d,{'train':('2024-12','2025-01'),'validation':('2025-01','2025-08')})
    with pytest.raises(ValueError): temporal_split(d,{'train':('2025-09','2025-09'),'test':('2024-12','2024-12')})

def test_encoder_and_scaler_fit_only_training():
    train=frame('2024-12'); test=frame('2025-09'); test['product']='unseen'; test['price_current']=99999
    model=make_pipeline(1,None).fit(train[FEATURES],train.target)
    assert model.named_steps['preprocess'].named_transformers_['num'].mean_[0]==train.price_current.mean()
    assert 'unseen' not in model.named_steps['preprocess'].named_transformers_['cat'].categories_[1]
    assert len(model.predict_proba(test[FEATURES]))==len(test)

def test_selection_api_never_accepts_test_data():
    import inspect
    assert list(inspect.signature(select_model).parameters)==['train','validation']
