# Métricas, incerteza e interpretação dos resultados

Os números desta página vêm da execução `20261125_141318_918857_a808538b_comparacao`. Figuras e tabelas correspondentes estão em [`relatorio/`](../relatorio/RELATORIO.md).

## 📌 Evento positivo e matriz de confusão

A classe positiva é a alta **superior** a 2% no mês seguinte. A matriz do modelo selecionado, no teste temporal:

| Classe real / previsão | 0: sem alerta | 1: alerta | Total |
| --- | ---: | ---: | ---: |
| 0: sem alta superior a 2% | 1.183 verdadeiros negativos (VN) | 1.078 falsos positivos (FP) | 2.261 |
| 1: alta superior a 2% | 223 falsos negativos (FN) | 696 verdadeiros positivos (VP) | 919 |
| Total | 1.406 | 1.774 | 3.180 |

Um falso positivo é um alerta sem alta superior a 2%; um falso negativo é uma alta não sinalizada. No teste, 1.078 dos 1.774 alertas foram falsos, cerca de **60,8%**. Esses números dependem do limiar e do período.

## 🧮 Métricas de classe

| Métrica | Fórmula | Interpretação neste problema |
| --- | --- | --- |
| Precisão | `VP / (VP + FP)` | Entre alertas, fração que realmente apresentou alta. |
| Recall ou sensibilidade | `VP / (VP + FN)` | Entre as altas reais, fração identificada. |
| F1 | `2 × precisão × recall / (precisão + recall)` | Média harmônica entre precisão e recall. |
| Acurácia | `(VP + VN) / N` | Fração de todas as previsões corretas. |
| Acurácia balanceada | `(sensibilidade + especificidade) / 2` | Média dos recalls das duas classes, quando ambas estão presentes. |
| Taxa de positivos previstos | `(VP + FP) / N` | Frequência com que a regra emite alerta. |

As classes estão desbalanceadas: 919 de 3.180 observações do teste, cerca de 28,9%, são positivas. Prever sempre classe 0 atinge acurácia de 71,1% sem encontrar alta alguma. Por isso acurácia isolada é insuficiente para a pergunta principal, e o critério de seleção usa F1.

## 📏 Intervalos de confiança: por que reamostrar séries

As 3.180 observações do teste **não são independentes**. Elas vêm de 785 séries, com média de 4,1 observações por série, e a mesma série reaparece em meses consecutivos com preços correlacionados. Um intervalo que tratasse cada linha como observação independente seria estreito demais.

Os intervalos usam **bootstrap por série**: cada uma das 2.000 reamostras sorteia 785 séries *inteiras* com reposição, preservando a dependência interna de cada uma. Reamostras que porventura fiquem com uma única classe são descartadas.

| Métrica no teste | Estimativa | IC 95% |
| --- | ---: | :---: |
| Precisão | 0,392 | [0,371 – 0,414] |
| Recall | 0,757 | [0,725 – 0,790] |
| F1 | 0,517 | [0,495 – 0,538] |
| Acurácia | 0,591 | [0,571 – 0,611] |
| Acurácia balanceada | 0,640 | [0,623 – 0,657] |
| ROC-AUC | 0,715 | [0,695 – 0,734] |
| Average precision | 0,538 | [0,506 – 0,571] |
| Brier | 0,178 | [0,172 – 0,185] |

## 🆚 Comparação com as referências e significância

| Resultado | Modelo selecionado | Sempre classe 0 | Repete alta anterior |
| --- | ---: | ---: | ---: |
| Precisão | 0,392 | 0,000 | 0,225 |
| Recall | 0,757 | 0,000 | 0,217 |
| F1 | **0,517** | 0,000 | 0,220 |
| Acurácia | 0,591 | **0,711** | 0,558 |

As duas referências são regras sem treinamento, avaliadas nas **mesmas linhas** do teste. "Repete alta anterior" prevê classe 1 se o preço de `t` subiu mais de 2% frente a `t−1`; não usa o preço futuro.

A mesma reamostragem por série produz o intervalo da **diferença** entre modelo e referência, que é o que responde se o ganho é real ou ruído amostral:

| Diferença | IC 95% | Contém zero? |
| --- | :---: | :---: |
| Ganho de F1 sobre "repete alta anterior" | **[+0,267 – +0,326]** | Não |
| Ganho de acurácia balanceada sobre "sempre classe 0" | **[+0,123 – +0,157]** | Não |

Ambos excluem zero com folga: **o ganho sobre as duas referências é estatisticamente significativo**. A acurácia do modelo ser menor que a da regra trivial é esperado e desejado — troca-se acerto na classe majoritária por capturar 696 das 919 altas, contra zero da regra trivial.

O código retorna zero para precisão sem positivos previstos; para grupos sem positivos reais, recall e F1 são `null`. Acurácia balanceada e ROC-AUC são `null` quando falta uma classe.

## 🏁 Comparação entre famílias de algoritmos

| Família | Melhor configuração | Limiar | F1 validação | F1 teste *(post-hoc)* |
| --- | --- | ---: | ---: | ---: |
| **Random forest** | `max_depth=10, min_samples_leaf=5` | 0,25 | **0,518** | 0,517 |
| Gradient boosting | `learning_rate=0,05` | 0,25 | 0,475 | *0,534* |
| Árvore de decisão | `max_depth=10` | 0,25 | 0,468 | 0,493 |
| Regressão logística | `C=10` | 0,25 | 0,439 | 0,503 |

A seleção foi decidida na coluna de validação, onde a random forest superou a regressão logística em 0,079 de F1. A coluna de teste é diagnóstico posterior, descrito em [pipeline e seleção](04-pipeline-e-selecao.md), e não realimentou escolha alguma.

Duas leituras importam. A primeira é que **o modelo linear não era a melhor escolha** para este problema — a hipótese inicial do projeto foi contrariada pela evidência. A explicação está na forma da relação entre variação passada e alta futura, medida no treino e salva em `reports/risk_by_variation.csv`: o risco cai de 0,643 (queda anterior maior que 20%) para 0,204 (preço inalterado) e volta a subir para 0,313 na faixa de 2 a 5%. O mínimo coincide com o regime de preço rígido, que concentra 36% das observações, e as inclinações de cada lado desse ponto são muito diferentes. Uma fronteira linear no logito não representa esse ponto anguloso; um corte de árvore o isola. A segunda é que **a faixa entre as quatro famílias no teste (0,04 em F1) é menor que a meia-largura do IC do próprio F1 (±0,02)**: elas são estatisticamente próximas e a ordem entre elas não é estável, tanto que o vencedor da validação não foi o vencedor do teste.

## 📈 Curvas e qualidade das probabilidades

**Curva precisão–recall:** a *average precision* (AP) resume a curva ponderando precisão pelos incrementos de recall; não é necessariamente a área trapezoidal interpolada. AP = 0,538, acima da prevalência de 0,289, referência útil sob esse desbalanceamento.[^1]

**ROC e ROC-AUC:** ROC-AUC de 0,715 indica capacidade de ordenar positivos acima de negativos nesta amostra. Ela não determina o limiar nem informa, sozinha, quantos alertas serão úteis.

**Brier:** média de `(pᵢ − yᵢ)²`, igual a 0,178 no teste; quanto menor, melhor. Reflete calibração e outras propriedades da distribuição, e não deve ser tratado como medida pura de calibração.

**Calibração:** o gráfico agrupa as predições em decis e compara probabilidade média com frequência observada, acompanhando a diagonal na faixa central. Nenhum calibrador adicional é aplicado; a curva é descritiva e não garante calibração futura.[^2]

## 🔍 O que o modelo usa

Importância por permutação sobre os 15 atributos de entrada, medindo a queda da average precision no teste ao embaralhar cada atributo:

| Atributo | Queda na average precision |
| --- | ---: |
| `variation_1m` | **+0,066** |
| `variation_2m` | **+0,039** |
| `product` | +0,011 |
| `rolling_std_3m` | +0,011 |
| `brand` | +0,006 |
| `price_current`, `rolling_mean_3m`, `rolling_min_3m` | ≈ 0 ou negativo |

**O sinal está nas variações relativas, não nos níveis de preço.** Esse achado tem consequência metodológica favorável: o nível médio de preço sobe de R$ 12,83 no treino para R$ 15,31 no teste, deriva inflacionária de cerca de 19%. Um modelo que dependesse do nível absoluto degradaria entre as partições; como o nível é praticamente ignorado, o modelo está protegido dessa deriva na prática.

Importância baixa não prova irrelevância: atributos redundantes dividem o crédito, e a medida continua sendo associação, não causalidade.

## 🗓️ Estabilidade e diferenças por produto

Nos 12 meses de teste, o recall variou de **0,559** (março/2026, 59 positivos) a **0,860** (janeiro/2026, 100 positivos); a precisão, de 0,341 a 0,558. Não há degradação sistemática ao longo do período: a correlação entre posição do mês e F1 é r = +0,053 (p = 0,87), e nem recall (r = −0,398, p = 0,20) nem precisão (r = +0,211, p = 0,51) têm tendência significativa — apesar de o modelo ter sido ajustado com dados até agosto/2025 e o último mês avaliado ser agosto/2026.

Entre produtos com pelo menos 30 observações, batata (recall 0,986), café (0,962) e frango peito (0,936) lideram; pão francês (0,389), óleo (0,390) e feijão (0,394) ficam na base. O custo aparece na precisão — café gera 138 falsos positivos e arroz 112, com precisão de 0,270 e 0,273.

A hipótese de que produtos mais voláteis tenham altas mais detectáveis **não se confirma** com os dados disponíveis: a correlação entre o desvio padrão da variação mensal do produto e seu recall é r = +0,343, não significativa com 14 produtos (p = 0,23). O arroz é o menos volátil da lista (0,070) e tem recall 0,857; o pão francês é mais volátil (0,135) e tem recall 0,389. A hipótese permanece em aberto.

Essas comparações são descritivas. Número de positivos, composição de séries, dependência temporal e multiplicidade afetam a força das conclusões; os relatórios da execução trazem as contagens completas.

## 🧭 Resposta à pesquisa

O histórico recente de preços **contém sinal preditivo real** sobre altas acima de 2%: o modelo identifica 75,7% delas (IC 95%: 72,5%–79,0%), contra 21,7% da melhor referência sem treinamento, com ganho de F1 cujo IC 95% exclui zero. A ressalva quantificada é a precisão de 0,392: três em cada cinco alertas são falsos. O estudo não estima retorno financeiro, custos de estoque nem garante generalização para fora do período e da amostra elegível.

[^1]: Scikit-learn, *average_precision_score*, https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html.
[^2]: Scikit-learn, *Probability calibration*, https://scikit-learn.org/stable/modules/calibration.html.
