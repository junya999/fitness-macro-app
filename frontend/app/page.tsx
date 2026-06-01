"use client";
import { useState, useEffect } from "react";

// 食事データと日次集計の型定義
interface MealLog {
  id: number; food_name: string; weight_g: number; calories: number;
  protein: number; fat: number; carbs: number; eaten_time?: string;
  base_nutrients?: { calories: number; protein: number; fat: number; carbs: number };
}
interface DailySummary {
  date: string; meals: MealLog[];
  total: { calories: number; protein: number; fat: number; carbs: number };
}

export default function Home() {
  const target = { kcal: 2000, p: 150, f: 60, c: 215 };
  
  // 各種状態管理（カレンダー日付、取得データ、新規登録用、編集用ポップアップなど）
  const [selectedDate, setSelectedDate] = useState("2026-06-01");
  const [summary, setSummary] = useState<DailySummary>({ date: selectedDate, total: { calories: 0, protein: 0, fat: 0, carbs: 0 }, meals: [] });
  const [isOpen, setIsOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false); // 分量修正ポップアップの開閉
  const [keyword, setKeyword] = useState("");
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [selectedFood, setSelectedFood] = useState<any | null>(null);
  const [editingMeal, setEditingMeal] = useState<MealLog | null>(null); // 現在修正中の食事データ
  const [weight, setWeight] = useState("100");
  const [editWeight, setEditWeight] = useState("100"); // 修正後のグラム数
  const [activeHour, setActiveHour] = useState("12");

  // 今日の一覧と合計データをバックエンドから取得
  const fetchSummary = () => {
    fetch(`http://localhost:8000/summary?date=${selectedDate}`)
      .then(res => res.json())
      .then(data => setSummary(data))
      .catch(err => console.error(err));
  };

  useEffect(() => {
    fetchSummary();
  }, [selectedDate]);

  // 食品キーワード検索
  const handleSearch = () => {
    if (!keyword) return;
    fetch(`http://localhost:8000/search?keyword=${encodeURIComponent(keyword)}`)
      .then(res => res.json())
      .then(data => setSearchResults(data.results || []))
      .catch(err => console.error(err));
  };

  // 新規食事登録
  const handleLogMeal = () => {
    if (!selectedFood) return;
    const timeStr = `${activeHour.padStart(2, "0")}:00`;
    fetch("http://localhost:8000/meals", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        food_name: selectedFood.name, calories: selectedFood.calories,
        protein: selectedFood.protein, fat: selectedFood.fat, carbs: selectedFood.carbs,
        weight_g: parseFloat(weight), eaten_date: `${selectedDate} ${timeStr}`
      })
    }).then(res => res.json()).then(() => {
      fetchSummary(); setIsOpen(false); setKeyword(""); setSearchResults([]); setSelectedFood(null);
    }).catch(err => console.error(err));
  };

  // 機能説明: 食事の削除APIを叩き、成功したらダッシュボードを即座に再取得
  const handleDeleteMeal = (mealId: number) => {
    fetch(`http://localhost:8000/meals/${mealId}`, { method: "DELETE" })
      .then(res => res.json())
      .then(() => fetchSummary())
      .catch(err => console.error(err));
  };

  // 機能説明: 食事の分量変更（上書き修正）APIを叩き、成功したらダッシュボードを即座に再取得
  const handleUpdateMeal = () => {
    if (!editingMeal) return;
    fetch(`http://localhost:8000/meals/${editingMeal.id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ weight_g: parseFloat(editWeight) })
    }).then(res => res.json()).then(() => {
      fetchSummary(); setIsEditOpen(false); setEditingMeal(null);
    }).catch(err => console.error(err));
  };

  const openLogModal = (hour: number) => {
    setActiveHour(String(hour));
    setIsOpen(true);
  };

  // 編集ポップアップを起動する
  const openEditModal = (meal: MealLog) => {
    setEditingMeal(meal);
    setEditWeight(String(meal.weight_g));
    setIsEditOpen(true);
  };

  const current = summary.total;
  const pct = Math.min((current.calories / target.kcal) * 100, 100);
  const hours = Array.from({ length: 24 }, (_, i) => i);

    return (
    // 機能説明: md:max-w-5xl でPC時は横幅を広げ、左右2列のレスポンシブ配置にします
    <main className="min-h-screen p-4 md:p-8 max-w-md md:max-w-5xl mx-auto bg-[#0d0d12] text-neutral-100 font-sans relative">
      
      {/* カレンダー日付選択ヘッダー */}
      <header className="flex justify-between items-center mb-6 md:mb-8">
        <div>
          <h1 className="text-xl md:text-2xl font-bold tracking-tight">食事管理ダッシュボード</h1>
          <input 
            type="date" 
            value={selectedDate} 
            onChange={(e) => setSelectedDate(e.target.value)}
            className="mt-2 bg-neutral-900 border border-neutral-800 rounded-xl px-3 py-1.5 md:px-4 md:py-2 text-xs font-bold text-orange-400 focus:outline-none focus:border-orange-500 cursor-pointer"
          />
        </div>
        <div className="w-10 h-10 rounded-full bg-orange-500 flex items-center justify-center font-bold text-base shadow-lg">J</div>
      </header>

      {/* レスポンシブ2列レイアウト */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-start">
        
        {/* ─── 左カラム：ダッシュボードサマリー ─── */}
        <div className="space-y-6">
          {/* 当日の総摂取カロリーメーター */}
          <div className="bg-neutral-900 rounded-3xl p-6 border border-neutral-800 shadow-xl text-center">
            <span className="text-5xl md:text-6xl font-black text-white tracking-tight">{current.calories}</span>
            <span className="text-sm md:text-base text-neutral-400 font-medium"> / {target.kcal} kcal</span>
            <div className="w-full bg-neutral-800 h-2.5 rounded-full mt-4 overflow-hidden">
              <div className="bg-orange-500 h-full rounded-full transition-all duration-500" style={{ width: `${pct}%` }}></div>
            </div>
          </div>

          {/* PFCバランスの進捗バー */}
          <div className="bg-neutral-900 rounded-3xl p-6 border border-neutral-800 shadow-xl space-y-5 text-xs md:text-sm">
            <h2 className="text-sm md:text-base font-bold text-neutral-300 mb-2">PFCバランス</h2>
            {[
              [ "Protein（たんぱく質）", current.protein, target.p, "bg-orange-400", "text-orange-400" ],
              [ "Fat（脂質）", current.fat, target.f, "bg-yellow-400", "text-yellow-400" ],
              [ "Carbs（炭水化物）", current.carbs, target.c, "bg-cyan-400", "text-cyan-400" ]
            ].map(([k, c, t, col, textCol]: any) => (
              <div key={k}>
                <div className="flex justify-between mb-1.5"><span className={`font-bold ${textCol}`}>{k}</span><span className="text-neutral-400 font-medium">{c}g / {t}g</span></div>
                <div className="w-full bg-neutral-800 h-2 md:h-2.5 rounded-full overflow-hidden"><div className={`${col} h-full`} style={{ width: `${(c/t)*100}%` }}></div></div>
              </div>
            ))}
          </div>
        </div>

        {/* ─── 右カラム：24時間タイムライン（PC版で自動ワイド化） ─── */}
        <div className="bg-neutral-900 rounded-3xl p-6 border border-neutral-800 shadow-xl text-xs md:text-sm w-full">
          <h2 className="text-sm md:text-base font-bold text-neutral-300 mb-4">24時間食事タイムライン</h2>
          <div className="space-y-4 max-h-[400px] md:max-h-[550px] overflow-y-auto pr-1">
            {hours.map((hour) => {
              const hourMeals = summary.meals.filter(m => {
                if (!m.eaten_time) return false;
                return parseInt(m.eaten_time.split(":")) === hour;
              });

              return (
                <div key={hour} className="flex gap-3 md:gap-4 items-center min-h-[46px] border-b border-neutral-800/40 pb-2.5 last:border-0">
                  <div className="w-10 md:w-12 text-neutral-500 font-bold text-right tabular-nums text-[11px] md:text-xs">
                    {String(hour).padStart(2, "0")}:00
                  </div>

                  <div className="flex-1 bg-neutral-950/50 rounded-xl p-2 md:p-3 min-h-[40px] flex flex-col justify-center border border-neutral-800/20 shadow-inner">
                    {hourMeals.length === 0 ? (
                      <span className="text-[11px] md:text-xs text-neutral-600 italic pl-1">食事なし</span>
                    ) : (
                      <div className="space-y-2">
                        {hourMeals.map((m, i) => (
                          <div key={i} className="flex justify-between items-center bg-neutral-900/90 px-2.5 py-1.5 rounded-xl border border-neutral-800 shadow-sm">
                            <div onClick={() => openEditModal(m)} className="cursor-pointer flex-1 mr-2 group">
                              <p className="font-bold text-neutral-100 text-[11px] md:text-xs group-hover:text-orange-400 transition-colors">{m.food_name} <span className="text-[10px] text-neutral-500 font-normal">📝修正</span></p>
                              <p className="text-[10px] md:text-[11px] text-neutral-400 mt-0.5 font-medium">{m.weight_g}g | P:{m.protein} F:{m.fat} C:{m.carbs}</p>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="font-black text-orange-400 text-[11px] md:text-xs">{m.calories} kcal</span>
                              <button onClick={() => handleDeleteMeal(m.id)} className="text-neutral-500 hover:text-red-400 transition-colors text-xs md:text-sm p-1">🗑️</button>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>

                  <button onClick={() => openLogModal(hour)} className="w-8 h-8 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-200 hover:text-white flex items-center justify-center text-base font-bold transition-all shadow-md active:scale-95">＋</button>
                </div>
              );
            })}
          </div>
        </div>

      </div>

      {/* ① 新規追加ポップアップ */}
      {isOpen && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-6 w-full max-w-sm max-h-[85vh] overflow-y-auto shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-white text-base">{activeHour.padStart(2, "0")}:00 の食事を記録</h3>
              <button onClick={() => setIsOpen(false)} className="text-neutral-400 text-sm hover:text-white">✕ 閉じる</button>
            </div>
            <div className="flex gap-2 mb-4">
              <input type="text" placeholder="食品名を入力..." value={keyword} onChange={e => setKeyword(e.target.value)} className="flex-1 bg-neutral-800 border border-neutral-700 rounded-xl px-3 py-2 text-sm text-white focus:outline-none focus:border-orange-500" />
              <button onClick={handleSearch} className="bg-orange-500 text-white font-bold text-sm px-4 py-2 rounded-xl">検索</button>
            </div>
            {searchResults.length > 0 && (
              <div className="space-y-2 mb-4 max-h-40 overflow-y-auto border-b border-neutral-800 pb-4">
                {searchResults.map((f, i) => (
                  <button key={i} onClick={() => setSelectedFood(f)} className={`w-full text-left p-3 rounded-xl border text-xs ${selectedFood?.name === f.name ? 'bg-orange-500/10 border-orange-500 text-white' : 'bg-neutral-800/50 border-neutral-800 text-neutral-300'}`}>
                    <div className="font-bold line-clamp-1">{f.name}</div>
                    <div className="text-neutral-400 text-[10px] mt-0.5">100g: {f.calories}kcal | P:{f.protein}g F:{f.fat}g C:{f.carbs}g</div>
                  </button>
                ))}
              </div>
            )}
            {selectedFood && (
              <div className="space-y-4 pt-2 border-t border-neutral-800 text-sm">
                <div>
                  <label className="font-bold text-neutral-400 block mb-1">分量（g）</label>
                  <input type="number" value={weight} onChange={e => setWeight(e.target.value)} className="w-full bg-neutral-800 border border-neutral-700 rounded-xl px-3 py-2 text-white focus:outline-none" />
                </div>
                <button onClick={handleLogMeal} className="w-full bg-orange-500 text-white font-bold py-3 rounded-xl text-sm">タイムラインに追加</button>
              </div>
            )}
          </div>
        </div>
      )}

      {/* ② 機能説明: 食事をタップした時に起動する分量の上書き修正用ポップアップ */}
      {isEditOpen && editingMeal && (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
          <div className="bg-neutral-900 border border-neutral-800 rounded-3xl p-6 w-full max-w-sm shadow-2xl">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-bold text-white text-base">分量を修正</h3>
              <button onClick={() => setIsEditOpen(false)} className="text-neutral-400 text-sm hover:text-white">✕ 閉じる</button>
            </div>
            <p className="text-xs font-bold text-orange-400 mb-4">{editingMeal.food_name}</p>
            <div className="space-y-4 text-sm">
              <div>
                <label className="font-bold text-neutral-400 block mb-1">新しい分量（g）</label>
                <input 
                  type="number" 
                  value={editWeight} 
                  onChange={e => setEditWeight(e.target.value)} 
                  className="w-full bg-neutral-800 border border-neutral-700 rounded-xl px-3 py-2 text-white focus:outline-none focus:border-orange-500" 
                />
              </div>
              <button onClick={handleUpdateMeal} className="w-full bg-orange-500 text-white font-bold py-3 rounded-xl text-sm hover:bg-orange-600 transition-colors">
                変更を確定する
              </button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}