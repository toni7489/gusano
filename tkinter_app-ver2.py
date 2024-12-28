import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from lxml import html
from urllib.parse import urljoin
import threading
import pandas as pd
import mimetypes
import webbrowser

# Funciones para obtener los enlaces, título, H1, meta descripción, código de estado y tipo
def extract_info_from_url(url, callback, processed_urls, depth=1):
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

    for link in unique_links:
        if not is_valid_url(link):
            continue
        if link in processed_urls:
            continue

        processed_urls.add(link)

        status_code = get_status_code(link)
        title = get_title(link)
        h1 = get_h1(link)
        meta_description = get_meta_description(link)
        file_type = get_file_type(link)

        result = {
            'Código de Respuesta': status_code,
            'URL': link,
            'Tipo': file_type,
            'Título': title,
            'Etiqueta H1': h1,
            'Meta Descripción': meta_description,
            'Profundidad': depth
        }

        callback(result)

        if depth < 3:  # Limitar la profundidad a 3, ajusta según sea necesario
            extract_info_from_url(link, callback, processed_urls, depth + 1)

    callback("FIN")

# Función para actualizar la interfaz mientras se obtiene la información
def analyze_url():
    url = url_entry.get()
    if not url:
        messagebox.showerror("Error", "Debes ingresar una URL.")
        return

    result_tree.delete(*result_tree.get_children())
    collected_data.clear()
    processed_urls.clear()
    result_tree.insert("", "end", text="Iniciando análisis...")

    def run_analysis():
        try:
            processed_urls.add(url)
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

    result_tree.insert("", "end", values=(result['Código de Respuesta'], result['URL'], result['Tipo'], result['Título'], result['Etiqueta H1'], result['Meta Descripción'], result['Profundidad']))

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
        return
    
    df = pd.DataFrame(collected_data)
    try:
        df.to_excel(file_path, index=False)
        messagebox.showinfo("Éxito", "Resultados exportados a Excel correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo exportar a Excel: {e}")

# Función para abrir URL al hacer doble clic en el Treeview
def open_url(event):
    selected_item = result_tree.selection()
    if selected_item:
        url = result_tree.item(selected_item[0])['values'][1]
        webbrowser.open(url)

# Variables globales
collected_data = []
processed_urls = set()

# Crear la interfaz gráfica
root = tk.Tk()
root.title("Analizador de Enlaces SEO")
root.configure(bg="#333333")  # Fondo gris oscuro

# Configuración de la ventana
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

window_width = int(screen_width * 0.8)
window_height = int(screen_height * 0.8)
x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
root.resizable(True, True)

# Crear estilo personalizado
style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Treeview",
    font=("Arial", 10),
    rowheight=25,
    background="#D3D3D3",  # Fondo gris claro
    fieldbackground="#D3D3D3",  # Fondo gris claro para las celdas
    foreground="black",
)
style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#444444", foreground="white")
style.map("Treeview", background=[("selected", "#666666")], foreground=[("selected", "white")])

# Crear un Frame para la URL
frame = tk.Frame(root, bg="#333333")
frame.pack(pady=10)

url_label = tk.Label(frame, text="Ingresa la URL:", bg="#333333", fg="white")
url_label.pack(side="left", padx=5)

url_entry = tk.Entry(frame, width=50)
url_entry.pack(side="left", padx=5)

analyze_button = tk.Button(frame, text="Iniciar Análisis", command=analyze_url)
analyze_button.pack(side="left", padx=5)

status_label = tk.Label(root, text="Esperando para iniciar el análisis...", bg="#333333", fg="white")
status_label.pack(pady=5)

link_count_label = tk.Label(root, text="Enlaces encontrados: 0", bg="#333333", fg="white")
link_count_label.pack(pady=5)

# Crear un árbol para mostrar los resultados
columns = ("Respuesta", "URL", "Tipo", "Título", "Etiqueta H1", "Meta Descripción", "Profundidad")
result_tree = ttk.Treeview(root, columns=columns, show="headings", height=20)
for col in columns:
    result_tree.heading(col, text=col)

result_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

# Agregar una barra de desplazamiento
scrollbar = tk.Scrollbar(root, orient="vertical", command=result_tree.yview)
result_tree.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

# Agregar evento para abrir la URL al hacer doble clic
result_tree.bind("<Double-1>", open_url)

# Botón de exportar a Excel
bottom_frame = tk.Frame(root, bg="#333333")
bottom_frame.pack(side="bottom", fill="x", pady=10)

export_button = tk.Button(bottom_frame, text="Exportar a Excel", command=export_to_excel)
export_button.pack(side="left", padx=10)

# Ejecutar la aplicación
root.mainloop()

