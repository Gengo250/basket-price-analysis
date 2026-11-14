# Experimentos, artefatos e reprodução

## 🗂️ Organização do projeto

| Caminho | Responsabilidade |
| --- | --- |
| `data/ICB_DADOS_2026.xlsx` | Fonte original, somente leitura no fluxo. |
| `notebooks/01_exploratory_data_analysis.ipynb` | Inspeção, qualidade, estatísticas e figuras exploratórias. |
| `notebooks/02_logistic_regression.ipynb` | Construção dos dados e execução intencional do treinamento. |
| `notebooks/03_model_evaluation.ipynb` | Leitura de experimento concluído e avaliação dos artefatos salvos. |
| `src/basket_price_prediction/config.py` | Caminhos, limites temporais, semente e lista de atributos. |
| `data.py`, `preprocessing.py`, `features.py` | Leitura, limpeza, agregação, atributos, alvo e divisão temporal. |
| `training.py`, `evaluation.py`, `visualization.py` | Pipeline logístico, seleção, métricas e figuras. |
| `experiments.py` | Criação de execução, persistência e recarga. |
| `tests/` | Verificações focadas com dados sintéticos. |
| `runs/results/` | Saídas locais de cada execução de treinamento. |

Os caminhos dos módulos listados sem prefixo estão em `src/basket_price_prediction/`. O projeto usa `uv`, o arquivo `pyproject.toml`, o `uv.lock` e Python 3.12.

## ▶️ Execução pelo Jupyter

A partir da raiz do projeto:

```bash
uv sync
uv run jupyter lab
```

1. Execute o notebook exploratório. Ele não treina o modelo.
2. Abra o notebook de regressão logística. Altere `RUN_TRAINING` para `True` e execute as células para criar um novo experimento. Alternativamente, inicie o Jupyter com `BASKET_TRAIN=1 uv run jupyter lab`.
3. Execute o notebook de avaliação. Por padrão, ele carrega o último experimento concluído por ordem do identificador; defina `EXPERIMENT` explicitamente para escolher outro. Ele não executa treinamento.

O notebook de avaliação precisa de pelo menos uma execução concluída. As saídas em `runs/` são locais e estão listadas no `.gitignore`; por isso, uma cópia do projeto pode exigir um treinamento novo antes da avaliação. O identificador citado no README refere-se à execução que produziu os resultados documentados e não assegura que esses arquivos tenham sido distribuídos com o código.

## 📦 Conteúdo de uma execução

Cada chamada intencional de `run_training()` cria um diretório único com data/hora UTC e sufixo aleatório. Se uma execução falhar após a criação, o manifesto registra `failed`; `load_experiment()` aceita somente `complete`. Diretórios anteriores não são substituídos.

```text
runs/results/<experimento>/
├── config.json                  # parâmetros, atributos, limiar e divisões
├── data_summary.json            # limpeza, elegibilidade e contagens
├── manifest.json                # status, versões, hashes e configuração
├── metrics.json                 # métricas de validação, teste e referências
├── model/logistic_regression.joblib
├── predictions/
│   ├── validation_predictions.csv
│   └── test_predictions.csv
├── figures/                     # curvas, matriz, grupos e coeficientes
└── reports/                     # classificação, candidatos, grupos e erros
```

A predição de validação é gerada pelo modelo ajustado apenas no treino; o `joblib` é o pipeline final reajustado em treino e validação. Logo, não se deve usar o modelo salvo para afirmar que ele gerou as probabilidades salvas de validação. A predição de teste, por sua vez, corresponde ao pipeline final salvo. As tabelas guardam identificadores, mês de atributos, mês-alvo, variação real, classe real, probabilidade e classe prevista.

O manifesto registra o SHA-256 da fonte e de `uv.lock`, versões Python e scikit-learn, horários UTC, status e configuração. O campo de commit fica `null` no fluxo atual. O notebook de avaliação confere o hash da fonte e verifica se o pipeline recarregado reproduz as probabilidades de teste. O hash identifica o conteúdo, mas por si só não documenta todos os detalhes do ambiente de execução.

O `joblib` é adequado para persistir o pipeline completo de pré-processamento e estimador. Assim como formatos baseados em pickle, pode executar código no carregamento; carregue apenas arquivos de confiança.[^1] A compatibilidade entre versões de bibliotecas não deve ser presumida: reproduza o ambiente do lockfile.

## ✅ Verificação e testes

```bash
uv run pytest -q
```

Os testes cobrem o limite de 2%, ausência de mês seguinte, lacunas, lags, janela sem futuro, separação de séries, divisão temporal, ajuste do transformador somente no treino, criação de diretórios distintos e recarga de artefatos. Eles usam amostras sintéticas pequenas e não alteram a planilha original. Uma passagem dos testes apoia a verificação dos contratos cobertos; ela não prova qualidade dos dados de origem nem desempenho futuro.

Para executar um notebook sem interface, por exemplo:

```bash
uv run jupyter nbconvert --to notebook --execute notebooks/01_exploratory_data_analysis.ipynb --output /tmp/eda-executada.ipynb
```

O kernel Jupyter exige comunicação local e o ambiente pode precisar permitir sockets locais. Para o notebook de treino não interativo, defina `BASKET_TRAIN=1`; cada execução intencional criará outra pasta em `runs/results/`.

## 🧾 Arquivos ignorados e rastreamento

A regra `/runs/` no `.gitignore` corresponde ao diretório `runs` na raiz e impede que arquivos ainda não rastreados nele sejam adicionados automaticamente. Ela não apaga arquivos locais e não deixa de rastrear arquivos que já tenham sido adicionados anteriormente. Uma eventual alteração de rastreamento de arquivos já existentes exige ação separada e deve preservar os arquivos locais.

[^1]: Scikit-learn, *Model persistence*, https://scikit-learn.org/stable/model_persistence.html.
