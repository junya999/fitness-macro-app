import os
import sqlite3
import urllib.request
import json
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
    
    # ⭕️ 文科省データに準拠した、自炊・基本食材用の標準データベース
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS foods (
        id INTEGER PRIMARY KEY,
        name TEXT, calories REAL, protein REAL, fat REAL, carbs REAL
    )""")
    cursor.execute("SELECT COUNT(*) FROM foods")
    if cursor.fetchone()[0] == 0:
        gov_sample_foods = [
            ("白米/精白米(文科省標準)", 156.0, 2.5, 0.3, 37.1),
            ("玄米(文科省標準)", 152.0, 2.8, 1.0, 34.2),
            ("鶏むね肉/皮なし(文科省標準)", 108.0, 22.3, 1.5, 0.0),
            ("鶏ささみ(文科省標準)", 98.0, 23.0, 0.8, 0.0),
            ("牛もも肉/赤身(文科省標準)", 125.0, 21.3, 3.8, 0.5),
            ("豚ヒレ肉(文科省標準)", 115.0, 22.2, 1.9, 0.2),
            ("鮭/サーモン(文科省標準)", 124.0, 22.3, 4.1, 0.1),
            ("卵/生(文科省標準)", 142.0, 12.3, 10.3, 0.3),
            ("バナナ/生(文科省標準)", 93.0, 1.1, 0.1, 22.5),
            ("アボカド/生(文科省標準)", 176.0, 2.5, 17.5, 6.2),
            ("ブロッコリー/生(文科省標準)", 37.0, 4.3, 0.4, 6.6),
            ("オートミール(文科省標準)", 350.0, 13.7, 5.7, 69.1)
        ]
        cursor.executemany("INSERT INTO foods (name, calories, protein, fat, carbs) VALUES (?, ?, ?, ?, ?)", gov_sample_foods)
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

# 1. ⭕️ 文科省データベース ＆ Open Food Facts API のハイブリッド爆速横断検索
@app.get("/search")
def search_food(keyword: str):
    results = []
    
    # 【ステップ1】文科省ベースの内部SQLiteデータベースを高速検索
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT name, calories, protein, fat, carbs FROM foods WHERE name LIKE ?", (f"%{keyword}%",))
        rows = cursor.fetchall()
        conn.close()
        for r in rows:
            results.append({"name": r[0], "calories": r[1], "protein": r[2], "fat": r[3], "carbs": r[4]})
    except Exception as e:
        print(f"SQLite検索エラー: {e}")

    # 【ステップ2】Open Food FactsのオンラインAPIを叩いて世界中の市販品・バーコードデータをリアルタイム検索
    try:
        # 日本向けの市販品データをキーワードでテキスト検索する公式エンドポイント
        url = f"https://openfoodfacts.org{urllib.parse.quote(keyword)}&search_simple=1&action=process&json=1&page_size=10"
        req = urllib.request.Request(url, headers={'User-Agent': 'FitnessMacroApp - PC - Version 1.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            data = json.loads(response.read().decode('utf-8'))
            products = data.get("products", [])
            
            for p in products:
                product_name = p.get("product_name_ja") or p.get("product_name")
                if not product_name:
                    continue
                
                # 製造会社・ブランド名があれば、分かりやすくドッキング
                brands = p.get("brands")
                if brands:
                    product_name = f"[{brands}] {product_name}"
                
                nutriments = p.get("nutriments", {})
                # Open Food Factsは基本的に「100gあたり」のデータが格納されています
                calories = nutriments.get("energy-kcal_100g") or nutriments.get("energy_100g", 0)
                protein = nutriments.get("proteins_100g", 0)
                fat = nutriments.get("fat_100g", 0)
                carbs = nutriments.get("carbohydrates_100g", 0)
                
                results.append({
                    "name": f"{product_name} (市販品)",
                    "calories": round(float(calories), 1),
                    "protein": round(float(protein), 1),
                    "fat": round(float(fat), 1),
                    "carbs": round(float(carbs), 1)
                })
    except Exception as e:
        print(f"Open Food Facts API連携エラー: {e}")

    return {"results": results}

# 2. タイムラインの一覧＆サマリー取得機能
@app.get("/summary")
def get_summary(date: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, food_name, weight_g, calories, protein, fat, carbs, strftime('%H:%M', eaten_date) FROM meals WHERE date(eaten_date) = date(?)", (date,))
    rows = cursor.fetchall()
    
    meals_list = []
    total = {"calories": 0.0, "protein": 0.0, "fat": 0.0, "carbs": 0.0}
    
    for r in rows:
        w_factor = r[2] / 100.0
        c_cal = round(r[3] * w_factor, 1)
        c_p = round(r[4] * w_factor, 1)
        c_f = round(r[5] * w_factor, 1)
        c_c = round(r[6] * w_factor, 1)
        
        meals_list.append({
            "id": r[0], "food_name": r[1], "weight_g": r[2],
            "calories": c_cal, "protein": c_p, "fat": c_f, "carbs": c_c, "eaten_time": r[7]
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
    return {"message": "世界中のデータベースと直結した理系マクロサーバーが正常稼働中です！"}