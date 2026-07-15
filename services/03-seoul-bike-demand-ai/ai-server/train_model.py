# ==========================================================
# Seoul Bike Demand AI - Train Model
# RandomForest Regression
# ==========================================================
# ----------------------------------------------------------
#    1. 라이브러리 import
# ----------------------------------------------------------
import os
import pandas as pd
import joblib

from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, r2_score

# ----------------------------------------------------------
#    2. 데이터 불러오기
# ----------------------------------------------------------
df = pd.read_csv(
    'data/seoul_bike_data.csv', 
    encoding='cp949'
)
print(df.head())


# ----------------------------------------------------------
#    3. 컬럼명 변경
# ----------------------------------------------------------
df.columns = [
    "date",
    "bike_count",
    "hour",
    "temperature",
    "humidity",
    "wind_speed",
    "visibility",
    "dew_point",
    "solar_radiation",
    "rainfall",
    "snowfall",
    "season",
    "holiday",
    "functioning_day"
]
print(df.columns.tolist())
print(df.head())

# ----------------------------------------------------------
#    4. Feature / Target 준비
# ----------------------------------------------------------
# 날짜는 문자열이므로 이번 모델에서는 제외
df = df.drop(columns=["date"])

# 문자열 컬럼을 숫자형으로 변환
df = pd.get_dummies(df)

X = df.drop(columns=["bike_count"])
y = df["bike_count"]

# ----------------------------------------------------------
#    5. Train / Test 데이터 분리
# ----------------------------------------------------------
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42
)

# ----------------------------------------------------------
#    6. RandomForest 회귀 모델 생성 및 학습
# ----------------------------------------------------------
model = RandomForestRegressor(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)


# ----------------------------------------------------------
#    7. 예측 및 간단 평가
# ----------------------------------------------------------
pred = model.predict(X_test)

mae = mean_absolute_error(y_test, pred)
r2 = r2_score(y_test, pred)

print("MAE:", round(mae, 2))
print("R2 Score:", round(r2, 4))

# ----------------------------------------------------------
#    8. 모델 저장
# ----------------------------------------------------------
os.makedirs("models", exist_ok=True)

joblib.dump(
    model,
    "models/bike_demand_model.pkl"
)

print("모델 저장 완료: models/bike_demand_model.pkl")
