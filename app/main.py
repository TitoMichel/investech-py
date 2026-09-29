from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

from .config import MONITOR_INTERVAL_SECONDS
from .monitor import executar_monitoramento

app = FastAPI(
    title="InvesTech - Monitor de Investimentos",
    version="1.0.0"
)

scheduler = BackgroundScheduler()


@app.get("/")
def raiz():
    return {
        "sistema": "InvesTech",
        "status": "online"
    }


@app.get("/health")
def health():
    return {
        "status": "ok"
    }


@app.on_event("startup")
def iniciar_monitor():
    executar_monitoramento()

    scheduler.add_job(
        executar_monitoramento,
        "interval",
        seconds=MONITOR_INTERVAL_SECONDS,
        id="monitor_investimentos",
        replace_existing=True
    )

    scheduler.start()


@app.on_event("shutdown")
def parar_monitor():
    if scheduler.running:
        scheduler.shutdown()
