# Previsão de aumentos de preços da cesta básica

Projeto acadêmico exploratório que estuda preços históricos por supermercado e produto. A pergunta é: **preços históricos ajudam a prever se o preço da mesma embalagem aumentará mais de 2% no mês seguinte?** As probabilidades são estimativas, não garantias de movimentos futuros.

## Dados disponíveis

A fonte presente no repositório é `data/ICB_DADOS_2026.xlsx`, aba `ACUMUL_DESAGREG`; não existe CSV no repositório original. O projeto lê a planilha diretamente e não a altera. Ela possui 46.264 registros, de setembro de 2022 a agosto de 2026, com colunas `Mes_Ano_Data`, `Data_Coleta`, `Estab`, `Produto`, `Marca`, `Preco`, `Quantidade` e `PPK`: 30 produtos e 51 estabelecimentos identificados.

Há 9.818 datas de coleta e 9.346 marcas ausentes e 1.743 duplicatas exatas. A última data individual de coleta registrada é outubro de 2025. Embora `PPK` corresponda a `Preco / Quantidade` na tolerância de R$ 0,01, a unidade da quantidade não é documentada para cada produto; não é seguro denominá-lo universalmente preço por quilo. O notebook exploratório detalha valores extremos, cobertura, descrições e quantidades. A interpretação e a origem das medições devem ser validadas com o responsável pelos dados.

## Documentação técnica e teórica

O [guia em docs/](docs/README.md) detalha a construção do alvo, atributos temporais, fundamentos matemáticos da regressão logística, pipeline, métricas, experimentos e limitações.

## Metodologia

- Remove-se somente a duplicata integral, exigem-se mês, produto, supermercado, preço e quantidade válidos, e mantém-se marca ausente como categoria explícita. Datas de coleta fora do mês de referência são excluídas; datas ausentes não são preenchidas. Observações distintas da mesma série no mesmo mês são agregadas pela mediana; preços extremos não são removidos automaticamente.
- Série = supermercado, produto, marca e quantidade. Utiliza-se o preço por embalagem comparável dentro da série. A marca desconhecida pode agrupar itens realmente diferentes.
- São exigidos preços nos meses consecutivos t, t−1 e t−2. O alvo é 1 se `(preço t+1 / preço t) − 1 > 0,02`; exatamente 2% pertence à classe 0. Sem preço no mês-calendário seguinte, não há alvo. Entram preços e variações históricas, estatísticas da janela t−2 até t, mês cíclico e categorias; o preço futuro nunca é atributo.
- A divisão considera o **mês-alvo**: treino setembro/2022–dezembro/2024; validação janeiro–agosto/2025; teste setembro/2025–agosto/2026. A janela histórica reduz o início efetivo do treino. Transformações são ajustadas somente nos dados de ajuste.
- `Pipeline` combina padronização numérica, one-hot com categorias desconhecidas e **LogisticRegression**, único classificador. Validam-se `C` em 0,1, 1 e 10, pesos de classe e limiares de 0,10 a 0,90. O critério é maior F1 na validação com precisão ≥ 0,35; o fallback, se necessário, é registrado. Após seleção, reajusta-se em treino + validação e avalia-se uma vez no teste. As predições de validação são do modelo antes do reajuste.
- Reportam-se precisão, recall, F1, acurácia, acurácia balanceada, ROC-AUC, average precision, Brier e matriz de confusão. As regras de nunca alertar, sempre alertar e repetir a alta anterior são referências sem treinamento no mesmo teste. Grupos sem positivos têm recall e F1 indefinidos; precisão sem previsões positivas é reportada como zero por convenção.

## Instalação e execução

É necessário `uv` e Python 3.12. Na raiz do repositório:

```bash
uv sync
uv run jupyter lab
```

Abra os notebooks nesta ordem:

1. `notebooks/01_exploratory_data_analysis.ipynb`: qualidade, cobertura e exploração.
2. `notebooks/02_logistic_regression.ipynb`: atributos, seleção e treino. Por padrão não cria uma execução; altere `RUN_TRAINING` para `True`, ou inicie o Jupyter com `BASKET_TRAIN=1 uv run jupyter lab` e execute o notebook. Cada chamada intencional cria um diretório novo.
3. `notebooks/03_model_evaluation.ipynb`: carrega automaticamente o último experimento concluído. Altere `EXPERIMENT` para outro diretório se desejar. Executar ou reabrir esse notebook não treina modelo.

Teste automatizado:

```bash
uv run pytest -q
```

A execução não interativa também é possível com `uv run jupyter nbconvert --to notebook --execute notebooks/01_exploratory_data_analysis.ipynb --output /tmp/eda-executada.ipynb`; para o notebook de treino defina `BASKET_TRAIN=1`, e execute a avaliação depois. Um kernel Jupyter precisa de sockets locais permitidos pelo ambiente.

## Estrutura e reprodutibilidade

- `data/`: planilha original preservada.
- `notebooks/`: explicações, exploração, treinamento e avaliação.
- `src/basket_price_prediction/`: carregamento, limpeza, atributos, treinamento, avaliação, gráficos e experimentos.
- `tests/`: testes sintéticos de rótulos, lacunas, separação, pipeline e persistência.
- `docs/`: explicações técnicas e teóricas do projeto e do modelo.
- `runs/results/<experimento>/`: configuração e métricas JSON, resumo de dados, manifesto, pipeline `joblib`, predições separadas, figuras e relatórios.
- `pyproject.toml`, `uv.lock`: dependências e versões resolvidas.

A pasta `runs/` está no `.gitignore`, portanto os resultados gerados são locais e podem não acompanhar uma cópia do repositório; rode o treinamento antes do notebook de avaliação quando não houver experimento concluído. A regra não altera o rastreamento de arquivos já adicionados anteriormente.

Cada execução tem identificador UTC com proteção contra colisões; nunca substitui resultados anteriores. O manifesto registra versões, parâmetros, SHA-256 da fonte e do lockfile, horários e status. O hash de commit é `null` porque as instruções locais proíbem comandos Git sem pedido explícito. Execuções interrompidas ou que falhem ficam identificadas como incompletas e não são carregadas como concluídas. O notebook de avaliação confere o hash e reproduz as probabilidades a partir do pipeline salvo. Carregue arquivos `joblib` somente de fontes confiáveis.

## Resultado observado

Experimento: `runs/results/20261114_142933_489430_ab7cee47_logreg/` (a segunda execução reproduziu os resultados da primeira). Dos 17.002 exemplos elegíveis, 4.957 (29,2%) têm alta superior a 2%. Treino, validação e teste contêm respectivamente 10.268, 3.554 e 3.180 exemplos. A seleção escolheu `C=10`, `class_weight=None`, `solver=liblinear` e limiar **0,25**.

| Métrica no teste | Resultado |
|---|---:|
| Precisão | 0,390 |
| Recall | 0,706 |
| F1 | 0,503 |
| Acurácia / balanceada | 0,596 / 0,629 |
| ROC-AUC | 0,702 |
| Average precision | 0,523 |
| Brier | 0,181 |

A matriz contém 1.246 verdadeiros negativos, 1.015 falsos positivos, 270 falsos negativos e 649 verdadeiros positivos. A referência sempre-zero tem acurácia 0,711, com recall 0. Sempre alertar atinge recall 1,000 e F1 0,448. Repetir a alta anterior tem F1 0,220. O modelo apresenta informação preditiva nesse período, mas a precisão de 39% mostra muitos alarmes falsos. O recall mensal varia entre 0,553 e 0,862; diferenças por produto devem ser lidas com os respectivos tamanhos e números de positivos nos relatórios.

## Limitações

Séries incompletas e a exigência de histórico podem enviesar a amostra para itens com maior continuidade. Marcas ausentes podem misturar produtos diferentes; embalagens, descrições, possíveis promoções e coleta não estão totalmente documentadas. A ausência de datas de coleta após outubro/2025 impede verificar diretamente se todas as observações estavam disponíveis no fim do mês de referência. Inflação, custos e outros fatores econômicos não são observados. Os coeficientes expressam associações do modelo, não efeitos causais; os resultados são exploratórios e não garantem desempenho futuro.
