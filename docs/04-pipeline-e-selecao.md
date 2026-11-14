# Pipeline, seleção e limiar de decisão

## 🔗 Transformação dos atributos

O pipeline é definido em [training.py](../src/basket_price_prediction/training.py). `ColumnTransformer` aplica um tratamento apropriado a cada grupo de colunas, e a saída alimenta uma única regressão logística.

| Grupo | Transformação | Efeito |
| --- | --- | --- |
| Numérico | `StandardScaler` | Para cada coluna, subtrai a média e divide pelo desvio padrão estimados no ajuste. |
| Categórico | `OneHotEncoder(handle_unknown="ignore")` | Aprende as categorias observadas no ajuste e cria indicadores binários. |

A escala facilita tratar atributos em unidades diferentes sob regularização. O escalonador aprende estatísticas no treino durante a seleção e novamente em treino + validação no ajuste final. As categorias desconhecidas no momento da transformação geram zeros para todos os indicadores daquela variável; isso permite processar o exemplo, mas não cria informação aprendida sobre a categoria inédita.[^1]

Os atributos completos entram por meio de uma lista explícita: 11 numéricos e quatro categóricos. Não há imputador no pipeline: as linhas sem o histórico exigido são excluídas antes de ajustar, e a marca ausente recebe um rótulo categórico explícito na limpeza.

## 🧪 Busca na validação

São treinadas seis configurações, combinando `C ∈ {0,1; 1; 10}` com `class_weight ∈ {None, "balanced"}`. Para cada configuração, o código calcula probabilidades no conjunto de validação e testa 17 limiares de `0,10` a `0,90` em passos de `0,05`, totalizando 102 pares configuração-limiar avaliados. O ajuste em si ocorre seis vezes na seleção; não é criado um classificador para cada limiar.

O critério é o maior F1 da classe positiva entre candidatos com precisão de pelo menos `0,35`. Em empate, escolhe-se maior precisão e, persistindo empate, menor limiar. Se nenhum candidato atingir a precisão mínima, o sistema escolhe o melhor F1 entre todos e registra esse fallback. A tabela integral é salva em `reports/validation_candidates.csv`.

A precisão mínima de 35% é uma decisão metodológica explícita para limitar alarmes falsos durante a seleção, não uma garantia de precisão de 35% em novos períodos. Após experimentar muitas configurações no mesmo conjunto de validação, a métrica de seleção pode ser otimista; o teste temporal serve para uma avaliação posterior independente dessa escolha.

## 🎚️ Probabilidade e decisão são coisas diferentes

O modelo retorna uma probabilidade `p`. A regra de decisão implementada é:

```text
previsão = 1, se p >= limiar
previsão = 0, se p < limiar
```

Um limiar menor tende a marcar mais observações como positivas; em geral aumenta a oportunidade de capturar altas, mas também pode aumentar falsos positivos. Precisão não precisa variar monotonicamente em dados finitos. O limiar é escolhido na validação, não no teste, e é salvo na configuração. Alterá-lo depois de inspecionar o teste transforma esse teste em parte do processo de seleção.

Na execução documentada, a seleção foi `C=10`, `class_weight=None` e limiar `0,25`. O limiar foi escolhido para o modelo ajustado apenas no treino e depois mantido ao reajustar o modelo em treino mais validação. Como o reajuste pode alterar a distribuição de probabilidades, a precisão e o recall obtidos no teste não são garantidos pela validação. O pipeline salvo contém o modelo reajustado; o limiar fica no `config.json`, separado do objeto `joblib`.

## 🔄 Sequência executada

1. Preparar séries mensais e exemplos elegíveis.
2. Dividir por mês-alvo em treino, validação e teste.
3. Ajustar cada pipeline candidato somente no treino.
4. Escolher configuração e limiar usando apenas a validação.
5. Salvar as predições de validação do modelo pré-reajuste.
6. Criar novo pipeline com os parâmetros selecionados e ajustá-lo em treino mais validação.
7. Gerar predições e métricas no teste e salvar o pipeline e os metadados.

Não há busca por outros algoritmos, nem validação cruzada aleatória. Uma avaliação futura com várias janelas temporais poderia investigar estabilidade, desde que se reserve novo período de teste independente ao final.

[^1]: Scikit-learn, *OneHotEncoder*, https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.OneHotEncoder.html; *StandardScaler*, https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html.
