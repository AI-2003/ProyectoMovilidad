import geopandas as gpd
import osmnx as ox
from shapely.geometry import MultiPoint
import json

# ================================================================
# Overview
# ================================================================
# This script processes official route data for Mexico City, transforms it into GeoDataFrames,
# and saves the resulting data as GeoJSON files. It extracts node information from a JSON file,
# constructs geometries using OSMnx, and categorizes route segments by branch and direction.

# ================================================================
# Paths to files and initial values
# Change these to fit your needs
# ================================================================
files_path = "Data/"
routes_filename = files_path + "branches_df.geojson"  # Path to save branches GeoJSON file
directions_filename = files_path + "branches_dir_df.geojson"  # Path to save branches with directions GeoJSON file

# Get the nodes and edges of the city
place_name = "Mexico City, Mexico"
G = ox.graph_from_place(place_name, network_type='drive')

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

# Load the official route JSON file
official_route_5 = open_json_file('Data/ruta_5.json')

# ================================================================
# Transform JSON info into a GeoDataFrame for branches
# ================================================================
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
# Transform JSON info into a GeoDataFrame for branches and directions
# ================================================================
rows = []
for branch, directions in official_route_5.items():
    for direction, types in directions.items():
        all_lines = []
        for line_type in ['confirmada', 'hueco', 'inconfirmada']:
            for segment in types[line_type]:
                points = [(G.nodes[i]['x'], G.nodes[i]['y']) for i in segment]
                all_lines.extend(points)
        geometry = MultiPoint(all_lines)
        rows.append({'Branch': branch, 'Direction': direction, 'geometry': geometry})
# Create GeoDataFrame
directions_gdf = gpd.GeoDataFrame(rows, columns=['Branch', 'Direction', 'geometry'])

# ================================================================
# Save the GeoDataFrames to GeoJSON files
# ================================================================
official_routes.to_file(routes_filename, driver="GeoJSON")
directions_gdf.to_file(directions_filename, driver="GeoJSON")
