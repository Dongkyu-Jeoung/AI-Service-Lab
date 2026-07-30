# train.py
# ==========================================================
# 전체 학습 파이프라인의 진입점(Entry Point).
#
#   데이터 수집 -> EDA -> Feature Engineering -> Scaling -> Sequence 생성
#   -> LSTM 모델 구축 -> 학습 -> 평가 -> Baseline 비교 -> 저장
#
# 학생은 이 파일 하나만 실행하면 STEP 1~9가 전부 순서대로 실행된다.
#
# 사용법:
#   cd services/10-stock-forecasting-lstm-ai/ai-model/src
#   python train.py --ticker AAPL
# ==========================================================

import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np
from tensorflow import keras

from config import (
    ARTIFACTS_DIR,
    BATCH_SIZE,
    EARLY_STOPPING_PATIENCE,
    EPOCHS,
    FEATURE_COLUMNS,
    LOOKBACK,
    RANDOM_SEED,
    TARGET_COLUMN,
)
from data_collector import fetch_stock_data
from eda import generate_eda_report
from evaluate import compare_with_baselines, compute_metrics, plot_loss_curve, plot_prediction_vs_actual, plot_residuals
from feature_engineering import build_features
from model import build_lstm_model
from preprocessing import create_sequences, fit_scaler, inverse_transform_target, split_data, transform_data

import tensorflow as tf

np.random.seed(RANDOM_SEED)
tf.random.set_seed(RANDOM_SEED)


def train_pipeline(ticker: str, epochs: int = EPOCHS, use_cache: bool = True) -> dict:
    """전체 파이프라인을 실행하고 최종 결과(메트릭 등) 딕셔너리를 반환한다."""
    started_at = time.time()
    ticker_dir = ARTIFACTS_DIR / ticker
    ticker_dir.mkdir(parents=True, exist_ok=True)

    # --------------------------------------------------
    # STEP 1. 데이터 수집
    # --------------------------------------------------
    print(f"\n[1/9] {ticker} 데이터 수집 중...")
    raw_df = fetch_stock_data(ticker, use_cache=use_cache)
    print(f"      -> {len(raw_df)}행, {raw_df.index.min().date()} ~ {raw_df.index.max().date()}")

    # --------------------------------------------------
    # STEP 2. EDA
    # --------------------------------------------------
    print("[2/9] EDA 보고서 생성 중...")
    eda_report_path = generate_eda_report(raw_df, ticker, ticker_dir)
    print(f"      -> {eda_report_path}")

    # --------------------------------------------------
    # STEP 3. Feature Engineering
    # --------------------------------------------------
    print("[3/9] Feature Engineering...")
    features_df = build_features(raw_df)
    print(f"      -> {len(features_df)}행, {len(FEATURE_COLUMNS)}개 피처")

    # --------------------------------------------------
    # STEP 4. Train/Val/Test 분할 + Scaling
    # --------------------------------------------------
    print("[4/9] 데이터 분할 및 Scaling (Train에만 fit)...")
    split = split_data(features_df)
    print(f"      -> Train {len(split.train)} / Val {len(split.val)} / Test {len(split.test)}")

    scaler = fit_scaler(split.train, FEATURE_COLUMNS)
    train_scaled = transform_data(split.train, scaler, FEATURE_COLUMNS)
    val_scaled = transform_data(split.val, scaler, FEATURE_COLUMNS)
    test_scaled = transform_data(split.test, scaler, FEATURE_COLUMNS)

    # --------------------------------------------------
    # STEP 5. Sequence 생성
    # --------------------------------------------------
    print(f"[5/9] Sequence 생성 (LOOKBACK={LOOKBACK})...")
    target_idx = FEATURE_COLUMNS.index(TARGET_COLUMN)
    X_train, y_train = create_sequences(train_scaled, target_idx)
    X_val, y_val = create_sequences(val_scaled, target_idx)
    X_test, y_test = create_sequences(test_scaled, target_idx)
    print(f"      -> X_train {X_train.shape}, X_val {X_val.shape}, X_test {X_test.shape}")

    # --------------------------------------------------
    # STEP 6. LSTM 모델 구축
    # --------------------------------------------------
    print("[6/9] LSTM 모델 구축...")
    model = build_lstm_model(input_shape=(X_train.shape[1], X_train.shape[2]))
    model.summary()

    # --------------------------------------------------
    # STEP 7. 학습
    # --------------------------------------------------
    print(f"[7/9] 학습 시작 (최대 {epochs} epoch, EarlyStopping patience={EARLY_STOPPING_PATIENCE})...")
    checkpoint_path = ticker_dir / "model.keras"

    callbacks = [
        keras.callbacks.EarlyStopping(
            monitor="val_loss",
            patience=EARLY_STOPPING_PATIENCE,
            restore_best_weights=True,
        ),
        keras.callbacks.ModelCheckpoint(
            filepath=str(checkpoint_path),
            monitor="val_loss",
            save_best_only=True,
        ),
    ]

    history = model.fit(
        X_train,
        y_train,
        validation_data=(X_val, y_val),
        epochs=epochs,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=2,
    )

    plot_loss_curve(history, ticker_dir / "plots" / "loss_curve.png")

    # --------------------------------------------------
    # STEP 8. 평가
    # --------------------------------------------------
    print("[8/9] 평가 중...")
    y_pred_scaled = model.predict(X_test, verbose=0).reshape(-1)

    n_features = len(FEATURE_COLUMNS)
    y_test_prices = inverse_transform_target(scaler, y_test, target_idx, n_features)
    y_pred_prices = inverse_transform_target(scaler, y_pred_scaled, target_idx, n_features)

    metrics = compute_metrics(y_test_prices, y_pred_prices)
    print(f"      -> MAE={metrics['MAE']}, RMSE={metrics['RMSE']}, MAPE={metrics['MAPE']}%, R2={metrics['R2']}")

    test_dates = split.test.index[LOOKBACK:]
    plot_prediction_vs_actual(test_dates, y_test_prices, y_pred_prices, ticker_dir / "plots" / "prediction_vs_actual.png")
    plot_residuals(y_test_prices, y_pred_prices, ticker_dir / "plots" / "residuals.png")

    baseline_df = compare_with_baselines(y_test_prices, y_pred_prices)
    baseline_path = ticker_dir / "baseline_comparison.md"
    baseline_path.write_text(
        f"# Baseline 비교 — {ticker}\n\n" + baseline_df.to_markdown(index=False) + "\n",
        encoding="utf-8",
    )
    print(f"      -> Baseline 비교표: {baseline_path}")

    # --------------------------------------------------
    # STEP 9. 저장 (model.keras는 ModelCheckpoint가 이미 저장함)
    # --------------------------------------------------
    print("[9/9] 아티팩트 저장 중...")

    scaler_path = ticker_dir / "scaler.pkl"
    with open(scaler_path, "wb") as f:
        pickle.dump(scaler, f)

    metadata = {
        "ticker": ticker,
        "lookback": LOOKBACK,
        "feature_columns": FEATURE_COLUMNS,
        "target_column": TARGET_COLUMN,
        "target_column_index": target_idx,
        "train_rows": len(split.train),
        "val_rows": len(split.val),
        "test_rows": len(split.test),
        "epochs_ran": len(history.history["loss"]),
        "test_metrics": metrics,
        "baseline_comparison": baseline_df.to_dict(orient="records"),
        "data_date_range": {
            "start": str(raw_df.index.min().date()),
            "end": str(raw_df.index.max().date()),
        },
        "trained_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "training_duration_sec": round(time.time() - started_at, 1),
    }
    metadata_path = ticker_dir / "metadata.json"
    metadata_path.write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"\n완료! 소요 시간: {metadata['training_duration_sec']}초")
    print(f"  - 모델: {checkpoint_path}")
    print(f"  - 스케일러: {scaler_path}")
    print(f"  - 메타데이터: {metadata_path}")

    return metadata


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="LSTM 주가 예측 모델 학습")
    parser.add_argument("--ticker", default="AAPL", help="종목 코드 (기본값: AAPL)")
    parser.add_argument("--epochs", type=int, default=EPOCHS, help=f"최대 epoch 수 (기본값: {EPOCHS})")
    parser.add_argument("--no-cache", action="store_true", help="데이터 캐시를 무시하고 새로 다운로드")
    args = parser.parse_args()

    train_pipeline(args.ticker, epochs=args.epochs, use_cache=not args.no_cache)
