import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from Functions.prepping import *
from Functions.maps import *
from Functions.points import *

# Load the CSV file and prepare
df = pd.read_csv('BD.csv')
route = 'RUTA 5'
plates = df[df['routeID: Descending'] == route]['busPlate: Descending'].unique()

def process_plate(plate):
    # Directly filter without copying the entire DataFrame
    filtered_df = df[(df['routeID: Descending'] == route) & (df['busPlate: Descending'] == plate)]
    formatted_df = format(filtered_df)
    grouped_df = group_within_intervals(formatted_df, 4, 120)
    closest_df = closest_points(grouped_df, 3)
    snapped_df = snap_to_roads(closest_df)
    return pd.DataFrame(snapped_df['StreetName'])

# Use ThreadPoolExecutor to process each plate in parallel
all_streets = []
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [executor.submit(process_plate, plate) for plate in plates]
    for future in as_completed(futures):
        all_streets.append(future.result())

# Concatenate and group
all_streets_df = pd.concat(all_streets)
street_counts = all_streets_df.groupby('StreetName').size().reset_index(name='Counts')

# Save to CSV
street_counts.to_csv('Data/street_counts.csv', index=False)