import sqlite3

def search_food(keyword):
    # データベースに接続
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    # あいまい検索（LIKE句）を使って、名前にキーワードが含まれる食品を検索
    # 例: 「%鶏むね%」とすることで、前後に文字があってもヒットします
    query = "SELECT name, calories, protein, fat, carbohydrates FROM foods WHERE name LIKE ?"
    cursor.execute(query, (f"%{keyword}%",))
    
    results = cursor.fetchall()
    conn.close()
    
    # 検索結果を綺麗に表示
    if not results:
        print(f"❌ 「{keyword}」に一致する食品は見つかりませんでした。")
        return
        
    print(f"🔎 「{keyword}」の検索結果（上位5件）:")
    print("-" * 60)
    for row in results[:5]:
        print(f"食品名: {row[0]}")
        print(f" └ カロリー: {row[1]}kcal | P: {row[2]}g | F: {row[3]}g | C: {row[4]}g")
        print("-" * 60)

# テストしたい検索キーワードを入れてみてください
search_food("むね")
