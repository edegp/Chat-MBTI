from huggingface_hub import snapshot_download

MODEL_IDS = {
    "energy": "HajimeOgawa/gemma3-4b-mbti-chat-energy",
    "mind": "HajimeOgawa/gemma3-4b-mbti-chat-mind",
    "nature": "HajimeOgawa/gemma3-4b-mbti-chat-nature",
    "tactics": "HajimeOgawa/gemma3-4b-mbti-chat-tactics",
}

BASE_DIR = "./model"  # 適宜変更

for key, repo in MODEL_IDS.items():
    local_dir = f"{BASE_DIR}/{key}"
    print(f"→ ダウンロード: {repo} → {local_dir}")
    snapshot_download(
        repo_id=repo,
        cache_dir=BASE_DIR,
        max_workers=2,
        etag_timeout=1200,
        local_dir_use_symlinks=False,
    )
print("✓ 4 モデル完了")
