## 開発環境
```
brew install postgressql
uv sync
uv run python app.py
```
## Docker
```
docker build . -t diagnosis-ai-api
docker run -t diagnosis-ai-api
```