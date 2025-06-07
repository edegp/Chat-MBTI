import socket
from typing import Union
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.checkpoint.memory import MemorySaver
from contextlib import _GeneratorContextManager
import psycopg2
import psycopg2.extras

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


def get_dsn() -> str:
    try:
        # Check if "db" hostname is resolvable (Docker environment)
        socket.gethostbyname("db")
        host = "db"
    except socket.gaierror:
        # If not, assume local development
        host = "localhost"
        print(f"Cannot resolve 'db' hostname. Using '{host}' for local development.")

    return f"postgresql://postgres:postgres@{host}:5432/diagnosis_ai?sslmode=disable"


DB_URI = get_dsn()


def init_db(dsn: str = DB_URI):
    """スキーマを作成する（idempotent）。"""
    with psycopg2.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA_SQL)
            conn.commit()


def create_checkpointer() -> (
    Union[_GeneratorContextManager[PostgresSaver], MemorySaver]
):
    """DB_CONNECTION_STRING から PostgresSaver を生成。
    初回実行時は自動でテーブルを作成します。"""

    try:
        # Use environment variable if set, otherwise construct default
        print(f"Connecting to PostgreSQL at: {DB_URI}")
        return PostgresSaver.from_conn_string(DB_URI)
    except Exception as e:
        print(f"PostgreSQL connection error: {e}")
        print("Falling back to in-memory checkpoint")
        return MemorySaver()


class ChatSessionDriver:
    def __init__(self):
        self.connection_pool = None
        self.conn = psycopg2.connect(get_dsn())

    def get_or_create_user(
        self, firebase_uid, email=None, display_name=None, photo_url=None
    ) -> str:
        """Get existing user or create a new one based on Firebase auth data"""
        with self.conn.cursor() as cur:
            # Try to find existing user
            cur.execute("SELECT id FROM users WHERE firebase_uid = %s", (firebase_uid,))
            result = cur.fetchone()

            if result:
                # Update last login time
                cur.execute(
                    "UPDATE users SET last_login = now() WHERE firebase_uid = %s RETURNING id",
                    (firebase_uid,),
                )
                user_id = cur.fetchone()[0]
            else:
                cur.execute(
                    """INSERT INTO users
                    (firebase_uid, email, display_name, photo_url)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id""",
                    (firebase_uid, email, display_name, photo_url),
                )
                user_id = cur.fetchone()[0]

            self.conn.commit()
            return str(user_id)

    def get_session_by_user_id(self, user_id, status="in_progress"):
        """Get chat session by user ID."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM chat_sessions WHERE user_id=%s AND status=%s",
                (user_id, status),
            )
            result = cur.fetchone()
            return str(result[0]) if result else None

    def create_session(self, user_id) -> str:
        """Create a new chat session for the user."""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO chat_sessions (user_id, status) VALUES (%s, 'in_progress') RETURNING id",
                (user_id,),
            )
            session_id = cur.fetchone()[0]
            self.conn.commit()
            return str(session_id)

    def close_session(self, session_id):
        """Close the chat session by setting its status to 'completed'."""
        with self.conn.cursor() as cur:
            cur.execute(
                "UPDATE chat_sessions SET status='completed', finished_at=now() WHERE id=%s",
                (session_id,),
            )
            self.conn.commit()


class GeneratedQuestionDriver:
    def __init__(self):
        self.connection_pool = None
        self.conn = psycopg2.connect(DB_URI)

    def post_question(
        self, session_id, personality_element_id, question, display_order, model_version
    ):
        print(
            f"Posting question: {question} for session {session_id}, personality element {personality_element_id}, order {display_order}, model version {model_version}"
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
            return question_id

    def get_id(self, session_id, order):
        """Get question ID from session_id and order."""
        with self.conn.cursor() as cur:
            cur.execute(
                "SELECT id FROM generated_questions WHERE session_id=%s AND display_order=%s",
                (session_id, order),
            )
            result = cur.fetchone()
            print(
                f"Getting question ID for session {session_id}, order {order}: {result}"
            )
            return result[0] if result else None


class UserAnswerDriver:
    def __init__(self):
        self.connection_pool = None
        self.conn = psycopg2.connect(DB_URI)

    def post_answer(self, question_id, answer_text):
        """Post user answer to the database."""
        with self.conn.cursor() as cur:
            cur.execute(
                "INSERT INTO user_answers (question_id, answer_text) VALUES ( %s, %s)",
                (question_id, answer_text),
            )
            self.conn.commit()
        return True


class QuestionOptionsDriver:
    def __init__(self):
        self.conn = psycopg2.connect(DB_URI)

    def save_options(self, question_id, options_list):
        """質問に対する選択肢を保存"""
        with self.conn.cursor() as cur:
            for i, option in enumerate(options_list):
                cur.execute(
                    """INSERT INTO question_options 
                       (question_id, option_text, display_order) 
                       VALUES (%s, %s, %s)""",
                    (question_id, option, i),
                )
            self.conn.commit()

    def get_options(self, question_id):
        """質問に対する選択肢を取得"""
        with self.conn.cursor() as cur:
            cur.execute(
                """SELECT option_text FROM question_options 
                   WHERE question_id = %s 
                   ORDER BY display_order""",
                (question_id,),
            )
            return [row[0] for row in cur.fetchall()]
