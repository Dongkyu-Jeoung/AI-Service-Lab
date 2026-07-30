// PredictionSummary.jsx — 우측 상단: 현재 가격 / 예측 가격 / 예상 등락률
export default function PredictionSummary({ prediction, ticker }) {
  if (!prediction) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <p className="text-sm text-slate-400">
          왼쪽에서 종목을 고르고 "예측 실행"을 눌러보세요. ({ticker} 선택됨)
        </p>
      </section>
    );
  }

  const isUp = prediction.predicted_change >= 0;

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-bold text-slate-900">{prediction.ticker} 다음 거래일 예측</h2>
        <span className="text-xs text-slate-400">기준일: {prediction.current_date}</span>
      </div>

      <div className="mt-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-400">현재 가격</p>
          <p className="mt-1 text-2xl font-bold text-slate-900">${prediction.current_price.toFixed(2)}</p>
        </div>
        <div className="rounded-xl bg-slate-50 p-4">
          <p className="text-xs font-medium text-slate-400">예측 가격</p>
          <p className="mt-1 text-2xl font-bold text-indigo-600">${prediction.predicted_price.toFixed(2)}</p>
        </div>
        <div className={`rounded-xl p-4 ${isUp ? "bg-emerald-50" : "bg-rose-50"}`}>
          <p className="text-xs font-medium text-slate-400">예상 등락률</p>
          <p className={`mt-1 text-2xl font-bold ${isUp ? "text-emerald-600" : "text-rose-600"}`}>
            {isUp ? "▲" : "▼"} {Math.abs(prediction.predicted_change_percent).toFixed(2)}%
          </p>
          <p className={`text-xs ${isUp ? "text-emerald-600" : "text-rose-600"}`}>
            {isUp ? "+" : ""}
            {prediction.predicted_change.toFixed(2)} 달러
          </p>
        </div>
      </div>

      <p className="mt-4 rounded-lg bg-amber-50 px-3 py-2 text-xs font-medium text-amber-700">
        ⚠ {prediction.disclaimer}
      </p>
    </section>
  );
}
