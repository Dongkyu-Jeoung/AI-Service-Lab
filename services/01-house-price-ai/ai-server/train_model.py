# 1. 라이브러리 import
import pandas as pd
import joblib

from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import (
    r2_score,
    mean_absolute_error,
    root_mean_squared_error
)

# 2. 데이터 호출
housing =  fetch_california_housing(as_frame=True)
df = housing.frame
# print(df.head())

# 3. Feature(X), Taret(y) 분리
x = df.drop(columns = 'MedHouseVal')
y = df['MedHouseVal']
# print(x.head(), y.head())

# 4. Train / Test 데이터 분리
X_train, X_test, y_train, y_test = \
    train_test_split(
        x,
        y,
        test_size= 0.2,
        random_state= 42
    )
# print(X_train.shape, y_train.shape)

# 5. Model(RandomForest) 생성
model = RandomForestRegressor(random_state=42)

# 학습
model.fit(X_train, y_train)

# 예측
pred = model.predict(X_test)
# print(pred[:10])

# 6. 모델 저장
joblib.dump(
    model,
    "models/house_price_model.pkl"
)

# 예측값  vs. 정답 비교
result_df = pd.DataFrame({
    "Actual": y_test.values,
    "Predict": pred
})

result_df["Error"] = result_df["Actual"] - result_df["Predict"]

# print(result_df.head(10))

# 성능 평가
r2 = r2_score(y_test, pred) # 얼마나 잘 맞았는가?
mae = mean_absolute_error(y_test, pred) # 평균적으로 얼마나 틀렸는가?
rmse = root_mean_squared_error(y_test, pred) # 큰 오차까지 고려한 평균 오차

print(f"R²   : {r2:.4f}")
print(f"MAE  : {mae:.4f}")
print(f"RMSE : {rmse:.4f}")