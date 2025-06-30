"""
データベースドライバーの包括的テスト（日本語版）
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import psycopg2
import socket
from src.driver.db import (
    create_checkpointer,
    ChatSessionDriver,
    GeneratedQuestionDriver,
    UserAnswerDriver,
    QuestionOptionsDriver,
    get_dsn,
)
from src.exceptions import ConnectionError, QueryError


class TestCheckpointerの作成:
    """チェックポインター作成機能のテスト"""

    @patch("src.driver.db.PostgresSaver.from_conn_string")
    def test_PostgreSQLチェックポインターの正常作成(self, mock_postgres_saver):
        """PostgreSQLチェックポインターが正常に作成されることをテスト"""
        mock_checkpointer = Mock()
        mock_postgres_saver.return_value = mock_checkpointer

        result = create_checkpointer()

        assert result == mock_checkpointer
        mock_postgres_saver.assert_called_once()

    @patch("src.driver.db.MemorySaver")
    @patch("src.driver.db.PostgresSaver.from_conn_string")
    def test_PostgreSQL接続失敗時のメモリSaverフォールバック(
        self, mock_postgres_saver, mock_memory_saver
    ):
        """PostgreSQL接続失敗時にMemorySaverにフォールバックすることをテスト"""
        mock_postgres_saver.side_effect = Exception("Connection failed")
        mock_memory_checkpointer = Mock()
        mock_memory_saver.return_value = mock_memory_checkpointer

        result = create_checkpointer()

        assert result == mock_memory_checkpointer
        mock_postgres_saver.assert_called_once()
        mock_memory_saver.assert_called_once()


class TestDSN生成:
    """データベース接続文字列生成のテスト"""

    @patch("socket.gethostbyname")
    def test_Docker環境でのDSN生成(self, mock_gethostbyname):
        """Docker環境でのDSN生成をテスト"""
        mock_gethostbyname.return_value = "172.17.0.2"

        dsn = get_dsn()

        assert "db:5432" in dsn
        assert "postgresql://postgres:postgres@" in dsn
        mock_gethostbyname.assert_called_once_with("db")

    @patch("socket.gethostbyname")
    def test_ローカル開発環境でのDSN生成(self, mock_gethostbyname):
        """ローカル開発環境でのDSN生成をテスト"""
        mock_gethostbyname.side_effect = socket.gaierror("Name resolution failed")

        dsn = get_dsn()

        assert "localhost:5432" in dsn
        assert "postgresql://postgres:postgres@" in dsn


class TestChatSessionDriver:
    """ChatSessionDriverのデータベース操作テスト"""

    def setup_method(self):
        """テスト前の準備"""
        self.mock_conn = Mock()
        self.mock_cursor = Mock()

        # context managerを正しくモック
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        self.mock_conn.cursor.return_value = mock_cursor_context

        with patch("psycopg2.connect", return_value=self.mock_conn):
            self.driver = ChatSessionDriver()

    def test_既存ユーザーの取得(self):
        """Firebase UIDによる既存ユーザー取得をテスト"""
        # 準備
        self.mock_cursor.fetchone.side_effect = [
            ("user-123",),  # 1回目の呼び出し: ユーザーが存在
            ("user-123",),  # 2回目の呼び出し: 更新後のユーザーIDを返す
        ]

        # 実行
        result = self.driver.get_or_create_user("firebase-uid-123", "test@example.com")

        # 検証
        assert result == "user-123"
        assert self.mock_cursor.execute.call_count == 2
        self.mock_conn.commit.assert_called_once()

    def test_新規ユーザーの作成(self):
        """存在しない場合の新規ユーザー作成をテスト"""
        # 準備
        self.mock_cursor.fetchone.side_effect = [
            None,  # 1回目の呼び出し: ユーザーが存在しない
            ("new-user-123",),  # 2回目の呼び出し: 新規ユーザーIDを返す
        ]

        # 実行
        result = self.driver.get_or_create_user(
            "firebase-uid-new", "newuser@example.com", "New User", "http://photo.url"
        )

        # 検証
        assert result == "new-user-123"
        self.mock_conn.commit.assert_called_once()

    def test_セッションの取得_成功(self):
        """既存セッションの取得をテスト"""
        # 準備
        self.mock_cursor.fetchone.return_value = ("session-123",)

        # 実行
        result = self.driver.get_current_session_by_user_id("user-123")

        # 検証
        assert result == "session-123"
        self.mock_cursor.execute.assert_called_once()

    def test_セッションの取得_見つからない場合(self):
        """セッションが存在しない場合をテスト"""
        # 準備
        self.mock_cursor.fetchone.return_value = None

        # 実行
        result = self.driver.get_current_session_by_user_id("user-123")

        # 検証
        assert result is None

    def test_セッションの作成_成功(self):
        """セッション作成の成功をテスト"""
        # 準備
        self.mock_cursor.fetchone.return_value = ("new-session-123",)

        # 実行
        result = self.driver.create_session("user-123")

        # 検証
        assert result == "new-session-123"
        self.mock_conn.commit.assert_called_once()

    def test_セッションのクローズ_成功(self):
        """セッションクローズの成功をテスト"""
        # 実行
        self.driver.close_session("session-123")

        # 検証
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()


class TestGeneratedQuestionDriver:
    """GeneratedQuestionDriverのデータベース操作テスト"""

    def setup_method(self):
        """テスト前の準備"""
        self.mock_conn = Mock()
        self.mock_cursor = Mock()

        # context managerを正しくモック
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        self.mock_conn.cursor.return_value = mock_cursor_context

        with patch("psycopg2.connect", return_value=self.mock_conn):
            self.driver = GeneratedQuestionDriver()

    def test_質問の投稿_成功(self):
        """質問投稿の成功をテスト"""
        # 準備
        self.mock_cursor.fetchone.return_value = ("question-123",)

        # 実行
        result = self.driver.post_question(
            "session-123", 1, "Test question?", 1, "gpt-4"
        )

        # 検証
        assert result == "question-123"
        self.mock_conn.commit.assert_called_once()

    def test_質問IDの取得_成功(self):
        """セッションと順序による質問ID取得をテスト"""
        # 準備
        self.mock_cursor.fetchone.return_value = ("question-123",)

        # 実行
        result = self.driver.get_id("session-123", 1)

        # 検証
        assert result == "question-123"

    def test_質問IDの取得_見つからない場合(self):
        """質問IDが見つからない場合をテスト"""
        # 準備
        self.mock_cursor.fetchone.return_value = None

        # 実行
        result = self.driver.get_id("session-123", 999)

        # 検証
        assert result is None


class TestUserAnswerDriver:
    """UserAnswerDriverのデータベース操作テスト"""

    def setup_method(self):
        """テスト前の準備"""
        self.mock_conn = Mock()
        self.mock_cursor = Mock()

        # context managerを正しくモック
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        self.mock_conn.cursor.return_value = mock_cursor_context

        with patch("psycopg2.connect", return_value=self.mock_conn):
            self.driver = UserAnswerDriver()

    def test_回答の投稿_成功(self):
        """回答投稿の成功をテスト"""
        # 実行
        result = self.driver.post_answer("question-123", "User's answer")

        # 検証
        assert result is True
        self.mock_cursor.execute.assert_called_once()
        self.mock_conn.commit.assert_called_once()


class TestQuestionOptionsDriver:
    """QuestionOptionsDriverのデータベース操作テスト"""

    def setup_method(self):
        """テスト前の準備"""
        self.mock_conn = Mock()
        self.mock_cursor = Mock()

        # context managerを正しくモック
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=self.mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        self.mock_conn.cursor.return_value = mock_cursor_context

        with patch("psycopg2.connect", return_value=self.mock_conn):
            self.driver = QuestionOptionsDriver()

    def test_選択肢の保存_成功(self):
        """選択肢保存の成功をテスト"""
        # 準備
        options = ["Option A", "Option B", "Option C"]

        # 実行
        self.driver.save_options("question-123", options)

        # 検証
        assert self.mock_cursor.execute.call_count == 3
        self.mock_conn.commit.assert_called_once()

    def test_選択肢の取得_成功(self):
        """選択肢取得の成功をテスト"""
        # 準備
        self.mock_cursor.fetchall.return_value = [
            ("Option A",),
            ("Option B",),
            ("Option C",),
        ]

        # 実行
        result = self.driver.get_options("question-123")

        # 検証
        assert result == ["Option A", "Option B", "Option C"]
        self.mock_cursor.execute.assert_called_once()


class TestDatabaseのエラーハンドリング:
    """データベースエラーハンドリングシナリオのテスト"""

    @patch("psycopg2.connect")
    def test_データベース接続エラーの処理(self, mock_connect):
        """データベース接続エラーの処理をテスト"""
        # 準備
        mock_connect.side_effect = psycopg2.OperationalError("Connection failed")

        # 実行・検証
        with pytest.raises(ConnectionError):
            ChatSessionDriver()

    def test_SQL実行エラーの処理(self):
        """SQL実行エラーの処理をテスト"""
        # 準備
        mock_conn = Mock()
        mock_cursor = Mock()

        # context managerを正しくモック
        mock_cursor_context = Mock()
        mock_cursor_context.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor_context.__exit__ = Mock(return_value=None)
        mock_conn.cursor.return_value = mock_cursor_context
        mock_cursor.execute.side_effect = psycopg2.Error("SQL execution failed")

        with patch("psycopg2.connect", return_value=mock_conn):
            driver = ChatSessionDriver()

        # 実行・検証 - QueryErrorが期待される（psycopg2.Errorをラップしている）
        with pytest.raises(QueryError):
            driver.get_or_create_user("firebase-uid")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
