from flask import Flask, render_template, request, send_file
import requests
from lxml import html
from urllib.parse import urljoin
import pandas as pd
import os

app = Flask(__name__)

# Función para extraer datos adicionales de una URL
def extract_page_data(url):
    try:
        response = requests.get(url, timeout=10)
        if 'text/html' in response.headers.get('Content-Type', ''):
            tree = html.fromstring(response.content)
            title = tree.xpath('//title/text()')
            h1 = tree.xpath('//h1/text()')
            meta_description = tree.xpath('//meta[@name="description"]/@content')

            return {
                "Código de Respuesta": response.status_code,
                "Título": title[0].strip() if title else "Sin título",
                "Etiqueta H1": h1[0].strip() if h1 else "Sin etiqueta H1",
                "Meta Descripción": meta_description[0].strip() if meta_description else "Sin meta descripción",
            }
        return {
            "Código de Respuesta": response.status_code,
            "Título": "No es HTML",
            "Etiqueta H1": "No es HTML",
            "Meta Descripción": "No es HTML",
        }
    except requests.RequestException as e:
        return {
            "Código de Respuesta": "Error",
            "Título": f"Error: {e}",
            "Etiqueta H1": "Error",
            "Meta Descripción": "Error",
        }

# Función recursiva para analizar enlaces
def analyze_links(url, depth, visited=None, counter=0):
    if visited is None:
        visited = set()

    if depth == 0 or url in visited:
        return [], counter

    visited.add(url)
    try:
        response = requests.get(url, timeout=10)
        if 'text/html' not in response.headers.get('Content-Type', ''):
            return [], counter

        tree = html.fromstring(response.content)
        links = tree.xpath('//a/@href')
        absolute_links = [urljoin(url, link) for link in links]
        unique_links = list(set(absolute_links) - visited)
    except Exception as e:
        print(f"Error procesando {url}: {e}")
        return [], counter

    counter += 1
    page_data = extract_page_data(url)
    print(f"Procesando {counter}: {url}")

    all_data = [{
        "URL": url,
        "Código de Respuesta": page_data["Código de Respuesta"],
        "Título": page_data["Título"],
        "Etiqueta H1": page_data["Etiqueta H1"],
        "Meta Descripción": page_data["Meta Descripción"],
        "Profundidad": depth,
    }]

    for link in unique_links:
        if not link.startswith(('http', 'https')):
            continue
        data, counter = analyze_links(link, depth - 1, visited, counter)
        all_data.extend(data)

    return all_data, counter


@app.route('/', methods=['GET', 'POST'])
def index():
    data = []
    total_links = 0

    if request.method == 'POST':
        url = request.form['url']
        depth = int(request.form['depth'])

        if url:
            print("Iniciando análisis...")
            data, total_links = analyze_links(url, depth)
            print(f"Análisis completado. Total de enlaces analizados: {total_links}")

            df = pd.DataFrame(data)
            output_file = "resultados.xlsx"
            df.to_excel(output_file, index=False, engine='openpyxl')

            return render_template('index.html', data=data, total_links=total_links, download_link=output_file)

    return render_template('index.html', data=data, total_links=total_links)


@app.route('/download/<filename>')
def download(filename):
    return send_file(filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)
