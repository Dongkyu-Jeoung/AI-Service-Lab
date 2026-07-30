# eda.py
# ==========================================================
# STEP 2. EDA (Exploratory Data Analysis, 탐색적 데이터 분석)
#
# 모델을 만들기 전에 데이터를 먼저 "눈으로" 살펴보는 단계.
# Shape/Info/Describe 같은 기초 통계부터, 가격 분포, 상관관계, 이동평균,
# 추세/계절성까지 확인하고, 결과를 그림(PNG)과 보고서(Markdown)로 남긴다.
# ==========================================================

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")  # 화면 없는 서버/Docker 환경에서도 그림을 파일로 저장할 수 있도록
import koreanize_matplotlib  # noqa: F401 - import만으로 matplotlib 기본 폰트를 한글 지원 폰트로 바꿔준다
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["axes.unicode_minus"] = False


def _save_fig(fig, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=120, bbox_inches="tight")
    plt.close(fig)


def basic_info(df: pd.DataFrame) -> dict:
    """Shape, Missing Value, Duplicate 등 가장 기본적인 데이터 점검."""
    return {
        "shape": {"rows": df.shape[0], "columns": df.shape[1]},
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": df.isnull().sum().to_dict(),
        "duplicate_rows": int(df.duplicated().sum()),
        "date_range": {"start": str(df.index.min().date()), "end": str(df.index.max().date())},
    }


def describe_stats(df: pd.DataFrame) -> pd.DataFrame:
    """Describe - 컬럼별 평균/표준편차/사분위수 등."""
    return df.describe()


def correlation_matrix(df: pd.DataFrame) -> pd.DataFrame:
    """OHLCV 컬럼 간 상관관계. Open/High/Low/Close는 서로 매우 강하게 상관되어
    있는 것이 정상이다(같은 날의 가격이므로) - Volume과의 상관관계가 더 흥미롭다.
    """
    return df[["Open", "High", "Low", "Close", "Volume"]].corr()


def plot_price_distribution(df: pd.DataFrame, output_dir: Path) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    axes[0].hist(df["Close"], bins=50, color="#6d28d9", alpha=0.8)
    axes[0].set_title("Close 가격 분포")
    axes[0].set_xlabel("Close ($)")
    axes[0].set_ylabel("빈도")

    axes[1].hist(df["Volume"], bins=50, color="#0891b2", alpha=0.8)
    axes[1].set_title("Volume 분포")
    axes[1].set_xlabel("Volume")
    axes[1].set_ylabel("빈도")

    fig.tight_layout()
    filename = "01_price_volume_distribution.png"
    _save_fig(fig, output_dir / filename)
    return filename


def plot_ohlc_boxplot(df: pd.DataFrame, output_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(8, 5))
    df[["Open", "High", "Low", "Close"]].plot(kind="box", ax=ax)
    ax.set_title("OHLC 분포 (Boxplot)")
    ax.set_ylabel("가격 ($)")
    filename = "02_ohlc_boxplot.png"
    _save_fig(fig, output_dir / filename)
    return filename


def plot_correlation_heatmap(corr: pd.DataFrame, output_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(corr, cmap="coolwarm", vmin=-1, vmax=1)
    ax.set_xticks(range(len(corr.columns)))
    ax.set_yticks(range(len(corr.columns)))
    ax.set_xticklabels(corr.columns, rotation=45, ha="right")
    ax.set_yticklabels(corr.columns)
    for i in range(len(corr.columns)):
        for j in range(len(corr.columns)):
            ax.text(j, i, f"{corr.iloc[i, j]:.2f}", ha="center", va="center", fontsize=9)
    fig.colorbar(im, ax=ax, label="상관계수")
    ax.set_title("OHLCV Correlation")
    filename = "03_correlation_heatmap.png"
    _save_fig(fig, output_dir / filename)
    return filename


def plot_close_timeseries_with_ma(df: pd.DataFrame, output_dir: Path) -> str:
    """Close 시계열 + 5/20/60일 이동평균을 한 그래프에."""
    ma5 = df["Close"].rolling(5).mean()
    ma20 = df["Close"].rolling(20).mean()
    ma60 = df["Close"].rolling(60).mean()

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(df.index, df["Close"], label="Close", color="#0f172a", linewidth=1)
    ax.plot(df.index, ma5, label="MA5", color="#f59e0b", linewidth=1)
    ax.plot(df.index, ma20, label="MA20", color="#10b981", linewidth=1)
    ax.plot(df.index, ma60, label="MA60", color="#ef4444", linewidth=1)
    ax.set_title("Close Time Series + Moving Average (5/20/60일)")
    ax.set_xlabel("Date")
    ax.set_ylabel("Close ($)")
    ax.legend()
    filename = "04_close_timeseries_ma.png"
    _save_fig(fig, output_dir / filename)
    return filename


def plot_volume_rolling_stats(df: pd.DataFrame, output_dir: Path, window: int = 20) -> str:
    """Volume Rolling Mean/Std - 거래량 추세와 변동성."""
    rolling_mean = df["Volume"].rolling(window).mean()
    rolling_std = df["Volume"].rolling(window).std()

    fig, axes = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
    axes[0].plot(df.index, df["Volume"], color="#94a3b8", linewidth=0.6, label="Volume")
    axes[0].plot(df.index, rolling_mean, color="#0891b2", linewidth=1.5, label=f"Rolling Mean({window}일)")
    axes[0].set_title("Volume + Rolling Mean")
    axes[0].legend()

    axes[1].plot(df.index, rolling_std, color="#dc2626", linewidth=1.2, label=f"Rolling Std({window}일)")
    axes[1].set_title("Volume Rolling Std (변동성)")
    axes[1].legend()

    fig.tight_layout()
    filename = "05_volume_rolling_stats.png"
    _save_fig(fig, output_dir / filename)
    return filename


def plot_trend_seasonality(df: pd.DataFrame, output_dir: Path) -> str:
    """Trend(장기 추세)와 Seasonality(계절성/주기성)를 간단히 분해해서 보여준다.

    statsmodels의 seasonal_decompose를 쓰면 더 정교하지만, 교육용으로는
    "60일 이동평균 = Trend", "Close - Trend = 잔차(주기성 힌트)"로 단순화해도
    충분히 개념을 전달할 수 있다.
    """
    trend = df["Close"].rolling(60, center=True).mean()
    residual = df["Close"] - trend

    fig, axes = plt.subplots(3, 1, figsize=(12, 8), sharex=True)
    axes[0].plot(df.index, df["Close"], color="#0f172a", linewidth=1)
    axes[0].set_title("원본 Close")

    axes[1].plot(df.index, trend, color="#6d28d9", linewidth=1.5)
    axes[1].set_title("Trend (60일 중심 이동평균)")

    axes[2].plot(df.index, residual, color="#f59e0b", linewidth=0.8)
    axes[2].axhline(0, color="gray", linewidth=0.8, linestyle="--")
    axes[2].set_title("Residual (Trend 제거 후 남은 변동 = 계절성/노이즈 힌트)")

    fig.tight_layout()
    filename = "06_trend_seasonality.png"
    _save_fig(fig, output_dir / filename)
    return filename


def generate_eda_report(df: pd.DataFrame, ticker: str, output_dir: Path) -> Path:
    """모든 EDA 통계/그림을 생성하고, 하나의 Markdown 보고서로 정리한다."""
    plots_dir = output_dir / "eda_plots"
    info = basic_info(df)
    desc = describe_stats(df)
    corr = correlation_matrix(df)

    img1 = plot_price_distribution(df, plots_dir)
    img2 = plot_ohlc_boxplot(df, plots_dir)
    img3 = plot_correlation_heatmap(corr, plots_dir)
    img4 = plot_close_timeseries_with_ma(df, plots_dir)
    img5 = plot_volume_rolling_stats(df, plots_dir)
    img6 = plot_trend_seasonality(df, plots_dir)

    report_path = output_dir / f"eda_report_{ticker}.md"
    lines = [
        f"# EDA Report — {ticker}",
        "",
        f"- 데이터 기간: {info['date_range']['start']} ~ {info['date_range']['end']}",
        f"- Shape: {info['shape']['rows']}행 x {info['shape']['columns']}열",
        f"- 결측치: {sum(info['missing_values'].values())}개",
        f"- 중복 행: {info['duplicate_rows']}개",
        "",
        "## Info (컬럼/자료형)",
        "",
        "| 컬럼 | 자료형 | 결측치 |",
        "|---|---|---|",
    ]
    for col in info["columns"]:
        lines.append(f"| {col} | {info['dtypes'][col]} | {info['missing_values'][col]} |")

    lines += [
        "",
        "## Describe (기초 통계량)",
        "",
        desc.to_markdown(),
        "",
        "## Correlation (OHLCV 상관관계)",
        "",
        corr.round(3).to_markdown(),
        "",
        f"![상관관계 히트맵](eda_plots/{img3})",
        "",
        "## Close / Volume 분포",
        "",
        f"![가격/거래량 분포](eda_plots/{img1})",
        "",
        "## OHLC Boxplot",
        "",
        f"![OHLC Boxplot](eda_plots/{img2})",
        "",
        "## Close Time Series + Moving Average",
        "",
        f"![Close+MA](eda_plots/{img4})",
        "",
        "## Volume Rolling Mean/Std",
        "",
        f"![Volume Rolling](eda_plots/{img5})",
        "",
        "## Trend / Seasonality",
        "",
        f"![Trend/Seasonality](eda_plots/{img6})",
        "",
    ]

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines), encoding="utf-8")

    # 요약 통계는 프론트/백엔드에서도 재사용할 수 있도록 JSON으로도 남긴다.
    summary_json = output_dir / f"eda_summary_{ticker}.json"
    summary_json.write_text(
        json.dumps(
            {
                "ticker": ticker,
                "shape": info["shape"],
                "date_range": info["date_range"],
                "missing_values": info["missing_values"],
                "duplicate_rows": info["duplicate_rows"],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    return report_path


if __name__ == "__main__":
    from config import ARTIFACTS_DIR
    from data_collector import fetch_stock_data

    ticker = "AAPL"
    raw = fetch_stock_data(ticker)
    path = generate_eda_report(raw, ticker, ARTIFACTS_DIR / ticker)
    print(f"EDA 보고서 생성 완료: {path}")
