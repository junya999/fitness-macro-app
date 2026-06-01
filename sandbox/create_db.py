import pandas as pd
import sqlite3
import re

# 1. データの読み込み
file_path = "food_data.xlsx"
df = pd.read_excel(file_path, skiprows=12, header=None)
cleaned_df = df[[3, 6, 9, 12, 22]].copy()
cleaned_df.columns = ["name", "calories", "protein", "fat", "carbohydrates"]

# 2. データを綺麗に掃除する関数（カッコの除去、Trや-を0にする）
def clean_value(val):
    val_str = str(val).strip()
    if val_str in ["-", "Tr", "tr", ""]:
        return 0.0
    # カッコ（例: "(2.9)"）があれば中身の数字だけを抜き出す
    val_str = re.sub(r"[()]", "", val_str)
    try:
        return float(val_str)
    except ValueError:
        return 0.0

# 各栄養素の列に掃除関数を適用
for col in ["calories", "protein", "fat", "carbohydrates"]:
    cleaned_df[col] = cleaned_df[col].apply(clean_value)

# 食品名が空っぽの行（ゴミデータ）を削除
cleaned_df = cleaned_df.dropna(subset=["name"])

# 3. データベース（SQLite）へ一括保存
# プロジェクトフォルダ内に「app.db」というデータベースファイルが自動作成されます
conn = sqlite3.connect("app.db")
cleaned_df.to_sql("foods", conn, if_exists="replace", index=False)
conn.close()

print("🎉 データの掃除が完了し、app.db の 'foods' テーブルに保存されました！")