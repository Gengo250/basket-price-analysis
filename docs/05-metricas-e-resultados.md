# Métricas e interpretação dos resultados

## 📌 Evento positivo e matriz de confusão

A classe positiva é a alta **superior** a 2% no mês seguinte. A matriz da execução `20261114_142933_489430_ab7cee47_logreg`, no teste temporal, tem linhas reais e colunas previstas:

| Classe real / previsão | 0: sem alerta | 1: alerta | Total |
| --- | ---: | ---: | ---: |
| 0: sem alta superior a 2% | 1.246 verdadeiros negativos (VN) | 1.015 falsos positivos (FP) | 2.261 |
| 1: alta superior a 2% | 270 falsos negativos (FN) | 649 verdadeiros positivos (VP) | 919 |
| Total | 1.516 | 1.664 | 3.180 |

Um falso positivo é um alerta sem alta superior a 2%; um falso negativo é uma alta que não foi sinalizada. No teste, 1.015 dos 1.664 alertas foram falsos, aproximadamente 61,0%. Esses números dependem do limiar e do período.

## 🧮 Métricas de classe

| Métrica | Fórmula | Interpretação neste problema |
| --- | --- | --- |
| Precisão | `VP / (VP + FP)` | Entre alertas, fração que realmente apresentou alta. |
| Recall ou sensibilidade | `VP / (VP + FN)` | Entre as altas reais, fração identificada. |
| F1 | `2 × precisão × recall / (precisão + recall)` | Média harmônica entre precisão e recall. |
| Acurácia | `(VP + VN) / N` | Fração de todas as previsões corretas. |
| Acurácia balanceada | `(sensibilidade + especificidade) / 2` | Média dos recalls das duas classes, quando ambas estão presentes. |
| Taxa de positivos previstos | `(VP + FP) / N` | Frequência com que a regra emite alerta. |

As classes estão desbalanceadas: 919 de 3.180 observações do teste, cerca de 28,9%, são positivas. Sempre prever classe 0 atinge acurácia de 71,1%, mas deixa de encontrar todas as altas. Portanto acurácia isolada é insuficiente para a pergunta principal.

| Resultado | Regressão logística | Sempre classe 0 | Repete alta anterior |
| --- | ---: | ---: | ---: |
| Precisão | 0,390 | 0,000 | 0,225 |
| Recall | 0,706 | 0,000 | 0,217 |
| F1 | 0,503 | 0,000 | 0,220 |
| Acurácia | 0,596 | 0,711 | 0,558 |

As duas referências são regras sem treinamento e usam as mesmas linhas elegíveis do teste. “Repete alta anterior” indica classe 1 se o preço de `t` subiu mais de 2% frente a `t−1`; não usa o preço futuro. Essa comparação contextualiza, mas não prova utilidade financeira.

O código retorna zero para precisão sem positivos previstos; para grupos sem casos positivos reais, recall e F1 são `null`. Acurácia balanceada e ROC-AUC são `null` quando falta uma classe. Pequenos grupos exigem cautela mesmo quando as métricas são calculáveis.

## 📈 Curvas e qualidade das probabilidades

**Curva precisão–recall:** avalia precisão e recall em vários limiares. A *average precision* (AP) resume a curva ponderando precisão pelos incrementos de recall; não é necessariamente a área trapezoidal interpolada. Neste teste, AP = 0,523, acima da prevalência de 0,289, uma referência útil para ordenação sob esse desbalanceamento.[^1]

**ROC e ROC-AUC:** a curva relaciona recall e taxa de falsos positivos para diferentes limiares; ROC-AUC de 0,702 indica capacidade de ordenar positivos acima de negativos nesta amostra. ROC-AUC não determina o limiar escolhido nem informa, sozinha, quantos alertas serão úteis.

**Brier:** média de `(pᵢ − yᵢ)²`; quanto menor, melhor para esse escore. O valor do teste foi 0,181. Ele reflete tanto calibração quanto outras propriedades da distribuição das probabilidades e não deve ser tratado como medida pura de calibração.

**Calibração:** entre previsões com probabilidade próxima de 0,3, espera-se uma frequência de positivos próxima de 30% se elas estiverem calibradas para aquele grupo e população. O gráfico de calibração agrupa as predições em decis e compara probabilidade média e frequência observada. Não é aplicado um calibrador adicional; a curva descritiva não garante calibração futura.[^2]

## 🗓️ Estabilidade e diferenças por produto

O recall mensal no teste variou de 0,553 a 0,862. Por exemplo, junho de 2026 teve 47 positivos e recall 0,553; dezembro de 2025 teve 87 positivos e recall 0,862. Isso mostra variação observada, não prova de que um mês do ano seja intrinsecamente mais fácil.

Entre os produtos com pelo menos 30 observações totais, pão francês teve recall 0,222 em 18 positivos, enquanto batata teve recall 0,958 em 72 positivos. Arroz teve recall 0,939, mas também 117 falsos positivos. Essas comparações são descritivas: número de positivos, composição de séries, dependência temporal e incerteza afetam a força das conclusões. Os relatórios incluem contagens completas por produto, supermercado e mês.

## 🧭 Resposta à pesquisa

Os resultados são compatíveis com a existência de sinal preditivo no período e na amostra elegíveis: a regressão logística superou as referências descritivas em recall/F1 e apresentou AP acima da prevalência. Entretanto, 61% dos alertas foram falsos, o recall variou no tempo e o estudo não estima retorno financeiro, custos ou garantia de generalização. A conclusão é exploratória e condicionada às limitações da fonte e do protocolo.

[^1]: Scikit-learn, *average_precision_score*, https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html.
[^2]: Scikit-learn, *Probability calibration*, https://scikit-learn.org/stable/modules/calibration.html.
