# InvesTech Monitor

Aplicação Python responsável por monitorar parâmetros de investimento cadastrados no MySQL, consultar cotações na Brapi e enviar propostas para uma fila do RabbitMQ.

## Fluxo

```text
MySQL → Python → Brapi → Python → RabbitMQ
```

O sistema:

* Busca os parâmetros ativos no MySQL.
* Consulta as cotações dos ativos na Brapi.
* Verifica se o preço atingiu o valor configurado para compra ou venda.
* Gera uma proposta.
* Envia a proposta para a fila `propostas`.
* Repete o processo conforme o intervalo configurado.

## Tecnologias

* Python
* FastAPI
* MySQL
* Brapi
* RabbitMQ
* Pika

## Configuração

Crie um arquivo `.env` na raiz:

```env
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=sua_senha
DB_NAME=investech

BRAPI_BASE_URL=https://brapi.dev
BRAPI_API_TOKEN=

RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=investech
RABBITMQ_PASSWORD=sua_senha
RABBITMQ_QUEUE=propostas
RABBITMQ_VHOST=/

MONITOR_INTERVAL_SECONDS=60
DECISION_COOLDOWN_SECONDS=300
DEFAULT_QUANTITY=1
NIVEL_RISCO_PADRAO=2
```

## Instalação

Crie o ambiente virtual:

```bash
python -m venv venv
```

Ative:

```bash
venv\Scripts\activate
```

Instale as dependências:

```bash
pip install -r requirements.txt
```

## Execução

Com MySQL e RabbitMQ executando:

```bash
uvicorn app.main:app --reload
```

Exemplo de saída:

```text
Iniciando monitoramento...
Ativos encontrados: VALE3
VALE3 | Preço atual: R$ 72.10
Proposta enviada para RabbitMQ: VALE3 | VENDA
Monitoramento finalizado.
```

## Mensagem enviada ao RabbitMQ

```json
{
  "tipoAtivo": "AÇÃO",
  "nomeAtivo": "VALE3",
  "tipoOperacao": "VENDA",
  "quantidadeSugerida": 10.0,
  "valorSugerido": 72.10,
  "descricaoProposta": "O preço atual atingiu o parâmetro configurado.",
  "nivelRisco": 2
}
```
