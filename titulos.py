import requests
from lxml import html  # Asegúrate de usar lxml.html
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

# Función para obtener el título de una página
def get_title(page_url, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(page_url, timeout=10)  # Aumenta el tiempo de espera
            # Verificar si el contenido es HTML (Content-Type: text/html)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                # Extraer el contenido del título
                title = page_tree.xpath('//title/text()')
                if title:
                    return title[0].strip()  # Limpiar el título
                else:
                    return 'Sin título'  # Si no se encuentra el título
            else:
                return 'No es una página HTML'  # Si no es HTML, devolver un mensaje
        except requests.RequestException as e:
            print(f"Intento {attempt + 1} fallido al acceder a {page_url}: {e}")
            attempt += 1
            time.sleep(delay)  # Espera entre intentos
    return 'Error al obtener título'

# Obtener el título de los enlaces
links_with_titles = []
for link in unique_links:
    if not is_valid_url(link):  # Saltar enlaces no válidos
        continue
    title = get_title(link)  # Obtener el título

    # Solo agregar si es una página HTML válida y tiene título
    if 'No es una página HTML' not in title:
        links_with_titles.append({
            'url': link,
            'title': title
        })

# Guardar los enlaces con título en un archivo JSON
output_file = 'enlaces_con_titulo.json'
with open(output_file, 'w') as file:
    json.dump(links_with_titles, file, indent=4)

# Mostrar los resultados en la consola
print(f"Enlaces con títulos extraídos y guardados en {output_file}")

# Mostrar los enlaces y sus títulos
for link in links_with_titles:
    print(f"URL: {link['url']}")
    print(f"Título: {link['title']}")
    print("-" * 40)
