"""Cria execução imutável e persiste artefatos auditáveis."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import uuid
import joblib
import pandas as pd
import sklearn
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter
from .config import DATASET, FEATURES, NUMERIC, CATEGORICAL, RESULTS, ROOT, SEED, SPLITS
from .data import load_data
from .preprocessing import prepare_monthly
from .features import build_supervised, temporal_split
from .training import select_model, make_pipeline, prediction_table
from .evaluation import calculate_metrics, group_performance, text_report
from .visualization import save_figures

def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def create_run(base: Path = RESULTS) -> Path:
    base.mkdir(parents=True,exist_ok=True)
    while True:
        path=base/(datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')+'_'+uuid.uuid4().hex[:8]+'_logreg')
        try:
            path.mkdir()
            return path
        except FileExistsError:
            continue

def write_json(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False,default=str)+'\n',encoding='utf-8')

def write_excel_report(table: pd.DataFrame, path: Path, title: str) -> None:
    """Exporta uma tabela Excel."""
    with pd.ExcelWriter(path, engine='openpyxl') as writer:
        table.to_excel(writer, sheet_name='Resultados', index=False, startrow=2)
        sheet = writer.sheets['Resultados']
        sheet.merge_cells(start_row=1, start_column=1, end_row=1, end_column=sheet.max_column)
        sheet['A1'] = title
        sheet.row_dimensions[1].height = 28
        sheet.row_dimensions[3].height = 22

        center = Alignment(horizontal='center', vertical='center', wrap_text=False)
        heading_font = Font(bold=True, color='FFFFFF')
        heading_fill = PatternFill(fill_type='solid', fgColor='245782')
        for cell in (sheet['A1'], *sheet[3]):
            cell.alignment = center
            cell.font = heading_font
            cell.fill = heading_fill

        for column in sheet.iter_cols(min_row=3):
            width = 12
            for cell in column:
                cell.alignment = center
                value = cell.value
                if isinstance(value, float):
                    cell.number_format = '0.000'
                    value = f'{value:.3f}'
                if value is not None:
                    width = max(width, len(str(value)) + 4)
            letter = get_column_letter(column[0].column)
            sheet.column_dimensions[letter].width = min(width, 255)
        sheet.freeze_panes = 'A4'
        sheet.auto_filter.ref = f'A3:{sheet.cell(sheet.max_row, sheet.max_column).coordinate}'

def run_training(dataset_path: Path = DATASET, results_dir: Path = RESULTS) -> Path:
    """Uma chamada intencional cria uma nova execução; teste entra só após seleção."""
    run=create_run(results_dir)
    for folder in ['model','predictions','figures','reports']:
        (run/folder).mkdir()
    now=datetime.now(timezone.utc).isoformat()
    write_json(run/'manifest.json',{'status':'running','started_utc':now})
    try:
        raw=load_data(dataset_path); monthly,clean=prepare_monthly(raw); data,feature_report=build_supervised(monthly); parts=temporal_split(data,SPLITS)
        _,selection,candidates,val=select_model(parts['train'],parts['validation'])
        threshold=selection['threshold']
        combined=pd.concat([parts['train'],parts['validation']],ignore_index=True)
        final=make_pipeline(selection['C'],selection['class_weight']).fit(combined[FEATURES],combined.target)
        # O teste é consultado apenas depois da seleção de hiperparâmetros e limiar.
        test=prediction_table(parts['test'],final.predict_proba(parts['test'][FEATURES])[:,1],threshold)
        metrics={'validation_before_refit':calculate_metrics(val.target,val.probability,threshold), 'test':calculate_metrics(test.target,test.probability,threshold), 'reference_test_always_zero':calculate_metrics(test.target,[0.0]*len(test),0.5), 'reference_test_previous_increase':calculate_metrics(test.target,(test.variation_1m.gt(.02) & ~test.variation_1m.sub(.02).abs().le(1e-12)).astype(float),.5)}
        comparison = pd.DataFrame(
            [
                {'Modelo ou referência': label, **{
                    title: metrics[key][metric]
                    for title, metric in [
                        ('Precisão', 'precision'),
                        ('Recall', 'recall'),
                        ('F1', 'f1'),
                        ('Acurácia', 'accuracy'),
                    ]
                }}
                for label, key in [
                    ('Regressão logística', 'test'),
                    ('Sempre sem alerta', 'reference_test_always_zero'),
                    ('Repete a alta anterior', 'reference_test_previous_increase'),
                ]
            ]
        )
        comparison.to_csv(run/'reports'/'model_comparison.csv', index=False, float_format='%.3f')
        write_excel_report(
            comparison, run/'reports'/'model_comparison.xlsx',
            'Comparação do modelo com as referências no teste',
        )
        summary={'cleaning':clean,'features':feature_report,'splits':{k:{'n':len(v),'class_counts':{str(int(i)):int(n) for i,n in v.target.value_counts().items()},'first_target_month':str(v.target_month.min().date()),'last_target_month':str(v.target_month.max().date())} for k,v in parts.items()}}
        config={'model':'sklearn.linear_model.LogisticRegression','selection':selection,'max_iter':2000,'solver':'liblinear','random_state':SEED,'features':FEATURES,'numeric':NUMERIC,'categorical':CATEGORICAL,'dataset':str(Path(dataset_path).relative_to(ROOT)) if Path(dataset_path).is_relative_to(ROOT) else str(dataset_path),'target_month_splits':SPLITS,'preprocessing':{'price':'preço da mesma embalagem; mediana mensal','entity':['supermarket','product','brand','quantity'],'history':'t, t-1, t-2 consecutivos','numeric':'StandardScaler','categorical':'OneHotEncoder(handle_unknown=ignore)','final_fit':'treino + validação','target':'aumento estritamente maior que 2%, próximo mês calendário'},'execution_utc':now}
        joblib.dump(final,run/'model'/'logistic_regression.joblib')
        val.to_csv(run/'predictions'/'validation_predictions.csv',index=False); test.to_csv(run/'predictions'/'test_predictions.csv',index=False); candidates.to_csv(run/'reports'/'validation_candidates.csv',index=False)
        for col in ['target_month','product','supermarket']:
            performance = group_performance(test, col, threshold)
            performance.to_csv(run/'reports'/f'performance_by_{col}.csv', index=False)
            if col == 'target_month':
                columns = {
                    'target_month': 'Mês-alvo',
                    'n': 'Observações',
                    'positives': 'Altas observadas',
                    'precision': 'Precisão',
                    'recall': 'Recall',
                    'f1': 'F1',
                    'accuracy': 'Acurácia',
                }
                monthly_report = performance[list(columns)].rename(columns=columns)
                monthly_report['Mês-alvo'] = monthly_report['Mês-alvo'].dt.strftime('%m/%Y')
                write_excel_report(
                    monthly_report, run/'reports'/'performance_by_target_month.xlsx',
                    'Desempenho do modelo por mês no teste',
                )
        for label,a,b in [('true_positive',1,1),('true_negative',0,0),('false_positive',0,1),('false_negative',1,0)]:
            test[(test.target==a)&(test.prediction==b)].sort_values('probability',ascending=False).head(20).to_csv(run/'reports'/f'{label}_examples.csv',index=False)
        save_figures(test,final,threshold,run/'figures')
        (run/'reports'/'classification_report.txt').write_text(text_report(test.target,test.prediction),encoding='utf-8')
        m=metrics['test']; cm=m['confusion_matrix']
        (run/'reports'/'experiment_summary.md').write_text(f"# Resultado do experimento\n\nNo teste temporal: {m['n']} observações, {m['positives']} altas; precisão {m['precision']:.3f}, recall {m['recall']:.3f}, F1 {m['f1']:.3f} e AP {m['average_precision']:.3f}. Houve {cm[0][1]} falsos positivos e {cm[1][0]} falsos negativos. O limiar {threshold:.2f} foi escolhido na validação anterior ao reajuste. Coeficientes são associações, não efeitos causais. A base não contém inflação nem fatores econômicos externos; mudanças de coleta e lacunas limitam a generalização.\n",encoding='utf-8')
        write_json(run/'config.json',config); write_json(run/'metrics.json',metrics); write_json(run/'data_summary.json',summary)
        write_json(run/'manifest.json',{'status':'complete','started_utc':now,'completed_utc':datetime.now(timezone.utc).isoformat(),'python_version':platform.python_version(),'sklearn_version':sklearn.__version__,'dataset_sha256':file_hash(Path(dataset_path)),'lockfile':'uv.lock','lockfile_sha256':file_hash(ROOT/'uv.lock'),'git_commit':None,'git_commit_note':'não consultado: instrução local proíbe comandos git sem pedido explícito','configuration':config})
    except Exception as exc:
        write_json(run/'manifest.json',{'status':'failed','started_utc':now,'error':repr(exc)})
        raise
    return run

def load_experiment(run: Path) -> dict:
    run=Path(run); manifest=json.loads((run/'manifest.json').read_text(encoding='utf-8'))
    if manifest['status']!='complete': raise ValueError('Experimento não concluído')
    return {'path':run,'manifest':manifest,'config':json.loads((run/'config.json').read_text(encoding='utf-8')),'metrics':json.loads((run/'metrics.json').read_text(encoding='utf-8')),'summary':json.loads((run/'data_summary.json').read_text(encoding='utf-8')),'model':joblib.load(run/'model'/'logistic_regression.joblib'),'validation':pd.read_csv(run/'predictions'/'validation_predictions.csv',parse_dates=['month','target_month']),'test':pd.read_csv(run/'predictions'/'test_predictions.csv',parse_dates=['month','target_month'])}
