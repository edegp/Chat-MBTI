import os
import socket
from typing import Union
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver, PickleCheckpointSerializer
from langgraph.checkpoint.memory import MemorySaver
from contextlib import _GeneratorContextManager


def create_checkpointer() -> _GeneratorContextManager[Union[PostgresSaver, MemorySaver]]:
    """DB_CONNECTION_STRING から PostgresSaver を生成。
    初回実行時は自動でテーブルを作成します。"""
    try:
        # Check if "db" hostname is resolvable (Docker environment)
        socket.gethostbyname("db")
        host = "db"
    except socket.gaierror:
        # If not, assume local development
        host = "localhost"
        print(f"Cannot resolve 'db' hostname. Using '{host}' for local development.")

    try:
        # Use environment variable if set, otherwise construct default
        db_uri = (
            f"postgresql://postgres:postgres@{host}:5432/diagnosis_ai?sslmode=disable"
        )
        print(f"Connecting to PostgreSQL at: {db_uri}")
        return PostgresSaver.from_conn_string(db_uri)
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        print("Falling back to in-memory checkpoint")
        return MemorySaver()
