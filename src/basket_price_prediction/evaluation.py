"""Métricas e tabelas, incluindo grupos com uma única classe."""
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, balanced_accuracy_score, confusion_matrix, roc_auc_score, average_precision_score, brier_score_loss, classification_report)
from .config import ENTITY, SEED, BOOTSTRAP_SAMPLES, CONFIDENCE_LEVEL, TARGET_THRESHOLD

INTERVAL_METRICS = ['precision','recall','f1','accuracy','balanced_accuracy','roc_auc','average_precision','brier_score']

from .config import INCREASE_THRESHOLD

def calculate_metrics(y, probability, threshold: float) -> dict:
    y = np.asarray(y, dtype=int); probability = np.asarray(probability, dtype=float)
    if y.size == 0 and probability.size == 0:
        return {
            'n': 0, 'positives': 0, 'negatives': 0, 'accuracy': None,
            'precision': None, 'recall': None, 'f1': None, 'balanced_accuracy': None,
            'roc_auc': None, 'average_precision': None, 'brier_score': None,
            'confusion_matrix': [[0, 0], [0, 0]], 'positive_prediction_rate': None,
        }
    pred = (probability >= threshold).astype(int)
    both = len(np.unique(y)) == 2
    return {'n':len(y), 'positives':int(y.sum()), 'negatives':int(len(y)-y.sum()), 'accuracy':float(accuracy_score(y,pred)), 'precision':float(precision_score(y,pred,zero_division=0)), 'recall':float(recall_score(y,pred,zero_division=0)) if y.sum() else None, 'f1':float(f1_score(y,pred,zero_division=0)) if y.sum() else None, 'balanced_accuracy':float(balanced_accuracy_score(y,pred)) if both else None, 'roc_auc':float(roc_auc_score(y,probability)) if both else None, 'average_precision':float(average_precision_score(y,probability)) if y.sum() else None, 'brier_score':float(brier_score_loss(y,probability)), 'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist(), 'positive_prediction_rate':float(pred.mean())}

def previous_increase_rule(data: pd.DataFrame) -> np.ndarray:
    """Referência sem treinamento: repete em t+1 a alta observada de t-1 para t."""
    return (data.variation_1m.gt(TARGET_THRESHOLD) & ~data.variation_1m.sub(TARGET_THRESHOLD).abs().le(1e-12)).to_numpy().astype(float)

def group_performance(predictions: pd.DataFrame, column: str, threshold: float) -> pd.DataFrame:
    rows=[]
    for group, subset in predictions.groupby(column, observed=True):
        metric=calculate_metrics(subset.target,subset.probability,threshold)
        rows.append({column:group, **metric, 'false_positives':metric['confusion_matrix'][0][1], 'false_negatives':metric['confusion_matrix'][1][0]})
    return pd.DataFrame(rows)

def bootstrap_intervals(predictions: pd.DataFrame, threshold: float, samples: int = BOOTSTRAP_SAMPLES, seed: int = SEED, level: float = CONFIDENCE_LEVEL) -> dict:
    """Reamostra séries inteiras: meses da mesma série não são observações independentes."""
    data=predictions.reset_index(drop=True)
    groups=list(data.groupby(ENTITY, observed=True, sort=True).indices.values())
    y=data.target.to_numpy(int); p=data.probability.to_numpy(float); rule=previous_increase_rule(data)
    rng=np.random.default_rng(seed); draws=[]
    for _ in range(samples):
        pick=np.concatenate([groups[i] for i in rng.integers(0,len(groups),len(groups))])
        if len(np.unique(y[pick])) < 2: continue
        model=calculate_metrics(y[pick],p[pick],threshold); reference=calculate_metrics(y[pick],rule[pick],.5)
        draws.append({**{k:model[k] for k in INTERVAL_METRICS}, 'f1_gain_over_previous_increase':model['f1']-reference['f1'], 'balanced_accuracy_gain_over_always_zero':model['balanced_accuracy']-.5})
    frame=pd.DataFrame(draws); low,high=(1-level)/2,(1+level)/2
    return {'samples':len(frame), 'requested_samples':samples, 'level':level, 'resampled_unit':ENTITY, 'series':len(groups), 'intervals':{c:{'low':float(frame[c].quantile(low)), 'median':float(frame[c].median()), 'high':float(frame[c].quantile(high))} for c in frame.columns}}

BANDS = [-np.inf,-.20,-.10,-.05,-.02,-1e-9,1e-9,.02,.05,.10,.20,np.inf]
BAND_LABELS = ['< -20%','-20 a -10%','-10 a -5%','-5 a -2%','-2 a 0%','preço inalterado','0 a 2%','2 a 5%','5 a 10%','10 a 20%','> 20%']

def risk_by_variation_band(data: pd.DataFrame) -> pd.DataFrame:
    """Risco observado por faixa da variação anterior; evidência da forma da relação."""
    band=pd.cut(data.variation_1m,BANDS,labels=BAND_LABELS)
    table=data.groupby(band,observed=False).agg(n=('target','size'),risk=('target','mean')).reset_index()
    return table.rename(columns={table.columns[0]:'band'}).dropna(subset=['risk'])

def collinearity_report(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """VIF por regressão de cada atributo sobre os demais, sem dependência adicional."""
    x=data[columns].to_numpy(float); x=(x-x.mean(0))/np.where(x.std(0)==0,1,x.std(0))
    correlation=np.abs(np.corrcoef(x,rowvar=False)); np.fill_diagonal(correlation,0)
    rows=[]
    for j,name in enumerate(columns):
        design=np.column_stack([np.ones(len(x)), np.delete(x,j,axis=1)])
        beta,*_=np.linalg.lstsq(design,x[:,j],rcond=None)
        explained=1-((x[:,j]-design@beta).var()/x[:,j].var())
        partner=int(np.argmax(correlation[j]))
        rows.append({'feature':name, 'r2_vs_others':float(explained), 'vif':float('inf') if explained>=1 else float(1/(1-explained)), 'max_abs_correlation':float(correlation[j,partner]), 'most_correlated_with':columns[partner]})
    return pd.DataFrame(rows).sort_values('vif',ascending=False).reset_index(drop=True)

def text_report(y, pred) -> str:
    event = f'Alta > {INCREASE_THRESHOLD:.0%}'
    return classification_report(y, pred, labels=[0, 1],
                                 target_names=[f'Sem {event.lower()}', event], zero_division=0)
