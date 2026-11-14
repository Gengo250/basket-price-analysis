"""Gráficos de avaliação gerados exclusivamente a partir de predições salvas."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns
from sklearn.calibration import calibration_curve
from sklearn.metrics import confusion_matrix, precision_recall_curve, roc_curve, auc
from .evaluation import group_performance

sns.set_theme(style='whitegrid')
def save_figures(pred, model, threshold: float, directory: Path) -> None:
    directory.mkdir(parents=True,exist_ok=True)
    def save(name):
        plt.tight_layout(); plt.savefig(directory/name,dpi=130,bbox_inches='tight'); plt.close()
    y=pred.target; p=pred.probability
    plt.figure(figsize=(5,4)); sns.heatmap(confusion_matrix(y,p>=threshold,labels=[0,1]),annot=True,fmt='d',cmap='Blues',xticklabels=['0','1'],yticklabels=['0','1']); plt.xlabel('Classe prevista'); plt.ylabel('Classe real'); plt.title('Matriz de confusão — teste'); save('confusion_matrix.png')
    precision,recall,thresholds=precision_recall_curve(y,p)
    plt.figure(); plt.plot(recall,precision); plt.axhline(y.mean(),ls='--',color='gray',label='Prevalência'); plt.xlabel('Recall'); plt.ylabel('Precisão'); plt.title('Curva precisão–recall'); plt.legend(); save('precision_recall_curve.png')
    if y.nunique()==2:
        fpr,tpr,_=roc_curve(y,p); plt.figure(); plt.plot(fpr,tpr,label=f'AUC = {auc(fpr,tpr):.3f}'); plt.plot([0,1],[0,1],'--',color='gray'); plt.xlabel('Taxa de falsos positivos'); plt.ylabel('Recall'); plt.title('Curva ROC'); plt.legend(); save('roc_curve.png')
    plt.figure(); sns.histplot(data=pred,x='probability',hue='target',stat='density',common_norm=False,bins=25,element='step'); plt.xlabel('Probabilidade prevista'); plt.ylabel('Densidade'); plt.title('Probabilidades por classe real'); save('probability_distribution.png')
    observed,mean=calibration_curve(y,p,n_bins=10,strategy='quantile'); plt.figure(); plt.plot(mean,observed,'o-'); plt.plot([0,1],[0,1],'--',color='gray'); plt.xlabel('Probabilidade média prevista'); plt.ylabel('Frequência observada'); plt.title('Calibração por decis'); save('calibration_curve.png')
    plt.figure(); plt.plot(thresholds,precision[:-1],label='Precisão'); plt.plot(thresholds,recall[:-1],label='Recall'); plt.axvline(threshold,color='gray',ls='--',label='Limiar escolhido'); plt.xlabel('Limiar de probabilidade'); plt.ylabel('Métrica'); plt.title('Precisão e recall por limiar'); plt.legend(); save('threshold_tradeoff.png')
    monthly=group_performance(pred,'target_month',threshold).sort_values('target_month'); plt.figure(figsize=(10,4)); plt.plot(monthly.target_month.astype(str),monthly.precision,'o-',label='Precisão'); plt.plot(monthly.target_month.astype(str),monthly.recall,'o-',label='Recall'); plt.plot(monthly.target_month.astype(str),monthly.f1,'o-',label='F1'); plt.xticks(rotation=45,ha='right'); plt.ylim(0,1); plt.xlabel('Mês-alvo'); plt.ylabel('Métrica'); plt.title('Desempenho mensal no teste'); plt.legend(); save('monthly_performance.png')
    for col,label in [('product','produto'),('supermarket','supermercado')]:
        table=group_performance(pred,col,threshold); table=table[(table.n>=30) & table.recall.notna()].sort_values('n',ascending=False).head(20).sort_values('recall')
        plt.figure(figsize=(9,max(4,len(table)*.28))); plt.barh(table[col].astype(str),table.recall.fillna(0)); plt.xlabel('Recall (mínimo 30 observações)'); plt.ylabel(label.capitalize()); plt.title(f'Recall por {label} no teste'); save(f'{col}_performance.png')
    names=model.named_steps['preprocess'].get_feature_names_out(); coeff=model.named_steps['classifier'].coef_[0]; ix=np.argsort(np.abs(coeff))[-20:]; ix=ix[np.argsort(coeff[ix])]
    plt.figure(figsize=(9,7)); plt.barh(names[ix],coeff[ix]); plt.xlabel('Coeficiente do logito'); plt.title('Coeficientes de maior magnitude — associação, não causalidade'); save('coefficients.png')
