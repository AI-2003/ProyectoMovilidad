# GPS Bus Route Analysis for Mexico City

## Overview
This project focuses on analyzing and processing GPS data for bus routes in Mexico City. It involves cleaning and transforming GPS data, comparing it with official route data, and visualizing the results through maps and CSV files. The project consists of several Python scripts, each dedicated to a specific aspect of the data processing and analysis workflow. Below is a detailed description of each script and its functionality.

## Scripts and Their Functionality

### `clasificator.py`
This script processes GPS data for a specific bus route, cleans the data, and compares it with official route data to determine the closest route variant. It generates a map that visually compares the GPS data with the predicted route variant and calculates the deviation. The results are displayed on a Folium map and saved to a file.

**Key Functions:**
- Clean and preprocess GPS data
- Compare GPS data with official route variants
- Generate visual maps showing deviations

### `deviation_analysis.py`
This script processes GPS data for a specific route, cleans the data, and calculates the deviation from the official route for each vehicle (identified by plate) on each day. The results, including the predicted branch of the route and mean deviation, are saved to a CSV file for further analysis.

**Key Functions:**
- Clean and preprocess GPS data
- Calculate deviation for each vehicle
- Save results to a CSV file

### `official_routes.py`
This script processes official route data for Mexico City, transforms it into GeoDataFrames, and saves the resulting data as GeoJSON files. It extracts node information from a JSON file, constructs geometries using OSMnx, and categorizes route segments by branch and direction.

**Key Functions:**
- Transform official route data into GeoDataFrames
- Construct geometries using OSMnx
- Categorize route segments and save as GeoJSON

### `routeAnalysis.py`
This script processes GPS data from a CSV file, evaluates it through various stages of cleaning and transformation, and generates maps to visualize the results. It includes initial filtering, grouping by coordinates and time intervals, finding the closest points, snapping points to roads, and extracting street names.

**Key Functions:**
- Clean and preprocess GPS data
- Group and filter data by coordinates and time
- Visualize results through maps

### `routeTracer.py`
This script processes geographical data to find and analyze streets in Mexico City. It uses OSMnx to obtain nodes and edges of the city's road network, then searches for streets by name, extracts points from geometries, and finds the closest points between two streets. The script also reads street names from a JSON file to process specific routes.

**Key Functions:**
- Obtain and analyze road network data using OSMnx
- Search and process streets by name
- Extract and analyze street geometries

### `streetNames.py`
This script processes GPS data from a CSV file, filters and formats the data for a specific route and its vehicles (buses), groups points within intervals, finds the closest points, snaps them to roads, and extracts street names. It uses concurrent processing to handle multiple vehicles in parallel and generates a CSV file with counts of street names.

**Key Functions:**
- Clean and preprocess GPS data
- Group and filter data by intervals
- Extract street names and generate CSV file

## Conclusion
Each script focuses on a specific aspect of data processing, from cleaning and transformation to comparison with official routes and visualization. Together, they provide a comprehensive toolkit for understanding the routes in the city.
