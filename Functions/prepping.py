import pandas as pd

# Standarize naming
def renameColumns(df):
    df.rename(columns={'timestamp': 'Time', 'placa': 'Plate', 'ruta': 'Route', 'latitud': 'Latitude', 'longitud': 'Longitude'}, inplace=True)
    return df

# Correct datatypes and filter to needs
def filter_and_format_df(df, route, plate, receivedStartTime, receivedEndTime, initialScale):
    filtered_df = df.copy()
    filtered_df = renameColumns(filtered_df)
    # Convert 'Time' to datetime
    filtered_df['Time'] = pd.to_datetime(filtered_df['Time'])
    # Filter DataFrame to match conditions
    filtered_df = filtered_df[(filtered_df['Route'] == route) &
                              (filtered_df['Plate'] == plate) &
                              (filtered_df['Time'] >= pd.to_datetime(receivedStartTime)) &
                              (filtered_df['Time'] <= pd.to_datetime(receivedEndTime))]
    # Reset the index of filtered_df to ensure sequential indexing after filtering
    filtered_df.reset_index(drop=True, inplace=True)
    # Set scale
    filtered_df['Scale'] = initialScale
    return filtered_df

# Function to format the DataFrame, adapting to the new structure
def format_df(df, initialScale=2):
    formatted_df = df.copy()
    formatted_df = renameColumns(formatted_df)
    # Convert 'Time' to datetime
    formatted_df['Time'] = pd.to_datetime(formatted_df['Time'])
    # Reset the index of formatted_df to ensure sequential indexing after filtering
    formatted_df.reset_index(drop=True, inplace=True)
    # Set scale
    formatted_df['Scale'] = initialScale
    return formatted_df
