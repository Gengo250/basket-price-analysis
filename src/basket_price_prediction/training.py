"""Seleção exclusivamente na validação e ajuste final treino + validação."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .config import NUMERIC, CATEGORICAL, FEATURES, SEED
from .evaluation import calculate_metrics

def make_pipeline(c: float, weight: str | None) -> Pipeline:
    return Pipeline([('preprocess',ColumnTransformer([('num',StandardScaler(),NUMERIC), ('cat',OneHotEncoder(handle_unknown='ignore'),CATEGORICAL)])), ('classifier',LogisticRegression(C=c,class_weight=weight,max_iter=2000,random_state=SEED,solver='liblinear'))])

def select_model(train: pd.DataFrame, validation: pd.DataFrame) -> tuple[Pipeline, dict, pd.DataFrame, pd.DataFrame]:
    """Máximo F1 com precisão >= 0,35; desempate por precisão e limiar menor."""
    candidates=[]; models={}; probs={}
    for c in [0.1,1.0,10.0]:
        for weight in [None,'balanced']:
            model=make_pipeline(c,weight).fit(train[FEATURES],train.target)
            key=(c,weight); models[key]=model
            probs[key]=model.predict_proba(validation[FEATURES])[:,1]
            for threshold in np.arange(.10,.91,.05):
                m=calculate_metrics(validation.target,probs[key],float(threshold))
                candidates.append({'C':c,'class_weight':weight,'threshold':round(float(threshold),2),'precision':m['precision'],'recall':m['recall'],'f1':m['f1']})
    table=pd.DataFrame(candidates)
    acceptable=table[table.precision>=.35]
    fallback=acceptable.empty
    ranked=(table if fallback else acceptable).sort_values(['f1','precision','threshold'],ascending=[False,False,True],kind='stable')
    best=ranked.iloc[0]; key=(float(best.C),best.class_weight)
    selection={'C':key[0], 'class_weight':key[1], 'threshold':float(best.threshold), 'criterion':'maior F1 na validação com precisão >= 0,35; desempate por precisão e menor limiar', 'fallback_no_candidate_met_precision':fallback}
    val=prediction_table(validation,probs[key],selection['threshold'])
    return models[key], selection, table, val

def prediction_table(data: pd.DataFrame, probability: np.ndarray, threshold: float) -> pd.DataFrame:
    cols=['supermarket','product','brand','quantity','month','target_month','price_current','variation_1m','actual_change','target']
    out=data[cols].copy(); out['probability']=probability; out['prediction']=(probability>=threshold).astype(int)
    return out
