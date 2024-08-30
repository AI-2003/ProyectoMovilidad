import csv
import json
from collections import OrderedDict
import geopandas as gpd
import pandas as pd


def leer_nombres_calles_osm(path):
    """
    Lee todos los nombres de calles desde un archivo y los devuelve en una lista en minúsculas.

    :param path: Ruta del archivo con los nombres de las calles
    :return: Lista de nombres de calles en minúsculas
    """
    with open(path, 'r', encoding="utf-8") as file:
        return [line.strip().lower() for line in file]


def leer_json(file_path):
    """
    Lee un archivo JSON y devuelve los datos.

    :param file_path: Ruta del archivo JSON
    :return: Datos del archivo JSON
    """
    with open(file_path, 'r', encoding="utf-8") as file:
        return json.load(file)


def leer_csv_ruta(path):
    """
    Lee un archivo CSV y lo convierte en una lista de listas, donde cada sublista contiene
    el encabezado de una columna y los datos combinados de esa columna.

    :param path: Ruta del archivo CSV
    :return: Lista de listas con los datos del CSV
    """
    with open(path, newline='', encoding='utf-8') as csvfile:
        rows = list(csv.reader(csvfile))

    if not rows:
        return []

    result = []
    for col_index in range(len(rows[0])):
        header = rows[0][col_index]
        combined_rows = " ".join(row[col_index].strip('"') for row in rows[1:])
        result.append([header, combined_rows])

    return result


def guardar_rutas_json(rutas, file_name):
    """
    Guarda una lista de rutas en un archivo JSON.

    :param rutas: Lista de rutas
    :param file_name: Nombre del archivo JSON
    """
    trips_json = [
        {'trip_number': i, 'ida': ruta[0], 'vuelta': ruta[1]}
        for i, ruta in enumerate(rutas)
    ]

    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(trips_json, json_file, ensure_ascii=False, indent=4)


def guardar_lista_nombres(list_of_lists, file_name):
    """
    Guarda una lista de listas de nombres en un archivo de texto.

    :param list_of_lists: Lista de listas de nombres
    :param file_name: Nombre del archivo de texto
    """
    with open(file_name, 'w', encoding='utf-8') as file:
        for i, trip in enumerate(list_of_lists):
            file.write(f"{i}\n")
            ida, vuelta = trip  # Asumiendo que cada lista tiene exactamente dos sublistas
            file.write(f"Ida: {' - '.join(map(str, ida))}\n")
            file.write(f"Vuelta: {' - '.join(map(str, vuelta))}\n")
            file.write('\n')  # Añadir una línea en blanco para separar los viajes


def guardar_lista_nombres_json(list_of_lists, file_name):
    """
    Guarda una lista de listas de nombres en un archivo JSON.

    :param list_of_lists: Lista de listas de nombres
    :param file_name: Nombre del archivo JSON
    """
    trips_json = [
        {'trip_number': i, 'ida': trip[0], 'vuelta': trip[1]}
        for i, trip in enumerate(list_of_lists)
    ]

    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(trips_json, json_file, ensure_ascii=False, indent=4)


def guardar_posibles_nombres(rutas, file_name):
    """
    Guarda una lista de posibles nombres de rutas en un archivo JSON.

    :param rutas: Lista de posibles nombres de rutas
    :param file_name: Nombre del archivo JSON
    """
    trips_json = [
        {
            'trip_number': i,
            'ida': [list(item) if isinstance(item, set) else item for item in ruta[0]],
            'vuelta': [list(item) if isinstance(item, set) else item for item in ruta[1]]
        }
        for i, ruta in enumerate(rutas)
    ]

    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(trips_json, json_file, ensure_ascii=False, indent=4)

def generar_coords(ruta, G):
    """
    Genera una lista de coordenadas (latitud y longitud) a partir de una lista de nodos.

    Parámetros:
    ruta (list): Lista de nodos.
    G (networkx.Graph): Grafo de la red de caminos.

    Retorno:
    list: Lista de tuplas de coordenadas (latitud, longitud).
    """
    # Crear un diccionario ordenado para eliminar duplicados preservando el orden
    ordered_dict = OrderedDict()

    # Rellenar el diccionario con los nodos de la ruta
    for sub_array in ruta:
        for element in sub_array:
            if element not in ordered_dict:
                ordered_dict[element] = None

    # Obtener la lista de nodos únicos
    ruta = list(ordered_dict.keys())

    coords = []

    # Convertir los nodos en coordenadas (latitud y longitud)
    for n in ruta:
        data = G.nodes[n]
        coords.append((data['y'], data['x']))

    return coords

def guardar_puntos_finales(rutas, G, file_name):
    """
    Guarda las coordenadas finales de las rutas en un archivo JSON.

    Parámetros:
    rutas (dict): Diccionario con las rutas procesadas.
    G (networkx.Graph): Grafo de la red de caminos.
    file_name (str): Nombre del archivo JSON donde se guardarán las coordenadas.

    Retorno:
    None
    """
    coordenadas_finales = {}

    for der in rutas:
        if der not in coordenadas_finales:
            coordenadas_finales[der] = {}

        for way in rutas[der]:
            nodos = rutas[der][way]

            confirmadas = nodos['confirmada']
            huecos = nodos['hueco']
            inconfirmadas = nodos['inconfirmada']

            # Generar las coordenadas para cada tipo de ruta
            c_coords = generar_coords(confirmadas, G)
            h_coords = generar_coords(huecos, G)
            i_coords = generar_coords(inconfirmadas, G)
            coordenadas_finales[der][way] = (c_coords, h_coords, i_coords)

    # Guardar las coordenadas finales en un archivo JSON
    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(coordenadas_finales, json_file, ensure_ascii=False, indent=4)


def cargar_gps_gdf(file_name):
    """
    Devuelve el GeoDataFrame que contiene las coordena

    Parámetros:
    file_name (str): Nombre del archivo csv que contiene los registros

    Retorno:
        gpd.GeoDataFrame: GeoDataFrame containing the info found on the csv
    """
    # Read csv
    df = pd.read_csv(file_name)
    # Standardize column names in the df.
    df.rename(columns={
            'timestamp': 'time',
            'placa': 'plate',
            'ruta': 'route',
            'latitud': 'latitude',
            'longitud': 'longitude'
        }, inplace=True)
    # Convert 'time' to datetime
    df['time'] = pd.to_datetime(df['time'])
    # Reset the index of formatted_df to ensure sequential indexing after filtering
    df.reset_index(drop=True, inplace=True)
    # Set scale
    df['scale'] = 2
    # Transform into gdf with geometry
    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.longitude, df.latitude)
    )
    return gdf

def guarda_predicciones(predicciones, file_name):
    """
    Guarda las predicciones hechas de las variantes seguidas

    Parámetros:
    predicciones (dict): Diccionario con las placas y sus predicciones por día
    file_name (str): Nombre del archivo JSON donde se guardarán las coordenadas.

    Retorno:
    None
    """

    with open(file_name, 'w', encoding='utf-8') as json_file:
        json.dump(predicciones, json_file, ensure_ascii=False, indent=4)