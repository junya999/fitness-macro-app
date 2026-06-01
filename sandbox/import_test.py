import pandas as pd
import sqlite3
import re

file_path = "amino_data.xlsx"

# スプレッドシートの画像を元に6行分をスキップして読み込み
df = pd.read_excel(file_path, skiprows=6, header=None)

# 正確な列番号を指定して抽出
# 1: 食品番号(B列)
# 7: イソロイシン(H), 8: ロイシン(I), 9: リシン(J), 10: メチオニン(K), 11: シスチン(L)
# 13: フェニルアラニン(N), 14: チロシン(O), 16: トレオニン(Q), 17: トリプトファン(R), 18: バリン(S), 19: ヒスチジン(T)
target_cols = [1, 7, 8, 9, 10, 11, 13, 14, 16, 17, 18, 19]
cleaned_amino = df[target_cols].copy()

# データベース用のカラム名を設定
cleaned_amino.columns = [
    "food_number", "isoleucine", "leucine", "lysine", 
    "methionine", "cystine", "phenylalanine", "tyrosine", 
    "threonine", "tryptophan", "valine", "histidine"
]

# データの掃除関数（カッコの除去、Trや-を0.0にする）
def clean_amino_value(val):
    val_str = str(val).strip()
    if val_str in ["-", "Tr", "tr", "", "0", "0.0", "nan"]:
        return 0.0
    val_str = re.sub(r"[()]", "", val_str)
    try:
        return float(val_str)
    except ValueError:
        return 0.0

# すべてのアミノ酸列に掃除を適用
amino_cols = [
    "isoleucine", "leucine", "lysine", "methionine", "cystine", 
    "phenylalanine", "tyrosine", "threonine", "tryptophan", "valine", "histidine"
]
for col in amino_cols:
    cleaned_amino[col] = cleaned_amino[col].apply(clean_amino_value)

# 食品番号（food_number）が空の行を削除
cleaned_amino = cleaned_amino.dropna(subset=["food_number"])

# 5桁の数字（01001など）が含まれる正しい行だけを残す
cleaned_amino = cleaned_amino[cleaned_amino["food_number"].astype(str).str.contains(r'^\d+')]

# 既存の app.db に「amino_acids」というテーブルで保存
conn = sqlite3.connect("app.db")
cleaned_amino.to_sql("amino_acids", conn, if_exists="replace", index=False)
conn.close()

print("🎉 アミノ酸データの掃除が完了し、'amino_acids' テーブルが正常に追加されました！")
