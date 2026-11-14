"""Métricas e tabelas, incluindo grupos com uma única classe."""
import numpy as np
import pandas as pd
from sklearn.metrics import (accuracy_score, precision_score, recall_score, f1_score, balanced_accuracy_score, confusion_matrix, roc_auc_score, average_precision_score, brier_score_loss, classification_report)

def calculate_metrics(y, probability, threshold: float) -> dict:
    y = np.asarray(y, dtype=int); probability = np.asarray(probability, dtype=float)
    pred = (probability >= threshold).astype(int)
    both = len(np.unique(y)) == 2
    return {'n':len(y), 'positives':int(y.sum()), 'negatives':int(len(y)-y.sum()), 'accuracy':float(accuracy_score(y,pred)), 'precision':float(precision_score(y,pred,zero_division=0)), 'recall':float(recall_score(y,pred,zero_division=0)) if y.sum() else None, 'f1':float(f1_score(y,pred,zero_division=0)) if y.sum() else None, 'balanced_accuracy':float(balanced_accuracy_score(y,pred)) if both else None, 'roc_auc':float(roc_auc_score(y,probability)) if both else None, 'average_precision':float(average_precision_score(y,probability)) if y.sum() else None, 'brier_score':float(brier_score_loss(y,probability)), 'confusion_matrix':confusion_matrix(y,pred,labels=[0,1]).tolist(), 'positive_prediction_rate':float(pred.mean())}

def group_performance(predictions: pd.DataFrame, column: str, threshold: float) -> pd.DataFrame:
    rows=[]
    for group, subset in predictions.groupby(column, observed=True):
        metric=calculate_metrics(subset.target,subset.probability,threshold)
        rows.append({column:group, **metric, 'false_positives':metric['confusion_matrix'][0][1], 'false_negatives':metric['confusion_matrix'][1][0]})
    return pd.DataFrame(rows)

def text_report(y, pred) -> str:
    return classification_report(y,pred,labels=[0,1],target_names=['Sem alta >2%', 'Alta >2%'],zero_division=0)
