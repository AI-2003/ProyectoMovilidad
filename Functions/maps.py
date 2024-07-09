import folium
from folium import plugins
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import nearest_points

def plot_points(df, map, with_info=True):
    """
    Display points on a folium map with optional tooltips.
    
    Args:
        df (pd.DataFrame): DataFrame containing Latitude, Longitude, Time, and Scale columns.
        map (folium.Map): Folium map object to plot the points on.
        with_info (bool): If True, display tooltips with information; if False, display plain markers.
    
    Returns:
        None
    """
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

def plot_lines(df, map):
    """
    Display lines connecting points on a folium map.
    
    Args:
        df (pd.DataFrame): DataFrame containing Latitude and Longitude columns.
        map (folium.Map): Folium map object to plot the lines on.
    
    Returns:
        None
    """
    locations = df[['Latitude', 'Longitude']].values.tolist()
    folium.PolyLine(locations, color='blue').add_to(map)

def plot_ant_path(df, map):
    """
    Display an animated path on a folium map using AntPath.
    
    Args:
        df (pd.DataFrame): DataFrame containing Latitude and Longitude columns.
        map (folium.Map): Folium map object to plot the animated path on.
    
    Returns:
        None
    """
    locations = df[['Latitude', 'Longitude']].values.tolist()
    ant_path = plugins.AntPath(locations, color='blue', delay=2000)
    ant_path.add_to(map)

def map_points(df, file_name, with_info=True):
    """
    Create a map displaying points and save it to a file.
    
    Args:
        df (pd.DataFrame): DataFrame containing Latitude, Longitude, Time, and Scale columns.
        file_name (str): Path to save the generated map.
        with_info (bool): If True, display tooltips with information; if False, display plain markers.
    
    Returns:
        folium.Map: Folium map object with the plotted points.
    """
    m = folium.Map(location=[df.iloc[0]['Latitude'], df.iloc[0]['Longitude']], zoom_start=13)
    plot_points(df, m, with_info)
    m.save(file_name)
    return m

def map_route(df, file_name, with_info=True):
    """
    Create a map displaying a route with points and save it to a file.
    
    Args:
        df (pd.DataFrame): DataFrame containing Latitude, Longitude, Time, and Scale columns.
        file_name (str): Path to save the generated map.
        with_info (bool): If True, display tooltips with information; if False, display plain markers.
    
    Returns:
        folium.Map: Folium map object with the plotted route and points.
    """
    m = folium.Map(location=[df.iloc[0]['Latitude'], df.iloc[0]['Longitude']], zoom_start=13)
    plot_lines(df, m)
    plot_points(df, m, with_info)
    m.save(file_name)
    return m

def map_path(df, file_name):
    """
    Create a map displaying an animated path and save it to a file.
    
    Args:
        df (pd.DataFrame): DataFrame containing Latitude and Longitude columns.
        file_name (str): Path to save the generated map.
    
    Returns:
        folium.Map: Folium map object with the plotted animated path.
    """
    m = folium.Map(location=[df.iloc[0]['Latitude'], df.iloc[0]['Longitude']], zoom_start=13)
    plot_ant_path(df, m)
    m.save(file_name)
    return m

def plot_nearest_points_lines(filtered_df, closest_route_variant, m):
    """
    Plot lines between pairs of closest points of GPS and official route data.
    
    Args:
        filtered_df (pd.DataFrame): Filtered GPS data.
        closest_route_variant (gpd.GeoDataFrame row): Closest route variant GeoDataFrame row.
        m (folium.Map): Folium map object to plot the lines on.
    
    Returns:
        None
    """
    gdf_points = gpd.GeoDataFrame(filtered_df, geometry=[Point(xy) for xy in zip(filtered_df.Longitude, filtered_df.Latitude)], crs="EPSG:4326")
    for _, point_row in gdf_points.iterrows():
        nearest_geom = nearest_points(point_row.geometry, closest_route_variant.geometry)
        point_coords = (nearest_geom[0].y, nearest_geom[0].x)
        nearest_point_coords = (nearest_geom[1].y, nearest_geom[1].x)
        folium.PolyLine([point_coords, nearest_point_coords], color='green').add_to(m)

def comparing_map(filtered_df, closest_route_variant, file_name, title='Comparing Map'):
    """
    Create a map comparing filtered GPS data with the closest route variant, including lines between closest points.
    
    Args:
        filtered_df (pd.DataFrame): Filtered GPS data.
        closest_route_variant (gpd.GeoDataFrame row): Closest route variant GeoDataFrame row.
        file_name (str): Path to save the generated map.
        title (str): Title to display on the map.
    
    Returns:
        folium.Map: Folium map object with the comparison data.
    """
    map_center = [filtered_df.iloc[0]['Latitude'], filtered_df.iloc[0]['Longitude']]
    m = folium.Map(location=map_center, zoom_start=14)
    plot_nearest_points_lines(filtered_df, closest_route_variant, m)
    for point in closest_route_variant.geometry.geoms:
        folium.CircleMarker(
            location=(point.y, point.x),
            radius=2,
            color='red',
            fill=True,
            fill_color='red',
            fill_opacity=0.3,
            popup='Route Variant Point'
        ).add_to(m)
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
    title_html = f'''
    <div style="position: fixed; 
                top: 10px; left: 50px; 
                background-color: white; z-index:9999; font-size:15px;
                border:2px solid grey; padding: 10px;">
        <b>{title}%</b>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
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
    m.save(file_name)
    return m
