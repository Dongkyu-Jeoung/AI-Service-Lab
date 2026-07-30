// services/api.js
// ---------------------------------------------------------------
// FastAPI 서버와 통신하는 유일한 창구.
// ---------------------------------------------------------------

import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: { "Content-Type": "application/json" },
});

export async function getServiceStatus() {
  const { data } = await api.get("/health");
  return data; // { status, trained_tickers }
}

export async function getTickers() {
  const { data } = await api.get("/tickers");
  return data; // { supported_tickers, trained_tickers }
}

export async function predictNextClose(ticker) {
  const { data } = await api.post("/predict", { ticker });
  return data;
}

export async function getStockHistory(ticker, days = 90) {
  const { data } = await api.get(`/stock/${ticker}/history`, { params: { days } });
  return data; // { ticker, data: [{date, close, ma5, ma20, ma60}, ...] }
}

export async function getModelInfo(ticker) {
  const { data } = await api.get(`/model/info/${ticker}`);
  return data;
}

export function plotUrl(ticker, filename) {
  return `${API_BASE_URL}/plots/${ticker}/plots/${filename}`;
}

export default api;
