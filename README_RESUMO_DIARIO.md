# Resumo diário de temperatura no MongoDB

## Objetivo

Este documento explica passo a passo como foi criado o script de resumo diário da temperatura, com cálculo de:

- valor máximo por dia
- valor mínimo por dia
- média diária
- quantidade de leituras por dia

A ideia é separar os dados brutos dos dados processados e guardar o resumo em uma collection específica do MongoDB.

---

## 1) Estrutura do projeto relevante

Os scripts já existentes no diretório `python` seguem esse padrão:

- `mongoDB.py`: conecta ao MongoDB e salva as leituras vindas do sensor
- `serial_reader.py`: lê os valores do Arduino e gera um documento com temperatura e timestamp
- `daily_resume.py`: agrega os dados por dia e salva o resumo geral

O fluxo principal é:

1. Arduino envia leitura da temperatura
2. Python lê e publica em MQTT
3. Python salva em MongoDB
4. Script de resumo lê os dados da collection de origem
5. Agrupa por dia
6. Salva o resultado em uma collection de resumo

---

## 2) Formato dos dados salvos no MongoDB

Os documentos da collection `sensor_data` seguem este formato:

```json
{
  "temperature": 26.4,
  "timestamp": "2026-08-20T08:15:30"
}
```

Isso significa que cada leitura possui:

- `temperature`: valor numérico da temperatura
- `timestamp`: data e hora da coleta em formato ISO

---

## 3) Problema a ser resolvido

O sistema coleta muitas leituras ao longo do dia. O que queremos não é apenas armazenar cada valor isoladamente, mas também responder perguntas como:

- Qual foi a maior temperatura do dia?
- Qual foi a menor?
- Qual foi a média?
- Quantas medições foram feitas?

Para isso, o ideal é criar um resumo diário.

---

## 4) Estratégia usada

A solução foi:

- percorrer todos os documentos da collection `sensor_data`
- verificar se cada documento tem dados válidos
- converter o `timestamp` em objeto `datetime`
- extrair a data (`YYYY-MM-DD`)
- agrupar os registros pela data
- calcular soma, contagem, mínimo e máximo
- calcular a média ao final
- salvar o resumo em `daily_summary`

---

## 5) Conexão com o MongoDB

O código começa com a conexão:

```python
from pymongo import MongoClient

MONGO_URI = "mongodb://localhost:27017/"
DB_NAME = "temperature-monitor"
SOURCE_COLLECTION = "sensor_data"
TARGET_COLLECTION = "daily_summary"

mongo_client = MongoClient(MONGO_URI)
db = mongo_client[DB_NAME]
source_collection = db[SOURCE_COLLECTION]
target_collection = db[TARGET_COLLECTION]
```

### O que isso representa

- `MONGO_URI`: endereço do MongoDB
- `DB_NAME`: banco de dados
- `SOURCE_COLLECTION`: collection com os dados brutos
- `TARGET_COLLECTION`: collection com os dados processados

Essa separação é importante em projetos reais porque deixa:

- dados brutos preservados
- dados resumidos prontos para consulta

---

## 6) Conversão do timestamp

Uma parte essencial foi converter o campo `timestamp` para o tipo `datetime`.

```python
def parse_timestamp(value):
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return None

    return None
```

### Por que isso é necessário?

Porque o timestamp veio como string, por exemplo:

```python
"2026-08-20T08:15:30"
```

Para agrupar por dia, o Python precisa transformar isso em um objeto de data/hora, para então fazer:

```python
day = timestamp.date().isoformat()
```

Essa linha retorna algo como:

```python
"2026-08-20"
```

---

## 7) Agrupamento por dia

A lógica central é esta:

```python
for doc in source_collection.find({
    "temperature": {"$exists": True},
    "timestamp": {"$exists": True}
}):
    temperature = doc.get("temperature")
    if temperature is None:
        continue

    timestamp = parse_timestamp(doc.get("timestamp"))
    if timestamp is None:
        continue

    day = timestamp.date().isoformat()
```

### O que acontece aqui?

Para cada documento:

- verifica se existe temperatura
- verifica se existe timestamp
- converte para data
- usa a data como chave de agrupamento

Assim, todos os registros do mesmo dia entram no mesmo bloco de cálculo.

---

## 8) Cálculo dos valores do resumo

Para cada dia, o código mantém um dicionário com:

```python
if day not in daily_data:
    daily_data[day] = {
        "sum": 0.0,
        "count": 0,
        "min": float("inf"),
        "max": float("-inf")
    }
```

Depois, atualiza:

```python
temp_value = float(temperature)
daily_data[day]["sum"] += temp_value
daily_data[day]["count"] += 1
daily_data[day]["min"] = min(daily_data[day]["min"], temp_value)
daily_data[day]["max"] = max(daily_data[day]["max"], temp_value)
```

### Esse bloco calcula:

- soma total das temperaturas do dia
- quantidade de leituras do dia
- menor valor do dia
- maior valor do dia

Quando o processo termina, a média é calculada assim:

```python
avg_temperature = values["sum"] / values["count"]
```

---

## 9) Estrutura do resumo final

O documento final salvo em `daily_summary` fica assim:

```python
summary = {
    "day": day,
    "max_temperature": round(values["max"], 2),
    "min_temperature": round(values["min"], 2),
    "avg_temperature": round(avg_temperature, 2),
    "readings_count": values["count"],
    "updated_at": datetime.utcnow()
}
```

### Exemplo de saída

```json
{
  "day": "2026-08-20",
  "max_temperature": 29.8,
  "min_temperature": 20.1,
  "avg_temperature": 24.7,
  "readings_count": 140,
  "updated_at": "2026-08-20T12:00:00.000Z"
}
```

---

## 10) Salvando no MongoDB sem duplicar dados

O código usa `update_one` com `upsert=True`:

```python
target_collection.update_one(
    {"day": day},
    {"$set": summary},
    upsert=True
)
```

### O que isso significa?

- se o dia ainda não existe, ele cria
- se o dia já existe, ele atualiza
- evita duplicidade

Essa abordagem é muito útil quando você quer manter um único resumo para cada data.

---

## 11) Por que esse padrão é útil em projetos reais

Esse tipo de script é muito comum em sistemas de:

- monitoramento industrial
- sensores IoT
- monitoramento climático
- analytics de uso
- automação e relatórios

A ideia geral é:

- coletar dados em tempo real
- guardar os dados crus
- processar depois em lote ou sob demanda
- criar resumos para facilitar consultas e dashboards

---

## 12) Como aplicar em outros projetos

Você pode reutilizar a mesma lógica para qualquer dado com a estrutura:

```json
{
  "valor": 123,
  "timestamp": "2026-08-20T12:00:00"
}
```

E então:

1. agrupar pela data
2. calcular mínimo/máximo/média
3. salvar em uma collection de resumo

O algoritmo muda pouco.

---

## 13) Observações importantes

### 1. Dados em string

Se os dados vierem como string, sempre converta antes de processar.

### 2. Agrupar por chave correta

Escolha uma chave como `day`, `month`, `hour`, `sensor_id` conforme a necessidade.

### 3. Guardar dados crus e processados separados

Isso deixa o projeto mais organizado e facilita manutenção.

### 4. Use `upsert` para evitar duplicidade

Essa prática é essencial em resumos diários ou mensais.

---

## 14) Resultado final

O resultado do processo foi criar a collection `daily_summary`, onde cada documento representa um único dia e contém:

- dia
- mínima da temperatura
- máxima da temperatura
- média da temperatura
- número de leituras
- data da atualização

Esse padrão é muito útil para dashboards, relatórios e análise histórica.

---

## 15) Arquivos principais

- [python/daily_resume.py](python/daily_resume.py) — script principal do resumo diário
- [python/mongoDB.py](python/mongoDB.py) — coleta e grava os dados brutos
- [python/serial_reader.py](python/serial_reader.py) — leitura do sensor e geração do documento com timestamp

---

## 16) Próximo passo sugerido

Se quiser evoluir o projeto, os próximos passos mais úteis são:

- criar um resumo por hora
- criar um resumo por mês
- criar uma API para consultar o resumo
- gerar gráficos no Node-RED usando a collection `daily_summary`

Esse é o tipo de estrutura que vale repetir em qualquer projeto de dados e monitoramento.
