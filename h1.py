import requests
from lxml import html
from urllib.parse import urljoin
import json
import time

# URL de la página principal
url = 'https://brotesverdesonline.com'

# Obtener el contenido de la página principal
response = requests.get(url)
tree = html.fromstring(response.content)

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

# Función para obtener los encabezados <h1> de una página
def get_h1(page_url, retries=3, delay=5):
    attempt = 0
    while attempt < retries:
        try:
            response = requests.get(page_url, timeout=10)  # Aumenta el tiempo de espera
            # Verificar si el contenido es HTML (Content-Type: text/html)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                h1_tags = page_tree.xpath('//h1/text()')  # Extraer texto de las etiquetas <h1>
                return h1_tags if h1_tags else ['Sin <h1>']
            else:
                return ['No es una página HTML']  # Si no es HTML, devolver un mensaje
        except requests.RequestException as e:
            print(f"Intento {attempt + 1} fallido al acceder a {page_url}: {e}")
            attempt += 1
            time.sleep(delay)  # Espera entre intentos
    return ['Error al obtener <h1>']

# Obtener los encabezados <h1> de los enlaces
links_with_h1 = []
for link in unique_links:
    if not is_valid_url(link):  # Saltar enlaces no válidos
        continue
    h1_tags = get_h1(link)  # Obtener los encabezados <h1>
    
    # Solo agregar si es una página HTML válida y contiene <h1>
    if 'No es una página HTML' not in h1_tags:
        cleaned_h1_tags = [tag.strip() for tag in h1_tags]  # Limpiar etiquetas <h1>
        links_with_h1.append({
            'url': link,
            'h1': cleaned_h1_tags
        })

# Contar los enlaces encontrados
count_html = len(set(urljoin(url, link) for link in html_links))
count_images = len(set(urljoin(url, link) for link in image_links))
count_css = len(set(urljoin(url, link) for link in css_links))
count_total = len(links_with_h1)

# Guardar los enlaces con encabezados <h1> en un archivo JSON
output_file = 'enlaces_con_h1.json'
with open(output_file, 'w') as file:
    json.dump(links_with_h1, file, indent=4)

# Mostrar los resultados en la consola
print(f"Enlaces encontrados (únicos):")
print(f"- Enlaces HTML: {count_html}")
print(f"- Enlaces de imágenes: {count_images}")
print(f"- Enlaces CSS: {count_css}")
print(f"- Total de enlaces con <h1>: {count_total}\n")

# Mostrar los enlaces y sus encabezados <h1>
for link in links_with_h1:
    print(f"URL: {link['url']}")
    print("Encabezados H1:")
    for h1 in link['h1']:
        print(f"- {h1}")
    print("-" * 40)

print(f"\nEnlaces con encabezados <h1> extraídos y guardados en {output_file}")
