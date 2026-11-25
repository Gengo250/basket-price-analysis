import pandas as pd
import pytest
from sklearn.preprocessing import StandardScaler
from basket_price_prediction.training import GRID, make_pipeline, rank_candidates, best_per_algorithm
from basket_price_prediction.config import FEATURES, MIN_PRECISION
from test_temporal_split import frame

@pytest.mark.parametrize('algorithm', sorted(GRID))
def test_every_family_fits_and_predicts_probabilities(algorithm):
    data=frame('2025-01', n=40)
    model=make_pipeline(algorithm,GRID[algorithm][0]).fit(data[FEATURES],data.target)
    probability=model.predict_proba(data[FEATURES])[:,1]
    assert len(probability)==len(data) and probability.min()>=0 and probability.max()<=1

def test_only_linear_family_is_scaled():
    numeric=lambda a: make_pipeline(a,GRID[a][0]).named_steps['preprocess'].transformers[0][1]
    assert isinstance(numeric('logistic_regression'),StandardScaler)
    assert all(numeric(a)=='passthrough' for a in GRID if a!='logistic_regression')

def candidates():
    return pd.DataFrame([
        {'algorithm':'random_forest','params':'{}','threshold':.30,'precision':.90,'recall':.10,'f1':.18,'roc_auc':.7,'average_precision':.5},
        {'algorithm':'logistic_regression','params':'{}','threshold':.25,'precision':.40,'recall':.70,'f1':.50,'roc_auc':.7,'average_precision':.5},
        {'algorithm':'decision_tree','params':'{}','threshold':.10,'precision':.20,'recall':.99,'f1':.95,'roc_auc':.6,'average_precision':.4},
    ])

def test_minimum_precision_filters_before_maximising_f1():
    # O F1 de 0,95 vem de precisão 0,20 e deve ser descartado pelo piso de precisão.
    best=rank_candidates(candidates()).iloc[0]
    assert best.algorithm=='logistic_regression' and best.precision>=MIN_PRECISION

def test_fallback_keeps_every_candidate_when_none_reaches_precision():
    weak=candidates().assign(precision=.10)
    assert rank_candidates(weak).iloc[0].f1==.95

def test_comparison_keeps_one_row_per_family_under_the_same_criterion():
    ranking=best_per_algorithm(candidates())
    assert ranking.algorithm.tolist()==['decision_tree','logistic_regression','random_forest']
    assert ranking.set_index('algorithm').loc['decision_tree'].f1==.95
