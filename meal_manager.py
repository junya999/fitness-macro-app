import sqlite3
from datetime import datetime

# ① 食事をログに登録する関数
def add_meal_log(food_name, kcal_100g, p_100g, f_100g, c_100g, weight_g, date_str=None):
    if date_str is None:
        date_str = datetime.now().strftime("%Y-%m-%d")
        
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    query = """
    INSERT INTO meal_logs (food_name, calories, protein, fat, carbs, weight_g, eaten_date)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    cursor.execute(query, (food_name, kcal_100g, p_100g, f_100g, c_100g, weight_g, date_str))
    conn.commit()
    conn.close()
    print(f"✅ 食事ログを追加しました: {food_name} を {weight_g}g ({date_str})")

# ② 1日の「合計マクロ栄養素」を自動集計する関数
def calculate_daily_summary(date_str):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    query = "SELECT food_name, calories, protein, fat, carbs, weight_g FROM meal_logs WHERE eaten_date = ?"
    cursor.execute(query, (date_str,))
    logs = cursor.fetchall()
    conn.close()
    
    if not logs:
        print(f"📅 {date_str} の食事記録はまだありません。")
        return

    print(f"\n📊 {date_str} の食事タイムライン＆合計マクロ:")
    print("=" * 60)
    
    total_kcal, total_p, total_f, total_c = 0.0, 0.0, 0.0, 0.0
    
    for row in logs:
        name, kcal_100, p_100, f_100, c_100, weight = row
        ratio = weight / 100.0
        
        actual_kcal = kcal_100 * ratio
        actual_p = p_100 * ratio
        actual_f = f_100 * ratio
        actual_c = c_100 * ratio
        
        total_kcal += actual_kcal
        total_p += actual_p
        total_f += actual_f
        total_c += actual_c
        
        print(f" 🍳 {name} ({weight}g) ➔ {actual_kcal:.1f}kcal | P: {actual_p:.1f}g | F: {actual_f:.1f}g | C: {actual_c:.1f}g")
        
    print("-" * 60)
    print(f"🔥 【1日の総合計】")
    print(f" カロリー: {total_kcal:.1f} kcal")
    print(f" タンパク質 (P): {total_p:.1f} g")
    print(f" 脂質 (F): {total_f:.1f} g")
    print(f" 炭水化物 (C): {total_c:.1f} g")
    print("=" * 60)

# --- テスト実行 ---
today = datetime.now().strftime("%Y-%m-%d")

# 鶏むね肉150gと、明治おいしい牛乳200mlを食べたとしてダミー登録
add_meal_log("にわとり［若どり肉］／むね／皮なし", 105.0, 23.3, 1.9, 0.0, 150, today)
add_meal_log("明治おいしい牛乳", 68.5, 3.4, 3.9, 4.95, 200, today)

# 今日の合計をパッと計算して表示
calculate_daily_summary(today)