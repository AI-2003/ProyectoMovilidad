import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import LineString, MultiPoint

def group_points(gdf, precision=4):
    """
    Avoid repetition of coordinates by grouping points with rounded coordinates.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing Point geometries.
        precision (int): Decimal precision for rounding coordinates.
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame with unique rounded coordinates and updated 'Scale' values.
    """
    rounded_gdf = gdf.copy()
    # Extract Latitude and Longitude from geometry and round them
    rounded_gdf['rounded_latitude'] = rounded_gdf.geometry.y.round(precision)
    rounded_gdf['rounded_longitude'] = rounded_gdf.geometry.x.round(precision)
    
    # Group by rounded coordinates to find the first index of each group and count occurrences
    grouped = rounded_gdf.groupby(['rounded_latitude', 'rounded_longitude'])
    first_index = grouped['rounded_latitude'].transform('idxmin')  # Get the index of the first occurrence
    counts = grouped['rounded_latitude'].transform('size')  # Get counts of each group for the 'Scale' calculation
    
    # Select rows that are the first occurrence in each group
    unique_gdf = rounded_gdf.loc[rounded_gdf.index.isin(first_index)].copy()
    
    # Calculate 'Scale' as twice the count of points rounded to that coordinate
    unique_gdf['scale'] = unique_gdf['scale'] * counts.loc[unique_gdf.index]
    
    # Ensure the resulting GeoDataFrame is ordered by the original index (ascending)
    unique_gdf.sort_index(inplace=True)
    return unique_gdf

def closest_points(gdf, check_ahead=10):
    """
    Find the closest point in the next few points to reduce noise and incorrect coordinates.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing Point geometries.
        check_ahead (int): Number of points to look ahead for the closest point.
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame with points selected based on closest proximity.
    """
    points = gdf.geometry
    closer_coords_indexes = [0]  # Starting point
    i = 0
    while i < len(points) - 1:
        # Calculate distances to the next few points defined by check_ahead or up to the end of the array
        next_points_range = slice(i + 1, min(i + 1 + check_ahead, len(points)))
        distances = points[next_points_range].distance(points.iloc[i])
        
        # Find the index of the minimum distance
        i_min_relative = np.argmin(distances)
        i_min = i + 1 + i_min_relative  # Adjust index relative to the entire dataset
        i = i_min  # Update the current index
        
        # Append the new index to the closer coordinates list
        closer_coords_indexes.append(i)
    
    return gdf.iloc[closer_coords_indexes]

def group_within_intervals(gdf, precision, time_interval_s):
    """
    Group points by time interval to avoid repetition of coordinates without losing return route information.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing Point geometries and Time column.
        precision (int): Decimal precision for rounding coordinates.
        time_interval_s (int): Time interval in seconds for grouping points.
    
    Returns:
        gpd.GeoDataFrame: Concatenated GeoDataFrame with points grouped within specified time intervals.
    """
    frames = []
    start_index = 0
    while start_index < len(gdf):
        # Get the limits of the interval
        start_time = gdf.iloc[start_index]['time']
        end_time = start_time + pd.Timedelta(seconds=time_interval_s)
        
        # Subset of points within the current time interval
        time_interval_gdf = gdf[(gdf['time'] >= start_time) & (gdf['time'] <= end_time)].copy()
        if not time_interval_gdf.empty:
            # Group and concat to join time intervals
            frames.append(group_points(time_interval_gdf, precision))
            # Update start_index for the next iteration based on the last index found + 1
            last_index_in_interval = time_interval_gdf.index[-1]
            start_index = last_index_in_interval + 1
        else:
            # If no points found in the interval, increment start_index to try the next point
            start_index += 1
            
    return gpd.GeoDataFrame(pd.concat(frames), crs=gdf.crs)

def clean_gps_data(gdf, rounding_precision, time_diff_threshold, closer_threshold):
    """
    Clean GPS data by grouping points, removing noise, and keeping only the closest points.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing raw GPS data.
        rounding_precision (int): Decimal precision for rounding coordinates.
        time_diff_threshold (int): Time interval in seconds for grouping points.
        closer_threshold (int): Number of points to look ahead for finding the closest point.
    
    Returns:
        gpd.GeoDataFrame: Cleaned GPS data.
    """
    filtered_gdf = gdf.copy()
    filtered_gdf.reset_index(drop=True, inplace=True)
    
    # Group within intervals
    grouped_gdf = group_within_intervals(filtered_gdf, rounding_precision, time_diff_threshold)
    # Uncomment if you want to standarize scales
    # grouped_gdf['scale'] = 2 
    
    # Points by closest in the next registered
    closest_gdf = closest_points(grouped_gdf, closer_threshold)
    
    return closest_gdf

def classify_route_variant(gdf, route_gdf):
    """
    Classify the route variant based on GPS data.
    
    Args:
        gdf (gpd.GeoDataFrame): GeoDataFrame containing GPS data.
        route_gdf (gpd.GeoDataFrame): GeoDataFrame containing official route data.
    
    Returns:
        tuple: Closest route variant (GeoDataFrame row) and the total distance (float).
    """
    # Initialize a dictionary to store the sum of distances for each route variant
    total_distances = {}
    # Calculate distance from each route variant to all points and sum these distances
    for route_index, route_row in route_gdf.iterrows():
        total_distance = 0
        # Sum distances from this route variant to each point
        for _, row in gdf.iterrows():
            distance = route_row.geometry.distance(row.geometry)
            total_distance += distance
        # Store the total distance for this route variant
        total_distances[route_index] = total_distance
    # Determine the route variant with the minimum total distance to all points
    closest_route_index = min(total_distances, key=total_distances.get)
    return route_gdf.loc[closest_route_index]  # Route variant and the deviation measure

def branches_gdf_from_coords(branch_dict):
    """
    Create a GeoDataFrame with 'branch' and 'geometry' columns from a dictionary.
    
    Args:
        branch_dict (dict): Dictionary where each key is a branch number and the value is another dictionary
                            with 'Ida' and 'Vuelta' keys containing lists of coordinate pairs.
    
    Returns:
        gpd.GeoDataFrame: GeoDataFrame with a 'branch' column and a 'geometry' column of LineStrings.
    """
    data = []
    for branch, routes in branch_dict.items():
        # Concatenate coordinates from 'Ida' and 'Vuelta'
        all_coords = routes['Ida'] + routes['Vuelta']
        # Create a LineString or a MultiPoint from the coordinates
        # points = LineString(all_coords)
        points = MultiPoint(all_coords)
        # Append the branch number and LineString geometry to the data list
        data.append({'branch': branch, 'geometry': points})
    # Create a GeoDataFrame from the data list
    gdf = gpd.GeoDataFrame(data, crs="EPSG:4326")  # Assuming WGS84 (latitude/longitude) CRS
    
    return gdf