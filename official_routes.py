import geopandas as gpd
import osmnx as ox
from shapely.geometry import MultiPoint
import json

files_path = "Data/"
routes_filename = files_path+"branches_df.geojson"
directions_filename = files_path+"branches_dir_df.geojson"


# Get the nodes and edges of the city
place_name = "Mexico City, Mexico"
G = ox.graph_from_place(place_name, network_type='drive')

# Get official variants from the pdf files
def openJSONfile(file_path):
    with open(file_path, 'r', encoding="utf-8") as file:
        return json.load(file)    
official_route_5 = openJSONfile('Data/ruta_5.json')


# Transform json info into a pandas gdf for branches
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


# Transform json info into a pandas gdf for branches and directions
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


# Save them to a geojson
official_routes.to_file(routes_filename, driver="GeoJSON")
directions_gdf.to_file(directions_filename, driver="GeoJSON")