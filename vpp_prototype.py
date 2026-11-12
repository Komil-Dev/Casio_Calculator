
# =====================================================
# AI-BASED VIRTUAL POWER PLANT (VPP) PROTOTYPE
# Forecasting + Optimization + Energy Management
# =====================================================

import numpy as np
import pandas as pd

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error

from scipy.optimize import linprog


# =====================================================
# 1. GENERATE SAMPLE HISTORICAL ENERGY DATA
# =====================================================

def generate_data(days=365):

    rng = np.random.default_rng(42)

    dates = pd.date_range(
        start="2024-01-01",
        periods=days * 24,
        freq="h"
    )

    hour = dates.hour.to_numpy()
    day = dates.dayofyear.to_numpy()
    weekday = dates.dayofweek.to_numpy()

    # Solar weather data
    seasonal = 0.72 + 0.28 * np.sin(
        2 * np.pi * (day - 80) / 365
    )

    daylight = np.maximum(
        0,
        np.sin(np.pi * (hour - 6) / 12)
    )

    cloud = rng.uniform(0, 0.65, len(dates))

    irradiance = (
        900 * seasonal * daylight * (1 - cloud)
        + rng.normal(0, 25, len(dates))
    )

    irradiance = np.clip(irradiance, 0, 1000)

    temperature = (
        18
        + 12 * np.sin(2 * np.pi * (day - 100) / 365)
        + 7 * np.sin(2 * np.pi * (hour - 8) / 24)
        + rng.normal(0, 2, len(dates))
    )

    # Solar PV actual power (simplified physical model)
    pv_power = (
        100
        * irradiance / 1000
        * np.clip(1 - 0.004 * (temperature - 25), 0.75, 1.1)
    )

    pv_power = np.clip(pv_power, 0, 100)

    # Electricity demand
    base_load = (
        48
        + 12 * np.sin(2 * np.pi * (hour - 7) / 24)
        + 8 * np.sin(2 * np.pi * (hour - 18) / 24)
    )

    morning_peak = np.where(
        (hour >= 6) & (hour <= 9), 12, 0
    )

    evening_peak = np.where(
        (hour >= 17) & (hour <= 22), 22, 0
    )

    weekend_effect = np.where(weekday >= 5, -5, 0)

    load = (
        base_load
        + morning_peak
        + evening_peak
        + 0.7 * np.maximum(temperature - 25, 0)
        + weekend_effect
        + rng.normal(0, 3, len(dates))
    )

    load = np.clip(load, 25, 110)

    data = pd.DataFrame({
        "hour": hour,
        "dayofyear": day,
        "dayofweek": weekday,
        "irradiance": irradiance,
        "temperature": temperature,
        "cloud": cloud,
        "pv_power": pv_power,
        "load": load
    })

    return data


# =====================================================
# 2. PREPARE DATA
# =====================================================

data = generate_data()

# Chronological train/test split
split = int(len(data) * 0.80)

train = data.iloc[:split]
test = data.iloc[split:]

pv_features = [
    "hour",
    "dayofyear",
    "irradiance",
    "temperature",
    "cloud"
]

load_features = [
    "hour",
    "dayofweek",
    "temperature"
]


# =====================================================
# 3. TRAIN MACHINE LEARNING MODELS
# =====================================================

pv_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

load_model = RandomForestRegressor(
    n_estimators=100,
    max_depth=12,
    min_samples_leaf=2,
    random_state=42,
    n_jobs=-1
)

# Train Solar PV model
pv_model.fit(
    train[pv_features],
    train["pv_power"]
)

# Train Load model
load_model.fit(
    train[load_features],
    train["load"]
)


# =====================================================
# 4. EVALUATE MODELS
# =====================================================

pv_test_prediction = pv_model.predict(
    test[pv_features]
)

load_test_prediction = load_model.predict(
    test[load_features]
)

pv_mae = mean_absolute_error(
    test["pv_power"],
    pv_test_prediction
)

load_mae = mean_absolute_error(
    test["load"],
    load_test_prediction
)

print("\n========== MODEL EVALUATION ==========")

print(f"Solar PV MAE: {pv_mae:.2f} kW")
print(f"Load MAE:     {load_mae:.2f} kW")


# =====================================================
# 5. PREPARE NEXT 24-HOUR WEATHER FORECAST
# =====================================================

future_dates = pd.date_range(
    start="2025-01-01",
    periods=24,
    freq="h"
)

rng = np.random.default_rng(7)

hour = future_dates.hour.to_numpy()
day = future_dates.dayofyear.to_numpy()
weekday = future_dates.dayofweek.to_numpy()

seasonal = 0.72 + 0.28 * np.sin(
    2 * np.pi * (day - 80) / 365
)

daylight = np.maximum(
    0,
    np.sin(np.pi * (hour - 6) / 12)
)

cloud = rng.uniform(0.05, 0.5, 24)

irradiance = (
    900 * seasonal * daylight * (1 - cloud)
)

temperature = (
    18
    + 12 * np.sin(2 * np.pi * (day - 100) / 365)
    + 7 * np.sin(2 * np.pi * (hour - 8) / 24)
    + rng.normal(0, 1.5, 24)
)

future_data = pd.DataFrame({
    "hour": hour,
    "dayofyear": day,
    "dayofweek": weekday,
    "irradiance": np.clip(irradiance, 0, 1000),
    "temperature": temperature,
    "cloud": cloud
})


# =====================================================
# 6. FORECAST SOLAR PV AND LOAD
# =====================================================

pv_forecast = np.clip(
    pv_model.predict(future_data[pv_features]),
    0,
    100
)

load_forecast = np.clip(
    load_model.predict(future_data[load_features]),
    20,
    120
)


# =====================================================
# 7. VPP BATTERY CONFIGURATION
# =====================================================

hours = 24
dt = 1.0

battery_capacity = 200       # kWh
battery_max_power = 50        # kW

initial_soc = 100             # kWh
minimum_soc = 20              # kWh
maximum_soc = 200             # kWh

charge_efficiency = 0.95
discharge_efficiency = 0.95

# Electricity buying price ($/kWh)
buy_price = np.array([
    0.08 if 0 <= h < 6
    else 0.16 if 6 <= h < 17
    else 0.28 if 17 <= h < 22
    else 0.12
    for h in hour
])

# Electricity selling price ($/kWh)
sell_price = np.full(hours, 0.05)


# =====================================================
# 8. OPTIMIZATION MODEL
# =====================================================

# Decision variables:
# Grid import:       0 ... 23
# Grid export:       24 ... 47
# Battery charging:  48 ... 71
# Battery discharge: 72 ... 95
# Battery SOC:       96 ... 120

n = hours

grid_import = slice(0, n)
grid_export = slice(n, 2*n)
charge = slice(2*n, 3*n)
discharge = slice(3*n, 4*n)
soc = slice(4*n, 5*n + 1)

number_of_variables = 5*n + 1

# Objective: minimize electricity cost
objective = np.zeros(number_of_variables)

objective[grid_import] = buy_price
objective[grid_export] = -sell_price

# Battery degradation cost
objective[charge] = 0.003
objective[discharge] = 0.003

A_eq = []
b_eq = []

# Energy balance constraints
for t in range(n):

    row = np.zeros(number_of_variables)

    row[t] = 1
    row[n+t] = -1
    row[2*n+t] = -1
    row[3*n+t] = 1

    A_eq.append(row)

    b_eq.append(
        load_forecast[t] - pv_forecast[t]
    )


# Battery SOC constraints
for t in range(n):

    row = np.zeros(number_of_variables)

    row[4*n+t+1] = 1
    row[4*n+t] = -1

    row[2*n+t] = -charge_efficiency * dt
    row[3*n+t] = dt / discharge_efficiency

    A_eq.append(row)
    b_eq.append(0)


# Initial SOC constraint
row = np.zeros(number_of_variables)
row[4*n] = 1

A_eq.append(row)
b_eq.append(initial_soc)


# Final SOC must return to initial SOC
row = np.zeros(number_of_variables)
row[5*n] = 1

A_eq.append(row)
b_eq.append(initial_soc)


# Variable limits
bounds = (
    [(0, None)] * n
    + [(0, None)] * n
    + [(0, battery_max_power)] * n
    + [(0, battery_max_power)] * n
    + [(minimum_soc, maximum_soc)] * (n+1)
)


# Solve optimization problem
result = linprog(
    c=objective,
    A_eq=np.array(A_eq),
    b_eq=np.array(b_eq),
    bounds=bounds,
    method="highs"
)


# =====================================================
# 9. DISPLAY OPTIMIZED VPP OPERATION
# =====================================================

if result.success:

    solution = result.x

    grid_import_values = solution[grid_import]
    grid_export_values = solution[grid_export]
    charge_values = solution[charge]
    discharge_values = solution[discharge]
    soc_values = solution[soc]

    print("\n========== VPP OPTIMIZATION ==========")

    results = pd.DataFrame({
        "Hour": hour,
        "PV_kW": pv_forecast,
        "Load_kW": load_forecast,
        "Charge_kW": charge_values,
        "Discharge_kW": discharge_values,
        "Grid_Import_kW": grid_import_values,
        "Grid_Export_kW": grid_export_values,
        "SOC_kWh": soc_values[1:]
    })

    print(results.round(2).to_string(index=False))

    # Cost without battery
    net_demand = load_forecast - pv_forecast

    baseline_cost = np.sum(
        np.maximum(net_demand, 0) * buy_price
        - np.maximum(-net_demand, 0) * sell_price
    )

    optimized_cost = result.fun

    print("\n========== FINAL VPP REPORT ==========")

    print(f"Cost without battery: ${baseline_cost:.2f}")
    print(f"Optimized VPP cost:   ${optimized_cost:.2f}")

    print(
        f"Cost reduction:       "
        f"${baseline_cost - optimized_cost:.2f}"
    )

    print(
        f"Total battery charge: "
        f"{np.sum(charge_values):.2f} kWh"
    )

    print(
        f"Total battery discharge: "
        f"{np.sum(discharge_values):.2f} kWh"
    )

    print(
        f"Final battery SOC: "
        f"{soc_values[-1]:.2f} kWh"
    )

else:

    print("Optimization failed!")
    print(result.message)



