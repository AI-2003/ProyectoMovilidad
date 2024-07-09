import pandas as pd

def renameColumns(df):
    """
    Standardize column names in the DataFrame.
    
    Args:
        df (pd.DataFrame): Original DataFrame with column names to be renamed.
    
    Returns:
        pd.DataFrame: DataFrame with standardized column names.
    """
    df.rename(columns={
        'timestamp': 'Time',
        'placa': 'Plate',
        'ruta': 'Route',
        'latitud': 'Latitude',
        'longitud': 'Longitude'
    }, inplace=True)
    return df

def filter_and_format_df(df, route, plate, receivedStartTime, receivedEndTime, initialScale):
    """
    Filter and format the DataFrame based on specified conditions.
    
    Args:
        df (pd.DataFrame): Original DataFrame.
        route (str): Route identifier to filter by.
        plate (str): Plate number to filter by.
        receivedStartTime (str): Start time for filtering.
        receivedEndTime (str): End time for filtering.
        initialScale (int): Initial scale value to add to the DataFrame (used for plotting).
    
    Returns:
        pd.DataFrame: Filtered and formatted DataFrame.
    """
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

def format_df(df, initialScale=2):
    """
    Format the DataFrame by standardizing column names, converting data types, and setting scale.
    
    Args:
        df (pd.DataFrame): Original DataFrame.
        initialScale (int): Initial scale value to add to the DataFrame (used for plotting).
    
    Returns:
        pd.DataFrame: Formatted DataFrame.
    """
    formatted_df = df.copy()
    formatted_df = renameColumns(formatted_df)
    # Convert 'Time' to datetime
    formatted_df['Time'] = pd.to_datetime(formatted_df['Time'])
    # Reset the index of formatted_df to ensure sequential indexing after filtering
    formatted_df.reset_index(drop=True, inplace=True)
    # Set scale
    formatted_df['Scale'] = initialScale
    return formatted_df
