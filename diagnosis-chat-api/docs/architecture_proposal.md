# Port & Adapter Architecture Proposal

## 現在の問題と理想的な構造

### 1. 依存関係の修正

#### 現在（問題あり）:

```
Controller → Usecase → Driver
                   ↘
                    Gateway
```

#### 理想（Port & Adapter）:

```
Controller → Application Service → Domain
               ↓                    ↓
            Outbound Port    ←   Business Logic
               ↓
        Gateway (Adapter) → Infrastructure
```

### 2. ディレクトリ構造の提案

#### **オプション 1: 標準的な Hexagonal Architecture**

```
src/
├── domain/                    # ビジネスロジック（最内層）
│   ├── entities/             # ドメインエンティティ
│   ├── value_objects/        # 値オブジェクト
│   └── services/             # ドメインサービス
├── ports/                    # インターフェース定義
│   ├── inbound/              # Primary ports (Application Service interfaces)
│   └── outbound/             # Secondary ports (Repository, LLM interfaces)
├── application/              # アプリケーションサービス
│   ├── services/             # ユースケース実装
│   └── dto/                  # データ転送オブジェクト
├── adapters/                 # アダプター層
│   ├── inbound/              # Primary adapters
│   │   ├── rest/             # REST API controllers
│   │   └── cli/              # CLI interfaces (future)
│   └── outbound/             # Secondary adapters
│       ├── persistence/      # データベースアダプター
│       ├── llm/              # LLMアダプター
│       └── auth/             # 認証アダプター
└── infrastructure/           # 外部技術の実装詳細
    ├── config/               # 設定ファイル
    ├── database/             # DB接続・マイグレーション
    └── external/             # 外部API設定
```

#### **オプション 2: DDD 風（より一般的）**

```
src/
├── domain/                   # ドメイン層
│   ├── entities/
│   ├── value_objects/
│   ├── repositories/         # Repository interfaces（ここにPort）
│   └── services/
├── application/              # アプリケーション層
│   ├── services/             # Application Services
│   ├── ports/                # Application用のPort
│   └── dto/
├── infrastructure/           # インフラ層
│   ├── persistence/          # Repository実装
│   ├── external/             # 外部サービス実装
│   └── config/
└── presentation/             # プレゼンテーション層
    ├── rest/                 # REST Controllers
    └── dto/                  # API用DTO
```

### 3. 具体的な実装例

#### Domain Port (インターフェース)

```python
# src/domain/ports/outbound/llm_port.py
from abc import ABC, abstractmethod
from typing import List

class LLMPort(ABC):
    @abstractmethod
    def generate_question(self, chat_history: str) -> str:
        pass

    @abstractmethod
    def generate_options(self, messages: str, existing_options: List[str]) -> str:
        pass
```

#### Application Service

```python
# src/application/services/mbti_service.py
from src.domain.ports.outbound.llm_port import LLMPort
from src.domain.ports.outbound.session_port import SessionPort

class MBTIService:
    def __init__(self, llm_port: LLMPort, session_port: SessionPort):
        self._llm = llm_port
        self._session = session_port

    def generate_question(self, user_id: str, messages: List[Message]) -> str:
        # ビジネスロジックのみ
        session = self._session.get_or_create_session(user_id)
        history = self._organize_history(messages)
        return self._llm.generate_question(history)
```

#### Adapter Implementation

```python
# src/adapters/outbound/llm/gemini_adapter.py
from src.domain.ports.outbound.llm_port import LLMPort

class GeminiLLMAdapter(LLMPort):
    def __init__(self, llm_client):
        self._client = llm_client

    def generate_question(self, chat_history: str) -> str:
        # Gemini固有の実装
        response = self._client.invoke(prompt)
        return response.content
```

#### Controller (Primary Adapter)

```python
# src/adapters/inbound/rest/mbti_controller.py
from src.application.services.mbti_service import MBTIService

class MBTIController:
    def __init__(self, mbti_service: MBTIService):
        self._service = mbti_service

    @router.post("/question")
    async def generate_question(self, request: QuestionRequest):
        # HTTP関連の処理のみ
        try:
            question = self._service.generate_question(
                request.user_id,
                request.messages
            )
            return {"question": question}
        except BusinessException as e:
            raise HTTPException(status_code=400, detail=str(e))
```

### 4. 依存性注入の設定

```python
# src/infrastructure/container.py
from dependency_injector import containers, providers

class Container(containers.DeclarativeContainer):
    # Infrastructure
    llm_client = providers.Singleton(ChatGoogleGenerativeAI, ...)

    # Adapters
    llm_adapter = providers.Factory(GeminiLLMAdapter, llm_client)
    session_adapter = providers.Factory(PostgresSessionAdapter, ...)

    # Services
    mbti_service = providers.Factory(
        MBTIService,
        llm_port=llm_adapter,
        session_port=session_adapter
    )

    # Controllers
    mbti_controller = providers.Factory(MBTIController, mbti_service)
```

## 命名規則について

### **一般的な Port & Adapter の命名**

私が最初に提案した「Usecase → Port → Adapter → Infrastructure」という表現は誤解を招くものでした。正確には：

#### **正しい依存関係の表現**

```
Application Service  →  Port (interface)
                           ↑ implements
                       Adapter  →  Infrastructure
```

### **業界標準の命名パターン**

1. **Port**: インターフェース（抽象）

   - `UserRepositoryPort`
   - `LLMServicePort`
   - `NotificationPort`

2. **Adapter**: Port の具体実装

   - `PostgresUserRepositoryAdapter`
   - `GeminiLLMServiceAdapter`
   - `EmailNotificationAdapter`

3. **Infrastructure**: 外部技術の設定・初期化
   - データベース接続
   - 外部 API 設定
   - 認証設定

### **よく見られる命名の違い**

| 概念             | パターン 1     | パターン 2     | パターン 3  |
| ---------------- | -------------- | -------------- | ----------- |
| インターフェース | Port           | Repository     | Gateway     |
| 実装             | Adapter        | RepositoryImpl | GatewayImpl |
| 外部技術         | Infrastructure | External       | Driver      |

### **現プロジェクトでの推奨命名**

現在のプロジェクトサイズと複雑さを考慮すると、**オプション 2（DDD 風）**が最も適していると思われます：

```
src/
├── domain/
│   ├── entities/         # Session, User, Question
│   ├── repositories/     # SessionRepository, QuestionRepository (interfaces)
│   └── services/         # MBTIDiagnosisService
├── application/
│   ├── services/         # MBTIApplicationService
│   └── dto/              # QuestionDTO, SessionDTO
├── infrastructure/
│   ├── persistence/      # PostgresSessionRepository, PostgresQuestionRepository
│   ├── llm/              # GeminiLLMService
│   └── auth/             # FirebaseAuthService
└── presentation/
    └── rest/             # MBTIController
```

## 移行のメリット

1. **テスタビリティ**: モックを使った単体テストが容易
2. **技術変更への対応**: LLM を Gemini から Claude3 に変更する際、Adapter のみ変更
3. **ビジネスロジックの保護**: 外部技術変更がドメインに影響しない
4. **明確な責任分離**: 各層の役割が明確
5. **スケーラビリティ**: 新機能追加時の影響範囲が限定的

## 移行の段階的アプローチ

1. **Phase 1**: Port インターフェースの定義
2. **Phase 2**: Application Service の作成
3. **Phase 3**: Adapter の実装
4. **Phase 4**: 依存性注入の導入
5. **Phase 5**: 既存コードのリファクタリング

この構造により、ビジネスロジックが技術詳細から完全に独立し、保守性とテスタビリティが大幅に向上します。

## 命名パターンの比較

### **現在のプロジェクトの命名（妥当性高い）**

現在使用されている `controller/gateway/driver/usecase` の命名は、特に以下の文脈で**非常に適切**です：

#### **現在の命名の妥当性**

- **Controller**: API 層として明確
- **Gateway**: 外部サービスへのアダプターとして直感的
- **Driver**: 外部技術の実装として適切
- **Usecase**: ビジネスロジックとして理解しやすい

#### **業界での使用例**

- **Netflix**: Gateway pattern for microservices
- **Amazon**: API Gateway service
- **Spring Cloud**: Gateway routing
- **Kubernetes**: Gateway controllers

### **命名パターンの選択指針**

| パターン                                       | 適用場面                   | メリット         |
| ---------------------------------------------- | -------------------------- | ---------------- |
| **Current (controller/gateway/driver)**        | API 中心、マイクロサービス | 直感的、役割明確 |
| **DDD 風 (domain/application/infrastructure)** | ドメイン駆動設計           | 理論的に正確     |
| **Clean Architecture 風**                      | 教科書的実装               | 学習しやすい     |
| **Spring Boot 風 (service/repository)**        | Java 系開発者              | 馴染みやすい     |

### **現在のプロジェクトでの推奨アプローチ**

現在の命名を**そのまま活用**して、依存関係のみ修正することを提案します：

```
src/
├── controller/          # API endpoints (現在の命名維持)
├── usecase/             # Business logic (現在の命名維持)
├── gateway/             # Adapters (現在の命名維持)
└── driver/              # External implementations (現在の命名維持)
```

#### **修正が必要なのは依存関係のみ**

**現在（問題）:**

```python
# usecase/graph.py
from ...driver.model import llm  # 直接依存
```

**修正後（理想）:**

```python
# usecase/graph.py
from ..gateway.llm_gateway import LLMGateway  # Gateway経由

# gateway/llm_gateway.py
from abc import ABC, abstractmethod

class LLMGateway(ABC):
    @abstractmethod
    def generate_question(self, prompt: str) -> str: pass

# gateway/gemini_llm_gateway.py
from ..driver.model import llm

class GeminiLLMGateway(LLMGateway):
    def generate_question(self, prompt: str) -> str:
        return llm.invoke(prompt).content
```
