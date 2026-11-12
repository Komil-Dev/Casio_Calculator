
# Project scenario
time = [8, 9, 10, 11, 12]

solar_irradiance = [200, 350, 500, 700, 900]
temperature = [20, 23, 26, 29, 32]

rated_power = 100
reference_irradiance = 1000

# Calculate Solar PV Power
solar_pv = []

for G in solar_irradiance:
    power = rated_power * G / reference_irradiance
    solar_pv.append(power)

# Display results
print("SOLAR PV RESULTS PROJECT")
print("-" * 45)

print(f"{'Time':<10}{'Irradiance':<15}{'PV Power'}")
print("-" * 45)

for i in range(len(time)):
    print(
        f"{time[i]:<10}"
        f"{solar_irradiance[i]:<15}"
        f"{solar_pv[i]:.1f} kW"
    )

# Maximum PV Power
max_power = max(solar_pv)

# Average PV Power
average_power = sum(solar_pv) / len(solar_pv)

# Final results
print("-" * 45)
print(f"Maximum PV Power: {max_power:.1f} kW")
print(f"Average PV Power: {average_power:.2f} kW")
