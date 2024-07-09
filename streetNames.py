import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from Functions.prepping import *
from Functions.maps import *
from Functions.points import *
from tqdm import tqdm

# ================================================================
# Overview
# ================================================================
# This script processes GPS data from a CSV file, filters and formats the data for a specific route and 
# its plates (buses), groups points within intervals, finds the closest points, snaps them to roads, 
# and extracts street names. It uses concurrent processing to handle multiple plates in parallel and 
# generates a CSV file with counts of street names.

# ================================================================
# Load the CSV file and prepare
# ================================================================
df = pd.read_csv('BD.csv')
route = 'RUTA 5'
plates = df[df['routeID: Descending'] == route]['busPlate: Descending'].unique()

def process_plate(plate):
    """
    Process GPS data for a specific bus plate: filter, format, group, find closest points, and snap to roads.
    
    Args:
        plate (str): Bus plate number to process.
    
    Returns:
        pd.DataFrame: DataFrame containing the street names.
    """
    # Directly filter without copying the entire DataFrame
    filtered_df = df[(df['routeID: Descending'] == route) & (df['busPlate: Descending'] == plate)]
    formatted_df = format_df(filtered_df)
    grouped_df = group_within_intervals(formatted_df, 4, 120)
    closest_df = closest_points(grouped_df, 3)
    snapped_df = snap_to_roads(closest_df)
    return pd.DataFrame(snapped_df['StreetName'])

# ================================================================
# Use ThreadPoolExecutor to process each plate in parallel
# ================================================================
all_streets = []
with ThreadPoolExecutor(max_workers=4) as executor:
    # Prepare futures and wrap them with tqdm for progress indication
    futures = {executor.submit(process_plate, plate): plate for plate in plates}
    for future in tqdm(as_completed(futures), total=len(plates), desc="Processing plates"):
        all_streets.append(future.result())

# ================================================================
# Concatenate and group street names
# ================================================================
all_streets_df = pd.concat(all_streets)
street_counts = all_streets_df.groupby('StreetName').size().reset_index(name='Counts')

# ================================================================
# Save to CSV
# ================================================================
street_counts.to_csv('Data/street_counts.csv', index=False)
