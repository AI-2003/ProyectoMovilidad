from itertools import product
from geopy.distance import geodesic


# Generar todas las combinaciones posibles entre los elementos de múltiples listas
def all_combinations(arrays):
    """
    Genera todas las combinaciones posibles entre los elementos de múltiples listas.

    :param arrays: Lista de listas con elementos a combinar
    :return: Lista de todas las combinaciones posibles
    """
    return list(product(*arrays))


# Generar conexiones entre calles
def generar_conexiones_entre_calles(calles, graph):
    """
    Genera las conexiones entre calles basadas en la cercanía de sus intersecciones.

    :param street_names: Lista de nombres de calles
    :param graph: Grafo de calles
    :return: Lista de datos de intersección
    """
    conexiones_totales = []
    conexiones_set = set()

    for i in range(len(calles) - 1):
        set1 = calles[i]
        set2 = calles[i + 1]

        conexiones = []

        for nombre1 in set1:
            for nombre2 in set2:
                intersecciones = checar_conexion_distancia(nombre1, nombre2, graph)
                for punto in intersecciones:
                    if punto[0] not in conexiones_set:
                        conexiones.append(punto)
                    conexiones_set.add(punto[0])

        conexiones_totales.append(conexiones)

    return conexiones_totales


# Verificar si dos calles están conectadas directamente
def checar_conexion(street1, street2, graph):
    """
    Verifica si dos calles están conectadas directamente en el grafo.

    :param street1: Nombre de la primera calle
    :param street2: Nombre de la segunda calle
    :param graph: Grafo de calles
    :return: Lista de nodos de intersección
    """
    if street2 == street1:
        return [], [], []

    edges_1, edges_2 = [], []

    for u, v, data in graph.edges(data=True):
        street_name = data.get('name', [])

        if street_name:
            street_name = [s.lower() for s in street_name] if isinstance(street_name, list) else [street_name.lower()]

            if street1 in street_name:
                edges_1.append((u, v))
            if street2 in street_name:
                edges_2.append((u, v))

    nodes_1 = set(node for edge in edges_1 for node in edge)
    nodes_2 = set(node for edge in edges_2 for node in edge)

    intersect_nodes_final = [(n1, street1, street2) for n1 in nodes_1 for n2 in nodes_2 if n1 == n2]

    return intersect_nodes_final, nodes_1, nodes_2


# Verificar si dos calles están conectadas dentro de una distancia específica
def checar_conexion_distancia(street1, street2, graph):
    """
    Verifica si dos calles están conectadas dentro de una distancia específica.

    :param street1: Nombre de la primera calle
    :param street2: Nombre de la segunda calle
    :param graph: Grafo de calles
    :return: Lista de nodos de intersección con distancia
    """

    intersect_nodes_final, nodes_1, nodes_2 = checar_conexion(street1, street2, graph)

    if intersect_nodes_final:
        return intersect_nodes_final

    distances = []

    for n1 in nodes_1:
        for n2 in nodes_2:
            point1 = (graph.nodes[n1]['y'], graph.nodes[n1]['x'])
            point2 = (graph.nodes[n2]['y'], graph.nodes[n2]['x'])
            distance = geodesic(point1, point2).meters
            distances.append((distance, n1))
            distances.append((distance, n2))

    unique_distances = sorted(set(distance for distance, _ in distances))
    if len(unique_distances) < 2:
        return []

    small1, small2 = unique_distances[:2]
    nodes_int = [t for t in distances if t[0] in [small1, small2]]

    for node in nodes_int:
        if node[0] <= 350:  # Umbral de distancia
            intersect_nodes_final.append((node[1], street1, street2))

    return intersect_nodes_final
