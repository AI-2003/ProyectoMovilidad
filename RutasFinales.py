from collections import OrderedDict
import folium
from folium import plugins
from geopy.distance import geodesic
import networkx as nx
import osmnx as ox

def coords(ruta):
    """
    Obtiene una lista de coordenadas únicas de la ruta.

    Parámetros:
    ruta (list): Lista de listas de coordenadas.

    Retorno:
    list: Lista de coordenadas únicas.
    """
    ordered_dict = OrderedDict((element, None) for sub_array in ruta for element in sub_array)
    return list(ordered_dict.keys())

# Prefijos comunes en nombres de calles
prefixes = ["cerrada ", "calzada ", "avenida ", "calle ", "prolongación "]

def remove_pre(name):
    """
    Elimina los prefijos comunes de los nombres de las calles.

    Parámetros:
    name (str): Nombre de la calle.

    Retorno:
    str: Nombre de la calle sin el prefijo.
    """
    for pre in prefixes:
        name = name.replace(pre, "")
    return name

def process_route(data, graph, G_undirected, rutas_finales_path):
    """
    Procesa la información de rutas y genera archivos HTML con mapas de las rutas.

    Parámetros:
    data (list): Lista de datos de rutas.
    graph (networkx.Graph): Grafo dirigido de la red de caminos.
    G_undirected (networkx.Graph): Grafo no dirigido de la red de caminos.
    rutas_finales_path (str): Ruta de la carpeta donde se guardarán los archivos HTML.

    Retorno:
    dict: Diccionario con las rutas procesadas.
    """
    rutas = {}

    for der in data:
        num = der['trip_number'] + 1
        ida, vuelta = der['ida'], der['vuelta']
        mWay = folium.Map(location=[19.4282233, -99.0569751], zoom_start=10)
        rutas[num] = {}

        for w, way in enumerate([ida, vuelta]):
            wayS, ColorDir = ('Vuelta', "blue") if w == 1 else ('Ida', "purple")
            routesFinal = []

            for nodes1, nodes2 in zip(way, way[1:]):
                setWay = {intersect for intersects in nodes1 + nodes2 for intersect in intersects}
                routes = []

                for n1 in nodes1:
                    data1 = G_undirected.nodes[n1[0]]
                    point1 = (data1['y'], data1['x'])

                    for n2 in nodes2:
                        data2 = G_undirected.nodes[n2[0]]
                        point2 = (data2['y'], data2['x'])
                        distance = geodesic(point1, point2).meters

                        if distance < 10000:
                            try:
                                route = nx.shortest_path(graph, n1[0], n2[0], weight='length')
                            except nx.NetworkXNoPath:
                                continue

                            count = sum(1 for node in setWay if node in route)

                            if count == 2:
                                con_street = True
                                for j in range(1, len(route) - 1):
                                    dataStr = graph.get_edge_data(route[j], route[j + 1])
                                    edge_names = dataStr[0].get('name')

                                    if edge_names:
                                        edge_names = edge_names if isinstance(edge_names, list) else [edge_names]

                                        for edge_name in edge_names:
                                            mod_edge_name = remove_pre(edge_name.lower()).strip()
                                            mod_setWay_name = remove_pre(n1[2].lower()).strip()

                                            if mod_setWay_name not in mod_edge_name and mod_edge_name not in mod_setWay_name:
                                                con_street = False
                                                break
                                if con_street:
                                    routes.append(route)

                routesFinal.append(routes)

            totalRouteConfirmed, totalRouteUnsure, totalRouteGap = [], [], []
            lastRoute = []

            for route1, route2 in zip(routesFinal, routesFinal[1:] + [None]):
                gaps, routesDraw, unSureRoutes = [], [], []

                if route2:
                    for r1 in route1:
                        for r2 in route2:
                            if lastRoute and r1[0] == lastRoute[-1] and r1[-1] == r2[0]:
                                routesDraw.append(r1)
                                noGaps = True
                            elif r1[-1] == r2[0]:
                                routesDraw.append(r1)
                            else:
                                gap_distance, gap_route = geodesic((data1['y'], data1['x']), (data2['y'], data2['x'])).meters, nx.shortest_path(graph, r1[-1], r2[0], weight='length')
                                if gap_distance < 500:
                                    gaps.append((gap_distance, gap_route, r1))
                else:
                    for r1 in route1:
                        if lastRoute and r1[0] == lastRoute[-1]:
                            routesDraw.append(r1)
                        else:
                            unSureRoutes.append(r1)

                if not routesDraw and gaps:
                    min_gap = min(gaps, key=lambda x: x[0])
                    if min_gap[0] < 500:
                        totalRouteGap.append(min_gap[1])
                        totalRouteConfirmed.append(min_gap[2])
                    lastRoute = min_gap[1]
                else:
                    totalRouteConfirmed.extend(routesDraw)
                    lastRoute = routesDraw[-1] if routesDraw else lastRoute

                totalRouteUnsure.extend(unSureRoutes)

            draw_routes(mWay, graph, G_undirected, wayS, ColorDir, totalRouteConfirmed, totalRouteGap, totalRouteUnsure)

            rutas[num][wayS] = {
                "confirmada": totalRouteConfirmed,
                "hueco": totalRouteGap,
                "inconfirmada": totalRouteUnsure
            }

        mWay.save(rutas_finales_path + str(num) + ".html")

    return rutas

def draw_routes(mWay, graph, G_undirected, wayS, ColorDir, confirmed, gaps, unsure):
    """
    Dibuja las rutas en el mapa.

    Parámetros:
    mWay (folium.Map): Objeto de mapa de Folium.
    graph (networkx.Graph): Grafo dirigido de la red de caminos.
    G_undirected (networkx.Graph): Grafo no dirigido de la red de caminos.
    wayS (str): Dirección de la ruta (Ida o Vuelta).
    ColorDir (str): Color de la ruta.
    confirmed (list): Lista de rutas confirmadas.
    gaps (list): Lista de rutas con huecos.
    unsure (list): Lista de rutas no confirmadas.
    """
    for rC in confirmed:
        draw_route(mWay, graph, G_undirected, rC, ColorDir, wayS, "green")

    for rG in gaps:
        draw_route(mWay, graph, G_undirected, rG, "green", wayS, "orange")

    for rU in unsure:
        draw_route(mWay, graph, G_undirected, rU, "orange", wayS, "orange")

def draw_route(mWay, graph, G_undirected, route, ColorDir, wayS, marker_color):
    """
    Dibuja una ruta específica en el mapa.

    Parámetros:
    mWay (folium.Map): Objeto de mapa de Folium.
    graph (networkx.Graph): Grafo dirigido de la red de caminos.
    G_undirected (networkx.Graph): Grafo no dirigido de la red de caminos.
    route (list): Lista de nodos que componen la ruta.
    ColorDir (str): Color de la ruta.
    wayS (str): Dirección de la ruta (Ida o Vuelta).
    marker_color (str): Color del marcador.
    """
    route_map = ox.plot_route_folium(graph, route, route_map=mWay, color=ColorDir)

    data1, data2 = G_undirected.nodes[route[0]], G_undirected.nodes[route[-1]]
    point1, point2 = (data1['y'], data1['x']), (data2['y'], data2['x'])

    # Añade marcadores en los puntos inicial y final de la ruta
    folium.Marker(point1, popup=f"{wayS} - {route[0]}").add_to(mWay)
    folium.Marker(point2, popup=f"{wayS} - {route[-1]}").add_to(mWay)

    # Dibuja la línea de la ruta en el mapa
    polyline = folium.PolyLine(locations=[point1, point2], color=ColorDir, weight=1, opacity=1)
    polyline.add_to(mWay)

    # Añade una línea con texto de flecha para indicar la dirección de la ruta
    plugins.PolyLineTextPath(polyline, '►', repeat=10, offset=8, attributes={'fill': marker_color, 'font-weight': 'bold', 'font-size': '20'}).add_to(mWay)
