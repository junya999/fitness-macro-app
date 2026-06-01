from fastapi import FastAPI, Query
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import sqlite3
import openfoodfacts
from datetime import datetime

app = FastAPI(
    title="食事管理アプリ API",
    description="ボディメイクに特化したPFC・カロリー・アミノ酸管理バックエンド",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

api_client = openfoodfacts.API(
    user_agent="FitnessMacroApp/1.0 (contact: your_email@example.com)",
    country="jp"
)

class MealCreate(BaseModel):
    food_name: str
    calories: float
    protein: float
    fat: float
    carbs: float
    weight_g: float
    eaten_date: str | None = None

# 機能説明: 分量変更時にフロントから受け取るデータの形
class MealUpdate(BaseModel):
    weight_g: float

@app.get("/", tags=["基本"])
def read_root():
    return {"message": "食事管理アプリのバックエンドサーバーが正常稼働中です！"}


# ─── ① ハイブリッド検索API ───
@app.get("/search", tags=["食品検索"])
def search_food(keyword: str = Query(..., description="検索したい食品名")):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    db_query = """
    SELECT f.name, f.calories, f.protein, f.fat, f.carbohydrates,
           a.isoleucine, a.leucine, a.lysine, a.methionine, a.cystine,
           a.phenylalanine, a.tyrosine, a.threonine, a.tryptophan, a.valine, a.histidine
    FROM foods f
    LEFT JOIN amino_acids a ON f.rowid = a.rowid 
    WHERE f.name LIKE ?
    """
    cursor.execute(db_query, (f"%{keyword}%",))
    db_results = cursor.fetchall()
    conn.close()
    
    if db_results:
        results = []
        for row in db_results[:5]:
            name, kcal, p, f, c = row[:5]
            amino_total = sum([val for val in row[5:] if val is not None])
            amino_score = 100 if (p > 0 and amino_total > 0) else 0
            results.append({
                "source": "local_db(一般食材)",
                "name": name, "calories": kcal, "protein": p, "fat": f, "carbs": c,
                "amino_score": amino_score
            })
        return {"keyword": keyword, "results": results}

    try:
        search_result = api_client.product.text_search(keyword, page_size=5)
        products = search_result.get("products", [])
        if products:
            results = []
            for product in products:
                name = product.get("product_name", "商品名不明")
                nutriments = product.get("nutriments", {})
                results.append({
                    "source": "open_food_facts(市販品)",
                    "name": name,
                    "calories": nutriments.get("energy-kcal_100g", 0),
                    "protein": nutriments.get("proteins_100g", 0),
                    "fat": nutriments.get("fat_100g", 0),
                    "carbs": nutriments.get("carbohydrates_100g", 0),
                    "amino_score": "市販品のためデータなし"
                })
            return {"keyword": keyword, "results": results}
    except Exception:
        pass
        
    return {"keyword": keyword, "results": [], "message": "食品が見つかりませんでした"}


# ─── ② 食事記録登録API ───
@app.post("/meals", tags=["食事ログ記録"])
def add_meal_log(meal: MealCreate):
    date_str = meal.eaten_date
    if not date_str:
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    query = """
    INSERT INTO meal_logs (food_name, calories, protein, fat, carbs, weight_g, eaten_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (meal.food_name, meal.calories, meal.protein, meal.fat, meal.carbs, meal.weight_g, date_str))
    conn.commit()
    conn.close()
    return {"status": "success", "message": f"{meal.food_name} を記録しました"}


# ─── ③ 食事記録分量変更API（新規追加） ───
@app.put("/meals/{meal_id}", tags=["食事ログ記録"])
def update_meal_log(meal_id: int, data: MealUpdate):
    """
    指定されたIDの食事記録の分量（グラム数）を上書き更新します。
    """
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE meal_logs SET weight_g = ? WHERE rowid = ?", (data.weight_g, meal_id))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "分量を更新しました"}


# ─── ④ 食事記録削除API ───
@app.delete("/meals/{meal_id}", tags=["食事ログ記録"])
def delete_meal_log(meal_id: int):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM meal_logs WHERE rowid = ?", (meal_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "message": "記録を削除しました"}


# ─── ⑤ 1日合計集計API（rowidの引き渡しに対応） ───
@app.get("/summary", tags=["食事ログ記録"])
def get_daily_summary(date: str = Query(None, description="集計したい日付 (例: YYYY-MM-DD)")):
    if not date:
        date = datetime.now().strftime("%Y-%m-%d")
        
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    query = "SELECT rowid, food_name, calories, protein, fat, carbs, weight_g, eaten_date FROM meal_logs WHERE eaten_date LIKE ?"
    cursor.execute(query, (f"{date}%",))
    logs = cursor.fetchall()
    conn.close()
    
    if not logs:
        return {"date": date, "total": {"calories": 0, "protein": 0, "fat": 0, "carbs": 0}, "meals": []}

    total_kcal, total_p, total_f, total_c = 0.0, 0.0, 0.0, 0.0
    meal_list = []
    
    for row in logs:
        meal_id, name, kcal_100, p_100, f_100, c_100, weight, raw_date = row
        ratio = weight / 100.0
        
        actual_kcal = kcal_100 * ratio
        actual_p = p_100 * ratio
        actual_f = f_100 * ratio
        actual_c = c_100 * ratio
        
        total_kcal += actual_kcal
        total_p += actual_p
        total_f += actual_f
        total_c += actual_c
        
        time_part = "12:00"
        if raw_date and " " in raw_date:
            time_part = raw_date.split(" ")[1]
        
        meal_list.append({
            "id": meal_id,
            "food_name": name, "weight_g": weight,
            "calories": round(actual_kcal, 1), "protein": round(actual_p, 1),
            "fat": round(actual_f, 1), "carbs": round(actual_c, 1),
            "eaten_time": time_part,
            "base_nutrients": {
                "calories": kcal_100, "protein": p_100, "fat": f_100, "carbs": c_100
            }
        })
        
    return {
        "date": date,
        "total": {
            "calories": round(total_kcal, 1), "protein": round(total_p, 1),
            "fat": round(total_f, 1), "carbs": round(total_c, 1)
        },
        "meals": meal_list
    }