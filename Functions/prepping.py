import pandas as pd

# Function to parse coordinates
def parse_coordinates(coord_str):
    x, y = coord_str.split(", ")
    return float(x), float(y)

# Filter and format the df
def filter_and_format_df(df, route, plate, receivedStartTime, receivedEndTime, initialScale):
    filtered_df = df.copy()
    # Convert 'receivedtime: Descending' to datetime
    filtered_df['receivedtime: Descending'] = pd.to_datetime(filtered_df['receivedtime: Descending'])
    # Filter DataFrame to match conditions
    filtered_df = filtered_df[(filtered_df['routeID: Descending'] == route) &
                        (filtered_df['busPlate: Descending'] == plate) &
                        (filtered_df['receivedtime: Descending'] >= pd.to_datetime(receivedStartTime)) &
                        (filtered_df['receivedtime: Descending'] <= pd.to_datetime(receivedEndTime))]
    # Reset the index of filtered_df to ensure sequential indexing after filtering
    filtered_df.reset_index(drop=True, inplace=True)
    # Parse and round coordinates based on the provided precision
    coords = filtered_df['Coordenadas: Descending'].apply(lambda x: pd.Series(parse_coordinates(x), index=['Latitude', 'Longitude']))
    filtered_df['Latitude'] = coords['Latitude']
    filtered_df['Longitude'] = coords['Longitude']
    filtered_df['Scale'] = initialScale
    return filtered_df
