import requests
from lxml import html  # Asegúrate de que esta es la importación correcta
from urllib.parse import urljoin
import json
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

# Función para obtener la meta descripción de una página
def get_meta_description(page_url, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(page_url, timeout=15)  # Aumenta el tiempo de espera (15 segundos)
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
        except requests.RequestException as e:
            print(f"Intento {attempt + 1} fallido al acceder a {page_url}: {e}")
            attempt += 1
            time.sleep(delay)  # Espera entre intentos
    return 'Error al obtener meta descripción'

# Obtener la meta descripción de los enlaces
links_with_meta_description = []
for link in unique_links:
    if not is_valid_url(link):  # Saltar enlaces no válidos
        continue
    meta_description = get_meta_description(link)  # Obtener la meta descripción

    # Solo agregar si es una página HTML válida y tiene meta descripción
    if 'No es una página HTML' not in meta_description:
        links_with_meta_description.append({
            'url': link,
            'meta_description': meta_description
        })

# Guardar los enlaces con meta descripción en un archivo JSON
output_file = 'enlaces_con_meta_descripcion.json'
with open(output_file, 'w') as file:
    json.dump(links_with_meta_description, file, indent=4)

# Mostrar los resultados en la consola
print(f"Enlaces con meta descripción extraídos y guardados en {output_file}")
print("Resultados:")
for link in links_with_meta_description:
    print(f"URL: {link['url']}")
    print(f"Meta descripción: {link['meta_description']}")
    print("-" * 40)  # Separador entre cada entrada
