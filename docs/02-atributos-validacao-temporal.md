# Atributos e validação temporal

## ⏱️ Linha do tempo de um exemplo

Considere a previsão feita ao fim de agosto de 2025 para o mês-alvo setembro de 2025. A construção utiliza preços de junho, julho e agosto; o preço de setembro é reservado ao cálculo do alvo. A disponibilidade ao fim do mês é uma hipótese do experimento e não pode ser totalmente comprovada quando a data de coleta está ausente.

```text
junho 2025       julho 2025       agosto 2025          setembro 2025
   P_(t-2)          P_(t-1)             P_t               P_(t+1)
      └──────── atributos disponíveis até t ────────┘      └─ alvo ─┘
```

As funções estão em [features.py](../src/basket_price_prediction/features.py); a lista efetivamente fornecida ao modelo está em [config.py](../src/basket_price_prediction/config.py).

## 📊 Atributos numéricos

Todos são calculados por série e usam no máximo o mês `t`:

| Atributo | Definição |
| --- | --- |
| `price_current` | Preço mensal `P_t`. |
| `price_lag_1`, `price_lag_2` | Preços `P_(t−1)` e `P_(t−2)`, quando esses meses de calendário existem. |
| `variation_1m` | `P_t / P_(t−1) − 1`. |
| `variation_2m` | `P_t / P_(t−2) − 1`; é variação acumulada de dois meses, não a soma das variações. |
| `rolling_mean_3m` | Média de `P_(t−2)`, `P_(t−1)` e `P_t`. |
| `rolling_std_3m` | Desvio padrão populacional dessa janela, com `ddof=0`. |
| `rolling_min_3m`, `rolling_max_3m` | Mínimo e máximo dos mesmos três preços. |
| `month_sin`, `month_cos` | `sen(2πm/12)` e `cos(2πm/12)`, para mês `m` de 1 a 12. |

A codificação cíclica aproxima dezembro e janeiro no círculo, evitando tratar os meses como categorias numéricas em linha reta. Por exemplo, junho e dezembro ficam em posições opostas. Ela representa sazonalidade anual potencial, mas não comprova que exista sazonalidade estável.

Os lags são obtidos após ordenar a série e são aceitos somente se a diferença entre os meses de calendário corresponder a 1 ou 2. O cálculo requer ambos os lags, impedindo que uma observação antiga seja tratada como o mês imediatamente anterior. Não há interpolação de preço nem atributo de mediana de mercado implementado.

## 🏷️ Categorias e colunas reservadas

As categorias são supermercado, produto, marca e quantidade. A quantidade é convertida em texto para ser tratada como identificador de embalagem. Mês, mês-alvo, alvo e variação futura ficam disponíveis para identificar linhas e avaliar, mas não pertencem à lista `FEATURES`. O preço futuro é usado na construção do rótulo e não é passado ao pipeline.

`OneHotEncoder` e `StandardScaler` são ajustados dentro do pipeline: durante a seleção, apenas no treino; no modelo final, no conjunto combinado de treino e validação. Esse cuidado impede que estatísticas de escala ou categorias do teste influenciem o ajuste. O `StandardScaler` é aplicado somente à família linear, pelos motivos descritos em [pipeline e comparação](04-pipeline-e-selecao.md).

## 🗓️ Divisão por mês-alvo

| Partição | Intervalo configurado do mês-alvo | Exemplos | Positivos |
| --- | --- | ---: | ---: |
| Treino | setembro/2022 a dezembro/2024 | 10.268 | 3.068 |
| Validação | janeiro/2025 a agosto/2025 | 3.554 | 970 |
| Teste | setembro/2025 a agosto/2026 | 3.180 | 919 |

Devido ao histórico mínimo, o primeiro alvo efetivo do treino foi dezembro de 2022. Em setembro de 2025, o teste usa informações até agosto de 2025. `temporal_split` verifica conjuntos não vazios, não sobreposição de meses-alvo e ordem cronológica; não há divisão aleatória nem validação cruzada aleatória.

O conjunto de validação escolhe família de algoritmo, hiperparâmetros e limiar. Em seguida, o pipeline selecionado é reajustado em treino mais validação. O teste é avaliado após essa escolha. As predições de validação salvas vêm do modelo treinado **antes** do reajuste e não são uma avaliação independente do pipeline final.

## 🛡️ Riscos de vazamento e fronteiras

- `P_(t+1)`, `actual_change` e `target` não são atributos; alterar o preço futuro não deve alterar os atributos de `t`.
- Dados do teste não são usados para escolher família de algoritmo, hiperparâmetros ou limiar; `select_model` recebe apenas treino e validação, e há teste que inspeciona sua assinatura.
- Transformações não são ajustadas no conjunto completo antes da divisão.
- A hipótese de que cada preço do mês estava disponível ao fechar o mês não pode ser verificada para as coletas sem data; isso é uma limitação de disponibilidade, não uma prova de vazamento.
- Série contínua e alvo observado são critérios de seleção; os resultados não se aplicam automaticamente às séries excluídas.

Os 28 testes sintéticos em [tests](../tests/) verificam, entre outros pontos, separação das séries, lacunas, janela histórica, alvos, ajuste do pré-processamento e o fato de que `select_model` não aceita o conjunto de teste em sua assinatura. Como referência adicional sobre o risco de contaminação do conjunto de teste, consulte as [recomendações do scikit-learn para evitar vazamento](https://scikit-learn.org/stable/common_pitfalls.html#data-leakage).[^1]

[^1]: Scikit-learn, *Common pitfalls and recommended practices: Data leakage*, https://scikit-learn.org/stable/common_pitfalls.html#data-leakage.
