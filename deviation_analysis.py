import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from Functions.prepping import *
from Functions.points import clean_gps_data, classify_route_variant


# ================================================================
# Paths to files and initial values
# Change these to fit your needs
# ================================================================
file_path = "Data/ruta5.csv"
ruta_5_json_path = "Data/ruta_5.json"
map_path = 'Maps/comparing_map.html'
branches_path = "Data/branches_df.geojson"
route = 'RUTA 5'
rounding_precision = 4
closer_threshold = 3
time_diff_threshold = 120
predictions_path = "Data/predictions_df.csv"


# ================================================================
# Get necessary data
# ================================================================

# Get data
df = pd.read_csv(file_path)
# Format and filter to this file needs
empiric_df = format_df(df)
empiric_df = empiric_df[empiric_df['Route'] == route]

# Get the official routes
# If file isn't there, run official_routes.py
branches_df = gpd.read_file(branches_path, driver="GeoJSON")

# ================================================================
# Calculte deviations
# ================================================================
records = []
# Iterate over each unique plate
for plate in tqdm(empiric_df['Plate'].unique(), desc="Processing plates"):
    plate_df = empiric_df[empiric_df['Plate'] == plate]
    sorted_dates = sorted(plate_df['Time'].dt.date.unique())
    # Iterate over each unique date for the current plate
    for day in tqdm(sorted_dates, desc=f"Processing dates for plate {plate}"):
        plate_date_df = plate_df[plate_df['Time'].dt.date == day]
        # Clean the data
        clean_df = clean_gps_data(plate_date_df,rounding_precision,time_diff_threshold,closer_threshold)
        # Make the prediction
        predicted_df, deviation = classify_route_variant(clean_df, branches_df)
        # Calculate mean deviation
        mean_deviation = deviation / clean_df.shape[0]  # deviation/points
        # Append the record to the list
        records.append({"Plate": plate, "Date": day, "Deviation": mean_deviation, "Predicted_Branch": predicted_df["Branch"]})

# Convert the records list to a DataFrame
deviations_df = pd.DataFrame(records)

# Save this info
deviations_df.to_csv(predictions_path, index=False)