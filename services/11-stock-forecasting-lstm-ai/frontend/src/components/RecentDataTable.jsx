// RecentDataTable.jsx — 좌측 패널: 최근 데이터 테이블
export default function RecentDataTable({ data }) {
  const recent = [...data].slice(-8).reverse();

  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
      <h2 className="mb-4 text-lg font-bold text-slate-900">최근 데이터</h2>

      {recent.length === 0 ? (
        <p className="text-sm text-slate-400">종목을 선택하면 최근 데이터가 표시됩니다.</p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-xs">
            <thead>
              <tr className="border-b border-slate-200 text-slate-400">
                <th className="py-2 text-left font-medium">날짜</th>
                <th className="py-2 text-right font-medium">종가</th>
                <th className="py-2 text-right font-medium">MA5</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((row) => (
                <tr key={row.date} className="border-b border-slate-100 last:border-0">
                  <td className="py-2 text-slate-600">{row.date}</td>
                  <td className="py-2 text-right font-semibold text-slate-900">${row.close.toFixed(2)}</td>
                  <td className="py-2 text-right text-slate-500">{row.ma5 ? `$${row.ma5.toFixed(2)}` : "-"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
