# InvesTech - API Python de Monitoramento

A aplicação consulta parâmetros ativos no MySQL, agrupa os parâmetros por ativo e faz uma única chamada de cotação por ativo.

Depois, a mesma cotação é usada para avaliar todos os parâmetros daquele ativo.

## Fluxo

1. Python consulta `parametro` onde `status_parametro = 1`.
2. Agrupa por `tipo_ativo + ativo_nome`.
3. Faz uma chamada para a brapi por grupo de ativo.
4. Obtém `regularMarketPrice`.
5. Avalia cada parâmetro.
6. Se a regra for atendida, envia um POST para `DECISAO_URL`.
7. O monitor repete o processo a cada `MONITOR_INTERVAL_SECONDS`.

## Regras implementadas

### COMPRA

```text
preço atual <= preco_maximo
```

### VENDA

```text
preço atual >= preco_minimo
```

`quantidade_maxima` é usada como `quantidadeAprovada`.

## Importante sobre propostaId

O JSON de decisão exige:

```json
"propostaId": 0
```

Porém, a tabela `parametro` fornecida não possui `proposta_id`.

Por isso o projeto envia `0` até que o relacionamento seja definido.

A opção mais consistente é adicionar:

```sql
ALTER TABLE parametro
ADD COLUMN proposta_id INT,
ADD CONSTRAINT fk_parametro_proposta
FOREIGN KEY (proposta_id) REFERENCES proposta(id);
```

Depois, o Python pode enviar:

```python
"propostaId": parametro["proposta_id"]
```

## Instalação

```bash
python -m venv venv
```

Windows:

```bash
venv\Scripts\activate
```

Linux:

```bash
source venv/bin/activate
```

Instale:

```bash
pip install -r requirements.txt
```

Copie:

```text
.env.example
```

para:

```text
.env
```

e configure MySQL, token da brapi e URL do backend.

Execute:

```bash
uvicorn app.main:app --reload
```

A API ficará em:

```text
http://localhost:8000
```

Documentação:

```text
http://localhost:8000/docs
```

## Otimização de chamadas

Exemplo:

```text
Parâmetro 1 -> PETR4 -> carteira 1
Parâmetro 2 -> PETR4 -> carteira 2
Parâmetro 3 -> PETR4 -> carteira 3
Parâmetro 4 -> BTC   -> carteira 1
```

O monitor não faz:

```text
GET PETR4
GET PETR4
GET PETR4
GET BTC
```

Ele faz:

```text
GET PETR4
GET BTC
```

e reutiliza as respostas.

Para ações, o cliente usa o endpoint de cotação da brapi.

Para cripto, usa:

```text
/api/v2/crypto?coin=BTC,ETH&currency=BRL
```

A documentação da brapi informa que esse endpoint aceita várias criptomoedas na mesma chamada.
