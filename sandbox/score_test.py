import sqlite3

def get_amino_score(keyword):
    conn = sqlite3.connect("app.db")
    cursor = conn.cursor()
    
    # 【超重要】食品名（foods）とアミノ酸（amino_acids）を食品番号（B列の番号）で合体させるSQL
    # 文科省データの1番目の列（B列）に食品番号が入っていたため、それをキーにします
    query = """
    SELECT f.name, f.calories, f.protein, f.fat, f.carbohydrates,
           a.isoleucine, a.leucine, a.lysine, a.methionine, a.cystine,
           a.phenylalanine, a.tyrosine, a.threonine, a.tryptophan, a.valine, a.histidine
    FROM foods f
    JOIN amino_acids a ON f.rowid = a.rowid 
    WHERE f.name LIKE ?
    """
    # ※簡易的な紐付けとしてrowid（行番号）を使用してみます
    
    cursor.execute(query, (f"%{keyword}%",))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        print(f"❌ 「{keyword}」のアミノ酸データが見つかりませんでした。")
        return

    name, kcal, p, f, c = row[:5]
    print(f"🔎 食品名: {name}")
    print(f" └ カロリー: {kcal}kcal | P: {p}g | F: {f}g | C: {c}g")
    
    # たんぱく質が0の場合はスコア計算不可
    if p <= 0:
        print(" └ アミノ酸スコア: 0 (たんぱく質が含まれていません)")
        return

    # 必須アミノ酸の数値（mg）を取得
    iso, leu, lys, met, cys, phe, tyr, thr, trp, val, his = row[5:]
    
    # 含有窒素1gあたりのアミノ酸量（mg/g N）に換算して計算するのが正式ですが、
    # 簡易的にアミノ酸がしっかり入っているか（例：卵や肉なら100になるか）ロジックをテストします
    # ここでは、アミノ酸の合計値が存在するかチェックしてみましょう
    amino_total = sum([iso, leu, lys, met, cys, phe, tyr, thr, trp, val, his])
    
    # 簡易判定（卵や肉など、アミノ酸が豊富な場合はスコア100と表示するロジックのベース）
    score = 100 if amino_total > 0 else 0
    print(f" └ アミノ酸スコア: {score} (総必須アミノ酸量: {amino_total:.1f}mg)")

# テスト実行（アマランサスや、アミノ酸が豊富な食材でテスト）
get_amino_score("あわ")