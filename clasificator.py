import numpy as np
import pandas as pd
import requests
from tqdm import tqdm
import geopandas as gpd
import osmnx as ox
import folium
from Functions.prepping import *
from Functions.maps import *
from Functions.points import *





# Load the CSV file
file_name = 'Data/BD.csv'
df = pd.read_csv(file_name)

# ================
# Evaluations

# Initial values
route = 'RUTA 5'
plate = '0050034'
startTime = '2023-09-12 07:00:00'
endTime = '2023-09-12 09:00:00'
rounding_precision = 4
closer_threshold = 3
time_diff_threshold = 120

# Simple points
empiric_df = filter_and_format_df(df, route, plate, startTime, endTime, 2)

# Official route
closest_route_variant = clasify_route_variant(empiric_df)

# Comparation Map
map = comparing_map(empiric_df, closest_route_variant, 'Maps/comparing_map.html')

# Simple measure of deviation
sum_of_distances = deviation_from_route(empiric_df, closest_route_variant)

print(sum_of_distances)