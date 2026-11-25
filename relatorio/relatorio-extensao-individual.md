# Relatório individual de extensão — modelo preenchível

> ⚠️ **Atenção:** o modelo oficial é fornecido pela instituição junto ao enunciado da atividade. Este arquivo **não substitui** esse modelo: ele é um rascunho de conteúdo para transportar para o formulário oficial. Confira os campos obrigatórios, a formatação e o prazo antes de submeter. Cada integrante do grupo deve submeter o seu próprio relatório na atividade de **EXTENSÃO**, para validação das horas.

---

## 1. Identificação

| Campo | Preencher |
| --- | --- |
| Nome completo | |
| Curso / semestre | |
| Disciplina | Aprendizado de Máquina — 6º semestre |
| Professor responsável | |
| Período de realização | |
| Carga horária dedicada | |
| Demais integrantes do grupo | |

## 2. Identificação da ação de extensão

**Título:** Previsão de altas de preço na cesta básica a partir de dados públicos de pesquisa de preços.

**Base utilizada:** `ICB_DADOS_2026.xlsx` — 46.264 coletas de preço em 51 estabelecimentos e 30 produtos, entre setembro/2022 e agosto/2026.

## 3. Público beneficiado

> *Personalize com o contato real que o grupo teve, se houve. Se não houve contato direto, descreva o público-alvo potencial com honestidade — não afirme interação que não ocorreu.*

O público-alvo são organizações que compram alimentos em volume para redistribuição ou consumo coletivo — bancos de alimentos, cozinhas comunitárias e associações de bairro — e programas de educação financeira e defesa do consumidor. São grupos que já lidam com a pesquisa de preços da cesta básica de forma retrospectiva e que se beneficiariam de uma leitura prospectiva dela.

A população final alcançada são famílias de baixa renda, para quem a cesta básica consome a maior fatia do orçamento e que têm menor capacidade de antecipar compras ou comparar estabelecimentos.

## 4. Objetivos

**Objetivo geral:** determinar se o histórico recente de preços permite antecipar altas acima de 2% no mês seguinte, e quantificar esse sinal com medida de incerteza, de modo que uma organização possa decidir se vale construir um alerta de compra sobre esses dados.

**Objetivos específicos:**
1. Avaliar a qualidade e a cobertura real da base pública de preços.
2. Construir um alvo temporalmente honesto, sem uso de informação futura.
3. Comparar famílias de algoritmos de aprendizado supervisionado sob o mesmo protocolo temporal.
4. Medir o desempenho contra referências sem treinamento e reportar intervalos de confiança.
5. Explicitar as limitações que restringem o uso prático do resultado.

## 5. Metodologia

> *Resumo para o formulário. O detalhamento completo está em `RELATORIO.md`, Seção 3.*

Os 46.264 registros brutos foram reduzidos a 43.948 observações mensais em 4.216 séries `(supermercado, produto, marca, quantidade)`, agregando por mediana e removendo duplicatas integrais, sem interpolar lacunas. O alvo é a alta estritamente acima de 2% no mês-calendário seguinte, limite justificado pela própria distribuição dos dados: 43,5% das variações mensais ficam dentro de ±2%, e 2% ao mês equivalem a 26,8% ao ano.

A divisão é cronológica pelo mês-alvo: treino até dez/2024, validação em 2025, teste de set/2025 a ago/2026. Quatro famílias de algoritmos — regressão logística, árvore de decisão, random forest e gradient boosting — foram comparadas em 24 configurações e 17 limiares, com seleção feita exclusivamente na validação. Os intervalos de confiança usam bootstrap de séries inteiras, respeitando a dependência entre meses de uma mesma série.

## 6. Atividades desenvolvidas

> *Descreva o que **você** fez. Ajuste a lista à sua participação real — a arguição é individual.*

- [ ] Análise exploratória e verificação de qualidade da base
- [ ] Construção do alvo e dos atributos temporais
- [ ] Implementação da validação temporal e das barreiras contra vazamento
- [ ] Comparação entre famílias de algoritmos e seleção do modelo
- [ ] Avaliação, intervalos de confiança e análise de erros
- [ ] Testes automatizados
- [ ] Documentação e redação do relatório

## 7. Resultados alcançados

A random forest foi selecionada na validação (F1 0,518), à frente de gradient boosting (0,475), árvore de decisão (0,468) e regressão logística (0,439). No teste temporal independente de 3.180 observações:

| Métrica | Resultado | IC 95% |
| --- | ---: | :---: |
| Recall | 0,757 | [0,725 – 0,790] |
| Precisão | 0,392 | [0,371 – 0,414] |
| F1 | 0,517 | [0,495 – 0,538] |
| ROC-AUC | 0,715 | [0,695 – 0,734] |

O modelo identificou 696 das 919 altas reais. O ganho de F1 sobre a referência "repete a alta anterior" tem IC 95% de **+0,267 a +0,326** — intervalo que exclui zero, confirmando significância estatística. A contrapartida medida é que 60,8% dos alertas emitidos foram falsos.

## 8. Relação entre teoria e prática

> *Esta seção costuma valer bastante na avaliação de extensão. Escreva com suas palavras. Pontos concretos deste projeto que servem de matéria-prima:*

- **Validação temporal não é detalhe.** Dividir aleatoriamente teria usado o futuro para prever o passado. A divisão por mês-alvo e a exigência de meses de calendário consecutivos foram decisões que mudaram a base de 43.948 para 17.002 exemplos — custo real assumido em nome da honestidade do resultado.
- **A métrica errada esconde o fracasso.** Prever sempre "sem alta" atinge 71,1% de acurácia e não serve para nada. Foi preciso escolher F1 com piso de precisão para que o critério refletisse o problema.
- **Comparar algoritmos mudou a conclusão.** A hipótese inicial era que a regressão logística bastava; a random forest a superou. Mas a diferença entre as quatro famílias ficou menor que o intervalo de confiança da medição — ou seja, aprendeu-se tanto com o resultado quanto com o tamanho da incerteza dele.
- **Nem todo coeficiente é interpretável.** O VIF infinito de quatro atributos mostrou que ler coeficientes individuais ali seria erro metodológico, o que levou ao uso de importância por permutação.
- **Dado público tem buraco.** A data de coleta some a partir de novembro/2025, em 10 dos 12 meses de teste. Reconhecer e declarar isso foi parte do trabalho.

## 9. Considerações finais

> *Avalie o que a atividade agregou à sua formação e ao público-alvo, e o que ficou em aberto. Sugestões de continuidade registradas no relatório técnico: definir o custo real de cada tipo de erro com a organização destinatária; substituir a janela única de validação por avaliação deslizante; incorporar preços ao produtor para testar atraso de repasse; obter documentação da pesquisa de coleta.*

---

**Local e data:**
**Assinatura:**
