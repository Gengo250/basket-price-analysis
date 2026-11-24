# Problema, dados e definição do alvo

## 🎯 Pergunta de pesquisa

A pergunta é: **dados históricos ajudam a prever se o preço de um produto, em um supermercado, aumentará mais de 2% no mês-calendário seguinte?** Cada exemplo corresponde a uma série de preço em um mês de referência. A saída é uma probabilidade para um evento binário, não uma previsão do valor monetário nem uma garantia de que a alta ocorrerá.

O estudo é exploratório e educacional. Ele avalia a capacidade preditiva sobre observações elegíveis da base, e não a inflação oficial ou uma cesta de consumo fixa.

## 📋 Fonte e esquema

A fonte disponível é `data/ICB_DADOS_2026.xlsx`, aba `ACUMUL_DESAGREG`. A versão inspecionada contém 46.264 linhas e cobre setembro de 2022 a agosto de 2026. O carregador lê a fonte sem modificá-la; não havia CSV original no repositório.

| Coluna | Significado usado no projeto |
| --- | --- |
| `Mes_Ano_Data` | Mês de referência da observação. |
| `Data_Coleta` | Data individual de coleta, quando presente. |
| `Estab` | Identificador do estabelecimento. |
| `Produto` | Descrição do produto. |
| `Marca` | Marca, quando informada. |
| `Preco` | Preço observado da embalagem. |
| `Quantidade` | Quantidade associada à embalagem; a unidade não está explicitada para todos os produtos. |
| `PPK` | Campo de preço por quantidade, cujo nome não comprova que a unidade seja quilograma. |

Na inspeção havia 30 produtos e 51 estabelecimentos distintos, 9.818 datas de coleta e 9.346 marcas ausentes e 1.743 duplicatas exatas. A última data individual de coleta presente é de outubro de 2025; a referência mensal continua até agosto de 2026. Logo, não é possível confirmar a disponibilidade efetiva de cada observação posterior a partir da data de coleta.

## 🧹 Limpeza e identidade da série

`prepare_monthly`, em [preprocessing.py](../src/basket_price_prediction/preprocessing.py), converte datas e números, normaliza o mês para o primeiro dia e retira espaços de identificadores. Remove duplicatas integrais e registros com mês, estabelecimento ou produto ausente, preço ou quantidade inválido/não positivo, ou data de coleta conhecida fora do mês de referência. Uma data de coleta ausente é mantida como ausente; marca ausente torna-se `(não informada)`.

A identidade é `(supermercado, produto, marca, quantidade)`. Assim, não se misturam intencionalmente embalagens de tamanhos diferentes. Porém, marcas não informadas podem representar produtos diferentes e descrições inconsistentes podem fragmentar séries. Para mais de um registro distinto da mesma série no mês, usa-se a **mediana** dos preços. A mediana reduz a influência de uma observação extrema, mas não verifica se ela é erro, promoção ou mudança legítima.

O campo `PPK` foi comparado com `Preco / Quantidade`: nenhuma diferença excedeu 0,01 na amostra válida. Isso não estabelece a unidade física do denominador. O alvo usa o preço original da mesma embalagem, e não uma comparação de `PPK` entre produtos ou unidades distintas. Um aumento percentual na mesma embalagem é independente de dividir ambos os preços pela mesma quantidade positiva.

O relatório da execução registrou 44.521 linhas válidas após remover duplicatas, 43.948 observações mensais agregadas e 4.216 séries. Nenhuma linha adicional foi excluída pelos critérios de mês, entidade, preço, quantidade ou coleta fora do mês nessa execução. Motivos de exclusão em geral podem se sobrepor e não devem ser somados sem conferir as interseções.

### Investigação de preços suspeitos

O diagnóstico trabalha com registros válidos antes da mediana mensal. Para cada registro, compara o preço com a mediana dos preços mensais da mesma série nos meses imediatamente anterior e posterior disponíveis. Também usa a mediana dos demais supermercados com o mesmo produto, marca e quantidade no mesmo mês quando há pelo menos dois outros supermercados. Cada supermercado contribui com uma mediana para essa comparação.

Um registro é sinalizado quando seu preço é pelo menos três vezes ou no máximo um terço de alguma referência. O notebook exploratório identifica produto, supermercado, marca, quantidade, mês, preço e a comparação que motivou o alerta. Quando a marca está ausente, o grupo pode conter embalagens de marcas distintas. Valores sinalizados são mantidos com ressalva, pois a comparação interna indica discrepância e a base não confirma a origem de cada valor.

## 🧮 Alvo de classificação

Para uma série e um mês de previsão `t`, sejam `P_t` o preço da embalagem em `t` e `P_(t+1)` o preço no mês-calendário imediatamente seguinte:

```text
variação futura = (P_(t+1) - P_t) / P_t
classe 1         = variação futura > 0,02
classe 0         = variação futura <= 0,02
```

Exemplo com `P_t = R$ 10,00`:

| Preço no mês seguinte | Variação | Classe |
| --- | ---: | ---: |
| R$ 10,30 | +3% | 1 |
| R$ 10,20 | +2% | 0 |
| R$ 9,80 | −2% | 0 |

O limite e a tolerância são definidos em [config.py](../src/basket_price_prediction/config.py). A comparação usa tolerância absoluta de `1e-12` ao redor de `0,02` para evitar que erro de representação de ponto flutuante transforme uma alta de exatamente 2% em classe 1. Assim, valores extremamente próximos e acima de 2% também são tratados como classe 0 dentro dessa tolerância.

Se não existir preço no mês seguinte, o rótulo não é criado. Por exemplo, janeiro seguido de março não constitui uma variação mensal de janeiro para fevereiro. O mês de `t+1` é salvo como `target_month`, e a variação real é armazenada apenas para avaliação, sem entrar nos atributos.

## 📉 Elegibilidade

Além do alvo válido, exige-se histórico consecutivo em `t`, `t−1` e `t−2`. Das 43.948 observações mensais, 15.108 não tinham observação no próximo mês-calendário; das 28.840 com alvo, 11.838 não tinham o histórico necessário. Restaram 17.002 exemplos, com 4.957 positivos e 12.045 negativos.

Essa exigência torna o experimento comparável e evita lacunas tratadas como meses adjacentes, mas favorece séries mais contínuas. Também significa que a base supervisionada atual só inclui linhas cujo futuro já é conhecido: o projeto avalia historicamente e não oferece uma rotina separada para emitir previsões prospectivas do último mês disponível.
