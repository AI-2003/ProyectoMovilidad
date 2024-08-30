import re
from unidecode import unidecode

# Función para reemplazar abreviaciones en el texto
def replace_abbreviations(text, replacements):
    """
    Reemplaza las abreviaciones en el texto según la lista de reemplazos proporcionada.

    Parámetros:
    text (str): El texto original donde se realizarán los reemplazos.
    replacements (list of tuples): Lista de tuplas donde cada tupla contiene una abreviación y su reemplazo.

    Retorna:
    str: El texto con las abreviaciones reemplazadas.
    """
    for abbr, replacement in replacements:
        pattern = re.compile(r'\b' + re.escape(abbr) + r'\b', re.IGNORECASE)
        text = pattern.sub(replacement, text)
    return text


# Función para eliminar duplicados consecutivos en una lista de nombres de calles
def remove_consecutive_duplicates(street_names):
    """
    Elimina los duplicados consecutivos en una lista de nombres de calles.

    Parámetros:
    street_names (list of str): Lista de nombres de calles.

    Retorna:
    list of str: Lista de nombres de calles sin duplicados consecutivos.
    """
    result = []
    prev_street = None
    for street in street_names:
        if street != prev_street:
            result.append(street)
            prev_street = street
    return result


# Función para extraer nombres de calles de un texto
def extraer_nombres(text):
    """
    Extrae los nombres de calles de un texto, normaliza y reemplaza abreviaciones, y elimina duplicados consecutivos.

    Parámetros:
    text (str): El texto original que contiene los nombres de calles.

    Retorna:
    list of str: Lista de nombres de calles extraídos y normalizados.
    """
    text = unidecode(text.lower())  # Convertir el texto a minúsculas y eliminar acentos

    # Expresión regular para dividir el texto en base a patrones específicos
    pattern = re.compile(r"(?i)(der\. |der.|derecha |der.- |der |y  la | CIERRE DE CIRCUITO |circunda | POR |PARTIENDO |CONTINPUA |izquierda |IZO |izq, |izq\. |izq |izo. |continua |continia |vuelta en |cont\. |hasta |circundar )")
    split_result = pattern.split(text)  # Dividir el texto en base al patrón

    # Ajustar el resultado dividido en función del primer elemento
    if split_result[0] == '':
        lista_calles = split_result[2:]
    else:
        lista_calles = split_result

    calles = []  # Lista para almacenar los nombres de calles extraídos
    replacements = [
        ("av", "avenida"),
        ("a", "avenida"),
        ("ma", "maria"),
        ("m", "maria"),
        ("lic", "licenciado"),
        ("calz", "calzada"),
        ("gral", "general"),
        ("prol", "prolongacion"),
        ("ing", "ingeniero"),
        ("arq", "arquitecto"),
        ("cda", "cerrada"),
        ("carr", "carretera"),
        ("gob", "gobernador"),
        ("diagonal", ""),
        ("lateral de", ""),
        ("dr", "doctor"),
        ("ign", "ignacio"),
        ("blvd", "boulevard")
    ]

    ### LIMPIEZA CRUDA DEL TEXTO ###
    # Iterar sobre los nombres de las calles divididos
    for i in range(0, len(lista_calles), 2):
        if i < len(lista_calles):
            calle = lista_calles[i].strip()  # Eliminar espacios en blanco al inicio y final del nombre de la calle
            if "retorno" in calle:
                calle = "RETORNO"
            elif "\"u\"" in calle or "\"u" in calle or "u\"" in calle :
                calle = "VUELTA EN U"
            elif "incorporacion" in calle:
                # Expresión regular para eliminar "incorporacion" del nombre de la calle
                pattern_incorporacion = re.compile(r'^(\b\w+\b\s*)*\bincorporacion\b\s*\b\w+\b\s*')
                calle = pattern_incorporacion.sub('', calle)

            # Reemplazar abreviaciones en el nombre de la calle
            calle = replace_abbreviations(calle, replacements)
            # Eliminar texto entre paréntesis y caracteres no alfanuméricos
            calle = re.sub(r"\([^)]*\)", "", calle)
            calle = re.sub(r'[^\w\s]', '', calle)
            calles.append(calle.strip())  # Añadir el nombre de la calle a la lista de nombres

    # Eliminar duplicados consecutivos y retornar la lista de nombres de calles
    return remove_consecutive_duplicates(calles[:-1])
