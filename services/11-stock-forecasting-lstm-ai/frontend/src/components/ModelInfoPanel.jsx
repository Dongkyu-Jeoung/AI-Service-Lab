// ModelInfoPanel.jsx — 모델 정보(성능 지표, 학습 데이터 범위 등)
export default function ModelInfoPanel({ info }) {
  if (!info) {
    return (
      <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <h2 className="mb-4 text-lg font-bold text-slate-900">모델 정보</h2>
        <p className="text-sm text-slate-400">종목을 선택하면 모델 정보가 표시됩니다.</p>
      </section>
    );
  }

  const metricItems = [
    { label: "MAE", value: info.test_metrics.MAE, hint: "평균 절대 오차 ($)" },
    { label: "RMSE", value: info.test_metrics.RMSE, hint: "평균 제곱근 오차 ($)" },
    { label: "MAPE", value: `${info.test_metrics.MAPE}%`, hint: "평균 절대 오차율" },
    { label: "R²", value: info.test_metrics.R2, hint: "설명력 (1에 가까울수록 좋음)" },
  ];

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-bold text-slate-900">모델 정보</h2>

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        {metricItems.map((item) => (
          <div key={item.label} className="rounded-xl bg-slate-50 p-3 text-center">
            <p className="text-[11px] font-medium text-slate-400">{item.label}</p>
            <p className="mt-1 text-lg font-bold text-slate-900">{item.value}</p>
          </div>
        ))}
      </div>

      <dl className="mt-5 grid grid-cols-1 gap-2 text-xs text-slate-500 sm:grid-cols-2">
        <div className="flex justify-between border-b border-slate-100 py-1.5">
          <dt>학습 시각</dt>
          <dd className="font-medium text-slate-700">{info.trained_at}</dd>
        </div>
        <div className="flex justify-between border-b border-slate-100 py-1.5">
          <dt>Lookback</dt>
          <dd className="font-medium text-slate-700">{info.lookback}일</dd>
        </div>
        <div className="flex justify-between border-b border-slate-100 py-1.5">
          <dt>학습 데이터 기간</dt>
          <dd className="font-medium text-slate-700">
            {info.data_date_range.start} ~ {info.data_date_range.end}
          </dd>
        </div>
        <div className="flex justify-between border-b border-slate-100 py-1.5">
          <dt>Train / Val / Test</dt>
          <dd className="font-medium text-slate-700">
            {info.train_rows} / {info.val_rows} / {info.test_rows}
          </dd>
        </div>
        <div className="flex justify-between border-b border-slate-100 py-1.5">
          <dt>사용 피처 개수</dt>
          <dd className="font-medium text-slate-700">{info.feature_count}개</dd>
        </div>
        <div className="flex justify-between border-b border-slate-100 py-1.5">
          <dt>실제 학습 Epoch</dt>
          <dd className="font-medium text-slate-700">{info.epochs_ran}</dd>
        </div>
      </dl>
    </section>
  );
}
