import Levenshtein as lev
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from unidecode import unidecode
import re


def reemplaza_abreviaciones(text, replacements):
    """
    Reemplaza abreviaciones en un texto con sus equivalentes completos.

    :param text: Texto original
    :param replacements: Lista de tuplas (abreviación, reemplazo)
    :return: Texto con las abreviaciones reemplazadas
    """
    for abbr, replacement in replacements:
        text = re.sub(r'\b' + re.escape(abbr) + r'\b', replacement, text)
    return text


def checar_similitud(phrase1, phrase2, threshold=0.95):
    """
    Verifica si dos frases son similares basadas en un umbral de similitud de Levenshtein.

    :param phrase1: Primera frase
    :param phrase2: Segunda frase
    :param threshold: Umbral de similitud (default 0.95)
    :return: True si las frases son similares, de lo contrario False
    """
    phrase1 = phrase1.lower()
    phrase2 = phrase2.lower()
    similarity = lev.ratio(phrase1, phrase2)
    return similarity >= threshold


def encontrar_nombre_similar(target, string_list):
    """
    Encuentra la cadena más similar a una cadena objetivo en una lista de cadenas usando similitud coseno y TF-IDF.

    :param target: Cadena objetivo
    :param string_list: Lista de cadenas para comparar
    :return: Cadena más similar a la cadena objetivo
    """
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform([target] + string_list)
    cosine_similarities = cosine_similarity(vectors[0:1], vectors[1:]).flatten()
    most_similar_index = np.argmax(cosine_similarities)
    return string_list[most_similar_index]


def encontrar_nombre_similar_2(target, terms):
    """
    Encuentra el término más similar a un objetivo en una lista de términos usando la distancia de Levenshtein.

    :param target: Término objetivo
    :param terms: Lista de términos para comparar
    :return: Término más similar al objetivo
    """
    min_distance = float('inf')
    most_similar_term = None

    for term in terms:
        distance = lev.distance(target, term.lower().strip())
        if distance < min_distance:
            min_distance = distance
            most_similar_term = term

    return most_similar_term.strip()


def crear_conjunto_posibles_nombres(lista_cruda, street_list):
    """
    Crea un conjunto de posibles nombres de calles basados en nombres dados y una lista de nombres de calles.

    :param names: Lista de nombres dados
    :param street_list: Lista de nombres de calles
    :return: Lista de conjuntos de posibles nombres de calles
    """
    nombres_calles = []
    skips = ["VUELTA EN U", "RETORNO", "GLORIETA"]
    replacements = [
        ("cerrada", ""),
        ("prolongacion", ""),
        ("carretera", ""),
        ("avenida", ""),
        ("calzada", ""),
        ("calle", "")
    ]
    prefixes = ["cerrada", "calzada", "avenida", "calle", "prolongacion"]

    for calle in lista_cruda:
        posibles_nombres = set()

        if calle in skips or "base" in calle:
            nombres_calles.append(posibles_nombres)
            continue

        nombre_base = reemplaza_abreviaciones(calle, replacements).strip()

        nombres_a_checar = set(f"{prefix} {nombre_base}" for prefix in prefixes)

        if len(calle.split()) > 1:
            nombres_a_checar.add(calle)

        if len(nombre_base.split()) > 1:
            nombres_a_checar.add(nombre_base)

        nombres_a_checar.add(encontrar_nombre_similar(calle, street_list).lower().strip())

        for street in street_list:
            for pos in nombres_a_checar:
                if checar_similitud(unidecode(pos), unidecode(street)) or unidecode(pos) in unidecode(street):
                    posibles_nombres.add(street)

        nombres_calles.append(posibles_nombres)

    return nombres_calles
