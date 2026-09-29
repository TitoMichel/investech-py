import logging
import time
from datetime import datetime

import requests

from .brapi_client import BrapiClient
from .config import (
    DECISAO_URL,
    DECISION_COOLDOWN_SECONDS,
    DEFAULT_QUANTITY
)
from .database import (
    buscar_parametros_ativos,
    criar_ativo_se_nao_existir
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)

# Guarda quando uma determinada condição foi enviada.
# Isso evita POST a cada ciclo enquanto o preço continua dentro da condição.
ultimo_envio = {}


def pode_enviar(chave):
    agora = time.time()
    ultimo = ultimo_envio.get(chave)

    if ultimo is None:
        return True

    return (agora - ultimo) >= DECISION_COOLDOWN_SECONDS


def registrar_envio(chave):
    ultimo_envio[chave] = time.time()


def analisar_parametro(parametro, cotacao):
    preco = float(cotacao["regularMarketPrice"])

    preco_minimo = float(parametro["preco_minimo"])
    preco_maximo = float(parametro["preco_maximo"])
    quantidade_maxima = float(parametro["quantidade_maxima"])

    # Regra de compra:
    # preço atual <= preço máximo que o usuário aceita pagar.
    if preco <= preco_maximo:
        return {
            "retornoProposta": "APROVADA",
            "motivo": (
                f"Preço atual ({preco:.2f}) está abaixo ou igual "
                f"ao preço máximo de compra ({preco_maximo:.2f})."
            ),
            "valorAprovado": preco,
            "quantidadeAprovada": quantidade_maxima,
            "tipoOperacao": "COMPRA",
        }

    # Regra de venda:
    # preço atual >= preço mínimo pelo qual o usuário aceita vender.
    if preco >= preco_minimo:
        return {
            "retornoProposta": "APROVADA",
            "motivo": (
                f"Preço atual ({preco:.2f}) está acima ou igual "
                f"ao preço mínimo de venda ({preco_minimo:.2f})."
            ),
            "valorAprovado": preco,
            "quantidadeAprovada": quantidade_maxima,
            "tipoOperacao": "VENDA",
        }

    return None


def enviar_decisao(decisao, parametro):
    # O seu JSON exige propostaId, mas a tabela parametro não possui
    # proposta_id. Por isso, por segurança, não inventamos esse ID.
    # O valor 0 deve ser substituído quando o relacionamento estiver definido.
    payload = {
        "retornoProposta": decisao["retornoProposta"],
        "motivo": decisao["motivo"],
        "valorAprovado": decisao["valorAprovado"],
        "quantidadeAprovada": decisao["quantidadeAprovada"],
        "tipoOperacao": decisao["tipoOperacao"],
        "propostaId": 0,
        "carteiraId": parametro["carteira_id"]
    }

    response = requests.post(
        DECISAO_URL,
        json=payload,
        timeout=10
    )

    response.raise_for_status()

    return response


def executar_monitoramento():
    logger.info("Iniciando ciclo de monitoramento...")

    parametros = buscar_parametros_ativos()

    if not parametros:
        logger.info("Nenhum parâmetro ativo encontrado.")
        return

    # Agrupa por tipo + símbolo.
    # Assim, vários parâmetros da mesma carteira não geram vários GETs.
    grupos = {}

    for parametro in parametros:
        chave = (
            parametro["tipo_ativo"].upper(),
            parametro["ativo_nome"].upper()
        )
        grupos.setdefault(chave, []).append(parametro)

    cliente = BrapiClient()

    acoes = [
        simbolo
        for (tipo, simbolo) in grupos
        if tipo in ("ACAO", "AÇÕES", "B3", "FII", "ETF", "BDR")
    ]

    criptos = [
        simbolo
        for (tipo, simbolo) in grupos
        if tipo in ("CRYPTO", "CRIPTO", "CRIPTOMOEDA")
    ]

    cotacoes = {}

    try:
        cotacoes.update(cliente.buscar_acoes(acoes))
    except Exception as erro:
        logger.exception("Erro ao consultar ações: %s", erro)

    try:
        cotacoes.update(cliente.buscar_criptos(criptos))
    except Exception as erro:
        logger.exception("Erro ao consultar criptomoedas: %s", erro)

    # Agora a cotação já foi obtida.
    # Todos os parâmetros daquele ativo usam a mesma resposta.
    for (tipo, simbolo), parametros_do_ativo in grupos.items():
        cotacao = cotacoes.get(simbolo)

        if not cotacao:
            logger.warning("Cotação não encontrada para %s", simbolo)
            continue

        preco = cotacao.get("regularMarketPrice")

        if preco is None:
            logger.warning("Preço não encontrado para %s", simbolo)
            continue

        for parametro in parametros_do_ativo:
            decisao = analisar_parametro(parametro, cotacao)

            if decisao is None:
                logger.info(
                    "%s | parâmetro %s não atendido | preço=%.2f",
                    simbolo,
                    parametro["id"],
                    preco
                )
                continue

            chave = (
                parametro["id"],
                decisao["tipoOperacao"]
            )

            if not pode_enviar(chave):
                logger.info(
                    "%s | parâmetro %s já enviado recentemente",
                    simbolo,
                    parametro["id"]
                )
                continue

            try:
                enviar_decisao(decisao, parametro)
                registrar_envio(chave)

                criar_ativo_se_nao_existir(
                    parametro["ativo_nome"],
                    parametro["tipo_ativo"],
                    preco
                )

                logger.info(
                    "%s | parâmetro %s atendido | %s | preço=%.2f",
                    simbolo,
                    parametro["id"],
                    decisao["tipoOperacao"],
                    preco
                )

            except Exception as erro:
                logger.exception(
                    "Erro ao enviar decisão do parâmetro %s: %s",
                    parametro["id"],
                    erro
                )
