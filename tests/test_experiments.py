import joblib
import pandas as pd
from basket_price_prediction.experiments import MODEL_FILE, create_run, load_experiment, write_json
from basket_price_prediction.training import make_pipeline
from basket_price_prediction.config import FEATURES
from test_temporal_split import frame

def test_unique_directories_and_existing_results(tmp_path):
    a=create_run(tmp_path); (a/'marker').write_text('kept'); b=create_run(tmp_path)
    assert a!=b and (a/'marker').read_text()=='kept'

def test_reload_and_prediction_records(tmp_path):
    run=create_run(tmp_path)
    for folder in ('model','predictions','reports'): (run/folder).mkdir()
    data=frame('2025-01'); model=make_pipeline('logistic_regression',{'C':1.,'class_weight':None}).fit(data[FEATURES],data.target)
    from basket_price_prediction.training import prediction_table
    pred=prediction_table(data,model.predict_proba(data[FEATURES])[:,1],.5)
    joblib.dump(model,run/'model'/MODEL_FILE)
    for name in ('test','validation'): pred.to_csv(run/'predictions'/f'{name}_predictions.csv',index=False)
    pd.DataFrame([{'algorithm':'logistic_regression','f1_validation':.5,'f1_test':.5}]).to_csv(run/'reports'/'model_comparison.csv',index=False)
    pd.DataFrame([{'feature':'price_current','vif':1.}]).to_csv(run/'reports'/'collinearity.csv',index=False)
    for name,obj in [('manifest',{'status':'complete'}),('config',{'threshold':.5}),('metrics',{}),('data_summary',{})]: write_json(run/f'{name}.json',obj)
    loaded=load_experiment(run)
    assert loaded['test'].target.tolist()==data.target.tolist()
    assert loaded['model'].predict_proba(data[FEATURES])[:,1].tolist()==model.predict_proba(data[FEATURES])[:,1].tolist()
    assert loaded['comparison'].algorithm.tolist()==['logistic_regression']
