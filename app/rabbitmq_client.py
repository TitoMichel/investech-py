import json
import pika

from app.config import (
    RABBITMQ_HOST,
    RABBITMQ_PORT,
    RABBITMQ_USER,
    RABBITMQ_PASSWORD,
    RABBITMQ_QUEUE,
    RABBITMQ_VHOST
)


class RabbitMQClient:

    def __init__(self):
        self.connection = None
        self.channel = None

    def conectar(self):
        credenciais = pika.PlainCredentials(
            RABBITMQ_USER,
            RABBITMQ_PASSWORD
        )

        parametros = pika.ConnectionParameters(
            host=RABBITMQ_HOST,
            port=RABBITMQ_PORT,
            virtual_host=RABBITMQ_VHOST,
            credentials=credenciais
        )

        self.connection = pika.BlockingConnection(parametros)
        self.channel = self.connection.channel()

        self.channel.queue_declare(
            queue=RABBITMQ_QUEUE,
            durable=True
        )

    def enviar(self, mensagem):
        if self.channel is None or self.channel.is_closed:
            self.conectar()

        self.channel.basic_publish(
            exchange="",
            routing_key=RABBITMQ_QUEUE,
            body=json.dumps(mensagem),
            properties=pika.BasicProperties(
                delivery_mode=2
            )
        )

        print(
            f"Proposta enviada para RabbitMQ: "
            f"{mensagem['nomeAtivo']} | "
            f"{mensagem['tipoOperacao']}"
        )

    def fechar(self):
        if self.connection and not self.connection.is_closed:
            self.connection.close()