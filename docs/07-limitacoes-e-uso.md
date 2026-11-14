# Limitações, validade e uso responsável

## 📊 A quem o resultado se aplica

O teste cobre observações elegíveis entre setembro de 2025 e agosto de 2026, com dois meses anteriores consecutivos e preço observado no mês-alvo. Trata-se de produtos, marcas, quantidades e estabelecimentos representados na fonte. Uma série ausente ou interrompida é excluída em vez de receber preços interpolados.

A continuidade necessária seleciona a amostra e pode deixar de fora produtos mais voláteis, itens descontinuados ou estabelecimentos com coleta irregular. Assim, o desempenho medido não deve ser generalizado automaticamente a todos os produtos, supermercados, consumidores ou localidades.

## 🧾 Limitações da observação

- **Marcas e descrições:** a categoria de marca não informada pode reunir marcas distintas; nomes diferentes também podem separar produtos equivalentes. Isso altera a interpretação de “mesmo produto”.
- **Embalagens e unidades:** quantidade numérica faz parte da chave, mas suas unidades físicas não estão documentadas em todas as categorias. Não se devem comparar diretamente `PPK` ou preços de unidades incompatíveis.
- **Preços extremos:** podem refletir erro, promoção, mudança de produto ou uma alta real. Nenhum extremo é removido automaticamente; uma investigação com dados de origem é necessária antes de classificá-lo como erro.
- **Data de coleta:** sua ausência após outubro de 2025 impede confirmar se cada preço estava disponível ao final do mês de referência. A comparação entre meses de referência mantém utilidade exploratória, mas a hipótese de disponibilidade precisa ser validada.
- **Método de coleta:** mudanças de cobertura, lojas, metodologia e frequência podem alterar a distribuição dos dados. A planilha, isoladamente, não explica todas essas mudanças.

## 📉 Limitações estatísticas

A avaliação usa um único recorte cronológico de validação e um de teste; as observações da mesma série e do mesmo mês não são necessariamente independentes. Não foram calculados intervalos de confiança nem executada avaliação temporal repetida. Comparações por produto e supermercado não controlam multiplicidade nem garantem que diferenças entre grupos sejam estáveis.

Inflação, custos de produção, promoções, sazonalidade econômica, impostos, disponibilidade e outros fatores podem afetar preços sem estar medidos explicitamente. Uma mudança nessas relações pode degradar a classificação e a calibração. A regressão logística fornece associações condicionais, não identifica causas.

O limite de decisão foi selecionado no conjunto de validação e transferido ao modelo reajustado. O conjunto de teste não foi usado nessa seleção, mas novas mudanças após examinar o teste exigiriam outro período independente para avaliação imparcial. O limite de 0,25 selecionado nesta execução não deve ser interpretado como escolha universal.

## 🚫 O que o modelo não entrega

- Não calcula o preço de `t+1`, a magnitude da alta nem o impacto monetário para uma cesta individual.
- Não garante que um produto específico aumentará ou permanecerá estável.
- Não substitui índice oficial de inflação ou aconselhamento financeiro.
- Não implementa rotina operacional separada para prever o último mês sem alvo conhecido: `build_supervised` retorna apenas exemplos históricos elegíveis com alvo observado.
- Não verifica a proveniência individual de uma coleta cuja data esteja ausente.

Uma probabilidade de 0,40 deve ser entendida como estimativa condicional do modelo, sujeita à calibração e às diferenças entre dados futuros e treinamento. Ela não significa certeza de aumento de 40% no preço.

## 🔎 Investigações futuras possíveis

Antes de uma aplicação prática, seria útil obter documentação da fonte e datas de coleta, validar identidade de produtos e unidades, examinar os extremos, testar janelas temporais adicionais com reserva de um teste final novo e avaliar incerteza por mês e série. Também seria necessário definir custos de falsos alertas e de altas não detectadas para escolher um limiar apropriado. Essas propostas são possibilidades de pesquisa; não são resultados do projeto atual.
