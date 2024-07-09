import pandas as pd
import geopandas as gpd
from tqdm import tqdm
from Functions.prepping import *
from Functions.points import clean_gps_data, classify_route_variant

# ================================================================
# Overview
# ================================================================
# This script processes GPS data for a specific route, cleans the data, and calculates the deviation 
# from the official route for each plate (vehicle) on each day. The results, including the predicted branch 
# of the route and mean deviation, are saved to a CSV file for further analysis.

# ================================================================
# Paths to files and initial values
# Change these to fit your needs
# ================================================================
file_path = "Data/ruta5.csv"  # Path to the CSV file containing the GPS data
ruta_5_json_path = "Data/ruta_5.json"  # Path to the JSON file containing the official route data
map_path = 'Maps/comparing_map.html'  # Path to save the comparison map
branches_path = "Data/branches_df.geojson"  # Path to the GeoJSON file containing branch route data
route = 'RUTA 5'  # Route identifier
rounding_precision = 4  # Precision for rounding coordinates
closer_threshold = 3  # Threshold for finding closest points
time_diff_threshold = 120  # Time interval in seconds for grouping points
predictions_path = "Data/predictions_df.csv"  # Path to save the predictions

# ================================================================
# Get necessary data
# ================================================================

# Load the GPS data from the CSV file
df = pd.read_csv(file_path)

# Format and filter the DataFrame to match the specific route
empiric_df = format_df(df)
empiric_df = empiric_df[empiric_df['Route'] == route]

# Load the official route branches from the GeoJSON file
branches_df = gpd.read_file(branches_path, driver="GeoJSON")

# ================================================================
# Calculate deviations
# ================================================================
records = []

# Iterate over each unique plate (vehicle)
for plate in tqdm(empiric_df['Plate'].unique(), desc="Processing plates"):
    plate_df = empiric_df[empiric_df['Plate'] == plate]
    sorted_dates = sorted(plate_df['Time'].dt.date.unique())
    
    # Iterate over each unique date for the current plate
    for day in tqdm(sorted_dates, desc=f"Processing dates for plate {plate}"):
        plate_date_df = plate_df[plate_df['Time'].dt.date == day]
        
        # Clean the GPS data for the specific date and plate
        clean_df = clean_gps_data(plate_date_df, rounding_precision, time_diff_threshold, closer_threshold)
        
        # Predict the branch of the route and calculate the deviation
        predicted_df, deviation = classify_route_variant(clean_df, branches_df)
        
        # Calculate the mean deviation
        mean_deviation = deviation / clean_df.shape[0]  # deviation divided by the number of points
        
        # Append the record to the list
        records.append({"Plate": plate, "Date": day, "Deviation": mean_deviation, "Predicted_Branch": predicted_df["Branch"]})

# Convert the records list to a DataFrame
deviations_df = pd.DataFrame(records)

# Save the deviations DataFrame to a CSV file
deviations_df.to_csv(predictions_path, index=False)
