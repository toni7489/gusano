import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from lxml import html
from urllib.parse import urljoin
import threading

# Funciones para obtener los enlaces, título, H1, meta descripción y código de estado
def extract_info_from_url(url, callback):
    response = requests.get(url)
    tree = html.fromstring(response.content)

    html_links = tree.xpath('//a/@href')
    image_links = tree.xpath('//img/@src')
    css_links = tree.xpath('//link[@rel="stylesheet"]/@href')

    all_links = html_links + image_links + css_links
    absolute_links = [urljoin(url, link) for link in all_links]
    unique_links = list(set(absolute_links))

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

    def get_meta_description(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                meta_description = page_tree.xpath('//meta[@name="description"]/@content')
                return meta_description[0].strip() if meta_description else 'Sin meta descripción'
            return 'No es una página HTML'
        except requests.RequestException:
            return 'Error al obtener meta descripción'

    def get_status_code(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            return response.status_code
        except requests.RequestException:
            return 'Error'

    data = []
    for link in unique_links:
        if not is_valid_url(link):  # Saltar enlaces no válidos
            continue
        title = get_title(link)
        h1 = get_h1(link)
        meta_description = get_meta_description(link)
        status_code = get_status_code(link)

        result = {
            'URL': link,
            'Título': title,
            'Etiqueta H1': h1,
            'Meta Descripción': meta_description,
            'Código de Respuesta': status_code
        }
        # Llamar al callback para insertar el resultado en el Treeview
        callback(result)

    callback("FIN")  # Indicador de fin de proceso

# Función para actualizar la interfaz mientras se obtiene la información
def analyze_url():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Debes ingresar una URL.")
        return

    result_tree.delete(*result_tree.get_children())  # Limpiar resultados previos
    result_tree.insert("", "end", text="Iniciando análisis...")

    # Crear hilo para no bloquear la interfaz
    def run_analysis():
        try:
            results = extract_info_from_url(url, update_treeview)
            status_label.config(text=f"Análisis completado.")
        except Exception as e:
            messagebox.showerror("Error", f"Hubo un problema al procesar la URL: {e}")
            status_label.config(text="Error en el análisis.")
    
    threading.Thread(target=run_analysis, daemon=True).start()

# Función que se llama para insertar los resultados en el Treeview
def update_treeview(result):
    if result == "FIN":
        return

    # Inserta el resultado en el Treeview de manera progresiva
    result_tree.insert("", "end", values=(result['URL'], result['Título'], result['Etiqueta H1'], result['Meta Descripción'], result['Código de Respuesta']))
    
    # Actualiza el contador de enlaces
    link_count_label.config(text=f"Enlaces encontrados: {len(result_tree.get_children())}")

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Analizador de Enlaces SEO")

# Configuración de la ventana
root.geometry("800x600")  # Tamaño inicial
root.resizable(True, True)  # Permitir el cambio de tamaño

# Crear un Frame para alinear la URL Label y el Entry en la misma línea
frame = tk.Frame(root)
frame.pack(pady=10)

url_label = tk.Label(frame, text="Ingresa la URL:")
url_label.pack(side="left", padx=5)

url_entry = tk.Entry(frame, width=50)
url_entry.pack(side="left", padx=5)

analyze_button = tk.Button(root, text="Iniciar Análisis", command=analyze_url)
analyze_button.pack(pady=10)

status_label = tk.Label(root, text="Esperando para iniciar el análisis...")
status_label.pack(pady=5)

link_count_label = tk.Label(root, text="Enlaces encontrados: 0")
link_count_label.pack(pady=5)

# Crear un árbol para mostrar los resultados
columns = ("URL", "Título", "Etiqueta H1", "Meta Descripción", "Código de Respuesta")
result_tree = ttk.Treeview(root, columns=columns, show="headings", height=20)
for col in columns:
    result_tree.heading(col, text=col)

result_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Agregar una barra de desplazamiento para el árbol de resultados
scrollbar = tk.Scrollbar(root, orient="vertical", command=result_tree.yview)
result_tree.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Ejecutar la aplicación
root.mainloop()
