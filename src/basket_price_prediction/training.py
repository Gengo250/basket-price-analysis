"""Seleção exclusivamente na validação e ajuste final treino + validação."""
import json
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier
from .config import NUMERIC, CATEGORICAL, FEATURES, SEED, MIN_PRECISION, THRESHOLDS
from .evaluation import calculate_metrics

ESTIMATORS = {'logistic_regression': LogisticRegression, 'decision_tree': DecisionTreeClassifier, 'random_forest': RandomForestClassifier, 'gradient_boosting': HistGradientBoostingClassifier}
FIXED = {'logistic_regression': {'solver':'liblinear','max_iter':2000}, 'decision_tree': {'min_samples_leaf':50}, 'random_forest': {'n_estimators':300,'n_jobs':-1}, 'gradient_boosting': {'max_iter':300,'early_stopping':False}}
# Apenas o modelo linear depende de escala; árvores são invariantes a transformação monotônica.
SCALED = {'logistic_regression'}
GRID = {
    'logistic_regression': [{'C':c,'class_weight':w} for c in (.1,1.,10.) for w in (None,'balanced')],
    'decision_tree': [{'max_depth':d,'class_weight':w} for d in (3,5,10) for w in (None,'balanced')],
    'random_forest': [{'max_depth':d,'min_samples_leaf':l,'class_weight':w} for d in (None,10) for l in (5,20) for w in (None,'balanced_subsample')],
    'gradient_boosting': [{'learning_rate':r,'class_weight':w} for r in (.05,.1) for w in (None,'balanced')],
}

def make_pipeline(algorithm: str, params: dict) -> Pipeline:
    """Mesmo pré-processamento para todos os algoritmos; só a escala numérica difere."""
    numeric = StandardScaler() if algorithm in SCALED else 'passthrough'
    estimator = ESTIMATORS[algorithm](random_state=SEED, **FIXED[algorithm], **params)
    return Pipeline([('preprocess',ColumnTransformer([('num',numeric,NUMERIC), ('cat',OneHotEncoder(handle_unknown='ignore',sparse_output=False),CATEGORICAL)])), ('classifier',estimator)])

def rank_candidates(table: pd.DataFrame) -> pd.DataFrame:
    """Critério único: maior F1 com precisão mínima; desempate por precisão, limiar e nome."""
    acceptable = table[table.precision >= MIN_PRECISION]
    return (table if acceptable.empty else acceptable).sort_values(['f1','precision','threshold','algorithm'], ascending=[False,False,True,True], kind='stable')

def select_model(train: pd.DataFrame, validation: pd.DataFrame) -> tuple[Pipeline, dict, pd.DataFrame, pd.DataFrame]:
    """Compara quatro famílias de algoritmos usando somente treino e validação."""
    candidates=[]; models={}; probs={}
    for algorithm, grid in GRID.items():
        for params in grid:
            key=(algorithm, json.dumps(params,sort_keys=True,default=str))
            models[key]=make_pipeline(algorithm,params).fit(train[FEATURES],train.target)
            probs[key]=models[key].predict_proba(validation[FEATURES])[:,1]
            for threshold in THRESHOLDS:
                m=calculate_metrics(validation.target,probs[key],float(threshold))
                candidates.append({'algorithm':algorithm,'params':key[1],'threshold':round(float(threshold),2),'precision':m['precision'],'recall':m['recall'],'f1':m['f1'],'roc_auc':m['roc_auc'],'average_precision':m['average_precision']})
    table=pd.DataFrame(candidates)
    fallback=bool((table.precision>=MIN_PRECISION).sum()==0)
    best=rank_candidates(table).iloc[0]; key=(best.algorithm,best.params)
    selection={'algorithm':best.algorithm, 'params':json.loads(best.params), 'threshold':float(best.threshold), 'criterion':f'maior F1 na validação com precisão >= {MIN_PRECISION:.2f}; desempate por precisão, menor limiar e nome do algoritmo', 'searched_algorithms':sorted(GRID), 'fits':len(models), 'candidate_rows':len(table), 'fallback_no_candidate_met_precision':fallback}
    val=prediction_table(validation,probs[key],selection['threshold'])
    return models[key], selection, table, val

def best_per_algorithm(table: pd.DataFrame) -> pd.DataFrame:
    """Melhor candidato de cada família sob exatamente o mesmo critério de seleção."""
    return pd.DataFrame([rank_candidates(table[table.algorithm==name]).iloc[0] for name in sorted(table.algorithm.unique())]).reset_index(drop=True)

def prediction_table(data: pd.DataFrame, probability: np.ndarray, threshold: float) -> pd.DataFrame:
    cols=['supermarket','product','brand','quantity','month','target_month','price_current','variation_1m','actual_change','target']
    out=data[cols].copy(); out['probability']=probability; out['prediction']=(probability>=threshold).astype(int)
    return out
