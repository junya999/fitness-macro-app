import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()

# 食事ログを保存するテーブル（部屋）を作成
cursor.execute("""
CREATE TABLE IF NOT EXISTS meal_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    food_name TEXT NOT NULL,
    calories REAL,
    protein REAL,
    fat REAL,
    carbs REAL,
    weight_g REAL NOT NULL,
    eaten_date TEXT NOT NULL
)
""")

conn.commit()
conn.close()

print("🎉 app.db に 'meal_logs'（食事ログ用の部屋）が正常に作成されました！")