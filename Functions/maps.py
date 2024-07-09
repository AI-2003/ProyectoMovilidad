import folium
from folium import plugins
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import nearest_points

# Display points
def plot_points(df, map, with_info=True):
    # Plot each point with a circle marker
    for index, row in df.iterrows():
        if with_info: 
            tooltip = f"Coord: ({row['Latitude']}, {row['Longitude']}), Time: {row['Time']}, Index: {index}"
            scale = row['Scale']
        else: 
            tooltip = ''
            scale = 2
        folium.CircleMarker(
            location=(row['Latitude'], row['Longitude']),
            radius=scale,  
            tooltip=tooltip,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.5
        ).add_to(map)

# Display route
def plot_lines(df, map):
    # Draw lines between points
    locations = df[['Latitude', 'Longitude']].values.tolist()
    folium.PolyLine(locations, color='blue').add_to(map)

# Display route with movement
def plot_ant_path(df, map):
    # Extract the locations from the DataFrame
    locations = df[['Latitude', 'Longitude']].values.tolist()
    # Create the AntPath and add it to the map
    ant_path = plugins.AntPath(locations, color='blue', delay=2000)
    ant_path.add_to(map)

# ===============================
# Display and save functions
        
def map_points(df, file_name, with_info=True):
    # Create a map
    m = folium.Map(location=[df.iloc[0]['Latitude'], df.iloc[0]['Longitude']], zoom_start=13)
    # Plot each point with a circle marker
    plot_points(df, m, with_info)
    m.save(file_name)
    return m

def map_route(df, file_name, with_info=True):
    # Create a map
    m = folium.Map(location=[df.iloc[0]['Latitude'], df.iloc[0]['Longitude']], zoom_start=13)
    # Plot the lines between each pair of coords
    plot_lines(df, m)
    # Plot each point with a circle marker
    plot_points(df, m, with_info)
    m.save(file_name)
    return m

def map_path(df, file_name):
    # Create a map
    m = folium.Map(location=[df.iloc[0]['Latitude'], df.iloc[0]['Longitude']], zoom_start=13)
    # Plot the lines between each pair of coords with movement
    plot_ant_path(df, m)
    m.save(file_name)
    return m

def plot_nearest_points_lines(filtered_df, closest_route_variant, m):
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
    

def comparing_map(filtered_df, closest_route_variant, file_name, title='Comparing Map'):
    # Initialize a folium map
    # Use the first point from filtered_df as the center for the folium map
    map_center = [filtered_df.iloc[0]['Latitude'], filtered_df.iloc[0]['Longitude']]
    m = folium.Map(location=map_center, zoom_start=14)
    plot_nearest_points_lines(filtered_df, closest_route_variant, m)
    for point in closest_route_variant.geometry.geoms:
        folium.CircleMarker(
            location=(point.y, point.x),  # Convert (lon, lat) to (lat, lon)
            radius=2,
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
            radius=2,
            color='blue',
            fill=True,
            fill_color='blue',
            fill_opacity=0.7,
            popup='Filtered_df Point',
            tooltip=tooltip
        ).add_to(m)
    # Add a title to the map
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; 
                background-color: white; z-index:9999; font-size:15px;
                border:2px solid grey; padding: 10px;">
        <b>{title}%</b>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    # Add a legend to the map
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; 
                background-color: white; z-index:9999; font-size:14px;
                border:2px solid grey; padding: 10px;">
        <i class="fa fa-circle" style="color:red"></i> Nodos de la variante predicha<br>
        <i class="fa fa-circle" style="color:blue"></i> Registros GPS (filtrados)<br>
        <i class="fa fa-minus" style="color:green"></i> Conexión entre datos GPS y punto más cercano de la variante predicha 
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    # Save and return the map
    m.save(file_name)
    return m