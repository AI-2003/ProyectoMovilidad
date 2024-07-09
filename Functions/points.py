import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
import geopandas as gpd
import osmnx as ox
from shapely.geometry import Point
import json
import folium
import networkx as nx
from collections import OrderedDict


# Avoid repetition of coordinates
def group_points(df, precision=4):
    rounded_df = df.copy()
    # Add rounded coordinates directly to the original DataFrame to preserve index
    rounded_df['RoundedLatitude'] = rounded_df['Latitude'].round(precision)
    rounded_df['RoundedLongitude'] = rounded_df['Longitude'].round(precision)
    # Group by rounded coordinates to find the first index of each group and count occurrences
    grouped = rounded_df.groupby(['RoundedLatitude', 'RoundedLongitude'])
    first_index = grouped['Latitude'].transform('idxmin')  # Get the index of the first occurrence
    counts = grouped['Latitude'].transform('size')  # Get counts of each group for the 'Scale' calculation
    # Select rows that are the first occurrence in each group
    unique_df = rounded_df.loc[rounded_df.index.isin(first_index)].copy()
    # Calculate 'Scale' as twice the count of points rounded to that coordinate
    unique_df['Scale'] = unique_df['Scale'] * counts.loc[unique_df.index]
    # Ensure the resulting DataFrame is ordered by the original index (ascending)
    unique_df.sort_index(inplace=True)
    return unique_df

# Find the closest point in the next check_ahead points
# Helps to lose noise and trash coordinates
def closest_points(df, check_ahead=10):
    latitudes = df['Latitude'].to_numpy()
    longitudes = df['Longitude'].to_numpy()
    closer_coords_indexes = [0] # Starting point
    # Start search
    i = 0
    while i<len(latitudes)-1:
        # Calculate distances to the next few points defined by check_ahead or up to the end of the array
        next_points_range = slice(i+1, min(i+1+check_ahead, len(latitudes)))
        lat_diff = latitudes[next_points_range] - latitudes[i]
        lon_diff = longitudes[next_points_range] - longitudes[i]
        # Calculate the Euclidean distance
        distances = np.sqrt(lat_diff**2 + lon_diff**2)
        # Find the index of the minimum distance
        i_min_relative = np.argmin(distances)
        i_min = i + 1 + i_min_relative  # Adjust index relative to the entire dataset
        i = i_min  # Update the current index
        # Append the new index to the closer coordinates list
        closer_coords_indexes.append(i)
    return df.iloc[closer_coords_indexes]

# Group by time interval to avoid repetition of coordinates without losing information of the return route
def group_within_intervals(df, precision, time_interval_s):
    frames =[]
    start_index = 0
    while start_index < len(df):
        # Get the limits of the interval
        start_time = df.iloc[start_index]['Time']
        end_time = start_time + pd.Timedelta(seconds=time_interval_s)
        # Subset of points within the current time interval
        time_interval_df = df[(df['Time'] >= start_time) & (df['Time'] <= end_time)].copy()
        if not time_interval_df.empty:
            # Group and concat to join time intervals
            frames.append(group_points(time_interval_df, precision))
            # Update start_index for the next iteration based on the last index found + 1
            last_index_in_interval = time_interval_df.index[-1]
            start_index = last_index_in_interval + 1
        else:
            # If no points found in the interval, increment start_index to try the next point
            start_index += 1
    return pd.concat(frames)

# Fit points to nearest road
def snap_to_roads(df, osrm_server_url='http://router.project-osrm.org'):
    # Create a copy of the DataFrame to avoid modifying the original
    snapped_df = df.copy()
    plate = df['Plate'][0]
    
    # Prepare an empty list for street names
    street_names = []
    
    # Wrap the iteration with tqdm for a progress bar
    for index, row in tqdm(snapped_df.iterrows(), total=len(snapped_df), desc=f"Plate {plate}: Snapping to roads"):
        # Construct the OSRM API request URL
        request_url = f"{osrm_server_url}/nearest/v1/driving/{row['Longitude']},{row['Latitude']}?number=1"
        
        # Make the request to the OSRM server
        response = requests.get(request_url)
        data = response.json()
        
        # Check if the request was successful and a nearest road was found
        if response.status_code == 200 and data['waypoints']:
            nearest_waypoint = data['waypoints'][0]
            # Update the coordinates with the snapped location
            snapped_df.at[index, 'Latitude'] = nearest_waypoint['location'][1]
            snapped_df.at[index, 'Longitude'] = nearest_waypoint['location'][0]
            
            # Attempt to retrieve the street name if available
            street_name = nearest_waypoint.get('name', 'Unknown')
            street_names.append(street_name)
        else:
            # If no road found, keep the original coordinates and use a placeholder for the street name
            street_names.append('Unknown')
    
    # Add the 'StreetName' column to the DataFrame
    snapped_df['StreetName'] = street_names
    
    return snapped_df



# Given a df wiht Latitude and Longitude columns, it gives back the predicted variant of the route that it represents
def classify_route_variant(df, route_df):
    if len(df['Route'].unique()) > 1:
        print("Invalid dataframe, it contains information on more than one route")
        return None
    else:
        # Convert filtered_df to a GeoDataFrame with Point geometries
        gdf_points = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df.Longitude, df.Latitude)], crs="EPSG:4326")
        # Ensure route_df is correctly set as a GeoDataFrame and has the correct CRS
        if not route_df.crs:
            route_df = route_df.set_crs("EPSG:4326")
        # Initialize a dictionary to store the sum of distances for each route variant and the nearest points
        total_distances = {}
        # Calculate distance from each route variant to all points and sum these distances
        for route_index, route_row in route_df.iterrows():
            total_distance = 0
            # Sum distances from this route variant to each point
            for _, row in gdf_points.iterrows():
                distance = route_row.geometry.distance(row.geometry)
                total_distance += distance
            # Store the total distance for this route variant
            total_distances[route_index] = total_distance
        # Determine the route variant with the minimum total distance to all points
        closest_route_index = min(total_distances, key=total_distances.get)
        return route_df.loc[closest_route_index], total_distances[closest_route_index] # Route variant and the deviation measure


    
def deviation_from_route(empiric_df, route_df):
    gdf_points = gpd.GeoDataFrame(empiric_df, geometry=[Point(xy) for xy in zip(empiric_df.Longitude, empiric_df.Latitude)], crs="EPSG:4326")
    total_distance = 0
    for _, row in gdf_points.iterrows():
        distance = route_df.geometry.distance(row.geometry)
        total_distance += distance
    return total_distance

def clean_gps_data(df, rounding_precision, time_diff_threshold, closer_threshold):
    filtered_df = df.copy()
    filtered_df.reset_index(drop=True, inplace=True)
    # Grouped within intervals
    grouped_df = group_within_intervals(filtered_df, rounding_precision, time_diff_threshold)
    grouped_df['Scale'] = 2
    # Points by closest in the next registered
    closest_df = closest_points(grouped_df, closer_threshold)
    return closest_df



# ==========================================================
# Harry's code
# Provides official route extracted from the pdfs
# ==========================================================

def coords(ruta, G):
  ordered_dict = OrderedDict()

  for sub_array in ruta:
      for element in sub_array:
          if element not in ordered_dict:
              ordered_dict[element] = None

  ruta = list(ordered_dict.keys())

  coords = []

  for n in ruta:
    data = G.nodes[n]
    coords.append((data['y'], data['x']))

  return coords

