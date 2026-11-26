# Experimentos, artefatos e reprodução

## 🗂️ Organização do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `data/ICB_DADOS_2026.xlsx` | Fonte original, somente leitura no fluxo. |
| `notebooks/01_exploratory_data_analysis.ipynb` | Inspeção, qualidade, estatísticas e figuras exploratórias. |
| `notebooks/02_model_comparison.ipynb` | Construção dos dados e execução intencional do treinamento. |
| `notebooks/03_model_evaluation.ipynb` | Leitura de experimento concluído e avaliação dos artefatos salvos. |
| `config.py` | Caminhos, limites temporais, semente, grade de limiares e lista de atributos. |
| `data.py`, `preprocessing.py`, `features.py` | Leitura, limpeza, agregação, atributos, alvo e divisão temporal. |
| `training.py` | Grade das quatro famílias, pipeline, critério de seleção e comparação. |
| `evaluation.py` | Métricas, bootstrap por série, colinearidade, perfil de risco e regras de referência. |
| `visualization.py` | Figuras de avaliação, comparação, intervalos e importância. |
| `experiments.py` | Criação de execução, persistência, publicação do relatório e recarga. |
| `tests/` | 28 verificações focadas com dados sintéticos. |
| `runs/results/` | Saídas locais de cada execução de treinamento. |
| `relatorio/` | Relatório consolidado e cópia versionada de figuras e tabelas. |

Os módulos listados sem prefixo estão em `src/basket_price_prediction/`. O projeto usa `uv`, `pyproject.toml`, `uv.lock` e Python 3.12.

## ▶️ Execução pelo Jupyter

A partir da raiz do projeto:

```bash
uv sync
uv run jupyter lab
```

1. Execute o notebook exploratório. Ele não treina modelo.
2. Abra o notebook de comparação. Altere `RUN_TRAINING` para `True` e execute as células para criar um novo experimento, ou inicie o Jupyter com `BASKET_TRAIN=1 uv run jupyter lab`.
3. Execute o notebook de avaliação. Por padrão carrega o último experimento concluído; defina `EXPERIMENT` para escolher outro. Ele não treina.

Fora do Jupyter, uma execução completa leva cerca de 100 segundos:

```bash
uv run python -c "from basket_price_prediction.experiments import run_training; print(run_training())"
```

O notebook de avaliação precisa de pelo menos uma execução concluída. As saídas em `runs/` são locais e estão no `.gitignore`; por isso uma cópia do projeto pode exigir treinamento novo antes da avaliação. A pasta `relatorio/`, ao contrário, é versionada e acompanha a entrega.

## 📦 Conteúdo de uma execução

Cada chamada intencional de `run_training()` cria um diretório único com data/hora UTC e sufixo aleatório. Se uma execução falhar após a criação, o manifesto registra `failed`; `load_experiment()` aceita somente `complete`. Diretórios anteriores não são substituídos.

```text
runs/results/<experimento>/
├── config.json                  # algoritmo, grade, limiar, atributos e divisões
├── data_summary.json            # limpeza, elegibilidade, contagens e VIF máximo
├── manifest.json                # status, versões, hashes e configuração
├── metrics.json                 # validação, teste, intervalos, referências e diagnóstico por família
├── model/pipeline.joblib        # pipeline final, qualquer que seja a família vencedora
├── predictions/
│   ├── validation_predictions.csv
│   └── test_predictions.csv
├── figures/                     # curvas, matriz, grupos, comparação, intervalos e importância
└── reports/
    ├── model_comparison.csv     # melhor configuração de cada família
    ├── collinearity.csv         # VIF e correlação máxima por atributo numérico
    ├── risk_by_variation.csv    # risco observado por faixa da variação anterior, no treino
    ├── validation_candidates.csv# os 408 pares configuração-limiar
    ├── performance_by_*.csv     # mês-alvo, produto e supermercado
    ├── *_examples.csv           # 20 exemplos de cada quadrante da matriz
    ├── classification_report.txt
    └── experiment_summary.md
```

O arquivo do modelo tem nome fixo `pipeline.joblib` porque a família vencedora pode mudar entre execuções; `load_experiment` ainda aceita nomes antigos de execuções anteriores.

A predição de validação vem do modelo ajustado apenas no treino; o `joblib` é o pipeline final reajustado em treino + validação. Logo, não se deve usar o modelo salvo para afirmar que ele gerou as probabilidades de validação. A predição de teste corresponde ao pipeline salvo.

O manifesto registra SHA-256 da fonte e de `uv.lock`, versões de Python e scikit-learn, horários UTC, status e configuração. O campo de commit fica `null` no fluxo atual. O notebook de avaliação confere o hash da fonte e verifica se o pipeline recarregado reproduz as probabilidades de teste.

O `joblib` é adequado para persistir o pipeline completo. Assim como formatos baseados em pickle, pode executar código no carregamento; carregue apenas arquivos de confiança.[^1] Reproduza o ambiente do lockfile em vez de presumir compatibilidade entre versões.

## 📤 Publicação do relatório

Ao final de uma execução bem-sucedida, `publish_report_assets` copia figuras e tabelas para `relatorio/figuras/` e `relatorio/tabelas/`, substituindo o conteúdo anterior e registrando a origem em `relatorio/ORIGEM.txt`. É isso que garante que gráficos e tabelas acompanhem a entrega mesmo com `runs/` ignorado.

Para desligar a publicação automática ou apontar o relatório para outra execução:

```python
run_training(publish=False)
publish_report_assets('runs/results/<experimento>')
```

Só execuções com status `complete` podem alimentar o relatório. O texto de `relatorio/RELATORIO.md` é escrito à mão e cita números de uma execução específica — ao republicar a partir de outra, confira se os valores citados continuam válidos.

## ✅ Verificação e testes

```bash
uv run pytest -q
```

Os 28 testes cobrem o limite estrito de 2%, ausência de mês seguinte, lacunas, lags, separação de séries, divisão temporal, ajuste do transformador somente no treino, ajuste e predição de cada uma das quatro famílias, aplicação do piso de precisão e do *fallback* no critério de seleção, uma linha por família na comparação, reprodutibilidade e cobertura dos intervalos de bootstrap, reamostragem por blocos de série, detecção de combinação linear exata pelo VIF, separação do regime de preço inalterado no perfil de risco, criação de diretórios distintos e recarga de artefatos.

Eles usam amostras sintéticas pequenas e não alteram a planilha original. Uma passagem apoia a verificação dos contratos cobertos; não prova qualidade dos dados de origem nem desempenho futuro.

Para executar um notebook sem interface:

```bash
uv run jupyter nbconvert --to notebook --execute notebooks/01_exploratory_data_analysis.ipynb --output /tmp/eda-executada.ipynb
```

O kernel Jupyter exige comunicação local e o ambiente pode precisar permitir sockets locais. Para o notebook de comparação não interativo, defina `BASKET_TRAIN=1`; cada execução intencional criará outra pasta em `runs/results/`.

## 🧾 Arquivos ignorados e rastreamento

A regra `/runs/` no `.gitignore` corresponde ao diretório `runs` na raiz e impede que arquivos ainda não rastreados nele sejam adicionados automaticamente. Ela não apaga arquivos locais e não deixa de rastrear arquivos já adicionados anteriormente. `relatorio/` não é ignorado: é a pasta destinada a acompanhar a entrega.

[^1]: Scikit-learn, *Model persistence*, https://scikit-learn.org/stable/model_persistence.html.
