import openfoodfacts

def search_market_product(keyword):
    print(f"🌐 公式SDKを使って「{keyword}」を検索中...")
    
    # 公式APIクライアントの初期化
    api = openfoodfacts.API(
        user_agent="FitnessMacroApp/1.0 (contact: your_email@example.com)",
        country="jp"
    )
    
    try:
        # 仕様に合わせ、エラーの原因だった fields 引数を削除して検索します
        search_result = api.product.text_search(
            keyword,
            page_size=3
        )
        
        products = search_result.get("products", [])
        
        if not products:
            print(f"❌ 「{keyword}」に一致する市販品は見つかりませんでした。")
            return
            
        print(f"\n🔎 「{keyword}」の検索結果:")
        print("=" * 60)
        for product in products:
            name = product.get("product_name", "商品名不明")
            nutriments = product.get("nutriments", {})
            
            # 100gまたは100mlあたりのPFC・カロリーを抽出
            kcal = nutriments.get("energy-kcal_100g", 0)
            p = nutriments.get("proteins_100g", 0)
            f = nutriments.get("fat_100g", 0)
            c = nutriments.get("carbohydrates_100g", 0)
            
            print(f"📦 商品名: {name}")
            print(f" └ カロリー: {kcal}kcal | P: {p}g | F: {f}g | C: {c}g (100g/mlあたり)")
            print("-" * 60)
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# テスト実行
search_market_product("明治おいしい牛乳")