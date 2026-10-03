import time


from app.rabbitmq_client import RabbitMQClient

from app.config import (
    DEFAULT_QUANTITY,
    DECISION_COOLDOWN_SECONDS,
    NIVEL_RISCO_PADRAO
)
from app.database import (
    buscar_parametros_ativos,
    atualizar_preco_ativo,
    criar_ativo_se_nao_existir
)
from app.brapi_client import BrapiClient


brapi = BrapiClient()
rabbitmq = RabbitMQClient()
ultimo_envio = {}


def analisar_parametro(parametro, preco):
    preco_minimo = (
        float(parametro["preco_minimo"])
        if parametro["preco_minimo"] is not None
        else None
    )

    preco_maximo = (
        float(parametro["preco_maximo"])
        if parametro["preco_maximo"] is not None
        else None
    )

    quantidade_maxima = (
        int(parametro["quantidade_maxima"])
        if parametro["quantidade_maxima"] is not None
        else DEFAULT_QUANTITY
    )

    nome_ativo = parametro["ativo_nome"].strip().upper()
    tipo_ativo = parametro["tipo_ativo"]

    if preco_maximo is not None and preco <= preco_maximo:
        return {
            "tipoAtivo": tipo_ativo,
            "nomeAtivo": nome_ativo,
            "tipoOperacao": "COMPRA",
            "quantidadeSugerida": float(quantidade_maxima),
            "valorSugerido": float(preco),
            "descricaoProposta": (
                f"O preço atual de {nome_ativo} é R$ {preco:.2f} "
                f"e atingiu o preço máximo configurado de "
                f"R$ {preco_maximo:.2f} para compra."
            ),
            "nivelRisco": NIVEL_RISCO_PADRAO
        }

    if preco_minimo is not None and preco >= preco_minimo:
        return {
            "tipoAtivo": tipo_ativo,
            "nomeAtivo": nome_ativo,
            "tipoOperacao": "VENDA",
            "quantidadeSugerida": float(quantidade_maxima),
            "valorSugerido": float(preco),
            "descricaoProposta": (
                f"O preço atual de {nome_ativo} é R$ {preco:.2f} "
                f"e atingiu o preço mínimo configurado de "
                f"R$ {preco_minimo:.2f} para venda."
            ),
            "nivelRisco": NIVEL_RISCO_PADRAO
        }

    return None

def pode_enviar(parametro_id, tipo_operacao):
    chave = (parametro_id, tipo_operacao)

    agora = time.time()
    ultimo = ultimo_envio.get(chave)

    if ultimo is None:
        return True

    return (agora - ultimo) >= DECISION_COOLDOWN_SECONDS


def registrar_envio(parametro_id, tipo_operacao):
    chave = (parametro_id, tipo_operacao)
    ultimo_envio[chave] = time.time()


def enviar_proposta(proposta):
    try:
        rabbitmq.enviar(proposta)
        return True

    except Exception as erro:
        print(f"Erro ao enviar proposta para RabbitMQ: {erro}")

def executar_monitoramento():
    print("Iniciando monitoramento...")

    parametros = buscar_parametros_ativos()

    if not parametros:
        print("Nenhum parâmetro ativo encontrado.")
        return

    # Guarda apenas os símbolos únicos.
    # Exemplo:
    # PETR4 -> 3 parâmetros
    # VALE3 -> 2 parâmetros
    #
    # A Brapi será consultada apenas uma vez para cada ativo.
    simbolos = set()

    for parametro in parametros:
        simbolo = parametro["ativo_nome"].strip().upper()

        if simbolo:
            simbolos.add(simbolo)

    if not simbolos:
        print("Nenhum ativo válido encontrado.")
        return

    print(f"Ativos encontrados: {', '.join(sorted(simbolos))}")

    # Busca todas as ações de uma vez
    cotacoes = brapi.buscar_acoes(sorted(simbolos))

    if not cotacoes:
        print("Nenhuma cotação foi encontrada.")
        return

    for parametro in parametros:

        parametro_id = parametro["id"]

        # Normaliza o nome do ativo
        simbolo = parametro["ativo_nome"].strip().upper()

        cotacao = cotacoes.get(simbolo)

        if not cotacao:
            print(f"Cotação não encontrada para {simbolo}")
            continue

        preco = cotacao.get("regularMarketPrice")

        if preco is None:
            print(f"Preço não encontrado para {simbolo}")
            continue

        print(
            f"{simbolo} | "
            f"Preço atual: R$ {preco:.2f}"
        )

        # Atualiza o preço atual do ativo no banco
        atualizar_preco_ativo(
            parametro["ativo_nome"],
            preco
        )

        # Verifica se o parâmetro foi atingido
        decisao = analisar_parametro(
            parametro,
            preco
        )

        if decisao is None:
            continue

        tipo_operacao = decisao["tipoOperacao"]

        # Evita enviar várias decisões iguais em sequência
        if not pode_enviar(
            parametro_id,
            tipo_operacao
        ):
            print(
                f"Cooldown ativo para parâmetro "
                f"{parametro_id} ({tipo_operacao})"
            )
            continue

        # Envia para a API Java
        enviado = enviar_proposta(decisao)
        if enviado:
            registrar_envio(
                parametro_id,
                tipo_operacao
            )

            # Garante que o ativo exista na tabela ativo
            criar_ativo_se_nao_existir(
                parametro["ativo_nome"],
                parametro["tipo_ativo"],
                preco
            )

    print("Monitoramento finalizado.")