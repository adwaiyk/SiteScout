import os
import joblib
import numpy as np
import pandas as pd
from xgboost import XGBRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Ensure the output directory exists
MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

def generate_synthetic_dataset(samples: int = 5000):
    """
    Generates realistic historical training samples correlating climate metrics
    (irradiance, temperature, wind speed) with power output (MWh) and capacity factors.
    """
    np.random.seed(42)
    
    # Solar Features
    solar_irradiance = np.random.uniform(2.5, 7.5, samples)  # kWh/m²/day
    avg_temp = np.random.uniform(10.0, 42.0, samples)         # °C
    system_capacity_solar = np.random.uniform(500, 5000, samples) # kW
    
    # Solar Physics-Informed Target
    temp_efficiency_loss = np.where(avg_temp > 25.0, (avg_temp - 25.0) * 0.004, 0)
    pr = 0.77 - temp_efficiency_loss + np.random.normal(0, 0.02, samples)
    solar_mwh = (solar_irradiance * 365 * system_capacity_solar * pr) / 1000
    solar_cf = (solar_mwh * 1000) / (system_capacity_solar * 8760) * 100

    # Wind Features
    wind_speed = np.random.uniform(1.0, 15.0, samples) # m/s at 50m
    system_capacity_wind = np.random.uniform(500, 5000, samples) # kW
    
    # Wind Physics-Informed Target (Cubic relationship with cut-in/cut-out limits)
    raw_cf = np.where(wind_speed < 3.0, 0.0, np.minimum(0.50, (0.087 * wind_speed) - 0.2))
    wind_cf = np.clip(raw_cf + np.random.normal(0, 0.025, samples), 0, 55)
    wind_mwh = (system_capacity_wind * 8760 * (wind_cf / 100)) / 1000

    solar_df = pd.DataFrame({
        'irradiance': solar_irradiance,
        'temperature': avg_temp,
        'capacity_kw': system_capacity_solar,
        'annual_mwh': solar_mwh,
        'capacity_factor': solar_cf
    })

    wind_df = pd.DataFrame({
        'wind_speed': wind_speed,
        'capacity_kw': system_capacity_wind,
        'annual_mwh': wind_mwh,
        'capacity_factor': wind_cf
    })

    return solar_df, wind_df


def train_solar_model(df: pd.DataFrame):
    print("\n--- Training Solar XGBoost Regressor ---")
    X = df[['irradiance', 'temperature', 'capacity_kw']]
    y = df['annual_mwh']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    print(f"Solar Model R² Score: {r2:.4f}")
    print(f"Solar Model MAE: {mae:.2f} MWh")
    print(f"Solar Model RMSE: {rmse:.2f} MWh")

    model_path = os.path.join(MODELS_DIR, "solar_model.joblib")
    joblib.dump(model, model_path)
    print(f"Saved Solar Model -> {model_path}")


def train_wind_model(df: pd.DataFrame):
    print("\n--- Training Wind XGBoost Regressor ---")
    X = df[['wind_speed', 'capacity_kw']]
    y = df['annual_mwh']

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = XGBRegressor(
        n_estimators=150,
        learning_rate=0.05,
        max_depth=5,
        random_state=42
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    r2 = r2_score(y_test, predictions)
    mae = mean_absolute_error(y_test, predictions)
    rmse = np.sqrt(mean_squared_error(y_test, predictions))

    print(f"Wind Model R² Score: {r2:.4f}")
    print(f"Wind Model MAE: {mae:.2f} MWh")
    print(f"Wind Model RMSE: {rmse:.2f} MWh")

    model_path = os.path.join(MODELS_DIR, "wind_model.joblib")
    joblib.dump(model, model_path)
    print(f"Saved Wind Model -> {model_path}")


if __name__ == "__main__":
    print("Generating dataset and training ML models...")
    solar_df, wind_df = generate_synthetic_dataset(samples=5000)
    train_solar_model(solar_df)
    train_wind_model(wind_df)
    print("\n All models trained and saved successfully!")