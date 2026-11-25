# Pipeline, comparação de algoritmos e limiar de decisão

## 🔗 Transformação dos atributos

O pipeline é definido em [training.py](../src/basket_price_prediction/training.py). `ColumnTransformer` aplica um tratamento a cada grupo de colunas, e a saída alimenta um dos quatro classificadores comparados.

| Grupo | Transformação | Efeito |
| --- | --- | --- |
| Numérico, modelo linear | `StandardScaler` | Subtrai a média e divide pelo desvio padrão estimados no ajuste. |
| Numérico, árvores | `passthrough` | Nenhuma. Árvores são invariantes a transformação monotônica; padronizar não mudaria corte algum. |
| Categórico | `OneHotEncoder(handle_unknown="ignore")` | Aprende as categorias observadas no ajuste e cria indicadores binários. |

Aplicar escala só onde ela importa é decisão metodológica, não economia de código: padronizar árvores sugeriria uma dependência que elas não têm. Com 29 estabelecimentos, 14 produtos, 76 marcas e 5 quantidades no treino, o one-hot produz 124 colunas — baixo o bastante para usar saída densa, exigida pelo gradient boosting por histograma.

O escalonador e o codificador aprendem no treino durante a seleção e novamente em treino + validação no ajuste final. Categorias desconhecidas na transformação geram zeros em todos os indicadores daquela variável; isso permite processar o exemplo sem criar informação aprendida sobre a categoria inédita.[^1]

Não há imputador no pipeline: linhas sem o histórico exigido são excluídas antes do ajuste, e marca ausente recebe rótulo categórico explícito na limpeza.

## 🧪 Busca na validação

A busca percorre **quatro famílias de algoritmos**, descritas em [modelos comparados](03-modelos-comparados.md):

| Família | Grade | Configurações |
| --- | --- | ---: |
| Regressão logística | `C ∈ {0,1; 1; 10}` × `class_weight ∈ {None, balanced}` | 6 |
| Árvore de decisão | `max_depth ∈ {3, 5, 10}` × `class_weight ∈ {None, balanced}` | 6 |
| Random forest | `max_depth ∈ {None, 10}` × `min_samples_leaf ∈ {5, 20}` × `class_weight ∈ {None, balanced_subsample}` | 8 |
| Gradient boosting | `learning_rate ∈ {0,05; 0,1}` × `class_weight ∈ {None, balanced}` | 4 |

Para cada uma das **24 configurações**, o código ajusta no treino, calcula probabilidades na validação e testa 17 limiares de `0,10` a `0,90` em passos de `0,05`: **408 pares configuração-limiar avaliados**. O ajuste ocorre 24 vezes; não se cria um classificador por limiar. A tabela integral fica em `reports/validation_candidates.csv`.

## 🎚️ Critério de seleção

A função `rank_candidates` concentra o critério em um único lugar:

> **Maior F1 da classe positiva entre os candidatos com precisão ≥ 0,35 na validação.** Desempate por maior precisão, depois menor limiar, depois nome do algoritmo.

F1 porque a assimetria de custo descrita em [problema e alvo](01-problema-dados-alvo.md) exige equilibrar recall e precisão, e acurácia é inadequada: prever sempre "sem alta" já atinge 71,1%. O piso de precisão impede que o critério degenere — sem ele, o melhor F1 da grade viria de um candidato que emite alerta quase sempre. O desempate por nome do algoritmo existe apenas para tornar a escolha determinística quando tudo mais empata.

Se nenhum candidato atingir a precisão mínima, o sistema escolhe o melhor F1 entre todos e registra esse *fallback* na configuração. O piso de 35% é decisão metodológica declarada, não garantia de precisão em novos períodos.

A mesma função é reaplicada **dentro de cada família** por `best_per_algorithm`, de modo que a comparação entre algoritmos use exatamente o critério que selecionou o vencedor — e não um critério mais favorável a um deles.

## 🔬 Diagnóstico posterior por família

Depois que a seleção está fechada, a melhor configuração de **cada** família é reajustada em treino + validação e avaliada no teste. Essa tabela vai para `reports/model_comparison.csv` e para a figura `model_comparison.png`.

Ela é **diagnóstico de transparência, não critério**. Nenhuma escolha de algoritmo, hiperparâmetro ou limiar foi revista depois de vê-la; o campo `post_hoc_note` em `config.json` registra isso junto aos resultados. A distinção importa: na execução documentada, a random forest venceu na validação mas o gradient boosting obteve o melhor F1 de teste. Trocar a escolha nesse ponto converteria o teste em conjunto de seleção e destruiria a única estimativa não enviesada disponível.

A leitura correta é que a diferença entre as quatro famílias no teste (0,04 em F1) é **menor que a meia-largura do intervalo de confiança do próprio F1** (±0,02), ou seja, as famílias são estatisticamente próximas e a ordem entre elas não é estável.

## 🎯 Probabilidade e decisão são coisas diferentes

Todo modelo retorna uma probabilidade `p`. A regra de decisão implementada é:

```text
previsão = 1, se p >= limiar
previsão = 0, se p < limiar
```

Um limiar menor tende a marcar mais observações como positivas; em geral aumenta a captura de altas e também os falsos positivos. Precisão não varia monotonicamente em dados finitos. O limiar é escolhido na validação, nunca no teste, e fica salvo em `config.json`, separado do objeto `joblib`.

Na execução documentada, a seleção foi `random_forest` com `max_depth=10`, `min_samples_leaf=5`, `class_weight=None` e limiar `0,25`. As quatro famílias convergiram para o mesmo limiar de 0,25 — indício de que a posição do corte é imposta pelo desequilíbrio de classes e pelo critério, mais do que pelo algoritmo.

O limiar foi escolhido para o modelo ajustado apenas no treino e mantido após o reajuste em treino + validação. Como o reajuste altera a distribuição de probabilidades, precisão e recall do teste não são garantidos pela validação. O pipeline salvo contém o modelo reajustado.

## 🔄 Sequência executada

1. Preparar séries mensais e exemplos elegíveis.
2. Dividir por mês-alvo em treino, validação e teste.
3. Ajustar as 24 configurações somente no treino.
4. Escolher família, hiperparâmetros e limiar usando apenas a validação.
5. Salvar as predições de validação do modelo pré-reajuste.
6. Reajustar a melhor configuração de cada família em treino + validação.
7. Gerar predições e métricas no teste, com intervalos por bootstrap de séries.
8. Salvar pipeline, metadados, comparação entre famílias e diagnóstico de colinearidade.

Não há validação cruzada aleatória, que embaralharia a ordem temporal. Uma avaliação futura com várias janelas deslizantes investigaria estabilidade, desde que se reserve novo período de teste independente ao final.

[^1]: Scikit-learn, *OneHotEncoder*, https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html; *StandardScaler*, https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html.
