from flask import Flask, render_template, request, send_file
import requests
from lxml import html
from urllib.parse import urljoin
import pandas as pd
import time
import os

app = Flask(__name__)

# Función para obtener enlaces, título, H1 y meta descripción
def extract_info_from_url(url):
    # Obtener el contenido de la página principal
    response = requests.get(url)
    tree = html.fromstring(response.content)

    # Extraer enlaces de distintos elementos
    html_links = tree.xpath('//a/@href')
    image_links = tree.xpath('//img/@src')
    css_links = tree.xpath('//link[@rel="stylesheet"]/@href')

    # Combinar todos los enlaces y convertirlos a absolutos
    all_links = html_links + image_links + css_links
    absolute_links = [urljoin(url, link) for link in all_links]

    # Eliminar duplicados
    unique_links = list(set(absolute_links))

    # Filtrar enlaces no válidos
    def is_valid_url(link):
        return link and link.startswith(('http', 'https', 'www'))

    def get_title(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                title = page_tree.xpath('//title/text()')
                return title[0].strip() if title else 'Sin título'
            return 'No es una página HTML'
        except requests.RequestException:
            return 'Error al obtener título'

    def get_h1(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                h1 = page_tree.xpath('//h1/text()')
                return h1[0].strip() if h1 else 'Sin etiqueta H1'
            return 'No es una página HTML'
        except requests.RequestException:
            return 'Error al obtener H1'

    def get_meta_description(page_url, retries=3, delay=5):
        attempt = 0
        while attempt < retries:
            try:
                response = requests.get(page_url, timeout=10)
                if 'text/html' in response.headers.get('Content-Type', ''):
                    page_tree = html.fromstring(response.content)
                    meta_description = page_tree.xpath('//meta[@name="description"]/@content')
                    if meta_description:
                        return meta_description[0].strip()
                    return 'Sin meta descripción'
                return 'No es una página HTML'
            except requests.RequestException:
                attempt += 1
                time.sleep(delay)
        return 'Error al obtener meta descripción'

    # Extraer los datos de los enlaces
    data = []
    for link in unique_links:
        if not is_valid_url(link):  # Saltar enlaces no válidos
            continue
        title = get_title(link)
        h1 = get_h1(link)
        meta_description = get_meta_description(link)
        
        # Agregar los datos al listado
        data.append({
            'URL': link,
            'Título': title,
            'Etiqueta H1': h1,
            'Meta Descripción': meta_description
        })

    return data


@app.route('/', methods=['GET', 'POST'])
def index():
    data = []
    if request.method == 'POST':
        url = request.form['url']
        if url:
            # Procesar el sitio web y obtener la información
            data = extract_info_from_url(url)
        else:
            data = []

        # Si hay datos, generar el archivo Excel
        if data:
            # Crear un DataFrame de pandas
            df = pd.DataFrame(data)
            output_file = "resultados.xlsx"
            df.to_excel(output_file, index=False, engine='openpyxl')

            return render_template('index.html', data=data, download_link=output_file)

    return render_template('index.html', data=data)


@app.route('/download/<filename>')
def download(filename):
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
