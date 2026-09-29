import mysql.connector
from mysql.connector import Error
from .config import (
    DB_HOST, DB_PORT, DB_USER, DB_PASSWORDS, DB_NAME
)

def get_connection():
    return mysql.connector.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORDS,
        database=DB_NAME
    )

def buscar_parametros_ativos():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute(
            '''
            SELECT
                id,
                status_parametro,
                quantidade_maxima,
                preco_minimo,
                preco_maximo,
                data_enviado,
                ativo_nome,
                tipo_ativo,
                carteira_id
            FROM parametro
            WHERE status_parametro = 1
            '''
        )
        return cursor.fetchall()
    finally:
        cursor.close()
        conn.close()

def atualizar_preco_ativo(nome_ativo, preco):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            '''
            UPDATE ativo
            SET preco_atual = %s
            WHERE nome = %s
            ''',
            (preco, nome_ativo)
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()

def criar_ativo_se_nao_existir(nome_ativo, tipo_ativo, preco):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(
            'SELECT id FROM ativo WHERE nome = %s LIMIT 1',
            (nome_ativo,)
        )
        ativo = cursor.fetchone()

        if ativo:
            cursor.execute(
                '''
                UPDATE ativo
                SET preco_atual = %s, tipo_ativo = %s
                WHERE id = %s
                ''',
                (preco, tipo_ativo, ativo[0])
            )
        else:
            cursor.execute(
                '''
                INSERT INTO ativo
                    (nome, tipo_ativo, preco_atual, status_ativo)
                VALUES
                    (%s, %s, %s, 1)
                ''',
                (nome_ativo, tipo_ativo, preco)
            )

        conn.commit()
    finally:
        cursor.close()
        conn.close()
