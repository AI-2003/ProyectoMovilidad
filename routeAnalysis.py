from Functions.prepping import *
from Functions.maps import *
from Functions.points import *

# Load the CSV file
file_name = 'BD.csv'
df = pd.read_csv(file_name)

# ================
# Evaluations

# Initial values
route = 'RUTA 5'
plate = '0050284'
startTime = '2023-04-11 07:00:00'
endTime = '2023-04-11 09:00:00'
rounding_precision = 4
closer_threshold = 3
time_diff_threshold = 120

# Simple points
filtered_df = filter_and_format_df(df, route, plate, startTime, endTime, 2)
map_points(filtered_df, 'Maps/points_map.html')

# Grouped points
grouped_df = group_points(filtered_df)
map_points(grouped_df, 'Maps/grouped_points_map.html')

# Grouped within intervals
grouped_within_interval_df = group_within_intervals(filtered_df, rounding_precision, time_diff_threshold)
map_points(grouped_within_interval_df, 'Maps/grouped_within_interval_points_map.html')
grouped_within_interval_df['Scale'] = 2
map_route(grouped_within_interval_df, 'Maps/route_map.html')
map_route(grouped_within_interval_df, 'Maps/grouped_points_route.html')

# Points by closest in the next registered
closest_df = closest_points(grouped_within_interval_df, closer_threshold)
map_route(closest_df, 'Maps/closer_point_route.html')
map_path(closest_df, 'Maps/ant_path_route.html')

# Points inside streets
snapped_df = snap_to_roads(closest_df)
map_path(snapped_df, 'Maps/snapped_route.html')


# Street names
streetList = list(set(snapped_df['StreetName']))
print(streetList)