# Limitações, validade e uso responsável

## 📊 A quem o resultado se aplica

O teste cobre observações elegíveis entre setembro de 2025 e agosto de 2026, com dois meses anteriores consecutivos e preço observado no mês-alvo. Trata-se de produtos, marcas, quantidades e estabelecimentos representados na fonte. Uma série ausente ou interrompida é excluída em vez de receber preços interpolados.

A continuidade necessária reduz 43.948 observações mensais a 17.002 exemplos e seleciona a amostra: pode deixar de fora produtos mais voláteis, itens descontinuados ou estabelecimentos com coleta irregular. O desempenho medido não deve ser generalizado automaticamente a todos os produtos, supermercados, consumidores ou localidades.

## 🧾 Limitações da observação

- **Marcas e descrições:** 9.346 registros não têm marca, e a categoria `(não informada)` pode reunir marcas distintas; nomes diferentes também podem separar produtos equivalentes. Isso altera a interpretação de "mesmo produto".
- **Embalagens e unidades:** a quantidade numérica faz parte da chave, mas suas unidades físicas não estão documentadas em todas as categorias. Não se devem comparar diretamente `PPK` ou preços de unidades incompatíveis.
- **Preços extremos:** podem refletir erro, promoção, mudança de produto ou alta real. Nenhum extremo é removido automaticamente; classificá-lo como erro exige investigação com os dados de origem.
- **Data de coleta:** está ausente em **100% dos registros a partir de novembro de 2025**, o que abrange 10 dos 12 meses-alvo do teste. Não é possível confirmar se cada preço estava disponível ao fim do mês de referência nesse período. Isso não é evidência de vazamento, mas é uma hipótese que permanece não testável sobre a maior parte do teste.
- **Método de coleta:** mudanças de cobertura, lojas, metodologia e frequência podem alterar a distribuição dos dados. A planilha, isoladamente, não explica essas mudanças.

## 📉 Limitações estatísticas

A avaliação usa um **único** recorte cronológico de validação e um de teste. Não há avaliação temporal deslizante, que mediria estabilidade em várias janelas.

As observações da mesma série não são independentes: 3.180 linhas de teste vêm de 785 séries, 4,1 por série. Os intervalos de confiança reportados **já tratam essa dependência**, reamostrando séries inteiras em vez de linhas isoladas; um intervalo calculado linha a linha seria estreito demais. Ainda assim, o bootstrap não corrige dependência *entre* séries do mesmo produto ou supermercado, nem choques de preço que atingem muitas séries no mesmo mês.

Comparações por produto e supermercado **não controlam multiplicidade**: com dezenas de grupos avaliados, algumas diferenças extremas aparecem por acaso. Os recalls de 0,986 da batata e 0,389 do pão francês devem ser lidos junto com o número de positivos de cada grupo.

**Otimismo de seleção:** 408 pares configuração-limiar foram avaliados no mesmo conjunto de validação. O teste temporal independente existe para medir o efeito disso. Na execução documentada a queda esperada não se materializou, mas uma reavaliação exigiria reservar novo período.

**Diagnóstico posterior por família.** O gradient boosting obteve o maior F1 observado no teste (0,534), seguido pela random forest (0,517). A comparação entre famílias no teste é descritiva. Um intervalo para o F1 da random forest quantifica a incerteza da sua própria estimativa. Uma inferência sobre o ganho de uma família sobre outra exigiria um intervalo da diferença pareada, com as mesmas séries reamostradas. A random forest foi selecionada pelo desempenho na validação.

Inflação, custos de produção, promoções, sazonalidade econômica, impostos e disponibilidade podem afetar preços sem estar medidos. Uma mudança nessas relações degrada classificação e calibração.

## 🔗 Colinearidade e interpretação

Os atributos de preço são fortemente redundantes, e em quatro casos a redundância é **exata**: `rolling_mean_3m` é, por construção, `(price_current + price_lag_1 + price_lag_2) / 3`. O VIF desses quatro atributos é infinito (`reports/collinearity.csv`), e `rolling_max_3m`, `rolling_min_3m` e `rolling_std_3m` ficam acima de 1.000.

Consequência direta: **os coeficientes individuais da regressão logística não são interpretáveis neste conjunto de atributos**, porque a repartição de peso entre variáveis perfeitamente colineares é matematicamente indeterminada. A predição não é afetada; apenas a leitura atributo a atributo é. Por isso a interpretação do projeto usa importância por permutação, descrita em [modelos comparados](03-modelos-comparados.md), e a figura de coeficientes só é gerada quando a família vencedora é linear, acompanhada de aviso explícito.

Importância por permutação também é associação, não causa. Um atributo redundante pode mostrar importância baixa apenas porque outro carrega a mesma informação.

## 📈 Deriva de nível de preço

O nível médio de preço sobe de R$ 12,83 no treino para R$ 15,31 no teste, deriva de cerca de 19% entre as partições. Um modelo que dependesse do nível absoluto tenderia a degradar.

As variações de um e dois meses tiveram as maiores importâncias individuais por permutação nessa execução. Atributos de preço correlacionados podem compartilhar informação, o que dificulta interpretar uma importância baixa. A diferença média de preços entre treino e teste descreve a amostra, com possíveis mudanças na composição dos itens. A robustez a mudanças no nível de preços exigiria uma avaliação específica.

## 🚫 O que o modelo não entrega

- Não calcula o preço de `t+1`, a magnitude da alta nem o impacto monetário para uma cesta individual.
- Não garante que um produto específico aumentará ou permanecerá estável.
- Não substitui índice oficial de inflação nem aconselhamento financeiro.
- Não estima retorno financeiro: o custo de um falso alarme e o prejuízo de uma alta não detectada não estão na base, e sem eles o limiar de 0,25 não é uma escolha final.
- Não implementa rotina prospectiva: `build_supervised` retorna apenas exemplos históricos com alvo observado.
- Não verifica a proveniência individual de uma coleta cuja data esteja ausente.

Uma probabilidade de 0,40 é estimativa condicional do modelo, sujeita à calibração e às diferenças entre dados futuros e de treinamento. Ela não significa certeza de aumento de 40% no preço.

## 🔎 Investigações futuras possíveis

Antes de uma aplicação prática, é necessário definir o custo de cada tipo de erro e avaliar eventuais ajustes de limiar na validação cronológica. Outras possibilidades incluem validar unidades, identidade do produto e disponibilidade dos dados, e verificar a estabilidade em outras janelas temporais.

Essas propostas são possibilidades de pesquisa, não resultados do projeto atual.
