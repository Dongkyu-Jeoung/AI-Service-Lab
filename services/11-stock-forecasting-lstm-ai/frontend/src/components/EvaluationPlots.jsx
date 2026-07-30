// EvaluationPlots.jsx — 학습 시 생성된 평가 그래프(실제 vs 예측, 잔차, Loss)를 이미지로 표시
import { plotUrl } from "../services/api";

const PLOTS = [
  { file: "prediction_vs_actual.png", title: "실제값 vs 예측값 (Test 구간)" },
  { file: "residuals.png", title: "Residual Plot (잔차 분석)" },
  { file: "loss_curve.png", title: "학습 Loss 곡선" },
];

export default function EvaluationPlots({ ticker }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-1 text-lg font-bold text-slate-900">모델 평가 그래프</h2>
      <p className="mb-4 text-xs text-slate-400">ai-model이 학습 시 Test 데이터로 생성한 그래프입니다.</p>

      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        {PLOTS.map((plot) => (
          <figure key={plot.file} className="overflow-hidden rounded-xl border border-slate-100">
            <img
              src={plotUrl(ticker, plot.file)}
              alt={plot.title}
              className="w-full bg-slate-50 object-contain"
              onError={(e) => {
                e.currentTarget.style.display = "none";
              }}
            />
            <figcaption className="border-t border-slate-100 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-500">
              {plot.title}
            </figcaption>
          </figure>
        ))}
      </div>
    </section>
  );
}
