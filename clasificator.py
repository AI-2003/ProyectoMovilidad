import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import MultiPoint, Point
from shapely.ops import nearest_points
import json
import folium

# ================================================================
# Overview
# ================================================================
# This script processes GPS data for a specific bus route, cleans the data, and compares it with official route 
# data to determine the closest route variant. It then generates a map that visually compares the GPS data 
# with the predicted route variant and calculates the deviation. The results are displayed on a folium map 
# and saved to a file.

# ================================================================
# Paths to files and initial values
# Change these to fit your needs
# ================================================================
file_path = "Data/ruta5.csv"  # Path to the CSV file containing the GPS data
ruta_5_json_path = "Data/ruta_5.json"  # Path to the JSON file containing the official route data
map_path = 'Maps/comparing_map.html'  # Path where the map will be saved

route = 'RUTA 5'  # Route identifier
plate = int('0050173')  # Plate number of the bus
startTime = '2023-02-27 00:00:00'  # Start time for filtering the data
endTime = '2023-02-27 23:59:59'  # End time for filtering the data

# ================================================================
# Functions for the main code
# ================================================================

def rename_columns(df):
    """
    Rename columns for standardization.
    
    Args:
        df (pd.DataFrame): DataFrame with original column names.
    
    Returns:
        pd.DataFrame: DataFrame with renamed columns.
    """
    df.rename(columns={'timestamp': 'Time', 'placa': 'Plate', 'ruta': 'Route', 'latitud': 'Latitude', 'longitud': 'Longitude'}, inplace=True)
    return df

def filter_and_format_df(df, route, plate, received_start_time, received_end_time, initial_scale):
    """
    Filter and format DataFrame based on specified conditions.
    
    Args:
        df (pd.DataFrame): Original DataFrame.
        route (str): Route identifier to filter by.
        plate (int): Plate number to filter by.
        received_start_time (str): Start time for filtering.
        received_end_time (str): End time for filtering.
        initial_scale (int): Initial scale value to add to the DataFrame (used for plotting).
    
    Returns:
        pd.DataFrame: Filtered and formatted DataFrame.
    """
    filtered_df = df.copy()
    filtered_df = rename_columns(filtered_df)
    # Convert 'Time' to datetime
    filtered_df['Time'] = pd.to_datetime(filtered_df['Time'])
    # Filter DataFrame to match conditions
    filtered_df = filtered_df[(filtered_df['Route'] == route) &
                              (filtered_df['Plate'] == plate) &
                              (filtered_df['Time'] >= pd.to_datetime(received_start_time)) &
                              (filtered_df['Time'] <= pd.to_datetime(received_end_time))]
    # Reset the index of filtered_df to ensure sequential indexing after filtering
    filtered_df.reset_index(drop=True, inplace=True)
    # Set scale (useful when plotting in folium)
    filtered_df['Scale'] = initial_scale
    return filtered_df

def classify_route_variant(df, route_df):
    """
    Classify the route variant based on GPS data.
    
    Args:
        df (pd.DataFrame): DataFrame containing GPS data.
        route_df (gpd.GeoDataFrame): GeoDataFrame containing official route's variations.
    
    Returns:
        tuple: Closest route variant (GeoDataFrame row) and the total distance (float).
    """
    if len(df['Route'].unique()) > 1:
        print("Invalid DataFrame, it contains information on more than one route")
        return None
    else:
        # Convert filtered_df to a GeoDataFrame with Point geometries
        gdf_points = gpd.GeoDataFrame(df, geometry=[Point(xy) for xy in zip(df.Longitude, df.Latitude)], crs="EPSG:4326")
        # Ensure route_df is correctly set as a GeoDataFrame and has the correct CRS
        if not route_df.crs:
            route_df = route_df.set_crs("EPSG:4326")
        # Initialize a dictionary to store the sum of distances for each route variant
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
        return route_df.loc[closest_route_index], total_distances[closest_route_index]  # Route variant and the deviation measure

def plot_nearest_points(filtered_df, closest_route_variant, m):
    """
    Plot the lines between pairs of closest points of GPS and official route data.
    
    Args:
        filtered_df (pd.DataFrame): Filtered GPS data.
        closest_route_variant (gpd.GeoDataFrame row): Closest route variant GeoDataFrame row.
        m (folium.Map): Folium map object to plot the lines on.
    """
    # Convert filtered_df to a GeoDataFrame with Point geometries
    gdf_points = gpd.GeoDataFrame(filtered_df, geometry=[Point(xy) for xy in zip(filtered_df.Longitude, filtered_df.Latitude)], crs="EPSG:4326")
    # Extract the coordinates of the nearest points
    for _, point_row in gdf_points.iterrows():
        # Find the nearest points on both geometries
        nearest_geom = nearest_points(point_row.geometry, closest_route_variant.geometry)
        point_coords = (nearest_geom[0].y, nearest_geom[0].x)
        nearest_point_coords = (nearest_geom[1].y, nearest_geom[1].x)
        # Create a green line between the point and the nearest point on the route
        folium.PolyLine([point_coords, nearest_point_coords], color='green').add_to(m)

def comparing_map(filtered_df, closest_route_variant, file_name):
    """
    Plot the GPS data and the predicted branch on a folium map.
    
    Args:
        filtered_df (pd.DataFrame): Filtered GPS data.
        closest_route_variant (gpd.GeoDataFrame row): Closest route variant GeoDataFrame row.
        file_name (str): File name to save the map as.
    
    Returns:
        folium.Map: Folium map object with the plotted data.
    """
    # Initialize a folium map
    # Use the first point from filtered_df as the center for the folium map
    map_center = [filtered_df.iloc[0]['Latitude'], filtered_df.iloc[0]['Longitude']]
    m = folium.Map(location=map_center, zoom_start=14)
    for point in closest_route_variant.geometry.geoms:
        folium.CircleMarker(
            location=(point.y, point.x),  # Convert (lon, lat) to (lat, lon)
            radius=3,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.3,
            popup='Route Variant Point'
        ).add_to(m)
    # Plot points from filtered_df
    for _, row in filtered_df.iterrows():
        tooltip = f"Coord: ({row['Latitude']}, {row['Longitude']}), Time: {row['Time']}"
        folium.CircleMarker(
            location=(row['Latitude'], row['Longitude']),
            radius=3,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.7,
            popup='Filtered_df Point',
            tooltip=tooltip
        ).add_to(m)
    plot_nearest_points(filtered_df, closest_route_variant, m)
    # Save and return the map
    m.save(file_name)
    return m

def open_json_file(file_path):
    """
    Simple function to open a JSON file.
    
    Args:
        file_path (str): Path to the JSON file.
    
    Returns:
        dict: Parsed JSON data.
    """
    with open(file_path, 'r', encoding="utf-8") as file:
        return json.load(file)    

# ================================================================
# Main code execution
# ================================================================

# Load the CSV file
df = pd.read_csv(file_path)

# Get the nodes and edges of the city
place_name = "Mexico City, Mexico"
G = ox.graph_from_place(place_name, network_type='drive')

# Get the GPS data for a certain bus on a certain time interval
empiric_df = filter_and_format_df(df, route, plate, startTime, endTime, 2)

# Get the official route's info
official_route_5 = open_json_file(ruta_5_json_path)

# Transform JSON info into a pandas GeoDataFrame
rows = []
for branch, directions in official_route_5.items():
    all_lines = []
    for direction, types in directions.items():
        for line_type in ['confirmada', 'hueco', 'inconfirmada']:
            for segment in types[line_type]:
                points = [(G.nodes[i]['x'], G.nodes[i]['y']) for i in segment]
                all_lines.extend(points)
    geometry = MultiPoint(all_lines)
    rows.append({'Branch': branch, 'geometry': geometry})

# Create GeoDataFrame
official_routes = gpd.GeoDataFrame(rows, columns=['Branch', 'geometry'])

# Predict what route branch the bus was following on that day
closest_route_variant, sum_of_distances = classify_route_variant(empiric_df, official_routes)

# Create comparison map
map = comparing_map(empiric_df, closest_route_variant, map_path)

# Print useful information
print(f'The predicted followed branch was {closest_route_variant["Branch"]}')
print(f'The deviation is {sum_of_distances}')
