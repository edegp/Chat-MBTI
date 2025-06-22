"""
フェーズベースコンテキストフィルタリング機能のテスト
会話コンテキストが5問ごとに適切にリセットされることを確認
"""

import pytest
from unittest.mock import Mock, patch
from src.driver.langgraph_driver import LangGraphDriver, _filter_messages_by_ph    def test_フェーズ計算の境界ケース(self):
        """フェーズ計算の境界ケースをテスト（10問制）"""
        # フェーズ1: 質問1-10
        assert ((1 - 1) // 10) + 1 == 1
        assert ((10 - 1) // 10) + 1 == 1

        # フェーズ2: 質問11-20
        assert ((11 - 1) // 10) + 1 == 2
        assert ((20 - 1) // 10) + 1 == 2

        # フェーズ3: 質問21-30
        assert ((21 - 1) // 10) + 1 == 3
        assert ((30 - 1) // 10) + 1 == 3

        # フェーズ4: 質問31-40
        assert ((31 - 1) // 10) + 1 == 4
        assert ((40 - 1) // 10) + 1 == 4ase.type import Message


class Test_フェーズコンテキストフィルタリング:
    """会話ワークフローにおけるフェーズベースコンテキストフィルタリングのテスト"""

    def setup_method(self):
        """テストフィクスチャのセットアップ"""
        self.mock_llm_port = Mock()
        self.mock_question_repo = Mock()
        self.mock_elements_repo = Mock()
        self.driver = LangGraphDriver(
            self.mock_llm_port, self.mock_question_repo, self.mock_elements_repo
        )

    def test_フェーズ1のメッセージフィルタリング(self):
        """フェーズ1（質問1-10）のメッセージフィルタリングをテスト"""
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

        # 検証: 質問1-3とその回答を含むべき（フェーズ1内の質問3まで）
        assert len(filtered) == 6  # 3つの質問＋3つの回答
        assert filtered[0]["content"] == "Question 1"
        assert filtered[1]["content"] == "Answer 1"
        assert filtered[2]["content"] == "Question 2"
        assert filtered[3]["content"] == "Answer 2"
        assert filtered[4]["content"] == "Question 3"
        assert filtered[5]["content"] == "Answer 3"

    def test_フェーズ2のメッセージフィルタリング(self):
        """フェーズ2（質問11-20）のメッセージフィルタリングをテスト"""
        # 準備: 24のメッセージを作成（12つの質問＋12つの回答）
        messages = []
        for i in range(
            1, 14
        ):  # 1-13の質問を作成（フェーズ1の質問1-10、フェーズ2の質問11-13）
            messages.append({"role": "assistant", "content": f"Question {i}"})
            messages.append({"role": "user", "content": f"Answer {i}"})

        # 実行: 質問13のフィルタリング（フェーズ2に属する）
        filtered = _filter_messages_by_phase(messages, 13)

        # 検証: フェーズ2から質問11-13とその回答を含むべき
        assert len(filtered) == 6  # フェーズ2の質問11-13とその回答
        assert filtered[0]["content"] == "Question 11"
        assert filtered[1]["content"] == "Answer 11"
        assert filtered[2]["content"] == "Question 12"
        assert filtered[3]["content"] == "Answer 12"
        assert filtered[4]["content"] == "Question 13"
        assert filtered[5]["content"] == "Answer 13"

    def test_フェーズ3のメッセージフィルタリング(self):
        """フェーズ3（質問21-30）のメッセージフィルタリングをテスト"""
        # 準備: 48のメッセージを作成（24の質問＋24の回答）
        messages = []
        for i in range(1, 25):  # 1-24の質問（フェーズ1,2,3の質問を含む）
            messages.append({"role": "assistant", "content": f"Question {i}"})
            messages.append({"role": "user", "content": f"Answer {i}"})

        # 実行: 質問23のフィルタリング（フェーズ3に属する）
        filtered = _filter_messages_by_phase(messages, 23)

        # 検証: フェーズ3から質問21-23とその回答を含むべき
        assert len(filtered) == 6  # フェーズ3の質問21-23とその回答
        assert filtered[0]["content"] == "Question 21"
        assert filtered[1]["content"] == "Answer 21"
        assert filtered[2]["content"] == "Question 22"
        assert filtered[3]["content"] == "Answer 22"
        assert filtered[4]["content"] == "Question 23"
        assert filtered[5]["content"] == "Answer 23"

    def test_フェーズ4のメッセージフィルタリング(self):
        """フェーズ4（質問31-40）のメッセージフィルタリングをテスト"""
        # 準備: 76のメッセージを作成（38の質問＋38の回答）
        messages = []
        for i in range(1, 39):  # 1-38の質問（フェーズ1-4の質問を含む）
            messages.append({"role": "assistant", "content": f"Question {i}"})
            messages.append({"role": "user", "content": f"Answer {i}"})

        # 実行: 質問38のフィルタリング（フェーズ4に属する）
        filtered = _filter_messages_by_phase(messages, 38)

        # 検証: フェーズ4から質問31-38とその回答を含むべき
        assert len(filtered) == 16  # フェーズ4の質問31-38とその回答
        assert filtered[0]["content"] == "Question 31"
        assert filtered[1]["content"] == "Answer 31"
        assert filtered[14]["content"] == "Question 38"
        assert filtered[15]["content"] == "Answer 38"

    def test_各フェーズの最初の質問のエッジケース(self):
        """各フェーズの最初の質問のフィルタリングをテスト"""
        # 準備: 空のメッセージ（会話の開始）
        messages = []

        # 実行・検証: 各フェーズの最初の質問は空のコンテキストを持つべき
        assert _filter_messages_by_phase(messages, 1) == []  # フェーズ1開始
        assert _filter_messages_by_phase(messages, 11) == []  # フェーズ2開始
        assert _filter_messages_by_phase(messages, 21) == []  # フェーズ3開始
        assert _filter_messages_by_phase(messages, 31) == []  # フェーズ4開始

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
        self.driver._generate_question_node(state)  # 戻り値は使用しない

        # 検証: LLMはフィルタリングされたコンテキストで呼び出されるべき（質問8より前のフェーズ1のメッセージのみ）
        args, kwargs = self.mock_llm_port.generate_question.call_args
        chat_history = args[0]

        # フェーズ1から質問8より前のメッセージを含むべき（質問1-7）
        assert "Question 1" in chat_history
        assert "Question 7" in chat_history
        assert "Question 8" not in chat_history  # 質問8は生成中

    @patch("src.driver.langgraph_driver.logger")
    def test_選択肢生成ノードがフィルタリングされたコンテキストを使用(
        self, mock_logger
    ):
        """選択肢生成ノードがフィルタリングされたメッセージを使用することをテスト"""
        # 準備: 2つのフェーズにわたるメッセージを含む状態を作成
        messages = []
        for i in range(1, 22):  # 2つのフェーズにわたる21の質問
            messages.append(Message(role="assistant", content=f"Question {i}"))
            messages.append(Message(role="user", content=f"Answer {i}"))

        state = {
            "messages": messages,
            "next_display_order": 22,  # 現在質問22（フェーズ3）
            "options": [],
        }

        self.mock_llm_port.generate_options.return_value = "Option A"

        # 実行: 選択肢生成ノードを呼び出し
        self.driver._generate_options_node(state)  # 戻り値は使用しない

        # 検証: LLMはフィルタリングされたコンテキストで呼び出されるべき（質問22より前のフェーズ3のメッセージのみ）
        # generate_optionsは3つの選択肢のために3回呼び出される
        first_call_args = self.mock_llm_port.generate_options.call_args_list[0]
        messages_text = first_call_args[0][0]

        # フェーズ3から質問22より前のメッセージのみを含むべき（質問21）
        assert "Question 21" in messages_text
        assert (
            "Question 22" not in messages_text
        )  # 質問22は生成中なのでコンテキストにない
        assert "Question 1\n" not in messages_text and messages_text.startswith(
            "assistant: Question 21"
        )  # フェーズ1から
        assert "Question 20" not in messages_text  # フェーズ2から

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
        """フェーズ遷移中にコンテキストが適切にリセットされることをテスト（10問制）"""
        # 準備: フェーズ1からのメッセージ（質問1-10）
        phase1_messages = []
        for i in range(1, 11):
            phase1_messages.append(
                {"role": "assistant", "content": f"Phase 1 Question {i}"}
            )
            phase1_messages.append({"role": "user", "content": f"Phase 1 Answer {i}"})

        # 実行: フェーズ2の開始（質問11）用にフィルタリング
        filtered_for_phase2 = _filter_messages_by_phase(phase1_messages, 11)

        # 検証: 空であるべき（新しいフェーズのフレッシュスタート）
        assert len(filtered_for_phase2) == 0

        # 準備: フェーズ2から1つの質問を追加
        phase2_start_messages = phase1_messages + [
            {"role": "assistant", "content": "Phase 2 Question 11"},
            {"role": "user", "content": "Phase 2 Answer 11"},
        ]

        # 実行: フェーズ2の継続（質問12）用にフィルタリング
        filtered_for_phase2_continue = _filter_messages_by_phase(
            phase2_start_messages, 12
        )

        # 検証: フェーズ2のメッセージのみを含むべき
        assert len(filtered_for_phase2_continue) == 2
        assert "Phase 2 Question 11" in filtered_for_phase2_continue[0]["content"]
        assert "Phase 1" not in str(filtered_for_phase2_continue)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
