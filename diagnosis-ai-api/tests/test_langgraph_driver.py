"""
フェーズベースコンテキストフィルタリング機能のテスト
会話コンテキストが5問ごとに適切にリセットされることを確認
"""

import pytest
from unittest.mock import Mock, patch
from src.driver.langgraph_driver import LangGraphDriver, _filter_messages_by_phase
from src.usecase.type import ChatState, Message


class Test_フェーズコンテキストフィルタリング:
    """会話ワークフローにおけるフェーズベースコンテキストフィルタリングのテスト"""

    def setup_method(self):
        """テストフィクスチャのセットアップ"""
        self.mock_llm_port = Mock()
        self.mock_question_repo = Mock()
        self.driver = LangGraphDriver(self.mock_llm_port, self.mock_question_repo)

    def test_フェーズ1のメッセージフィルタリング(self):
        """フェーズ1（質問1-5）のメッセージフィルタリングをテスト"""
        # 準備: 8つのメッセージを作成（4つの質問＋4つの回答）
        messages = [
            {"role": "assistant", "content": "Question 1"},
            {"role": "user", "content": "Answer 1"},
            {"role": "assistant", "content": "Question 2"},
            {"role": "user", "content": "Answer 2"},
            {"role": "assistant", "content": "Question 3"},
            {"role": "user", "content": "Answer 3"},
            {"role": "assistant", "content": "Question 4"},
            {"role": "user", "content": "Answer 4"},
        ]

        # 実行: 質問3のフィルタリング（フェーズ1に属する）
        filtered = _filter_messages_by_phase(messages, 3)

        # 検証: 質問1-2とその回答を含むべき（質問3より前の質問）
        assert len(filtered) == 4  # 2つの質問＋2つの回答
        assert filtered[0]["content"] == "Question 1"
        assert filtered[1]["content"] == "Answer 1"
        assert filtered[2]["content"] == "Question 2"
        assert filtered[3]["content"] == "Answer 2"

    def test_フェーズ2のメッセージフィルタリング(self):
        """フェーズ2（質問6-10）のメッセージフィルタリングをテスト"""
        # 準備: 12のメッセージを作成（6つの質問＋6つの回答）
        messages = []
        for i in range(1, 7):
            messages.append({"role": "assistant", "content": f"Question {i}"})
            messages.append({"role": "user", "content": f"Answer {i}"})

        # 実行: 質問7のフィルタリング（フェーズ2に属する）
        filtered = _filter_messages_by_phase(messages, 7)

        # 検証: フェーズ2から質問6とその回答のみを含むべき（質問7より前のフェーズ2の質問）
        assert len(filtered) == 2  # フェーズ2から1つの質問＋1つの回答
        assert filtered[0]["content"] == "Question 6"
        assert filtered[1]["content"] == "Answer 6"

    def test_フェーズ3のメッセージフィルタリング(self):
        """フェーズ3（質問11-15）のメッセージフィルタリングをテスト"""
        # 準備: 24のメッセージを作成（12の質問＋12の回答）
        messages = []
        for i in range(1, 13):
            messages.append({"role": "assistant", "content": f"Question {i}"})
            messages.append({"role": "user", "content": f"Answer {i}"})

        # 実行: 質問13のフィルタリング（フェーズ3に属する）
        filtered = _filter_messages_by_phase(messages, 13)

        # 検証: フェーズ3から質問11-12とその回答のみを含むべき（質問13より前のフェーズ3の質問）
        assert len(filtered) == 4  # フェーズ3から2つの質問＋2つの回答
        assert filtered[0]["content"] == "Question 11"
        assert filtered[1]["content"] == "Answer 11"
        assert filtered[2]["content"] == "Question 12"
        assert filtered[3]["content"] == "Answer 12"

    def test_フェーズ4のメッセージフィルタリング(self):
        """フェーズ4（質問16-20）のメッセージフィルタリングをテスト"""
        # 準備: 34のメッセージを作成（17の質問＋17の回答）
        messages = []
        for i in range(1, 18):  # 質問18のフィルタリングをテストするために17の質問が必要
            messages.append({"role": "assistant", "content": f"Question {i}"})
            messages.append({"role": "user", "content": f"Answer {i}"})

        # 実行: 質問18のフィルタリング（フェーズ4に属する）
        filtered = _filter_messages_by_phase(messages, 18)

        # 検証: フェーズ4から質問16-17とその回答のみを含むべき（質問18より前のフェーズ4の質問）
        assert len(filtered) == 4  # フェーズ4から2つの質問＋2つの回答
        assert filtered[0]["content"] == "Question 16"
        assert filtered[1]["content"] == "Answer 16"
        assert filtered[2]["content"] == "Question 17"
        assert filtered[3]["content"] == "Answer 17"

    def test_各フェーズの最初の質問のエッジケース(self):
        """各フェーズの最初の質問のフィルタリングをテスト"""
        # 準備: 空のメッセージ（会話の開始）
        messages = []

        # 実行・検証: 各フェーズの最初の質問は空のコンテキストを持つべき
        assert _filter_messages_by_phase(messages, 1) == []  # フェーズ1開始
        assert _filter_messages_by_phase(messages, 6) == []  # フェーズ2開始
        assert _filter_messages_by_phase(messages, 11) == []  # フェーズ3開始
        assert _filter_messages_by_phase(messages, 16) == []  # フェーズ4開始

    def test_無効な質問番号でのフィルタリング(self):
        """無効な質問番号でのフィルタリングをテスト"""
        messages = [{"role": "assistant", "content": "Question 1"}]

        # 実行・検証: 無効な質問番号は空を返すべき
        assert _filter_messages_by_phase(messages, 0) == []
        assert _filter_messages_by_phase(messages, -1) == []

    @patch("src.driver.langgraph_driver.logger")
    def test_質問生成ノードがフィルタリングされたコンテキストを使用(self, mock_logger):
        """質問生成ノードがフィルタリングされたメッセージを使用することをテスト"""
        # 準備: 複数フェーズにわたるメッセージを含む状態を作成
        messages = []
        for i in range(1, 8):  # 2つのフェーズにわたる7つの質問
            messages.append(Message(role="assistant", content=f"Question {i}"))
            messages.append(Message(role="user", content=f"Answer {i}"))

        state = {
            "messages": messages,
            "next_display_order": 8,  # 質問8を投げようとしている（フェーズ2）
            "session_id": "test_session",
            "personality_element_id": 1,
            "answers": {},
        }

        self.mock_llm_port.generate_question.return_value = "Generated Question 8"
        self.mock_question_repo.save_question.return_value = "q8_id"

        # 実行: 質問生成ノードを呼び出し
        result = self.driver._generate_question_node(state)

        # 検証: LLMはフィルタリングされたコンテキストで呼び出されるべき（質問8より前のフェーズ2のメッセージのみ）
        args, kwargs = self.mock_llm_port.generate_question.call_args
        chat_history = args[0]

        # フェーズ2から質問8より前のメッセージのみを含むべき（質問6-7）
        assert "Question 6" in chat_history
        assert "Question 7" in chat_history
        assert "Question 8" not in chat_history  # 質問8は生成中
        assert "Question 1" not in chat_history  # フェーズ1から
        assert "Question 5" not in chat_history  # フェーズ1から

    @patch("src.driver.langgraph_driver.logger")
    def test_選択肢生成ノードがフィルタリングされたコンテキストを使用(
        self, mock_logger
    ):
        """選択肢生成ノードがフィルタリングされたメッセージを使用することをテスト"""
        # 準備: 3つのフェーズにわたるメッセージを含む状態を作成
        messages = []
        for i in range(1, 12):  # 3つのフェーズにわたる11の質問
            messages.append(Message(role="assistant", content=f"Question {i}"))
            messages.append(Message(role="user", content=f"Answer {i}"))

        state = {
            "messages": messages,
            "next_display_order": 12,  # 現在質問12（フェーズ3）
            "options": [],
        }

        self.mock_llm_port.generate_options.return_value = "Option A"

        # 実行: 選択肢生成ノードを呼び出し
        result = self.driver._generate_options_node(state)

        # 検証: LLMはフィルタリングされたコンテキストで呼び出されるべき（質問12より前のフェーズ3のメッセージのみ）
        # generate_optionsは3つの選択肢のために3回呼び出される
        first_call_args = self.mock_llm_port.generate_options.call_args_list[0]
        messages_text = first_call_args[0][0]

        # フェーズ3から質問12より前のメッセージのみを含むべき（質問11）
        assert "Question 11" in messages_text
        assert (
            "Question 12" not in messages_text
        )  # 質問12は生成中なのでコンテキストにない
        assert "Question 1\n" not in messages_text and messages_text.startswith(
            "assistant: Question 11"
        )  # フェーズ1から
        assert "Question 10" not in messages_text  # フェーズ2から

    def test_フェーズ計算の境界ケース(self):
        """境界の質問番号でのフェーズ計算をテスト"""
        # フェーズ1: 質問1-5
        assert ((1 - 1) // 5) + 1 == 1
        assert ((5 - 1) // 5) + 1 == 1

        # フェーズ2: 質問6-10
        assert ((6 - 1) // 5) + 1 == 2
        assert ((10 - 1) // 5) + 1 == 2

        # フェーズ3: 質問11-15
        assert ((11 - 1) // 5) + 1 == 3
        assert ((15 - 1) // 5) + 1 == 3

        # フェーズ4: 質問16-20
        assert ((16 - 1) // 5) + 1 == 4
        assert ((20 - 1) // 5) + 1 == 4

    def test_フェーズ遷移時のコンテキストリセット(self):
        """フェーズ遷移中にコンテキストが適切にリセットされることをテスト"""
        # 準備: フェーズ1からのメッセージ（質問1-5）
        phase1_messages = []
        for i in range(1, 6):
            phase1_messages.append(
                {"role": "assistant", "content": f"Phase 1 Question {i}"}
            )
            phase1_messages.append({"role": "user", "content": f"Phase 1 Answer {i}"})

        # 実行: フェーズ2の開始（質問6）用にフィルタリング
        filtered_for_phase2 = _filter_messages_by_phase(phase1_messages, 6)

        # 検証: 空であるべき（新しいフェーズのフレッシュスタート）
        assert len(filtered_for_phase2) == 0

        # 準備: フェーズ2から1つの質問を追加
        phase2_start_messages = phase1_messages + [
            {"role": "assistant", "content": "Phase 2 Question 6"},
            {"role": "user", "content": "Phase 2 Answer 6"},
        ]

        # 実行: フェーズ2の継続（質問7）用にフィルタリング
        filtered_for_phase2_continue = _filter_messages_by_phase(
            phase2_start_messages, 7
        )

        # 検証: フェーズ2のメッセージのみを含むべき
        assert len(filtered_for_phase2_continue) == 2
        assert "Phase 2 Question 6" in filtered_for_phase2_continue[0]["content"]
        assert "Phase 1" not in str(filtered_for_phase2_continue)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
