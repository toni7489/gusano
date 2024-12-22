import requests
from lxml import html
from urllib.parse import urljoin
import json

# URL de la página web
url = 'https://brotesverdesonline.com'

# Obtener el contenido de la página
response = requests.get(url)
tree = html.fromstring(response.content)

# Extraer enlaces de distintos elementos
html_links = tree.xpath('//a/@href')  # Enlaces de etiquetas <a>
image_links = tree.xpath('//img/@src')  # Enlaces de imágenes <img>
css_links = tree.xpath('//link[@rel="stylesheet"]/@href')  # Enlaces a archivos CSS

# Combinar todos los enlaces y convertirlos a absolutos
all_links = html_links + image_links + css_links
absolute_links = [urljoin(url, link) for link in all_links]

# Contar los enlaces encontrados
count_html = len(html_links)
count_images = len(image_links)
count_css = len(css_links)
count_total = len(absolute_links)

# Guardar los enlaces en un archivo JSON con un enlace por línea
output_file = 'enlaces.json'
with open(output_file, 'w') as file:
    for link in absolute_links:
        file.write(json.dumps(link) + '\n')  # Cada enlace en una línea en formato JSON

# Mostrar los resultados en la consola
print(f"Enlaces encontrados:")
print(f"- Enlaces HTML: {count_html}")
print(f"- Enlaces de imágenes: {count_images}")
print(f"- Enlaces CSS: {count_css}")
print(f"- Total de enlaces: {count_total}\n")

for link in absolute_links:
    print(link)

print(f"\nEnlaces extraídos y guardados en {output_file}")
