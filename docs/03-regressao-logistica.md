# Fundamentos da regressão logística

## 🎯 O que o modelo estima

A regressão logística é um classificador supervisionado que, neste projeto, estima a probabilidade condicional do evento `y = 1`: alta superior a 2% no mês seguinte, dadas as características disponíveis para a série no mês de previsão. O nome contém “regressão” porque há uma combinação linear de atributos no modelo; a saída usada aqui é uma classificação binária e uma probabilidade.

Para atributos transformados `x = (x₁, ..., xₚ)`, o modelo calcula:

```text
z = β₀ + β₁x₁ + β₂x₂ + ... + βₚxₚ
p = σ(z) = 1 / (1 + exp(−z))
```

`z` é um escore real e `σ` é a função logística, que o mapeia para o intervalo de 0 a 1. Por exemplo, `z = 0` resulta em `p = 0,5`. O modelo é linear **no logito**, não necessariamente na probabilidade. Como os atributos são derivados da história e das categorias, a probabilidade estimada pode mudar de maneira não linear quando o preço original muda.

A probabilidade é uma estimativa aprendida nos dados disponíveis, não uma frequência garantida para cada produto. Sua interpretação depende de calibração e de a relação aprendida continuar válida em outros períodos.

## 📐 Chances e logito

A chance (*odds*) de um evento com probabilidade `p` é `p / (1 − p)`. O logito é o logaritmo natural dessa chance:

```text
logito(p) = ln(p / (1 − p)) = β₀ + Σ βⱼxⱼ
```

Se um único atributo transformado aumenta uma unidade e todos os demais ficam fixos, o logito varia em `βⱼ`, e a chance é multiplicada por `exp(βⱼ)`. Isso não significa que a probabilidade aumente em `βⱼ` pontos percentuais. Por exemplo, um coeficiente hipotético `β = ln(2)` dobra a chance: se ela era 1 para 1 (`p = 0,5`), passa a 2 para 1 (`p ≈ 0,667`).

Para atributos numéricos deste projeto, uma unidade no espaço transformado corresponde a um desvio padrão estimado no conjunto de ajuste, não a R$ 1 ou um ponto percentual. Para categorias one-hot, os coeficientes dependem do conjunto completo de indicadores e da regularização. Para comparar duas categorias conhecidas da mesma variável, a diferença entre seus coeficientes é mais informativa que interpretar um coeficiente isoladamente; ainda assim, as demais variáveis permanecem fixas na interpretação.

## 🧮 Como os parâmetros são aprendidos

Para observações independentes, a probabilidade atribuída à classe observada é `pᵢ` quando `yᵢ=1` e `1−pᵢ` quando `yᵢ=0`. O ajuste logístico minimiza uma função de perda logarítmica, equivalente a maximizar a verossimilhança, junto com uma penalidade de regularização:

```text
perda logarítmica = − Σᵢ [ yᵢ ln(pᵢ) + (1−yᵢ) ln(1−pᵢ) ]
objetivo qualitativo = perda logarítmica ponderada + penalidade L2
```

A escrita acima mostra a ideia geral; normalizações, pesos e tratamento do intercepto dependem da implementação. No scikit-learn, `liblinear` representa o intercepto por uma característica sintética e o regulariza também, sujeito a `intercept_scaling`. O projeto usa o valor padrão desse parâmetro. A documentação oficial detalha as opções e a compatibilidade de solver e penalidade.[^1]

Uma predição confiante e errada recebe penalidade alta. No ajuste ponderado, erros de observações de classes diferentes podem contribuir com pesos diferentes; isso modifica a função otimizada e pode mudar as probabilidades estimadas.

## ⚙️ Regularização e parâmetros

A penalidade L2 desestimula coeficientes de grande magnitude e pode reduzir ajuste excessivo. Ela não garante generalização, causalidade ou eliminação de atributos irrelevantes. `C` controla inversamente a intensidade de regularização: em condições comparáveis, menor `C` implica regularização mais forte; maior `C`, mais fraca. A configuração escolhida neste estudo foi `C=10` entre as opções avaliadas `0,1`, `1` e `10`.

O código cria `LogisticRegression(solver="liblinear", max_iter=2000, random_state=42, C=..., class_weight=...)`. `liblinear` é o otimizador; continua sendo regressão logística, não um segundo classificador. `max_iter` é um limite, não uma garantia de convergência. `random_state` controla o estado aleatório usado pelo solver quando aplicável. O projeto avalia pesos `None` e `"balanced"`; para `balanced`, o scikit-learn usa pesos inversamente proporcionais à frequência da classe no conjunto de ajuste. A execução observada selecionou `None`.[^1]

## 🔍 Interpretação e limitações

Os coeficientes descrevem associações condicionais no modelo ajustado. Eles não demonstram causa e efeito: promoções, inflação, custos, sazonalidade, mudanças de coleta e outros fatores podem interferir sem estar representados. Preços atuais, lags e estatísticas da mesma janela são correlacionados; isso pode tornar coeficientes individuais instáveis, mesmo que as predições sejam úteis. Categorias raras, regularização e o tratamento de marcas desconhecidas também afetam a interpretação.

O gráfico de maiores magnitudes é exploratório. Uma grande magnitude não é uma medida universal de importância causal ou de variação de probabilidade, e não se deve comparar diretamente atributos em escalas e frequências distintas sem considerar as transformações.

[^1]: Scikit-learn, *LogisticRegression*, https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html.
