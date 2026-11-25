"""Gráficos de avaliação gerados exclusivamente a partir de predições salvas."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.inspection import permutation_importance
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve, auc
from .config import FEATURES, INCREASE_THRESHOLD, SEED
from .evaluation import group_performance, risk_by_variation_band

sns.set_theme(style='whitegrid')
def save_figures(pred, model, threshold: float, directory: Path, features=None, ranking=None, intervals=None, profile=None) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    def save(name):
        plt.tight_layout(); plt.savefig(directory/name,dpi=130,bbox_inches='tight'); plt.close()
    y=pred.target; p=pred.probability
    plt.figure(figsize=(6, 4))
    sns.heatmap(
        confusion_matrix(y, p >= threshold, labels=[0, 1]),
        annot=True, fmt='d', cmap='Blues',
        xticklabels=['Sem alerta', 'Com alerta'],
        yticklabels=[f'Sem alta > {INCREASE_THRESHOLD:.0%}', f'Com alta > {INCREASE_THRESHOLD:.0%}'],
    )
    plt.yticks(rotation=0)
    plt.xlabel('Previsão')
    plt.ylabel('Observação')
    plt.title('Matriz de confusão no teste')
    save('confusion_matrix.png')
    precision,recall,thresholds=precision_recall_curve(y,p)
    plt.figure(); plt.plot(recall,precision); plt.axhline(y.mean(),ls='--',color='gray',label='Prevalência'); plt.xlabel('Recall'); plt.ylabel('Precisão'); plt.title('Curva precisão–recall'); plt.legend(); save('precision_recall_curve.png')
    if y.nunique()==2:
        fpr,tpr,_=roc_curve(y,p); plt.figure(); plt.plot(fpr,tpr,label=f'AUC = {auc(fpr,tpr):.3f}'); plt.plot([0,1],[0,1],'--',color='gray'); plt.xlabel('Taxa de falsos positivos'); plt.ylabel('Recall'); plt.title('Curva ROC'); plt.legend(); save('roc_curve.png')
    plt.figure(); sns.histplot(data=pred,x='probability',hue='target',stat='density',common_norm=False,bins=25,element='step'); plt.xlabel(f'Probabilidade prevista de alta > {INCREASE_THRESHOLD:.0%}'); plt.ylabel('Densidade'); plt.title('Probabilidades por classe real'); save('probability_distribution.png')
    observed,mean=calibration_curve(y,p,n_bins=10,strategy='quantile'); plt.figure(); plt.plot(mean,observed,'o-'); plt.plot([0,1],[0,1],'--',color='gray'); plt.xlabel('Probabilidade média prevista'); plt.ylabel('Frequência observada'); plt.title('Calibração por decis'); save('calibration_curve.png')
    plt.figure(); plt.plot(thresholds,precision[:-1],label='Precisão'); plt.plot(thresholds,recall[:-1],label='Recall'); plt.axvline(threshold,color='gray',ls='--',label='Limiar escolhido'); plt.xlabel('Limiar de probabilidade'); plt.ylabel('Métrica'); plt.title('Precisão e recall por limiar'); plt.legend(); save('threshold_tradeoff.png')
    monthly=group_performance(pred,'target_month',threshold).sort_values('target_month'); plt.figure(figsize=(10,4)); plt.plot(monthly.target_month.astype(str),monthly.precision,'o-',label='Precisão'); plt.plot(monthly.target_month.astype(str),monthly.recall,'o-',label='Recall'); plt.plot(monthly.target_month.astype(str),monthly.f1,'o-',label='F1'); plt.xticks(rotation=45,ha='right'); plt.ylim(0,1); plt.xlabel('Mês-alvo'); plt.ylabel('Métricas do classificador (0–1)'); plt.title('Desempenho mensal no teste'); plt.legend(); save('monthly_performance.png')
    months = monthly.target_month.dt.strftime('%m/%Y')
    fig, ax = plt.subplots(figsize=(11, 4.5))
    totals = ax.bar(months, monthly.n, color='#dce6ef', label='Observações no teste')
    increases = ax.bar(months, monthly.positives, color='#245782', label=f'Altas observadas acima de {INCREASE_THRESHOLD:.0%}')
    ax.bar_label(totals, padding=3, fontsize=8)
    ax.bar_label(increases, label_type='center', color='white', fontsize=8)
    ax.set_ylim(0, monthly.n.max() * 1.15)
    ax.set(xlabel='Mês-alvo', ylabel='Número de observações', title='Altas observadas por mês no teste')
    ax.tick_params(axis='x', labelrotation=45)
    ax.legend()
    save('monthly_observed_increases.png')

    for col,label in [('product','produto'),('supermarket','supermercado')]:
        table=group_performance(pred,col,threshold); table=table[(table.n>=30) & table.recall.notna()].sort_values('n',ascending=False).head(20).sort_values('recall')
        labels = [
            f'{row[col]} (n={row.n}, altas={row.positives})'
            for _, row in table.iterrows()
        ]
        plt.figure(figsize=(10, max(4, len(table) * .32)))
        plt.barh(labels, table.recall.fillna(0))
        plt.xlim(0, 1)
        plt.xlabel('Recall (fração das altas identificadas)')
        plt.ylabel(label.capitalize())
        plt.title(f'Recall por {label} no teste (mínimo de 30 observações)')
        save(f'{col}_performance.png')
    if features is not None: save_importance(features,pred.target,model,directory,save)
    elif hasattr(model.named_steps['classifier'],'coef_'): save_coefficients(model,directory,save)
    if profile is not None: save_risk_profile(profile,directory,save)
    if ranking is not None: save_comparison(ranking,directory,save)
    if intervals is not None: save_intervals(intervals,directory,save)

def save_importance(features, target, model, directory: Path, save) -> None:
    """Permutação sobre os atributos de entrada: medida comparável entre famílias."""
    result=permutation_importance(model,features[FEATURES],target,scoring='average_precision',n_repeats=5,random_state=SEED,n_jobs=-1)
    order=np.argsort(result.importances_mean)
    plt.figure(figsize=(9,6)); plt.barh(np.array(FEATURES)[order],result.importances_mean[order],xerr=result.importances_std[order]); plt.xlabel('Queda média da average precision ao permutar o atributo'); plt.title('Importância por permutação no teste — associação, não causalidade'); save('permutation_importance.png')
    if hasattr(model.named_steps['classifier'],'coef_'): save_coefficients(model,directory,save)

def save_coefficients(model, directory: Path, save) -> None:
    names=model.named_steps['preprocess'].get_feature_names_out(); coeff=model.named_steps['classifier'].coef_[0]; ix=np.argsort(np.abs(coeff))[-20:]; ix=ix[np.argsort(coeff[ix])]
    plt.figure(figsize=(9,7)); plt.barh(names[ix],coeff[ix]); plt.xlabel('Coeficiente do logito'); plt.title('Coeficientes de maior magnitude\nPreços e estatísticas da janela são colineares: não leia um coeficiente isoladamente'); save('coefficients.png')

def save_risk_profile(train, directory: Path, save) -> None:
    """Calculado no treino: a forma da relação é leitura do modelo, não do teste."""
    table=risk_by_variation_band(train)
    plt.figure(figsize=(10,4.2)); bars=plt.bar(table.band.astype(str),table.risk,color=sns.color_palette()[0])
    plt.axhline(train.target.mean(),ls='--',color='gray',label=f'Prevalência geral ({train.target.mean():.3f})')
    for bar,n in zip(bars,table.n): plt.text(bar.get_x()+bar.get_width()/2,bar.get_height()+.012,f'n={n}',ha='center',fontsize=8)
    plt.xticks(rotation=35,ha='right'); plt.ylim(0,max(table.risk)*1.22); plt.xlabel('Variação do preço no mês anterior'); plt.ylabel('P(alta > 2% no mês seguinte)')
    plt.title('Risco observado por faixa de variação anterior — treino'); plt.legend(); save('risk_by_variation.png')

def save_comparison(ranking, directory: Path, save) -> None:
    """Validação decide; o teste por família é diagnóstico posterior, não critério."""
    r=ranking.sort_values('f1_validation'); pos=np.arange(len(r)); height=.38
    plt.figure(figsize=(9,max(3.5,len(r)*.9)))
    plt.barh(pos+height/2,r.f1_validation,height,label='F1 na validação (critério de seleção)')
    if 'f1_test' in r: plt.barh(pos-height/2,r.f1_test,height,label='F1 no teste (diagnóstico posterior)')
    plt.yticks(pos,r.algorithm); plt.xlabel('F1 da classe positiva'); plt.xlim(0,max(r.f1_validation.max(),r.get('f1_test',r.f1_validation).max())*1.35)
    plt.title('Comparação entre famílias de algoritmos'); plt.legend(loc='upper center',bbox_to_anchor=(.5,-.18),ncol=2,frameon=False); save('model_comparison.png')

def save_intervals(intervals: dict, directory: Path, save) -> None:
    """Barras de erro por reamostragem de séries inteiras, não de linhas isoladas."""
    labels={'precision':'Precisão','recall':'Recall','f1':'F1','balanced_accuracy':'Acurácia\nbalanceada','roc_auc':'ROC-AUC','average_precision':'Average\nprecision'}
    shown=[k for k in labels if k in intervals['intervals']]
    median=[intervals['intervals'][k]['median'] for k in shown]
    low=[median[i]-intervals['intervals'][k]['low'] for i,k in enumerate(shown)]
    high=[intervals['intervals'][k]['high']-median[i] for i,k in enumerate(shown)]
    plt.figure(figsize=(8,4)); plt.errorbar([labels[k] for k in shown],median,yerr=[low,high],fmt='o',capsize=5); plt.ylim(0,1); plt.ylabel('Valor'); plt.title(f"Intervalos de {intervals['level']:.0%} por bootstrap de {intervals['series']} séries"); save('metric_intervals.png')
