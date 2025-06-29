import yaml
import re
import pandas as pd
from google.cloud import exceptions


def load_config(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)
    return config


def make_prompt(messages, element_name, element_description, label) -> str:
    prompt_template = (
        "あなたは性格診断AIです。"
        "以下のユーザーとアシスタントのメッセージのやり取りを見て、ユーザーが{element_name}のうち、どちらに属するかを判定してください。\n\n"
        "{element_description}\n\n"
        "[messages]\n"
        "{messages}"
        "出力のフォーマットは、以下のものを必ず守ってください。\n"
        "[reason]:理由1\n理由2\n理由3\n[judge]:{label}"
    )
    return prompt_template.format(
        element_name=element_name,
        element_description=element_description,
        messages=messages,
        label=label,
    )


def truncate_messages(messages: str, max_length: int) -> str:
    """ "指定した文字数以上のメッセージをユーザーの返答で終わる形で切り捨てる"""
    # no truncated
    if len(messages) <= max_length:
        return messages

    truncated = messages[:max_length]
    matches = list(re.finditer(r"ユーザー:.*$", truncated, re.MULTILINE))

    if not matches:
        return truncated

    last_match = matches[-1]
    cut_pos = last_match.end()

    return truncated[:cut_pos]


def preprocess(
    messages, element_name, element_description, label, message_max_length=2000
) -> str:
    """メッセージの履歴をLLMに渡す形式に変換"""
    # messages truncated
    messages = truncate_messages(messages, message_max_length)

    # make input
    prompt = make_prompt(messages, element_name, element_description, label)
    return prompt


def remove_special_token(response) -> str:
    """LLMのレスポンスに含まれる特殊トークンを省く"""
    output = response.replace("<bos>", "").replace("<eos>", "")
    return output


def judge_response_follow_format(text: str, true_labels: list[str]):
    """
    gemmaの出力がフォーマットに従っているか確認

      - [reason] パートと [judge] パートに分かれているか
      - ラベルが正しい値か(I or E など).

    Returns:
      (is_valid, errors):
        is_valid (bool): True if the format is correct, False otherwise.
        errors (list): A list of error messages for any violations.
    """
    errors = []
    lines = text.strip().splitlines()

    # Check the first line starts with "[reason]:"
    first_line = lines[0]
    if not first_line.startswith("[reason]:"):
        error = "最初の行が '[reason]:' で始まっていません。"
        errors.append(error)

    # Find the line that starts with "[judge]:"
    judge_line_index = None
    for idx, line in enumerate(lines):
        if line.startswith("[judge]:"):
            judge_line_index = idx
            break
    if judge_line_index is None:
        errors.append("'[judge]:' パートが見つかりません。")
    else:
        # Ensure judge is the last line
        if judge_line_index != len(lines) - 1:
            errors.append("[judge] セクションは最後の行である必要があります。")
        # Validate the label after "[judge]:"
        judge_label = lines[judge_line_index][len("[judge]:") :].strip()
        if judge_label not in true_labels:
            errors.append(
                "ラベルが正しい値ではありません。（現在の値: '{}'）".format(judge_label)
            )

    # If there were any errors, the format is invalid
    is_valid = len(errors) == 0
    return is_valid, errors


def make_report_prompt(element_name, messages, judge_and_reason) -> str:
    """レポート作成用のプロンプトを生成"""

    report_prompt_template = (
        "あなたは優秀なAIアシスタントです。"
        "性格診断AIがユーザーの会話の履歴からMBTIにおける{element_name}について診断した結果とその理由を与えるので、"
        "それらを参照して性格なレポートを生成してください。"
        "判断の理由は3つ含まれているので、{report_format}の形を取ったマークダウン形式で出力してください。"
        "[messages]\n{messages}\n\n[judge and reason]{judge_and_reason}\n"
    )

    report_format = (
        "## 1. 理由1\n\n  理由3の説明\n\n"
        "## 2. 理由2\n\n  理由2の説明\n\n"
        "## 3. 理由3\n\n  理由3の説明\n\n"
    )

    return report_prompt_template.format(
        element_name=element_name,
        report_format=report_format,
        messages=messages,
        judge_and_reason=judge_and_reason,
    )


def read_csv_from_gcs(gcs_path: str, **kwargs) -> pd.DataFrame | None:
    """
    GCS上のCSVファイルをdataframeとして読み込む
    """
    try:
        print(f"Reading CSV from: {gcs_path}")
        df = pd.read_csv(gcs_path, **kwargs)
        return df
    except exceptions.NotFound:
        print(f"Error: File not found at {gcs_path}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None


def transoform_to_chat_history_format(df):
    messages = ""
    for idx in range(len(df)):
        question = df["Question"].iloc[idx]
        ansewer = df["Answer"].iloc[idx]
        one_turn_message = f"アシスタント: {question}\nユーザー: {ansewer}\n"
        messages += one_turn_message
    return messages


def make_judge_input_list(message_df: pd.DataFrame) -> list[str]:
    """ "チャット履歴を各elementごとに分割して、判定用llmに渡す形式に変換"""

    phase_df_list = []
    for phase in range(1, 5):
        phase_df = message_df[message_df["Phase"] == phase]
        phase_df_list.append(phase_df)

    messages_list = []
    for phase_df in phase_df_list:
        messages = transoform_to_chat_history_format(phase_df)
        messages_list.append(messages)

    return messages_list
