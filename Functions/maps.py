import folium
from folium import plugins

# Display points
def plot_points(df, map, with_info=True):
    # Plot each point with a circle marker
    for index, row in df.iterrows():
        if with_info: 
            tooltip = f"Coord: ({row['Latitude']}, {row['Longitude']}), Time: {row['receivedtime: Descending']}, Index: {index}"
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