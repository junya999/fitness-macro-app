import os
import shutil

# 1. 必要なフォルダ（部屋）を作成
os.makedirs("src", exist_ok=True)
os.makedirs("sandbox", exist_ok=True)

# 2. 本番用・これからも使うコアスクリプトを「src」に移動
core_files = ["search_gateway.py"]
for f in core_files:
    if os.path.exists(f):
        shutil.move(f, f"src/{f}")

# 3. 実験し終わったテストスクリプトを「sandbox」に移動
test_files = [
    "api_test.py", "create_amino_db.py", "create_db.py", 
    "import_test.py", "score_test.py", "search_test.py"
]
for f in test_files:
    if os.path.exists(f):
        shutil.move(f, f"sandbox/{f}")

print("📁 フォルダの整理が完了しました！コア機能は 'src'、実験用は 'sandbox' に入っています。")