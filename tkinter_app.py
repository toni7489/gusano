import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from lxml import html
from urllib.parse import urljoin
import threading
import pandas as pd
import mimetypes

# Funciones para obtener los enlaces, título, H1, meta descripción, código de estado y tipo
def extract_info_from_url(url, callback, processed_urls):
    response = requests.get(url)
    tree = html.fromstring(response.content)

    html_links = tree.xpath('//a/@href')
    image_links = tree.xpath('//img/@src')
    css_links = tree.xpath('//link[@rel="stylesheet"]/@href')
    js_links = tree.xpath('//script[@src]/@src')

    all_links = html_links + image_links + css_links + js_links
    absolute_links = [urljoin(url, link) for link in all_links]
    unique_links = list(set(absolute_links))

    def is_valid_url(link):
        return link and link.startswith(('http', 'https', 'www'))

    def get_file_type(page_url):
        # Intentar identificar el tipo de archivo usando la extensión del archivo en la URL
        file_type, _ = mimetypes.guess_type(page_url)
        if file_type:
            if 'image' in file_type:
                return 'Imagen'
            elif 'html' in file_type:
                return 'HTML'
            elif 'css' in file_type:
                return 'CSS'
            elif 'javascript' in file_type or 'js' in file_type:
                return 'JavaScript'
        # Si no se puede determinar a partir de la extensión, hacer una verificación con HEAD
        try:
            response = requests.head(page_url, timeout=10)
            content_type = response.headers.get('Content-Type', '')
            if 'image' in content_type:
                return 'Imagen'
            elif 'html' in content_type:
                return 'HTML'
            elif 'css' in content_type:
                return 'CSS'
            elif 'javascript' in content_type or 'js' in content_type:
                return 'JavaScript'
            return 'Desconocido'
        except requests.RequestException:
            return 'Error'

    def get_status_code(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            return response.status_code
        except requests.RequestException as e:
            return f'Error: {e}'

    def get_title(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                title = page_tree.xpath('//title/text()')
                return title[0].strip() if title else 'Sin título'
            return ''
        except requests.RequestException:
            return 'Error al obtener título'

    def get_h1(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                h1 = page_tree.xpath('//h1/text()')
                return h1[0].strip() if h1 else 'Sin etiqueta H1'
            return ''
        except requests.RequestException:
            return 'Error al obtener H1'

    def get_meta_description(page_url):
        try:
            response = requests.get(page_url, timeout=10)
            if 'text/html' in response.headers.get('Content-Type', ''):
                page_tree = html.fromstring(response.content)
                meta_description = page_tree.xpath('//meta[@name="description"]/@content')
                return meta_description[0].strip() if meta_description else 'Sin meta descripción'
            return ''
        except requests.RequestException:
            return 'Error al obtener meta descripción'

    # Recorrer los enlaces únicos obtenidos de la página
    for link in unique_links:
        if not is_valid_url(link):  # Saltar enlaces no válidos
            continue
        if link in processed_urls:  # Verificar si la URL ya fue procesada
            continue

        # Marcar la URL como procesada
        processed_urls.add(link)

        # Obtener información del enlace
        status_code = get_status_code(link)  # Capturar el código de respuesta
        title = get_title(link)
        h1 = get_h1(link)
        meta_description = get_meta_description(link)
        file_type = get_file_type(link)

        result = {
            'Código de Respuesta': status_code,  # Ahora está primero
            'URL': link,
            'Tipo': file_type,  # Ahora está segundo
            'Título': title,
            'Etiqueta H1': h1,
            'Meta Descripción': meta_description,
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
    collected_data.clear()  # Limpiar datos previos
    processed_urls.clear()  # Limpiar URLs procesadas previamente
    result_tree.insert("", "end", text="Iniciando análisis...")

    # Crear hilo para no bloquear la interfaz
    def run_analysis():
        try:
            processed_urls.add(url)  # Agregar la URL inicial como procesada
            extract_info_from_url(url, update_treeview, processed_urls)
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
    item_id = result_tree.insert("", "end", values=(result['Código de Respuesta'], result['URL'], result['Tipo'], result['Título'], result['Etiqueta H1'], result['Meta Descripción']))

    # Alternar colores de fondo de las filas (filas de gris claro y gris oscuro alternadas)
    row_index = len(result_tree.get_children()) - 1  # Índice de la fila

    if row_index % 2 == 0:  # Filas pares color gris oscuro
        result_tree.item(item_id, tags=("dark_gray_row",))
    else:  # Filas impares color gris claro
        result_tree.item(item_id, tags=("light_gray_row",))

    # Actualizar el contador de enlaces
    collected_data.append(result)
    link_count_label.config(text=f"Enlaces encontrados: {len(result_tree.get_children())}")

# Función para exportar resultados a Excel
def export_to_excel():
    if not collected_data:
        messagebox.showerror("Error", "No hay datos para exportar.")
        return
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".xlsx",
        filetypes=[("Archivos de Excel", "*.xlsx")],
        title="Guardar como"
    )
    if not file_path:
        return  # El usuario canceló el guardado
    
    df = pd.DataFrame(collected_data)
    try:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Éxito", "Resultados exportados a Excel correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar a Excel: {e}")

# Variables globales
collected_data = []
processed_urls = set()  # Conjunto para almacenar las URLs procesadas

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Analizador de Enlaces SEO")

# Configuración de la ventana para adaptarse al tamaño de la pantalla
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Configurar tamaño inicial (80% de la pantalla) y centrar
window_width = int(screen_width * 0.8)
window_height = int(screen_height * 0.8)
x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
root.resizable(True, True)

# Crear un Frame para la URL
frame = tk.Frame(root)
frame.pack(pady=10)

url_label = tk.Label(frame, text="Ingresa la URL:")
url_label.pack(side="left", padx=5)

url_entry = tk.Entry(frame, width=50)
url_entry.pack(side="left", padx=5)

analyze_button = tk.Button(frame, text="Iniciar Análisis", command=analyze_url)
analyze_button.pack(side="left", padx=5)

status_label = tk.Label(root, text="Esperando para iniciar el análisis...")
status_label.pack(pady=5)

link_count_label = tk.Label(root, text="Enlaces encontrados: 0")
link_count_label.pack(pady=5)

# Crear un árbol para mostrar los resultados
columns = ("Respuesta", "URL", "Tipo", "Título", "Etiqueta H1", "Meta Descripción")
result_tree = ttk.Treeview(root, columns=columns, show="headings", height=20)
for col in columns:
    result_tree.heading(col, text=col)

result_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Agregar una barra de desplazamiento
scrollbar = tk.Scrollbar(root, orient="vertical", command=result_tree.yview)
result_tree.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Botón de exportar a Excel al final de la interfaz
bottom_frame = tk.Frame(root)
bottom_frame.pack(side="bottom", fill="x", pady=10)

export_button = tk.Button(bottom_frame, text="Exportar a Excel", command=export_to_excel)
export_button.pack(side="left", padx=10)

# Ejecutar la aplicación
root.mainloop()
