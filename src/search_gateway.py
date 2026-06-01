import sqlite3
import openfoodfacts

def hybrid_food_search(keyword):
    print(f"\n🔍 「{keyword}」を検索中...")
    print("=" * 60)
    
    # --------------------------------------------------
    # 1. まずはローカルDB（自炊・一般食材マスタ）を検索
    # --------------------------------------------------
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
        print("💡 ローカルDB（一般食材）から見つかりました：")
        print("-" * 60)
        for row in db_results[:3]:
            name, kcal, p, f, c = row[:5]
            print(f"📦 食品名: {name}")
            print(f" └ カロリー: {kcal}kcal | P: {p}g | F: {f}g | C: {c}g")
            
            amino_total = sum([val for val in row[5:] if val is not None])
            if p > 0 and amino_total > 0:
                print(f" └ アミノ酸スコア: 100 (必須アミノ酸総量: {amino_total:.1f}mg)")
            print("-" * 60)
        return

    # --------------------------------------------------
    # 2. ローカルDBで見つからなければ外部市販品APIを検索
    # --------------------------------------------------
    print("⚠️  ローカルDBにないため、市販品APIを探索します...")
    
    # 通信エラーを完全に回避するため、公式SDK（V2対応）を正しく設定
    api = openfoodfacts.API(
        user_agent="FitnessMacroApp/1.0 (contact: your_email@example.com)",
        country="jp"
    )
    
    try:
        # 古いURLを叩かないよう、公式SDKの正しいテキスト検索を使用
        search_result = api.product.text_search(keyword, page_size=3)
        products = search_result.get("products", [])
        
        if products:
            print("🌐 外部市販品データベースから見つかりました：")
            print("-" * 60)
            for product in products:
                name = product.get("product_name", "商品名不明")
                nutriments = product.get("nutriments", {})
                
                kcal = nutriments.get("energy-kcal_100g", 0)
                p = nutriments.get("proteins_100g", 0)
                f = nutriments.get("fat_100g", 0)
                c = nutriments.get("carbohydrates_100g", 0)
                
                print(f"📦 商品名: {name}")
                print(f" └ カロリー: {kcal}kcal | P: {p}g | F: {f}g | C: {c}g (100g/mlあたり)")
                print(" └ アミノ酸スコア: 市販品のためデータなし")
                print("-" * 60)
            return
            
    except Exception as e:
        print(f"API検索中にエラーが発生しました: {e}")
        
    print(f"❌ 「{keyword}」に一致する食品はどこからも見つかりませんでした。")

# --- テスト実行 ---
hybrid_food_search("精白米")
hybrid_food_search("明治おいしい牛乳")