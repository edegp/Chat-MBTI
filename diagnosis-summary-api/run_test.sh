%%bash


GCS_DATA_PATH="gs://mbti_qa_data_collection/mbti_data/小川創_INTP/小川創_INTP_all_data_20250621_060100.csv"


# --- 基本設定 ---
API_URL="http://127.0.0.1:8000/generate-report-stream"


# --- テスト実行 ---
echo "🚀 APIサーバーにリクエストを送信します..."
echo "   GCS Path: ${GCS_DATA_PATH}"
echo "--------------------------------------------------"

curl -X POST \
     -N \
     -H "Content-Type: application/json" \
     -d "{\"data_path\": \"${GCS_DATA_PATH}\"}" \
     "${API_URL}" | jq .

echo "--------------------------------------------------"
echo "✅ テストが完了しました。"