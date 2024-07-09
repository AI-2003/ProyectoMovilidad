import pandas as pd
import geopandas as gpd
import osmnx as ox
from shapely.geometry import MultiPoint, Point
from shapely.ops import nearest_points
import json
import folium

# ================================================================
# Paths to files and initial values
# Change these to fit your needs
# ================================================================
file_path = "Data/ruta5.csv"
ruta_5_json_path = "Data/ruta_5.json"
map_path = 'Maps/comparing_map.html'

route = 'RUTA 5'
plate = int('0050173')
startTime = '2023-02-27 00:00:00'
endTime = '2023-02-27 23:59:59'



# ================================================================
# Functions for the main code
# ================================================================

# Used to have a standar across the code
def renameColumns(df):
    df.rename(columns={'timestamp': 'Time', 'placa': 'Plate', 'ruta': 'Route', 'latitud': 'Latitude', 'longitud': 'Longitude'}, inplace=True)
    return df

# Only get the info you want from the whole df
def filter_and_format_df(df, route, initialScale, plate, receivedStartTime, receivedEndTime):
    filtered_df = df.copy()
    filtered_df = renameColumns(filtered_df)
    # Convert 'Time' to datetime
    filtered_df['Time'] = pd.to_datetime(filtered_df['Time'])
    # Filter DataFrame to match conditions
    filtered_df = filtered_df[(filtered_df['Route'] == route) ]#&
                              #(filtered_df['Plate'] == plate) &
                              #(filtered_df['Time'] >= pd.to_datetime(receivedStartTime)) &
                              #(filtered_df['Time'] <= pd.to_datetime(receivedEndTime))]
    # Reset the index of filtered_df to ensure sequential indexing after filtering
    filtered_df.reset_index(drop=True, inplace=True)
    # Set scale (useful when plotting in folium)
    filtered_df['Scale'] = initialScale
    return filtered_df

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

# Plot the lines between pairs of closest points of gps and official route data
def plot_nearest_points(filtered_df, closest_route_variant, m):
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

# Plot the gps data and the predicted branch
def comparing_map(filtered_df, closest_route_variant, file_name):
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

# Simple function to open a json path
def openJSONfile(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return json.load(file)    



# ================================================================
# Get untreated data
# ================================================================
# Load the CSV file
df = pd.read_csv(file_path)
# Get the nodes and edges of the city
place_name = "Mexico City, Mexico"
G = ox.graph_from_place(place_name, network_type='drive')



# ================================================================
# Get the gps data for a certain bus on a certain time interval
# ================================================================
# Simple points
empiric_df = filter_and_format_df(df, route, plate, startTime, endTime, 2)



# ================================================================
# Get the official route's info
# This is achieved by retrievieng the nodes Harry got
# ================================================================
# Get official variants from the pdf files
official_route_5 = openJSONfile(ruta_5_json_path)
# Transform json info into a pandas gdf
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



# ================================================================
# Predict what route branch the bus was following on that day
# ================================================================
# Clasify into one of the route's branches and get the simple measure of deviation
closest_route_variant, sum_of_distances = classify_route_variant(empiric_df, official_routes)
# Comparation Map
map = comparing_map(empiric_df, closest_route_variant, map_path)

# ================================================================
# Print useful info
# ================================================================
print(f'The predicted followed branch was {closest_route_variant["Branch"]}')
print(f'The deviation is {sum_of_distances}')