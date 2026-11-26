# Previsão de aumentos de preços da cesta básica

Projeto acadêmico de extensão que estuda preços históricos por supermercado e produto. A pergunta é: **preços históricos ajudam a prever se o preço da mesma embalagem aumentará mais de 2% no mês seguinte?** As probabilidades são estimativas, não garantias de movimentos futuros.

👉 **O relatório do trabalho está em [`relatorio/RELATORIO.md`](relatorio/RELATORIO.md)**, organizado por Questão, Objetivo e Motivação, Método e Conclusão, com as figuras e tabelas versionadas em `relatorio/figuras/` e `relatorio/tabelas/`. O modelo preenchível do relatório individual de extensão está em [`relatorio/relatorio-extensao-individual.md`](relatorio/relatorio-extensao-individual.md).

## Dados disponíveis

A fonte presente no repositório é `data/ICB_DADOS_2026.xlsx`, aba `ACUMUL_DESAGREG`; não existe CSV no repositório original. O projeto lê a planilha diretamente e não a altera. Ela possui 46.264 registros, de setembro de 2022 a agosto de 2026, com colunas `Mes_Ano_Data`, `Data_Coleta`, `Estab`, `Produto`, `Marca`, `Preco`, `Quantidade` e `PPK`: 30 produtos e 51 estabelecimentos identificados.

Há 9.818 datas de coleta e 9.346 marcas ausentes e 1.743 duplicatas exatas. A data de coleta está ausente em **100% dos registros a partir de novembro/2025**, o que abrange 10 dos 12 meses-alvo do teste. Embora `PPK` corresponda a `Preco / Quantidade` na tolerância de R$ 0,01, a unidade da quantidade não é documentada para cada produto; não é seguro denominá-lo universalmente preço por quilo. O notebook exploratório detalha valores extremos, cobertura, descrições e quantidades. A interpretação e a origem das medições devem ser validadas com o responsável pelos dados.

## Documentação técnica e teórica

O [guia em docs/](docs/README.md) detalha a construção do alvo, atributos temporais, fundamentos dos quatro modelos comparados, pipeline, métricas, experimentos e limitações.

## Metodologia

- Remove-se somente a duplicata integral, exigem-se mês, produto, supermercado, preço e quantidade válidos, e mantém-se marca ausente como categoria explícita. Datas de coleta fora do mês de referência são excluídas; datas ausentes não são preenchidas. Observações distintas da mesma série no mesmo mês são agregadas pela mediana; preços extremos não são removidos automaticamente.
- Série = supermercado, produto, marca e quantidade. Utiliza-se o preço por embalagem comparável dentro da série. A marca desconhecida pode agrupar itens realmente diferentes.
- São exigidos preços nos meses consecutivos t, t−1 e t−2. O alvo é 1 se `(preço t+1 / preço t) − 1 > 0,02`; exatamente 2% pertence à classe 0. O limite de 2% é justificado pelos próprios dados: 43,5% das variações mensais ficam dentro de ±2%, em 36,4% das transições o preço não muda nem um centavo, e 2% ao mês compostos equivalem a 26,8% ao ano. Sem preço no mês-calendário seguinte, não há alvo. Entram preços e variações históricas, estatísticas da janela t−2 até t, mês cíclico e categorias; o preço futuro nunca é atributo.
- A divisão considera o **mês-alvo**: treino setembro/2022–dezembro/2024; validação janeiro–agosto/2025; teste setembro/2025–agosto/2026. A janela histórica reduz o início efetivo do treino. Transformações são ajustadas somente nos dados de ajuste.
- **Quatro famílias de algoritmos são comparadas** sob o mesmo pré-processamento e o mesmo critério: regressão logística, árvore de decisão, random forest e gradient boosting por histograma — 24 configurações × 17 limiares = 408 candidatos. Só a família linear recebe `StandardScaler`. O critério é maior F1 na validação com precisão ≥ 0,35, com desempate por precisão, menor limiar e nome; o fallback, se necessário, é registrado. Após a seleção, reajusta-se em treino + validação e avalia-se uma vez no teste. As predições de validação são do modelo antes do reajuste.
- Reportam-se precisão, recall, F1, acurácia, acurácia balanceada, ROC-AUC, average precision, Brier e matriz de confusão, com IC de 95% por bootstrap de séries inteiras para as oito métricas numéricas — as 3.180 observações de teste vêm de 785 séries e não são independentes. As regras sempre-zero e repetição da alta anterior são referências sem treinamento, no mesmo teste, e a mesma reamostragem produz o intervalo da diferença. Grupos sem positivos têm recall e F1 indefinidos; precisão sem previsões positivas é reportada como zero por convenção.

## Instalação e execução

É necessário `uv` e Python 3.12. Na raiz do repositório:

```bash
uv sync
uv run jupyter lab
```

Abra os notebooks nesta ordem:

1. `notebooks/01_exploratory_data_analysis.ipynb`: qualidade, cobertura e exploração.
2. `notebooks/02_model_comparison.ipynb`: atributos, comparação entre famílias, seleção e treino. Por padrão não cria uma execução; altere `RUN_TRAINING` para `True`, ou inicie o Jupyter com `BASKET_TRAIN=1 uv run jupyter lab`. Cada chamada intencional cria um diretório novo.
3. `notebooks/03_model_evaluation.ipynb`: carrega automaticamente o último experimento concluído. Altere `EXPERIMENT` para outro diretório se desejar. Executar ou reabrir esse notebook não treina modelo.

Fora do Jupyter, uma execução completa leva cerca de 100 segundos:

```bash
uv run python -c "from basket_price_prediction.experiments import run_training; print(run_training())"
uv run pytest -q
```

## Estrutura e reprodutibilidade

- `data/`: planilha original preservada.
- `notebooks/`: explicações, exploração, comparação de modelos e avaliação.
- `src/basket_price_prediction/`: carregamento, limpeza, atributos, treinamento, avaliação, gráficos e experimentos.
- `tests/`: 28 testes sintéticos de rótulos, lacunas, separação, famílias de algoritmos, critério de seleção, bootstrap, colinearidade, perfil de risco e persistência.
- `docs/`: explicações técnicas e teóricas do projeto e dos modelos.
- `relatorio/`: relatório do trabalho, modelo individual de extensão e cópia versionada de figuras e tabelas.
- `runs/results/<experimento>/`: configuração e métricas JSON, resumo de dados, manifesto, pipeline `joblib`, predições separadas, figuras e relatórios.
- `pyproject.toml`, `uv.lock`: dependências e versões resolvidas.

A pasta `runs/` está no `.gitignore`, portanto os resultados gerados são locais. Por isso `publish_report_assets` copia figuras e tabelas da execução para `relatorio/`, que **é versionado e acompanha a entrega**; a origem exata fica registrada em `relatorio/ORIGEM.txt`.

Cada execução tem identificador UTC com proteção contra colisões; nunca substitui resultados anteriores. O manifesto registra versões, parâmetros, SHA-256 da fonte e do lockfile, horários e status. O hash de commit é `null` porque as instruções locais proíbem comandos Git sem pedido explícito. Execuções interrompidas ou que falhem ficam identificadas como incompletas e não são carregadas como concluídas. O notebook de avaliação confere o hash e reproduz as probabilidades a partir do pipeline salvo. Carregue arquivos `joblib` somente de fontes confiáveis.

## Resultado observado

Experimento: `runs/results/20261125_141318_918857_a808538b_comparacao/` (a reexecução de auditoria reproduziu a seleção, o F1 e a matriz de confusão do teste). Dos 17.002 exemplos elegíveis, 4.957 (29,2%) têm alta superior a 2%. Treino, validação e teste contêm respectivamente 10.268, 3.554 e 3.180 exemplos.

A comparação entre famílias foi decidida na validação:

| Família | Limiar | F1 validação | F1 teste *(diagnóstico posterior)* |
| --- | ---: | ---: | ---: |
| **Random forest** (selecionada) | 0,25 | **0,518** | 0,517 |
| Gradient boosting | 0,25 | 0,475 | *0,534* |
| Árvore de decisão | 0,25 | 0,468 | 0,493 |
| Regressão logística | 0,25 | 0,439 | 0,503 |

A random forest (`max_depth=10`, `min_samples_leaf=5`, `class_weight=None`) teve F1 de 0,518 e precisão de 40,2% na validação. A mesma configuração venceria sem aplicar o piso de 35%. As diferenças entre famílias no teste são descritivas.

| Métrica no teste | Resultado | IC 95% |
|---|---:|:---:|
| Precisão | 0,392 | [0,371 – 0,414] |
| Recall | 0,757 | [0,725 – 0,790] |
| F1 | 0,517 | [0,495 – 0,538] |
| Acurácia / balanceada | 0,591 / 0,640 | [0,571 – 0,611] / [0,623 – 0,657] |
| ROC-AUC | 0,715 | [0,695 – 0,734] |
| Average precision | 0,538 | [0,506 – 0,571] |
| Brier | 0,178 | [0,172 – 0,185] |

A matriz contém 1.183 verdadeiros negativos, 1.078 falsos positivos, 223 falsos negativos e 696 verdadeiros positivos. O IC 95% do ganho de F1 sobre repetir a alta anterior vai de **+0,267 a +0,326**. O IC do ganho de acurácia balanceada sobre nunca alertar vai de **+0,123 a +0,157**. Os dois intervalos ficam acima de zero sob o bootstrap por série.

No teste retrospectivo, a precisão de 39,2% indica que cerca de três em cada cinco alertas foram falsos. O recall mensal variou de 0,559 a 0,860. As variações de um e dois meses apresentaram as maiores importâncias individuais por permutação. Estimar a contribuição do histórico exigiria uma comparação com e sem seus atributos.

## Limitações

Séries incompletas e a exigência de histórico podem enviesar a amostra para itens com maior continuidade. Marcas ausentes podem misturar produtos diferentes; embalagens, descrições, possíveis promoções e coleta não estão totalmente documentadas. A ausência de datas de coleta após outubro/2025 impede verificar diretamente se todas as observações estavam disponíveis no fim do mês de referência. Os atributos de preço são fortemente colineares — `rolling_mean_3m` é combinação linear exata de `price_current`, `price_lag_1` e `price_lag_2`, com VIF infinito —, de modo que coeficientes individuais não são interpretáveis e a leitura do modelo usa importância por permutação. Inflação, custos e outros fatores econômicos não são observados. Os resultados expressam associações, não efeitos causais; são exploratórios e não garantem desempenho futuro.
