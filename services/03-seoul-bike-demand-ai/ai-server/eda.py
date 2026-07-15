# ================================================================
# EDA (Exploratory Data Analysis / 탐색적 데이터 분석)
#
# 목적
# 1. 데이터 구조 이해
# 2. 데이터 품질 확인
# 3. 데이터 분포 분석
# 4. 변수 간 관계 분석
#
# 작업 순서
# 데이터 이해 > 그래프 > 통계 > 상관관계 분석
# ================================================================

# ----------------------------------------------------------------
#    1. 라이브러리 import
# ----------------------------------------------------------------
import pandas as pd
import matplotlib.pyplot as plt

# ----------------------------------------------------------------
#    2. 데이터 불러오기
# ----------------------------------------------------------------
df = pd.read_csv('data/seoul_bike_data.csv', encoding="cp949")
print(df.head())

# ----------------------------------------------------------------
#    3. 컬럼명 변경
# ----------------------------------------------------------------
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

# ----------------------------------------------------------------
#    4. 데이터 구조 확인
# ----------------------------------------------------------------
# 4-1. 데이터 크기 확인
print(df.shape)

# 4-2. 데이터 정보 확인
print(df.info())

# 4-3. 컬럼 확인
print(df.columns)
# 💡 Target(정답) 값은 무엇일까요? Rented Bike Count
# 💡 Feature(입력값) 값은 무엇일까요? Temperature, Humidity, Wind speed, Rainfall, Snowfall, Hour, Season

# ----------------------------------------------------------------
#    5. 데이터 품질 확인(Data Quality Check)
# ----------------------------------------------------------------
# 5-1. 결측치 확인
print(df.isnull().sum())

# 5-2. 중복 데이터 확인
print(df.duplicated().sum())

# 5-3. 기초 통계량 확인
print(df.describe())

# ----------------------------------------------------------------
#    6. 데이터 분포 분석(Histogram)
# ----------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

fig.suptitle(
    "Seoul Bike Sharing Demand - Histogram Analysis",
    fontsize=16,
    fontweight="bold"
)

# 6-1. Target(Rented Bike Count) 분포 확인
df['bike_count'].hist(ax=axes[0], bins=30)
axes[0].set_title('Bike Count')
axes[0].set_xlabel('Bike Count')
axes[0].set_ylabel('Frequency')
axes[0].grid(alpha=0.3)

# 6-2. Temperature 분포 확인
df['temperature'].hist(ax=axes[1], bins=30)
axes[1].set_title('Temperature')
axes[1].set_xlabel('Temperature')
axes[1].set_ylabel('Frequency')
axes[1].grid(alpha=0.3)

plt.tight_layout()
plt.show()

# ----------------------------------------------------------------
#    7. 변수 관계 분석(Scatter Plot)
# ----------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(10, 5))

fig.suptitle(
    "EDA - Scatter Plot Analysis",
    fontsize=16,
    fontweight="bold"
)

# Temperature vs Bike Count
axes[0].scatter(
    df["temperature"],
    df["bike_count"],
    alpha=0.5
)
axes[0].set_title("Temperature vs Bike Count")
axes[0].set_xlabel("Temperature (°C)")
axes[0].set_ylabel("Bike Count")

# Humidity vs Bike Count
axes[1].scatter(
    df["humidity"],
    df["bike_count"],
    alpha=0.5
)
axes[1].set_title("Humidity vs Bike Count")
axes[1].set_xlabel("Humidity (%)")
axes[1].set_ylabel("Bike Count")

plt.tight_layout()
plt.subplots_adjust(top=0.88)
plt.show()

# ----------------------------------------------------------------
#    8. 상관관계 분석(Correlation Analysis)
# ----------------------------------------------------------------
# 8-1. 숫자형 데이터만 선택
numeric_df = df.select_dtypes(include="number")

# 8-2. 상관계수 계산
corr = numeric_df.corr()
print(corr)

# 8-3. bike_count 컬럼과의 상관관계 분석
corr_bike = (
    corr["bike_count"]
    .sort_values(ascending=False)
    .to_frame(name="Correlation")
)
print(corr_bike)

# ----------------------------------------------------------------
#    이상치 확인은 데이터에 따라서 추가하기!!
# ----------------------------------------------------------------