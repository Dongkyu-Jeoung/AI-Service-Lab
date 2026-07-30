// TickerSelector.jsx — 좌측 패널: 종목 선택 + 예측 실행 버튼
export default function TickerSelector({ supportedTickers, trainedTickers, selectedTicker, onSelect, onPredict, loading }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-bold text-slate-900">종목 선택</h2>

      <div className="flex flex-col gap-2">
        {supportedTickers.map((ticker) => {
          const isTrained = trainedTickers.includes(ticker);
          const isSelected = ticker === selectedTicker;
          return (
            <button
              key={ticker}
              type="button"
              disabled={!isTrained}
              onClick={() => onSelect(ticker)}
              className={[
                "flex items-center justify-between rounded-xl border px-4 py-3 text-left text-sm font-semibold transition",
                isSelected
                  ? "border-indigo-600 bg-indigo-50 text-indigo-700"
                  : "border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100",
                !isTrained && "cursor-not-allowed opacity-40",
              ].join(" ")}
            >
              <span>{ticker}</span>
              {!isTrained && <span className="text-xs font-normal text-slate-400">미학습</span>}
            </button>
          );
        })}
      </div>

      <button
        type="button"
        onClick={onPredict}
        disabled={loading || !trainedTickers.includes(selectedTicker)}
        className="mt-6 w-full rounded-xl bg-indigo-600 px-4 py-3 text-sm font-bold text-white transition hover:bg-indigo-700 disabled:cursor-not-allowed disabled:bg-indigo-300"
      >
        {loading ? "예측 실행 중..." : "예측 실행"}
      </button>

      <p className="mt-3 text-xs leading-relaxed text-slate-400">
        "미학습" 종목은 아직 모델이 학습되지 않았습니다. <code className="rounded bg-slate-100 px-1">ai-model/src/train.py --ticker &lt;종목&gt;</code>
        을 실행해 학습하세요.
      </p>
    </section>
  );
}
