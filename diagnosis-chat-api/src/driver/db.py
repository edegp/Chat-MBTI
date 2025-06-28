import os
import socket
import logging
import sys
import traceback
from typing import Union, Generator, Optional, Any
from contextlib import contextmanager

# Import psycopg3 instead of psycopg
import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from urllib.parse import quote_plus

from src.exceptions import (
    ConnectionError,
    QueryError,
    SessionNotFoundError,
)

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS users (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    firebase_uid    TEXT UNIQUE NOT NULL,  -- Firebase user ID
    email           TEXT UNIQUE,
    display_name    TEXT,
    photo_url       TEXT,          -- Profile photo from Firebase
    created_at      TIMESTAMP NOT NULL DEFAULT now(),
    last_login      TIMESTAMP
);

CREATE TABLE IF NOT EXISTS chat_sessions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id         UUID NOT NULL REFERENCES users(id),
    status          TEXT NOT NULL CHECK (status IN ('in_progress','completed')),
    started_at      TIMESTAMP NOT NULL DEFAULT now(),
    finished_at     TIMESTAMP,
    current_q_index INT     NOT NULL DEFAULT 0
);

CREATE SEQUENCE IF NOT EXISTS personality_elements_id_seq;
CREATE TABLE IF NOT EXISTS personality_elements (
    id              INT PRIMARY KEY DEFAULT nextval('personality_elements_id_seq'),
    name            TEXT NOT NULL UNIQUE
);
INSERT INTO personality_elements (name) VALUES
('energy'), ('mind'), ('nature'), ('tactics')
ON CONFLICT (name) DO NOTHING;

CREATE TABLE IF NOT EXISTS generated_questions (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    personality_element_id INT NOT NULL REFERENCES personality_elements(id) ON DELETE CASCADE,
    display_order   INT  NOT NULL,
    question_text   TEXT NOT NULL,
    meta            JSONB,
    model_version   TEXT,
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS generated_questions_session_x ON generated_questions(session_id);

CREATE TABLE IF NOT EXISTS question_options (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id     UUID NOT NULL REFERENCES generated_questions(id) ON DELETE CASCADE,
    option_text     TEXT NOT NULL,
    display_order   INT NOT NULL,  -- 選択肢の表示順序
    created_at      TIMESTAMP NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS question_options_question_x ON question_options(question_id);


CREATE TABLE IF NOT EXISTS user_answers (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    question_id     UUID NOT NULL REFERENCES generated_questions(id) ON DELETE CASCADE,
    answer_text     TEXT NOT NULL,
    ts              TIMESTAMP NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS user_answers_session_x ON user_answers(question_id);

"""

SQL_CONNECTION_NAME = os.getenv("SQL_CONNECTION_NAME")
DB_SOCKET_PATH = f"/cloudsql/{SQL_CONNECTION_NAME}"
# Environment variables for secure DB user management


try:
    # Application user credentials must be set via environment (e.g., Secret Manager)
    APP_DB_USER = os.environ["DB_APP_USER"]
    APP_DB_PASS = os.environ["DB_APP_PASS"]
except KeyError as e:
    raise RuntimeError(
        f"Required environment variable {e.args[0]} not set for application DB user"
    )

try:
    # Admin (superuser) credentials for role setup
    ADMIN_DB_USER = os.environ["DB_ADMIN_USER"]
    ADMIN_DB_PASS = os.environ["DB_ADMIN_PASS"]
except KeyError as e:
    raise RuntimeError(
        f"Required environment variable {e.args[0]} not set for admin DB user"
    )

# グローバルコネクションプール
_connection_pool = None


def get_dsn() -> str:
    # Read database name and use application user credentials
    db_name = os.getenv("DB_NAME", "diagnosis_ai")
    db_user = APP_DB_USER
    db_pass = quote_plus(APP_DB_PASS)
    socket_path = DB_SOCKET_PATH
    if SQL_CONNECTION_NAME is not None:
        logger.info("Connecting via Unix socket", extra={"socket_path": socket_path})
        return f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket_path}"

    # Use custom host if provided (e.g., Cloud Run TCP or other env)
    db_host = os.environ.get("DB_HOST")
    if db_host:
        return (
            f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}?sslmode=disable"
        )

    # Fallback to Docker 'db' hostname or localhost
    try:
        socket.gethostbyname("db")
        host = "db"
    except socket.gaierror as e:
        host = "localhost"

    return f"postgresql://{db_user}:{db_pass}@{host}:5432/{db_name}?sslmode=disable"


DB_URI = get_dsn()


def get_connection_pool() -> ConnectionPool:
    """シングルトンコネクションプールを取得または作成"""
    global _connection_pool
    if _connection_pool is None:
        try:
            # psycopg3 connection poolの作成
            _connection_pool = ConnectionPool(
                conninfo=DB_URI,
                min_size=3,
                max_size=20,
                # kwargs={"row_factory": dict_row},
            )
            logger.info("DB connection pool initialized with min=3, max=20 connections")
        except Exception as e:
            logger.error(f"Failed to create connection pool: {str(e)}")
            raise
    return _connection_pool


@contextmanager
def get_db_connection() -> Generator[psycopg.Connection, None, None]:
    """接続を安全に取得して返却するコンテキストマネージャー"""
    pool = get_connection_pool()
    conn = None
    try:
        # psycopg3でpoolから接続を取得
        conn = pool.getconn()
        # 自動コミット無効化
        conn.autocommit = False
        yield conn
    except Exception as e:
        logger.error(f"Connection error: {str(e)}")
        traceback.print_exc()
        if conn:
            try:
                conn.rollback()
            except Exception as rollback_error:
                logger.error(f"Rollback error: {str(rollback_error)}")
        raise ConnectionError(f"Database connection error: {str(e)}")
    finally:
        if conn:
            try:
                # 例外が発生していなければコミット
                if sys.exc_info()[0] is None:
                    conn.commit()
                # 接続をプールに返却
                pool.putconn(conn)
            except Exception as e:
                logger.error(f"Error returning connection to pool: {str(e)}")


def init_postgres(dsn: str = DB_URI) -> None:
    """Initialize PostgreSQL schema and extensions."""
    try:
        logger.info("Initializing PostgreSQL schema")

        # Connect with psycopg3
        conn = psycopg.connect(dsn)
        conn.autocommit = True

        with conn.cursor() as cur:
            # Create extensions
            cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

            # For role management, avoid parameter substitution in DO blocks
            # Instead, use format or interpolate values directly
            db_user = os.environ.get("POSTGRES_USER", "postgres")
            db_password = os.environ.get("POSTGRES_PASSWORD", "postgres")

            # Create role if needed - properly escape identifiers and literals
            cur.execute(
                f"""
                DO $$
                BEGIN
                    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{db_user}') THEN
                        EXECUTE format('CREATE ROLE %I LOGIN PASSWORD %L', '{db_user}', '{db_password}');
                    END IF;
                END
                $$;
                """
            )

            # Create tables
            cur.execute(SCHEMA_SQL)

            logger.info("PostgreSQL schema initialized successfully")
    except psycopg.Error as e:
        error = ConnectionError(
            "Failed to initialize PostgreSQL schema",
            {"dsn": dsn, "error_code": e.pgcode, "error_message": str(e)},
        )
        error.log_error(logger)
        raise error
    except Exception as e:
        error = ConnectionError(
            "Unexpected error during PostgreSQL initialization",
            {"dsn": dsn, "error": str(e)},
        )
        error.log_error(logger)
        raise error
    finally:
        if "conn" in locals() and conn:
            conn.close()


@contextmanager
def create_checkpointer() -> Union[Generator[PostgresSaver, None, None], MemorySaver]:
    """Generate PostgresSaver from DB_CONNECTION_STRINGget_session_by_user_id. Tables are created automatically on first run."""
    try:
        with get_db_connection() as conn:
            yield PostgresSaver(conn)
    except Exception as e:
        logger.warning(
            "PostgreSQL connection failed, falling back to memory checkpointer",
            extra={"error": str(e), "db_uri": DB_URI},
        )
        return MemorySaver()


# 接続のラップ用の共通ベースクラス
class BaseDBDriver:
    """すべてのDBドライバーの基底クラス"""

    def __init__(self):
        # 接続を保持せず、必要時にプールから取得
        pass

    @contextmanager
    def get_connection(self):
        """DB接続を安全に取得"""
        with get_db_connection() as conn:
            yield conn


class ChatSessionDriver(BaseDBDriver):
    def get_or_create_user(
        self, firebase_uid, email=None, display_name=None, photo_url=None
    ) -> str:
        """Get existing user or create a new one based on Firebase auth data"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    # Try to find existing user
                    cur.execute(
                        "SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,)
                    )
                    result = cur.fetchone()

                    if result:
                        # Update last login time
                        cur.execute(
                            "UPDATE users SET last_login = now() WHERE firebase_uid = %s RETURNING id",
                            (firebase_uid,),
                        )
                        user_id = cur.fetchone()[0]
                        logger.info(
                            "Existing user login updated",
                            extra={"user_id": str(user_id)},
                        )
                    else:
                        cur.execute(
                            """INSERT INTO users
                            (firebase_uid, email, display_name, photo_url)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id""",
                            (firebase_uid, email, display_name, photo_url),
                        )
                        user_id = cur.fetchone()[0]
                        logger.info("New user created", extra={"user_id": str(user_id)})

                    conn.commit()
                    return str(user_id)

        except psycopg.Error as e:
            if conn:
                conn.rollback()
            error = QueryError(
                "Failed to get or create user",
                {
                    "firebase_uid": firebase_uid,
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error
        except Exception as e:
            if conn:
                conn.rollback()
            error = QueryError(
                "Unexpected error during user operation",
                {"firebase_uid": firebase_uid, "error": str(e)},
            )
            error.log_error(logger)
            raise error

    def get_session_by_user_id(self, user_id, status="in_progress"):
        """Get chat session by user ID."""
        try:
            logger.info(
                "Getting session by user ID",
                extra={"user_id": user_id, "status": status},
            )

            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM chat_sessions WHERE user_id=%s AND status=%s",
                        (user_id, status),
                    )
                    result = cur.fetchone()
                    session_id = str(result[0]) if result else None

                    if session_id:
                        logger.info("Session found", extra={"session_id": session_id})
                    else:
                        logger.info(
                            "No session found for user",
                            extra={"user_id": user_id, "status": status},
                        )

                    return session_id

        except psycopg.Error as e:
            error = QueryError(
                "Failed to get session by user ID",
                {
                    "user_id": user_id,
                    "status": status,
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error

    def create_session(self, user_id) -> str:
        """Create a new chat session for the user."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO chat_sessions (user_id, status) VALUES (%s, 'in_progress') RETURNING id",
                        (user_id,),
                    )
                    session_id = cur.fetchone()[0]
                    conn.commit()

                    logger.info(
                        "Session created successfully",
                        extra={"session_id": str(session_id), "user_id": user_id},
                    )
                    return str(session_id)
        except psycopg.Error as e:
            if conn:
                conn.rollback()
            error = QueryError(
                "Failed to create session",
                {"user_id": user_id, "error_code": e.pgcode, "error_message": str(e)},
            )
            error.log_error(logger)
            raise error

    def close_session(self, session_id):
        """Close the chat session by setting its status to 'completed'."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE chat_sessions SET status='completed', finished_at=now() WHERE id=%s",
                        (session_id,),
                    )
                    if cur.rowcount == 0:
                        raise SessionNotFoundError(
                            "Session not found", {"session_id": session_id}
                        )
                    conn.commit()

                logger.info(
                    "Session closed successfully", extra={"session_id": session_id}
                )

        except SessionNotFoundError:
            raise  # Re-raise the custom exception
        except psycopg.Error as e:
            if conn:
                conn.rollback()
            error = QueryError(
                "Failed to close session",
                {
                    "session_id": session_id,
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error


class GeneratedQuestionDriver(BaseDBDriver):
    def post_question(
        self, session_id, personality_element_id, question, display_order, model_version
    ):
        try:
            logger.info(
                "Posting question",
                extra={
                    "session_id": session_id,
                    "personality_element_id": personality_element_id,
                    "display_order": display_order,
                    "model_version": model_version,
                    "question_preview": question[:50] + "..."
                    if len(question) > 50
                    else question,
                },
            )
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    question_id = cur.execute(
                        """INSERT INTO generated_questions
                            (session_id, personality_element_id, display_order, question_text, model_version)
                            VALUES (%s,%s,%s,%s,%s)
                            RETURNING id
                        """,
                        (
                            session_id,
                            personality_element_id,
                            display_order,
                            question,
                            model_version,
                        ),
                    )
                    question_id = cur.fetchone()[0]
                    conn.commit()
                    return question_id

        except psycopg.Error as e:
            if conn:
                conn.rollback()
            error = QueryError(
                "Failed to post question",
                {
                    "session_id": session_id,
                    "personality_element_id": personality_element_id,
                    "display_order": display_order,
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error

    def get_id(self, session_id, order):
        """Get question ID from session_id and order."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id FROM generated_questions WHERE session_id=%s AND display_order=%s",
                        (session_id, order),
                    )
                    result = cur.fetchone()
                    question_id = result[0] if result else None

                    if question_id:
                        logger.info(
                            "Question ID found", extra={"question_id": str(question_id)}
                        )
                    else:
                        logger.warning(
                            "Question ID not found",
                            extra={"session_id": session_id, "order": order},
                        )

                    return question_id

        except psycopg.Error as e:
            error = QueryError(
                "Failed to get question ID",
                {
                    "session_id": session_id,
                    "order": order,
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error


class UserAnswerDriver(BaseDBDriver):
    def post_answer(self, question_id, answer_text):
        """Post user answer to the database."""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "INSERT INTO user_answers (question_id, answer_text) VALUES ( %s, %s)",
                        (question_id, answer_text),
                    )
                    conn.commit()

            logger.info(
                "User answer posted successfully",
                extra={"question_id": str(question_id)},
            )
            return True

        except psycopg.Error as e:
            if conn:
                conn.rollback()
            error = QueryError(
                "Failed to post user answer",
                {
                    "question_id": str(question_id),
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error


class QuestionOptionsDriver(BaseDBDriver):
    def save_options(self, question_id, options_list):
        """質問に対する選択肢を保存"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    for i, option in enumerate(options_list):
                        cur.execute(
                            """INSERT INTO question_options
                            (question_id, option_text, display_order)
                            VALUES (%s, %s, %s)""",
                            (question_id, option, i),
                        )
                    conn.commit()

            logger.info(
                "Question options saved successfully",
                extra={
                    "question_id": str(question_id),
                    "options_count": len(options_list),
                },
            )

        except psycopg.Error as e:
            if conn:
                conn.rollback()
            error = QueryError(
                "Failed to save question options",
                {
                    "question_id": str(question_id),
                    "options_count": len(options_list),
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error

    def get_options(self, question_id):
        """質問に対する選択肢を取得"""
        try:
            with self.get_connection() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """SELECT option_text FROM question_options
                        WHERE question_id = %s
                        ORDER BY display_order""",
                        (question_id,),
                    )
                    options = [row[0] for row in cur.fetchall()]

            logger.info(
                "Question options retrieved successfully",
                extra={"question_id": str(question_id), "options_count": len(options)},
            )
            return options

        except psycopg.Error as e:
            error = QueryError(
                "Failed to get question options",
                {
                    "question_id": str(question_id),
                    "error_code": e.pgcode,
                    "error_message": str(e),
                },
            )
            error.log_error(logger)
            raise error
