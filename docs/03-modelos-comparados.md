# Fundamentos dos modelos comparados

Quatro famílias de classificadores supervisionados disputam o mesmo problema sob o mesmo pré-processamento e o mesmo critério de seleção. Elas diferem no **viés indutivo**: o tipo de fronteira que cada uma consegue representar. Comparar famílias com vieses diferentes é o que transforma "usei um modelo" em "escolhi este modelo porque".

| Família | Fronteira que representa | Custo e risco |
| --- | --- | --- |
| Regressão logística | Linear no logito | Barata e interpretável; não representa relações em U |
| Árvore de decisão | Cortes retangulares sucessivos | Legível; instável e propensa a ajuste excessivo |
| Random forest | Média de muitas árvores decorrelacionadas | Reduz variância; perde a leitura direta de regras |
| Gradient boosting | Soma de árvores rasas que corrigem resíduos | Costuma dominar dados tabulares; mais sensível a hiperparâmetros |

Todas estimam a mesma quantidade: `P(y = 1 | x)`, a probabilidade de alta superior a 2% no mês seguinte. A decisão binária vem depois, pelo limiar.

## 🎯 Regressão logística

Para atributos transformados `x = (x₁, ..., xₚ)`, o modelo calcula:

```text
z = β₀ + β₁x₁ + β₂x₂ + ... + βₚxₚ
p = σ(z) = 1 / (1 + exp(−z))
```

`z` é um escore real e `σ` é a função logística, que o mapeia para o intervalo de 0 a 1. Por exemplo, `z = 0` resulta em `p = 0,5`. O modelo é linear **no logito**, não necessariamente na probabilidade.

### Chances e logito

A chance (*odds*) de um evento com probabilidade `p` é `p / (1 − p)`. O logito é o logaritmo natural dessa chance:

```text
logito(p) = ln(p / (1 − p)) = β₀ + Σ βⱼxⱼ
```

Se um único atributo transformado aumenta uma unidade e todos os demais ficam fixos, o logito varia em `βⱼ`, e a chance é multiplicada por `exp(βⱼ)`. Isso não significa que a probabilidade aumente em `βⱼ` pontos percentuais. Um coeficiente hipotético `β = ln(2)` dobra a chance: se ela era 1 para 1 (`p = 0,5`), passa a 2 para 1 (`p ≈ 0,667`).

Para atributos numéricos deste projeto, uma unidade no espaço transformado corresponde a um desvio padrão estimado no conjunto de ajuste, não a R$ 1 ou um ponto percentual.

### Como os parâmetros são aprendidos

O ajuste minimiza uma função de perda logarítmica, equivalente a maximizar a verossimilhança, junto com uma penalidade de regularização:

```text
perda logarítmica = − Σᵢ [ yᵢ ln(pᵢ) + (1−yᵢ) ln(1−pᵢ) ]
objetivo qualitativo = perda logarítmica ponderada + penalidade L2
```

A escrita acima mostra a ideia geral; normalizações, pesos e tratamento do intercepto dependem da implementação. No scikit-learn, `liblinear` representa o intercepto por uma característica sintética e o regulariza também. Uma predição confiante e errada recebe penalidade alta.

A penalidade L2 desestimula coeficientes de grande magnitude. `C` controla inversamente a intensidade da regularização: menor `C` implica regularização mais forte. O projeto avalia `C ∈ {0,1; 1; 10}` e pesos `None` e `"balanced"`.[^1]

## 🌳 Árvore de decisão

A árvore particiona o espaço de atributos por cortes sucessivos do tipo `atributo ≤ valor`. Em cada nó, escolhe-se o corte que mais reduz a impureza das classes resultantes; o padrão do scikit-learn é o índice de Gini:

```text
Gini(nó) = 1 − Σ_k p_k²
```

onde `p_k` é a proporção da classe `k` naquele nó. Um nó puro tem Gini igual a zero. A folha prevê a proporção de positivos observada nela, que é usada diretamente como probabilidade.

Duas propriedades importam aqui. A primeira é que a árvore **captura relações não monótonas e pontos angulosos sem que eles sejam especificados**. O perfil descritivo do treino ilustra por que essa flexibilidade pode ser relevante: o risco cai de 0,643 para 0,204 conforme a variação do mês anterior vai de −20% até zero, atinge o mínimo exatamente no regime de preço inalterado — onde se concentram 36% das observações — e volta a subir modestamente em 2 a 5%. Um logito linear em `variation_1m` não produz um mínimo local nesse ponto com inclinações tão diferentes de cada lado; um corte de árvore isola esse regime diretamente. A segunda é que a árvore é **invariante a transformação monotônica** dos atributos: padronizar não muda corte algum, razão pela qual o `StandardScaler` é aplicado somente ao modelo linear.

O controle de ajuste excessivo é feito por `max_depth ∈ {3, 5, 10}` com `min_samples_leaf = 50` fixo, que impede folhas minúsculas memorizando séries individuais.[^2]

## 🌲 Random forest

Uma árvore isolada tem variância alta: pequenas mudanças nos dados produzem árvores muito diferentes. A random forest ataca exatamente esse problema ajustando muitas árvores sobre amostras *bootstrap* dos dados e sorteando um subconjunto de atributos em cada corte. A probabilidade final é a média das probabilidades das árvores.

```text
p(x) = (1/B) Σ_b p_b(x)
```

A média de `B` preditores aproximadamente não enviesados e **pouco correlacionados entre si** reduz a variância sem elevar o viés na mesma proporção — é daí que vem o ganho. O sorteio de atributos por corte existe para decorrelacionar as árvores; sem ele, todas tenderiam a usar o mesmo atributo dominante na raiz.

O projeto usa `n_estimators = 300` fixo, com `max_depth ∈ {None, 10}`, `min_samples_leaf ∈ {5, 20}` e `class_weight ∈ {None, "balanced_subsample"}`.[^3]

Uma consequência prática relevante para esta base: por fazer cortes univariados, a floresta **tolera atributos fortemente correlacionados** sem o problema de indeterminação que a colinearidade causa nos coeficientes lineares. A importância, porém, se dilui entre atributos redundantes, razão pela qual a interpretação usa permutação sobre os atributos de entrada.

## 📈 Gradient boosting por histograma

Enquanto a floresta constrói árvores **em paralelo** e tira a média, o boosting as constrói **em sequência**, cada uma corrigindo o erro acumulado das anteriores. O modelo é uma soma de árvores rasas:

```text
F_m(x) = F_(m−1)(x) + ν · h_m(x)
```

onde `h_m` é ajustada ao gradiente negativo da perda logarítmica em `F_(m−1)` e `ν` é a taxa de aprendizado (`learning_rate`), que encolhe cada contribuição. Taxa menor exige mais árvores, mas costuma generalizar melhor.

A variante `HistGradientBoostingClassifier` agrupa os valores de cada atributo em histogramas de até 256 compartimentos antes de procurar cortes, o que torna o ajuste muito mais rápido com perda desprezível de qualidade. O projeto usa `max_iter = 300` com `early_stopping` desligado — a parada antecipada reservaria internamente uma fração dos dados, o que introduziria uma divisão aleatória não cronológica dentro do treino.

Avaliam-se `learning_rate ∈ {0,05; 0,1}` e `class_weight ∈ {None, "balanced"}`.[^4]

## ⚖️ Pesos de classe

As classes são desbalanceadas: cerca de 29% de positivos. Com `class_weight="balanced"`, o scikit-learn pondera cada classe inversamente à sua frequência no conjunto de ajuste, aumentando o custo de errar a classe minoritária. Isso modifica a função otimizada e desloca as probabilidades estimadas.

Pesos de classe e limiar de decisão atacam o mesmo desequilíbrio por caminhos diferentes, e o projeto avalia os dois conjuntamente em vez de assumir que um deles basta. Na execução documentada, todas as quatro famílias selecionaram `class_weight = None` com limiar `0,25` — ou seja, ajustar o limiar foi suficiente, e reponderar as classes não acrescentou ganho.

## 🔍 Interpretação: por que permutação, e não coeficientes

Os coeficientes da regressão logística descrevem associações condicionais no modelo ajustado, nunca causa e efeito. Neste conjunto de atributos há um problema adicional e mais severo: `rolling_mean_3m` é, por construção, `(price_current + price_lag_1 + price_lag_2) / 3`, uma **combinação linear exata** dos outros três. O VIF desses quatro atributos é infinito, e a repartição do peso entre eles é matematicamente indeterminada — veja `relatorio/tabelas/collinearity.csv`.

Soma-se a isso que árvores e florestas não possuem coeficientes, e que `feature_importances_` baseada em impureza é enviesada a favor de atributos contínuos e de alta cardinalidade.

Por isso a interpretação usa **importância por permutação sobre os 15 atributos de entrada**, medindo a queda da *average precision* no teste ao embaralhar cada atributo. A medida é comparável entre famílias, atua antes do one-hot (e portanto não fragmenta categorias em dezenas de colunas) e não depende da forma funcional do modelo. Ela continua sendo associação, não causalidade: um atributo redundante pode mostrar importância baixa simplesmente porque outro carrega a mesma informação.

[^1]: Scikit-learn, *LogisticRegression*, https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html.
[^2]: Scikit-learn, *Decision Trees*, https://scikit-learn.org/stable/modules/tree.html.
[^3]: Scikit-learn, *Forests of randomized trees*, https://scikit-learn.org/stable/modules/ensemble.html#forest.
[^4]: Scikit-learn, *Histogram-Based Gradient Boosting*, https://scikit-learn.org/stable/modules/ensemble.html#histogram-based-gradient-boosting.
