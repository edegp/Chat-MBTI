import socket
import logging
from typing import Union
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from contextlib import _GeneratorContextManager
import psycopg2
import psycopg2.extras
import os
from urllib.parse import quote_plus

from src.exceptions import (
    ConnectionError,
    QueryError,
    DataIntegrityError,
    SessionNotFoundError,
    create_error_response,
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

# CREATE TABLE IF NOT EXISTS diagnoses (
#     id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
#     session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
#     model_version   TEXT,
#     trait_scores    JSONB,
#     created_at      TIMESTAMP NOT NULL DEFAULT now()
# );
# CREATE TABLE IF NOT EXISTS personal_descriptions (
#     id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
#     session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
#     text            TEXT,
#     created_at      TIMESTAMP NOT NULL DEFAULT now()
# );

# CREATE TABLE IF NOT EXISTS avatars (
#     id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
#     session_id      UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
#     image_url       TEXT,
#     prompt_text     TEXT,
#     created_at      TIMESTAMP NOT NULL DEFAULT now()
# );

# UUIDアダプターを登録（ファイルの先頭に追加）
psycopg2.extras.register_uuid()
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


def get_dsn() -> str:
    logger.info("Constructing database connection string")
    # Read database name and use application user credentials
    db_name = os.getenv("DB_NAME", "diagnosis_ai")
    db_user = APP_DB_USER
    db_pass = quote_plus(APP_DB_PASS)
    socket_path = DB_SOCKET_PATH
    logger.info(f"Using database: {db_name}, user: {db_user} via socket: {socket_path}")
    logger.debug(f"Database connection details {db_pass}")
    if SQL_CONNECTION_NAME is not None:
        logger.info("Connecting via Unix socket", extra={"socket_path": socket_path})
        return f"postgresql://{db_user}:{db_pass}@/{db_name}?host={socket_path}"

    # Use custom host if provided (e.g., Cloud Run TCP or other env)
    db_host = os.environ.get("DB_HOST")
    if db_host:
        logger.info(
            "Connecting via DB_HOST environment variable",
            extra={"unix_socket": db_host},
        )
        return (
            f"postgresql://{db_user}:{db_pass}@{db_host}:5432/{db_name}?sslmode=disable"
        )

    # Fallback to Docker 'db' hostname or localhost
    try:
        socket.gethostbyname("db")
        host = "db"
        logger.info(
            "Connecting to database in Docker environment", extra={"host": host}
        )
    except socket.gaierror as e:
        host = "localhost"
        logger.info(
            "Database connection fallback to local development",
            extra={"host": host, "reason": str(e)},
        )

    return f"postgresql://{db_user}:{db_pass}@{host}:5432/{db_name}?sslmode=disable"


DB_URI = get_dsn()


def init_postgres(dsn: str = DB_URI):
    """スキーマを作成する（idempotent）。"""
    logger.info("Initializing PostgreSQL database %s", dsn)
    if SQL_CONNECTION_NAME is None and not os.getenv("DB_HOST"):
        try:
            # Connect as superuser to set up local app user
            with psycopg2.connect(dsn) as admin_conn:
                with admin_conn.cursor() as cur_admin:
                    cur_admin.execute(
                        f"CREATE ROLE IF NOT EXISTS {APP_DB_USER} LOGIN PASSWORD %s;",
                        (APP_DB_PASS,),
                    )
                    cur_admin.execute(
                        f"GRANT CONNECT ON DATABASE {os.getenv('DB_NAME', 'diagnosis_ai')} TO {APP_DB_USER};"
                    )
                    cur_admin.execute(f"GRANT USAGE ON SCHEMA public TO {APP_DB_USER};")
                    cur_admin.execute(
                        f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {APP_DB_USER};"
                    )
                    cur_admin.execute(
                        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {APP_DB_USER};"
                    )
            logger.info("Local DB user ensured", extra={"app_user": APP_DB_USER})
        except Exception as e:
            logger.warning(
                "Local DB user setup skipped or failed", extra={"error": str(e)}
            )

    try:
        logger.info("Initializing PostgreSQL schema", extra={"dsn": dsn})
        with psycopg2.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(SCHEMA_SQL)
                conn.commit()
        logger.info("PostgreSQL schema initialization completed successfully")
    except psycopg2.Error as e:
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


def create_checkpointer() -> (
    Union[_GeneratorContextManager[PostgresSaver], MemorySaver]
):
    """DB_CONNECTION_STRING から PostgresSaver を生成。
    初回実行時は自動でテーブルを作成します。"""

    try:
        # Use environment variable if set, otherwise construct default
        logger.info("Creating PostgreSQL checkpointer", extra={"db_uri": DB_URI})
        checkpointer = PostgresSaver.from_conn_string(DB_URI)
        logger.info("PostgreSQL checkpointer created successfully")
        return checkpointer
    except Exception as e:
        logger.warning(
            "PostgreSQL connection failed, falling back to memory checkpointer",
            extra={"error": str(e), "db_uri": DB_URI},
        )
        return MemorySaver()


class ChatSessionDriver:
    def __init__(self):
        self.connection_pool = None
        try:
            self.conn = psycopg2.connect(get_dsn())
            logger.info("ChatSessionDriver initialized successfully")
        except psycopg2.Error as e:
            error = ConnectionError(
                "Failed to establish database connection for ChatSessionDriver",
                {"error_code": e.pgcode, "error_message": str(e)},
            )
            error.log_error(logger)
            raise error

    def get_or_create_user(
        self, firebase_uid, email=None, display_name=None, photo_url=None
    ) -> str:
        """Get existing user or create a new one based on Firebase auth data"""
        try:
            logger.info(
                "Getting or creating user",
                extra={
                    "firebase_uid": firebase_uid,
                    "email": email,
                    "display_name": display_name,
                },
            )

            with self.conn.cursor() as cur:
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
                        "Existing user login updated", extra={"user_id": str(user_id)}
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

                self.conn.commit()
                return str(user_id)

        except psycopg2.Error as e:
            self.conn.rollback()
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
            self.conn.rollback()
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

            with self.conn.cursor() as cur:
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

        except psycopg2.Error as e:
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
            logger.info("Creating new session", extra={"user_id": user_id})

            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO chat_sessions (user_id, status) VALUES (%s, 'in_progress') RETURNING id",
                    (user_id,),
                )
                session_id = cur.fetchone()[0]
                self.conn.commit()

                logger.info(
                    "Session created successfully",
                    extra={"session_id": str(session_id), "user_id": user_id},
                )
                return str(session_id)

        except psycopg2.Error as e:
            self.conn.rollback()
            error = QueryError(
                "Failed to create session",
                {"user_id": user_id, "error_code": e.pgcode, "error_message": str(e)},
            )
            error.log_error(logger)
            raise error

    def close_session(self, session_id):
        """Close the chat session by setting its status to 'completed'."""
        try:
            logger.info("Closing session", extra={"session_id": session_id})

            with self.conn.cursor() as cur:
                cur.execute(
                    "UPDATE chat_sessions SET status='completed', finished_at=now() WHERE id=%s",
                    (session_id,),
                )
                if cur.rowcount == 0:
                    raise SessionNotFoundError(
                        "Session not found", {"session_id": session_id}
                    )
                self.conn.commit()

            logger.info("Session closed successfully", extra={"session_id": session_id})

        except SessionNotFoundError:
            raise  # Re-raise the custom exception
        except psycopg2.Error as e:
            self.conn.rollback()
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


class GeneratedQuestionDriver:
    def __init__(self):
        self.connection_pool = None
        try:
            self.conn = psycopg2.connect(DB_URI)
            logger.info("GeneratedQuestionDriver initialized successfully")
        except psycopg2.Error as e:
            error = ConnectionError(
                "Failed to establish database connection for GeneratedQuestionDriver",
                {"error_code": e.pgcode, "error_message": str(e)},
            )
            error.log_error(logger)
            raise error

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

            with self.conn.cursor() as cur:
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
                self.conn.commit()

                logger.info(
                    "Question posted successfully",
                    extra={"question_id": str(question_id)},
                )
                return question_id

        except psycopg2.Error as e:
            self.conn.rollback()
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
            logger.info(
                "Getting question ID", extra={"session_id": session_id, "order": order}
            )

            with self.conn.cursor() as cur:
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

        except psycopg2.Error as e:
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


class UserAnswerDriver:
    def __init__(self):
        self.connection_pool = None
        try:
            self.conn = psycopg2.connect(DB_URI)
            logger.info("UserAnswerDriver initialized successfully")
        except psycopg2.Error as e:
            error = ConnectionError(
                "Failed to establish database connection for UserAnswerDriver",
                {"error_code": e.pgcode, "error_message": str(e)},
            )
            error.log_error(logger)
            raise error

    def post_answer(self, question_id, answer_text):
        """Post user answer to the database."""
        try:
            logger.info(
                "Posting user answer",
                extra={
                    "question_id": str(question_id),
                    "answer_preview": answer_text[:100] + "..."
                    if len(answer_text) > 100
                    else answer_text,
                },
            )

            with self.conn.cursor() as cur:
                cur.execute(
                    "INSERT INTO user_answers (question_id, answer_text) VALUES ( %s, %s)",
                    (question_id, answer_text),
                )
                self.conn.commit()

            logger.info(
                "User answer posted successfully",
                extra={"question_id": str(question_id)},
            )
            return True

        except psycopg2.Error as e:
            self.conn.rollback()
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


class QuestionOptionsDriver:
    def __init__(self):
        try:
            self.conn = psycopg2.connect(DB_URI)
            logger.info("QuestionOptionsDriver initialized successfully")
        except psycopg2.Error as e:
            error = ConnectionError(
                "Failed to establish database connection for QuestionOptionsDriver",
                {"error_code": e.pgcode, "error_message": str(e)},
            )
            error.log_error(logger)
            raise error

    def save_options(self, question_id, options_list):
        """質問に対する選択肢を保存"""
        try:
            logger.info(
                "Saving question options",
                extra={
                    "question_id": str(question_id),
                    "options_count": len(options_list),
                },
            )

            with self.conn.cursor() as cur:
                for i, option in enumerate(options_list):
                    cur.execute(
                        """INSERT INTO question_options
                           (question_id, option_text, display_order)
                           VALUES (%s, %s, %s)""",
                        (question_id, option, i),
                    )
                self.conn.commit()

            logger.info(
                "Question options saved successfully",
                extra={
                    "question_id": str(question_id),
                    "options_count": len(options_list),
                },
            )

        except psycopg2.Error as e:
            self.conn.rollback()
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
            logger.info(
                "Getting question options", extra={"question_id": str(question_id)}
            )

            with self.conn.cursor() as cur:
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

        except psycopg2.Error as e:
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
