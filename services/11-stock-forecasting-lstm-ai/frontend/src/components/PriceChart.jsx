// PriceChart.jsx — 최근 주가 차트 + Moving Average (recharts, 실시간 데이터)
import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

export default function PriceChart({ data }) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-bold text-slate-900">최근 주가 차트 (Close + Moving Average)</h2>

      {data.length === 0 ? (
        <p className="text-sm text-slate-400">종목을 선택하면 차트가 표시됩니다.</p>
      ) : (
        <div className="h-80 w-full">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 8, right: 16, left: 0, bottom: 8 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
              <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={30} />
              <YAxis tick={{ fontSize: 11 }} domain={["auto", "auto"]} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="close" name="Close" stroke="#0f172a" dot={false} strokeWidth={1.5} />
              <Line type="monotone" dataKey="ma5" name="MA5" stroke="#f59e0b" dot={false} strokeWidth={1.2} />
              <Line type="monotone" dataKey="ma20" name="MA20" stroke="#10b981" dot={false} strokeWidth={1.2} />
              <Line type="monotone" dataKey="ma60" name="MA60" stroke="#ef4444" dot={false} strokeWidth={1.2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </section>
  );
}
