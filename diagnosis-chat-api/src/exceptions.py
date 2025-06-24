"""
カスタム例外クラス定義

MBTI診断アプリケーション用のカスタム例外を定義し、
適切なエラーハンドリングとログ記録を可能にします。
"""

import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class MBTIApplicationError(Exception):
    """MBTIアプリケーションの基底例外クラス"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.details = details or {}
        super().__init__(self.message)

    def log_error(self, logger_instance: Optional[logging.Logger] = None):
        """エラーログを出力"""
        log = logger_instance or logger
        log.error(
            f"{self.__class__.__name__}: {self.message}",
            extra={"details": self.details},
        )


class DatabaseError(MBTIApplicationError):
    """データベース関連エラーの基底クラス"""

    pass


class ConnectionError(DatabaseError):
    """データベース接続エラー"""

    pass


class QueryError(DatabaseError):
    """SQLクエリ実行エラー"""

    pass


class DataIntegrityError(DatabaseError):
    """データ整合性エラー"""

    pass


class WorkflowError(MBTIApplicationError):
    """ワークフロー実行エラーの基底クラス"""

    pass


class LLMError(WorkflowError):
    """LLM呼び出しエラー"""

    pass


class LLMRateLimitError(LLMError):
    """LLMレート制限エラー"""

    pass


class LLMTimeoutError(LLMError):
    """LLMタイムアウトエラー"""

    pass


class BusinessLogicError(MBTIApplicationError):
    """ビジネスロジックエラーの基底クラス"""

    pass


class SessionError(BusinessLogicError):
    """セッション関連エラー"""

    pass


class SessionNotFoundError(SessionError):
    """セッションが見つからないエラー"""

    pass


class SessionStateError(SessionError):
    """セッション状態エラー"""

    pass


class AssessmentError(BusinessLogicError):
    """MBTI診断関連エラー"""

    pass


class QuestionGenerationError(AssessmentError):
    """質問生成エラー"""

    pass


class InvalidResponseError(AssessmentError):
    """無効な回答エラー"""

    pass


class AssessmentIncompleteError(AssessmentError):
    """診断未完了エラー"""

    pass


class ValidationError(MBTIApplicationError):
    """バリデーションエラー"""

    pass


class InvalidInputError(ValidationError):
    """無効な入力エラー"""

    pass


class AuthenticationError(MBTIApplicationError):
    """認証エラー"""

    pass


class AuthorizationError(MBTIApplicationError):
    """認可エラー"""

    pass


# エラーレスポンス用のユーティリティ関数
def create_error_response(
    error: MBTIApplicationError, status: str = "error"
) -> Dict[str, Any]:
    """カスタム例外からエラーレスポンスを生成"""
    return {
        "status": status,
        "message": error.message,
        "error_type": error.__class__.__name__,
        "details": error.details,
    }
