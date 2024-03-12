import numpy as np
import pandas as pd
import requests

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
        start_time = df.iloc[start_index]['receivedtime: Descending']
        end_time = start_time + pd.Timedelta(seconds=time_interval_s)
        # Subset of points within the current time interval
        time_interval_df = df[(df['receivedtime: Descending'] >= start_time) & (df['receivedtime: Descending'] <= end_time)].copy()
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
    total = len(snapped_df)
    # Prepare an empty list for street names
    street_names = []
    progress=0
    for index, row in snapped_df.iterrows():
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
        print(progress,'/', total)
        progress+=1
    print('100%')
    # Add the 'StreetName' column to the DataFrame
    snapped_df['StreetName'] = street_names
    return snapped_df