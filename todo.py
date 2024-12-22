import requests
from lxml import html  # Asegúrate de que esta es la importación correcta
from urllib.parse import urljoin
import pandas as pd
import time

# URL de la página principal
url = 'https://brotesverdesonline.com'

# Obtener el contenido de la página principal
response = requests.get(url)
tree = html.fromstring(response.content)  # Usar lxml.html.fromstring()

# Extraer enlaces de distintos elementos
html_links = tree.xpath('//a/@href')  # Enlaces de etiquetas <a>
image_links = tree.xpath('//img/@src')  # Enlaces de imágenes <img>
css_links = tree.xpath('//link[@rel="stylesheet"]/@href')  # Enlaces a archivos CSS

# Combinar todos los enlaces y convertirlos a absolutos
all_links = html_links + image_links + css_links
absolute_links = [urljoin(url, link) for link in all_links]

# Eliminar duplicados
unique_links = list(set(absolute_links))

# Filtrar enlaces no válidos como 'javascript:void(0);', '#', etc.
def is_valid_url(url):
    return url and url.startswith(('http', 'https', 'www'))

# Función para obtener el título de la página
def get_title(page_url):
    try:
        response = requests.get(page_url, timeout=10)
        if 'text/html' in response.headers.get('Content-Type', ''):
            page_tree = html.fromstring(response.content)
            title = page_tree.xpath('//title/text()')
            return title[0].strip() if title else 'Sin título'
        else:
            return 'No es una página HTML'
    except requests.RequestException:
        return 'Error al obtener título'

# Función para obtener la etiqueta H1
def get_h1(page_url):
    try:
        response = requests.get(page_url, timeout=10)
        if 'text/html' in response.headers.get('Content-Type', ''):
            page_tree = html.fromstring(response.content)
            h1 = page_tree.xpath('//h1/text()')
            return h1[0].strip() if h1 else 'Sin etiqueta H1'
        else:
            return 'No es una página HTML'
    except requests.RequestException:
        return 'Error al obtener H1'

# Función para obtener la meta descripción de una página
def get_meta_description(page_url, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(page_url, timeout=10)
            # Verificar si el contenido es HTML (Content-Type: text/html)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                # Extraer el contenido de la meta descripción
                meta_description = page_tree.xpath('//meta[@name="description"]/@content')
                if meta_description:
                    return meta_description[0].strip()  # Limpiar la descripción
                else:
                    return 'Sin meta descripción'  # Si no se encuentra la meta descripción
            else:
                return 'No es una página HTML'  # Si no es HTML, devolver un mensaje
        except requests.RequestException:
            attempt += 1
            time.sleep(delay)  # Espera entre intentos
    return 'Error al obtener meta descripción'

# Obtener los datos de los enlaces
data = []

for link in unique_links:
    if not is_valid_url(link):  # Saltar enlaces no válidos
        continue
    
    title = get_title(link)  # Obtener el título
    h1 = get_h1(link)        # Obtener la etiqueta H1
    meta_description = get_meta_description(link)  # Obtener la meta descripción
    
    # Agregar los datos al listado
    data.append({
        'URL': link,
        'Título': title,
        'Etiqueta H1': h1,
        'Meta Descripción': meta_description
    })

# Crear un DataFrame de pandas
df = pd.DataFrame(data)

# Guardar los datos en un archivo Excel
output_file = 'enlaces_con_info.xlsx'
df.to_excel(output_file, index=False, engine='openpyxl')

# Mostrar los resultados en la consola
print(f"Enlaces con información extraída y guardados en {output_file}")
print("Resultados:")
print(df)
