// PredictionHistory.jsx — 이번 브라우저 세션에서 실행한 예측 기록
// 별도 DB 없이 브라우저 localStorage에만 저장한다(교육용 프로젝트의 단순화).
export default function PredictionHistory({ history, onClear }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-bold text-slate-900">Prediction History</h2>
        {history.length > 0 && (
          <button type="button" onClick={onClear} className="text-xs font-medium text-slate-400 hover:text-slate-600">
            기록 지우기
          </button>
        )}
      </div>

      {history.length === 0 ? (
        <p className="text-sm text-slate-400">아직 실행한 예측이 없습니다.</p>
      ) : (
        <ul className="flex flex-col gap-2">
          {history.map((item, index) => {
            const isUp = item.predicted_change >= 0;
            return (
              <li
                key={index}
                className="flex items-center justify-between rounded-xl border border-slate-100 bg-slate-50 px-4 py-2.5 text-sm"
              >
                <div>
                  <span className="font-bold text-slate-900">{item.ticker}</span>
                  <span className="ml-2 text-xs text-slate-400">{item.requestedAt}</span>
                </div>
                <div className="text-right">
                  <span className="font-medium text-slate-700">${item.predicted_price.toFixed(2)}</span>
                  <span className={`ml-2 text-xs font-semibold ${isUp ? "text-emerald-600" : "text-rose-600"}`}>
                    {isUp ? "▲" : "▼"} {Math.abs(item.predicted_change_percent).toFixed(2)}%
                  </span>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
