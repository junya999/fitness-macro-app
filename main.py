import os
import sqlite3
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS meals (
        id INTEGER PRIMARY KEY,
        food_name TEXT, calories REAL, protein REAL, fat REAL, carbs REAL,
        weight_g REAL, eaten_date TEXT
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY,
        name TEXT, calories REAL, protein REAL, fat REAL, carbs REAL
    )""")
    cursor.execute("SELECT COUNT(*) FROM foods")
    if cursor.fetchone()[0] == 0:
        sample_foods = [
            ("鶏むね肉", 108.0, 22.3, 1.5, 0.0),
            ("サラダチキン", 110.0, 24.0, 1.0, 1.0),
            ("おいしい牛乳", 69.0, 3.4, 3.8, 4.8),
            ("白米", 156.0, 2.5, 0.3, 37.1)
        ]
        cursor.executemany("INSERT INTO foods (name, calories, protein, fat, carbs) VALUES (?, ?, ?, ?, ?)", sample_foods)
        conn.commit()
    conn.close()

init_db()

class MealCreate(BaseModel):
    food_name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    weight_g: float
    eaten_date: str

# 1. 食品のキーワード検索機能（⭕️ 絶対にシステムバグで消えない構造に修復）
@app.get("/search")
def search_food(keyword: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name, calories, protein, fat, carbs FROM foods WHERE name LIKE ?", (f"%{keyword}%",))
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append({
            "name": row[0],
            "calories": row[1],
            "protein": row[2],
            "fat": row[3],
            "carbs": row[4]
        })
    return {"results": results}

# 2. タイムラインの一覧＆サマリー取得機能（⭕️ こちらもデータ構造を完全修復）
@app.get("/summary")
def get_summary(date: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, food_name, weight_g, calories, protein, fat, carbs, strftime('%H:%M', eaten_date) FROM meals WHERE date(eaten_date) = date(?)", (date,))
    rows = cursor.fetchall()
    
    meals_list = []
    total = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    
    for row in rows:
        w_factor = row[2] / 100.0
        c_cal = round(row[3] * w_factor, 1)
        c_p = round(row[4] * w_factor, 1)
        c_f = round(row[5] * w_factor, 1)
        c_c = round(row[6] * w_factor, 1)
        
        meals_list.append({
            "id": row[0], "food_name": row[1], "weight_g": row[2],
            "calories": c_cal, "protein": c_p, "fat": c_f, "carbs": c_c, "eaten_time": row[7]
        })
        total["calories"] += c_cal
        total["protein"] += c_p
        total["fat"] += c_f
        total["carbs"] += c_c

    conn.close()
    return {"date": date, "meals": meals_list, "total": {k: round(v, 1) for k, v in total.items()}}

# 3. 新しい食事の登録機能
@app.post("/meals")
def add_meal(meal: MealCreate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO meals (food_name, calories, protein, fat, carbs, weight_g, eaten_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)""", (meal.food_name, meal.calories, meal.protein, meal.fat, meal.carbs, meal.weight_g, meal.eaten_date))
    conn.commit()
    conn.close()
    return {"status": "success"}

class WeightUpdate(BaseModel):
    weight_g: float

# 4. 食事の分量上書き修正機能
@app.put("/meals/{meal_id}")
def update_meal(meal_id: int, data: WeightUpdate):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("UPDATE meals SET weight_g = ? WHERE id = ?", (data.weight_g, meal_id))
    conn.commit()
    conn.close()
    return {"status": "success"}

# 5. 食事の削除機能
@app.delete("/meals/{meal_id}")
def delete_meal(meal_id: int):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meals WHERE id = ?", (meal_id,))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.get("/")
def read_root():
    return {"message": "食事管理アプリのバックエンドサーバーが正常稼働中です！"}