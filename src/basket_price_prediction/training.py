"""Seleção exclusivamente na validação e ajuste final treino + validação."""
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from .config import (
    NUMERIC, CATEGORICAL, FEATURES, SEED, LOGISTIC_MAX_ITER, LOGISTIC_SOLVER,
    C_CANDIDATES, CLASS_WEIGHT_CANDIDATES, ALERT_THRESHOLD_CANDIDATES, MIN_VALIDATION_PRECISION,
)
from .evaluation import calculate_metrics

def make_pipeline(c: float, weight: str | None) -> Pipeline:
    return Pipeline([('preprocess',ColumnTransformer([('num',StandardScaler(),NUMERIC), ('cat',OneHotEncoder(handle_unknown='ignore'),CATEGORICAL)])), ('classifier',LogisticRegression(C=c,class_weight=weight,max_iter=LOGISTIC_MAX_ITER,random_state=SEED,solver=LOGISTIC_SOLVER))])

def select_model(train: pd.DataFrame, validation: pd.DataFrame) -> tuple[Pipeline, dict, pd.DataFrame, pd.DataFrame]:
    """Seleciona pelo F1 na validação, aplicando o piso configurado de precisão."""
    candidates=[]; models={}; probs={}
    for c in C_CANDIDATES:
        for weight in CLASS_WEIGHT_CANDIDATES:
            model=make_pipeline(c,weight).fit(train[FEATURES],train.target)
            key=(c,weight); models[key]=model
            probs[key]=model.predict_proba(validation[FEATURES])[:,1]
            for threshold in ALERT_THRESHOLD_CANDIDATES:
                m=calculate_metrics(validation.target,probs[key],float(threshold))
                candidates.append({'C':c,'class_weight':weight,'threshold':threshold,'precision':m['precision'],'recall':m['recall'],'f1':m['f1']})
    table=pd.DataFrame(candidates)
    acceptable=table[table.precision >= MIN_VALIDATION_PRECISION]
    fallback=acceptable.empty
    ranked=(table if fallback else acceptable).sort_values(['f1','precision','threshold'],ascending=[False,False,True],kind='stable')
    best=ranked.iloc[0]; key=(float(best.C),best.class_weight)
    criterion = 'maior F1 na validação'
    if not fallback:
        criterion += f' com precisão >= {MIN_VALIDATION_PRECISION:g}'
    selection = {
        'C': key[0],
        'class_weight': key[1],
        'threshold': float(best.threshold),
        'criterion': criterion + '; desempate por precisão e menor limiar',
        'min_validation_precision': MIN_VALIDATION_PRECISION,
        'C_candidates': C_CANDIDATES,
        'class_weight_candidates': CLASS_WEIGHT_CANDIDATES,
        'threshold_candidates': ALERT_THRESHOLD_CANDIDATES,
        'fallback_no_candidate_met_precision': fallback,
    }
    val=prediction_table(validation,probs[key],selection['threshold'])
    return models[key], selection, table, val

def prediction_table(data: pd.DataFrame, probability: np.ndarray, threshold: float) -> pd.DataFrame:
    cols=['supermarket','product','brand','quantity','month','target_month','price_current','variation_1m','actual_change','target']
    out=data[cols].copy(); out['probability']=probability; out['prediction']=(probability>=threshold).astype(int)
    return out
