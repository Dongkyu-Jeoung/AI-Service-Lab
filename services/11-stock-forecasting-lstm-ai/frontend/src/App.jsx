import { useEffect, useState } from "react";

import TickerSelector from "./components/TickerSelector";
import RecentDataTable from "./components/RecentDataTable";
import PredictionSummary from "./components/PredictionSummary";
import PriceChart from "./components/PriceChart";
import EvaluationPlots from "./components/EvaluationPlots";
import ModelInfoPanel from "./components/ModelInfoPanel";
import PredictionHistory from "./components/PredictionHistory";
import { getModelInfo, getStockHistory, getTickers, predictNextClose } from "./services/api";

const HISTORY_STORAGE_KEY = "stock_forecasting_prediction_history";
const DEFAULT_TICKER = "AAPL";

function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function extractErrorMessage(error) {
  const response = error?.response;
  if (!response) return "FastAPI 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인해주세요.";
  return response.data?.detail ?? "알 수 없는 오류가 발생했습니다.";
}

export default function App() {
  const [tickersInfo, setTickersInfo] = useState({ supported_tickers: [], trained_tickers: [] });
  const [selectedTicker, setSelectedTicker] = useState(DEFAULT_TICKER);
  const [chartData, setChartData] = useState([]);
  const [modelInfo, setModelInfo] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [history, setHistory] = useState(loadHistory);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    getTickers()
      .then((data) => {
        setTickersInfo(data);
        if (data.trained_tickers.length > 0 && !data.trained_tickers.includes(DEFAULT_TICKER)) {
          setSelectedTicker(data.trained_tickers[0]);
        }
      })
      .catch(() => setTickersInfo({ supported_tickers: [], trained_tickers: [] }));
  }, []);

  useEffect(() => {
    getStockHistory(selectedTicker)
      .then((data) => setChartData(data.data))
      .catch(() => setChartData([]));

    // 미학습 종목이면 백엔드가 404를 반환하고, catch에서 자연스럽게 null로 처리된다.
    getModelInfo(selectedTicker)
      .then(setModelInfo)
      .catch(() => setModelInfo(null));
  }, [selectedTicker]);

  function handleSelectTicker(ticker) {
    setSelectedTicker(ticker);
    setPrediction(null);
    setError("");
  }

  async function handlePredict() {
    setLoading(true);
    setError("");
    try {
      const result = await predictNextClose(selectedTicker);
      setPrediction(result);

      const entry = { ...result, requestedAt: new Date().toLocaleString("ko-KR") };
      const nextHistory = [entry, ...history].slice(0, 20);
      setHistory(nextHistory);
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(nextHistory));
    } catch (err) {
      setError(extractErrorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  function handleClearHistory() {
    setHistory([]);
    localStorage.removeItem(HISTORY_STORAGE_KEY);
  }

  return (
    <main className="mx-auto min-h-screen max-w-7xl px-4 py-10 sm:px-6 lg:px-8">
      <header className="mb-8 text-center">
        <p className="mb-3 inline-block rounded-full bg-indigo-100 px-4 py-1.5 text-sm font-bold text-indigo-700">
          AI Service Blueprint
        </p>
        <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 sm:text-4xl">Stock Forecasting AI</h1>
        <p className="mt-3 text-slate-500">LSTM으로 다음 거래일 종가를 예측하는 교육용 시계열 프로젝트</p>
        <p className="mx-auto mt-3 max-w-2xl rounded-xl border border-amber-200 bg-amber-50 px-4 py-2 text-xs font-semibold text-amber-700">
          ⚠ 이 서비스는 교육 목적으로 제작되었으며, 실제 투자 판단에 사용해서는 안 됩니다.
        </p>
      </header>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-[320px_minmax(0,1fr)]">
        {/* 좌측 */}
        <div className="flex flex-col gap-6">
          <TickerSelector
            supportedTickers={tickersInfo.supported_tickers}
            trainedTickers={tickersInfo.trained_tickers}
            selectedTicker={selectedTicker}
            onSelect={handleSelectTicker}
            onPredict={handlePredict}
            loading={loading}
          />
          <RecentDataTable data={chartData} />
        </div>

        {/* 우측 */}
        <div className="flex flex-col gap-6">
          {error && (
            <p className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm font-medium text-rose-600">
              {error}
            </p>
          )}
          <PredictionSummary prediction={prediction} ticker={selectedTicker} />
          <PriceChart data={chartData} />
          {modelInfo && <EvaluationPlots ticker={selectedTicker} />}
          <ModelInfoPanel info={modelInfo} />
          <PredictionHistory history={history} onClear={handleClearHistory} />
        </div>
      </div>

      <footer className="mt-12 text-center text-xs text-slate-400">
        Yahoo Finance(yfinance) 데이터 기반 · LSTM(TensorFlow/Keras) · 교육/포트폴리오 목적
      </footer>
    </main>
  );
}
