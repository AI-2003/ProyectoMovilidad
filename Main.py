import os
import glob
import datetime
import osmnx as ox

from ProcesamientoArchivos import (
    leer_csv_ruta, guardar_lista_nombres_json, guardar_lista_nombres, leer_nombres_calles_osm,
    guardar_rutas_json, guardar_posibles_nombres, leer_json, guardar_puntos_finales, cargar_gps_gdf,
    guarda_predicciones
)
from PuntosConexion import generar_conexiones_entre_calles
from PosiblesNombres import crear_conjunto_posibles_nombres
from ListaCrudaNombres import extraer_nombres
from Predicciones import clean_gps_data, classify_route_variant, branches_gdf_from_coords

from tqdm import tqdm
import time

# PASO 0: Cargar la base de datos de nombres de calles
from RutasFinales import process_route

def cargar_nombres_de_calle(path):
    """
    Carga los nombres de calles desde un archivo.

    Parámetros:
    path (str): Ruta al archivo con los nombres de las calles.

    Retorno:
    list: Lista de nombres de calles.
    """
    return leer_nombres_calles_osm(path)

# Configuración inicial
def configurar_directorio_salida(ruta_escogida):
    """
    Configura el directorio de salida donde se guardarán los archivos generados.

    Parámetros:
    ruta_escogida (str): Nombre de la ruta seleccionada.

    Retorno:
    str: Ruta del directorio de salida.
    """
    date_folder = f"{ruta_escogida}_{datetime.datetime.now().strftime('%Y%m%d')}"
    output_directory = f"./OUTPUT/{date_folder}"
    os.makedirs(output_directory, exist_ok=True)
    os.makedirs(output_directory + "/mapas", exist_ok=True)
    return output_directory

# PASO 1: Extraer la lista cruda de nombres de los archivos base
def extraer_lista_cruda_nombres(folder_path):
    """
    Extrae la lista cruda de nombres de calles desde archivos CSV.

    Parámetros:
    folder_path (str): Ruta a la carpeta que contiene los archivos CSV.

    Retorno:
    list: Lista de listas de nombres extraídos.
    """
    start_time = time.time()
    csv_files = glob.glob(folder_path)
    derivaciones_listas_nombres = []

    for file_path in tqdm(csv_files, desc="Extrayendo nombres de archivos CSV"):
        tables = leer_csv_ruta(file_path)
        derivacion = []

        for table in tables:
            text = table[1]
            routes_list = extraer_nombres(text)
            derivacion.append(routes_list)

        derivaciones_listas_nombres.append(derivacion)

    end_time = time.time()
    print(f"Tiempo total para extraer nombres crudos: {end_time - start_time:.2f} segundos")
    return derivaciones_listas_nombres

# PASO 2: Obtener posibles nombres de calles
def obtener_posibles_nombres(derivaciones_listas_nombres, street_list):
    """
    Obtiene posibles nombres de calles a partir de la lista cruda de nombres.

    Parámetros:
    derivaciones_listas_nombres (list): Lista de listas de nombres extraídos.
    street_list (list): Lista de nombres de calles conocidas.

    Retorno:
    list: Lista de listas de posibles nombres de calles.
    """
    start_time = time.time()
    derivaciones_listas_posibles_nombres = []

    for derivacion in tqdm(derivaciones_listas_nombres, desc="Obteniendo posibles nombres de calles"):
        ida = derivacion["ida"]
        vuelta = derivacion["vuelta"]

        pos_calles_ida = crear_conjunto_posibles_nombres(ida, street_list)
        pos_calles_vuelta = crear_conjunto_posibles_nombres(vuelta, street_list)

        derivaciones_listas_posibles_nombres.append((pos_calles_ida, pos_calles_vuelta))

    end_time = time.time()
    print(f"Tiempo total para obtener posibles nombres: {end_time - start_time:.2f} segundos")
    return derivaciones_listas_posibles_nombres

# PASO 3: Generar conexiones entre calles
def generar_conexiones(derivaciones_listas_posibles_nombres, street_data):
    """
    Genera las conexiones entre calles a partir de los posibles nombres de calles.

    Parámetros:
    derivaciones_listas_posibles_nombres (list): Lista de listas de posibles nombres de calles.
    street_data (networkx.Graph): Grafo con los datos de las calles.

    Retorno:
    list: Lista de listas de conexiones entre calles.
    """
    start_time = time.time()
    derivaciones_listas_posibles_puntos = []

    for pos_ruta in tqdm(derivaciones_listas_posibles_nombres, desc="Generando conexiones entre calles"):
        street_data_ida = generar_conexiones_entre_calles(pos_ruta["ida"], street_data)
        street_data_vuelta = generar_conexiones_entre_calles(pos_ruta["vuelta"], street_data)
        derivaciones_listas_posibles_puntos.append((street_data_ida, street_data_vuelta))

    end_time = time.time()
    print(f"Tiempo total para generar conexiones: {end_time - start_time:.2f} segundos")
    return derivaciones_listas_posibles_puntos

# PASO 4: Predecir variantes seguidas por día
def genera_predicciones(gps_df, coordenadas_variantes, rounding_precision,time_diff_threshold, closer_threshold):
    """
    Predice qué variante de la ruta escogida sigue cada placa cada día

    Parámetros:
    gps_df (gpd.GeoDataFrame): DF con los puntos seguidos por las unidades
    coordenadas_variantes (list): lista con las coordenadas de ida y de regreso de cada variante
    rounding_precision (int): Precision decimal para redondear coordenadas
    time_diff_threshold (int): Intervalo de tiempo en segundos para agrupar coordendas
    closer_threshold (int): Numero de puntos que verificar hacia delante para encontrar el más cercano

    Retorno:
    dict: Diccionario de tuplas de fecha y ruta predecida por cada placa 
    """
    # Format coordinates list into a gdf
    branches_gdf = branches_gdf_from_coords(coordenadas_variantes)
    # Predict branch followed
    records = {}
    for plate in tqdm(gps_df['plate'].unique(), desc="Processing plates"):
        plate_gdf = gps_df[gps_df['plate'] == plate]
        sorted_dates = sorted(plate_gdf['time'].dt.date.unique())
        records[plate] = {}
        for day in tqdm(sorted_dates, desc=f"Processing dates for plate {plate}"):
            plate_date_gdf = plate_gdf[plate_gdf['time'].dt.date == day]
            clean_gdf = clean_gps_data(plate_date_gdf, rounding_precision, time_diff_threshold, closer_threshold)
            predicted_gdf = classify_route_variant(clean_gdf, branches_gdf)
            records[plate][day] = predicted_gdf["branch"]
    return records

def main(skip_to_step=None):
    """
    Función principal que coordina todos los pasos para procesar las rutas.

    Parámetros:
    skip_to_step (int, opcional): Paso al que se desea saltar (1, 2, 3 o 4). Si no se proporciona, se ejecutarán todos los pasos.

    Retorno:
    None
    """
    # Configuración de ruta y directorio de salida

    ###
    ruta_escogida = "Ruta5"
    ###

    output_directory = configurar_directorio_salida(ruta_escogida)

    # Ruta a los archivos
    input_path = f"./INPUT/Tablas/{ruta_escogida}/Derivaciones/*.csv"
    gps_df_path = f"./INPUt/GPS/{ruta_escogida}.csv"
    lista_nombres_path = os.path.join(output_directory, f"{ruta_escogida}_raw_names.txt")
    lista_nombres_json_path = os.path.join(output_directory, f"{ruta_escogida}_raw_names.json")
    pos_nombres_path = os.path.join(output_directory, f"{ruta_escogida}_pos_nombres_.txt")
    pos_conexiones_path = os.path.join(output_directory, f"{ruta_escogida}_pos_rutas.txt")
    mapas_finales_folder_path = f"{output_directory}/mapas/"
    coordenadas_finales_path = os.path.join(output_directory, f"{ruta_escogida}_final_coords.txt")
    predicciones_path = os.path.join(output_directory, f"{ruta_escogida}_predicciones.json")

    if skip_to_step is None or skip_to_step <= 1:
        #### Extraer lista cruda de nombres ####
        print("\nGenerando lista cruda de nombres")
        derivaciones_listas_nombres = extraer_lista_cruda_nombres(input_path)

        # Guardar lista cruda de nombres en archivos
        guardar_lista_nombres(derivaciones_listas_nombres, lista_nombres_path)
        guardar_lista_nombres_json(derivaciones_listas_nombres, lista_nombres_json_path)

    derivaciones_listas_nombres = leer_json(lista_nombres_json_path)

    if skip_to_step is None or skip_to_step <= 2:
        # Ruta base de nombres de calles
        street_names_path = 'INPUT/OSMNames.txt'
        street_list = cargar_nombres_de_calle(street_names_path)

        #### Obtener posibles nombres de calles ####
        print("\nGenerando lista de nombres posibles")
        derivaciones_listas_posibles_nombres = obtener_posibles_nombres(derivaciones_listas_nombres, street_list)

        # Guardar posibles nombres en archivo
        guardar_posibles_nombres(derivaciones_listas_posibles_nombres, pos_nombres_path)

    # Configuración de OSMNX
    ox.config(use_cache=True, log_console=False)
    mexico_city_street_data = ox.graph_from_place("Mexico City, Mexico", network_type='drive')

    if skip_to_step is None or skip_to_step <= 3:
        #### Leer rutas desde archivo y generar conexiones ####
        print("\nGenerando lista de conexiones entre calles")
        rutas = leer_json(pos_nombres_path)
        derivaciones_listas_posibles_puntos = generar_conexiones(rutas, mexico_city_street_data)

        # Guardar rutas generadas en archivo
        guardar_rutas_json(derivaciones_listas_posibles_puntos, pos_conexiones_path)

    pos_conexiones = leer_json(pos_conexiones_path)

    print("\nGenerando mapas finales y coordenadas de ruta")
    G_undirected = mexico_city_street_data.to_undirected()

    puntos_rutas_finales = process_route(pos_conexiones, mexico_city_street_data, G_undirected, mapas_finales_folder_path)

    guardar_puntos_finales(puntos_rutas_finales, G_undirected, coordenadas_finales_path)


    if skip_to_step is None or skip_to_step <= 4:
        ### Leer coordenadas desde archivo y predecir variantes seguidas por día ###
        print("\nPrediciendo ruta seguida por día")
        coordenadas = leer_json(coordenadas_finales_path)
        gps_df = cargar_gps_gdf(gps_df_path)
        predicciones = genera_predicciones(gps_df, coordenadas)

        # Guarda las predicciones hechas
        guarda_predicciones(predicciones, predicciones_path)

    predicciones = leer_json(predicciones_path)



if __name__ == "__main__":
    skip_to_step = None
    try:
        skip_to_step = int(input("Ingrese el paso al cual desea saltar (1, 2, 3 o 4) o presione Enter para ejecutar todos los pasos: "))
    except ValueError:
        pass

    main(skip_to_step)
