import numpy as np
import requests
import osmnx as ox
import json
import itertools
from shapely.geometry import Point

# ================================================================
# Overview
# ================================================================
# This script processes geographical data to find and analyze streets in Mexico City. It uses OSMnx to obtain
# nodes and edges of the city's road network, then uses functions to search for streets by name, extract points
# from geometries, and find the closest points between two streets. The script also reads street names from a JSON file
# to process specific routes.

# =======================================================
# Function to get the edges rows that correspond to the streets with similar name to street_name
def get_street(street_name, edges_gdf):
    """
    Search for streets by name using the Nominatim API and filter edges GeoDataFrame.
    
    Args:
        street_name (str): Name of the street to search for.
        edges_gdf (GeoDataFrame): GeoDataFrame containing the edges of the city's road network.
    
    Returns:
        GeoDataFrame: Filtered GeoDataFrame with edges that have similar names to the given street name.
    """
    # Use Nominatim API as search engine
    url = f"https://nominatim.openstreetmap.org/search?street={street_name}&format=json&city=Mexico City"
    # Make the request
    response = requests.get(url)
    if response.status_code == 200:
        results = response.json()
        if len(results) == 0:
            print(f'No streets found with name {street_name}')
            return None
    else:
        print(f'Something failed in the request for {street_name}')
        return None
    # Filter edges_gdf
    unique_names = list(set([result['name'] for result in results]))
    return edges_gdf[edges_gdf['name'].isin(unique_names)]

# =======================================================
# Function to get the points inside a linestring
def flatten_linestring_to_points(gdf):
    """
    Extract all points from MultiLineString geometries in a GeoDataFrame.
    
    Args:
        gdf (GeoDataFrame): GeoDataFrame containing MultiLineString geometries.
    
    Returns:
        list: List of Point objects extracted from the MultiLineString geometries.
    """
    points_list = []
    for geom in gdf.geometry:
        points_list.extend([Point(pt) for pt in geom.coords])
    return points_list

# =======================================================
# Function to get the closest two points between two streets
def get_closest_points(street1_gdf, street2_gdf):
    """
    Find the closest pair of points between two streets.
    
    Args:
        street1_gdf (GeoDataFrame): GeoDataFrame containing the first street's geometries.
        street2_gdf (GeoDataFrame): GeoDataFrame containing the second street's geometries.
    
    Returns:
        tuple: Pair of Point objects representing the closest points between the two streets.
    """
    points_street1 = flatten_linestring_to_points(street1_gdf)
    points_street2 = flatten_linestring_to_points(street2_gdf)
    # Calculate distances between each pair of points and find the pair with the minimum distance
    min_distance = np.inf
    closest_pair = (None, None)
    for point1, point2 in itertools.product(points_street1, points_street2):
        distance = point1.distance(point2)
        if distance < min_distance:
            min_distance = distance
            closest_pair = (point1, point2)
    return closest_pair

# =======================================================
# Get nodes and edges
ox.config(use_cache=True, log_console=True)
place_name = "Mexico City, Mexico"
G = ox.graph_from_place(place_name, network_type='drive')
nodes_gdf, edges_gdf = ox.graph_to_gdfs(G)

# =======================================================
# Start processing info
ruta = 'RUTA 5'
trip = 0
direction = 'ida'

# Get the list of street names from the JSON file
filename = f'Data/CallesRutas/{ruta}.json'
with open(filename, 'r') as file:
    street_names = json.load(file)[trip][direction] 
if len(street_names) == 0:
    raise Exception("Something failed")
