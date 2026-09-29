import requests
from .config import BRAPI_BASE_URL, BRAPI_API_TOKEN

class BrapiClient:

    def __init__(self):
        self.session = requests.Session()

        if BRAPI_API_TOKEN:
            self.session.headers.update({
                "Authorization": f"Bearer {BRAPI_API_TOKEN}"
            })

    def buscar_acoes(self, simbolos):
        if not simbolos:
            return {}

        # Uma chamada para vários ativos.
        url = f"{BRAPI_BASE_URL}/api/quote/{','.join(simbolos)}"

        response = self.session.get(url, timeout=10)
        response.raise_for_status()

        dados = response.json()

        resultado = {}

        for ativo in dados.get("results", []):
            resultado[ativo["symbol"]] = ativo

        return resultado

    def buscar_criptos(self, simbolos):
        if not simbolos:
            return {}

        url = f"{BRAPI_BASE_URL}/api/v2/crypto"

        response = self.session.get(
            url,
            params={
                "coin": ",".join(simbolos),
                "currency": "BRL"
            },
            timeout=10
        )
        response.raise_for_status()

        dados = response.json()

        resultado = {}

        for ativo in dados.get("coins", []):
            resultado[ativo["coin"]] = ativo

        return resultado
