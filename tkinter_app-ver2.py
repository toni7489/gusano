import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import requests
from lxml import html
from urllib.parse import urljoin
import threading
import pandas as pd
import mimetypes
import webbrowser
import json





def open_results(): # Implementa la lógica para abrir resultados guardados
    file_path = filedialog.askopenfilename(
        defaultextension=".json",
        filetypes=[("Archivos JSON", "*.json")],
        title="Abrir análisis guardado"
    )
    
    if not file_path:
        return
    
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            loaded_data = json.load(file)
        
        result_tree.delete(*result_tree.get_children())
        collected_data.clear()
        
        for item in loaded_data:
            result_tree.insert("", "end", values=(
                item['Código de Respuesta'],
                item['URL'],
                item['Tipo'],
                item['Título'],
                item['Etiqueta H1'],
                item['Meta Descripción'],
                item['Profundidad']
            ))
            collected_data.append(item)
        
        link_count_label.config(text=f"Enlaces encontrados: {len(collected_data)}")
        status_label.config(text="Resultados cargados correctamente.")
        messagebox.showinfo("Éxito", "Análisis cargado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo cargar el análisis: {e}")



def save_results():# Logica para guardar resultados
    if not collected_data:
        messagebox.showerror("Error", "No hay datos para guardar.")
        return
    
    file_path = filedialog.asksaveasfilename(
        defaultextension=".json",
        filetypes=[("Archivos JSON", "*.json")],
        title="Guardar análisis"
    )
    
    if not file_path:
        return
    
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            json.dump(collected_data, file, ensure_ascii=False, indent=4)
        messagebox.showinfo("Éxito", "Análisis guardado correctamente.")
    except Exception as e:
        messagebox.showerror("Error", f"No se pudo guardar el análisis: {e}")


def show_config(): # Logica de configuracion
    config_window = tk.Toplevel(root)
    config_window.title("Configuración")
    config_window.geometry("400x200")
    config_window.resizable(False, False)

    tk.Label(config_window, text="Profundidad máxima de escaneo:").grid(row=0, column=0, padx=10, pady=5, sticky="e")
    depth_entry = tk.Entry(config_window)
    depth_entry.insert(0, "3")  # Valor predeterminado
    depth_entry.grid(row=0, column=1, padx=10, pady=5)

    tk.Label(config_window, text="Tiempo de espera (segundos):").grid(row=1, column=0, padx=10, pady=5, sticky="e")
    timeout_entry = tk.Entry(config_window)
    timeout_entry.insert(0, "10")  # Valor predeterminado
    timeout_entry.grid(row=1, column=1, padx=10, pady=5)

    tk.Label(config_window, text="Dominios excluidos (separados por coma):").grid(row=2, column=0, padx=10, pady=5, sticky="e")
    excluded_entry = tk.Entry(config_window)
    excluded_entry.grid(row=2, column=1, padx=10, pady=5)

    def save_config():
        global max_depth, request_timeout, excluded_domains
        max_depth = int(depth_entry.get())
        request_timeout = int(timeout_entry.get())
        excluded_domains = [domain.strip() for domain in excluded_entry.get().split(',') if domain.strip()]
        config_window.destroy()
        messagebox.showinfo("Configuración", "Configuración guardada correctamente.")

    save_button = tk.Button(config_window, text="Guardar", command=save_config)
    save_button.grid(row=3, column=0, columnspan=2, pady=20)


def filter_results():
    # Implementa la lógica para filtrar resultados
    pass

def show_manual():
    # Implementa la lógica para mostrar el manual de usuario
    pass

def show_about():
    messagebox.showinfo("Acerca de", "Analizador de Enlaces SEO\nVersión 1.0\n© 2024 Tu Nombre")

def new_analysis(): #Comienza un analisis nuevo
    url_entry.delete(0, tk.END)
    result_tree.delete(*result_tree.get_children())
    collected_data.clear()
    processed_urls.clear()
    status_label.config(text="Esperando para iniciar el análisis...")
    link_count_label.config(text="Enlaces encontrados: 0")



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
        if depth < 3:
            extract_info_from_url(link, callback, processed_urls, depth + 1)
    callback("FIN")

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

def update_treeview(result):
    if result == "FIN":
        return
    result_tree.insert("", "end", values=(result['Código de Respuesta'], result['URL'], result['Tipo'], result['Título'], result['Etiqueta H1'], result['Meta Descripción'], result['Profundidad']))
    collected_data.append(result)
    link_count_label.config(text=f"Enlaces encontrados: {len(result_tree.get_children())}")

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

def open_url(event):
    selected_item = result_tree.selection()
    if selected_item:
        url = result_tree.item(selected_item[0])['values'][1]
        webbrowser.open(url)

collected_data = []
processed_urls = set()

root = tk.Tk()
root.title("Analizador de Enlaces SEO")
root.configure(bg="#333333")

# Crear la barra de menú
menu_bar = tk.Menu(root)
root.config(menu=menu_bar)

file_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Archivo", menu=file_menu)
file_menu.add_command(label="Nuevo análisis", command=new_analysis)
file_menu.add_command(label="Abrir resultados", command=open_results)
file_menu.add_command(label="Guardar resultados", command=save_results)
file_menu.add_separator()
file_menu.add_command(label="Salir", command=root.quit)

tools_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Herramientas", menu=tools_menu)
tools_menu.add_command(label="Configuración", command=show_config)
tools_menu.add_command(label="Filtrar resultados", command=filter_results)

help_menu = tk.Menu(menu_bar, tearoff=0)
menu_bar.add_cascade(label="Ayuda", menu=help_menu)
help_menu.add_command(label="Manual de usuario", command=show_manual)
help_menu.add_command(label="Acerca de", command=show_about)



screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()
window_width = int(screen_width * 0.8)
window_height = int(screen_height * 0.8)
x_position = (screen_width - window_width) // 2
y_position = (screen_height - window_height) // 2
root.geometry(f"{window_width}x{window_height}+{x_position}+{y_position}")
root.resizable(True, True)

style = ttk.Style()
style.theme_use("clam")
style.configure(
    "Treeview",
    font=("Arial", 10),
    rowheight=25,
    background="#D3D3D3",
    fieldbackground="#D3D3D3",
    foreground="black",
)
style.configure("Treeview.Heading", font=("Arial", 12, "bold"), background="#444444", foreground="white")
style.map("Treeview", background=[("selected", "#666666")], foreground=[("selected", "white")])

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

columns = ("Respuesta", "URL", "Tipo", "Título", "Etiqueta H1", "Meta Descripción", "Profundidad")
result_tree = ttk.Treeview(root, columns=columns, show="headings", height=20)
for col in columns:
    result_tree.heading(col, text=col)
result_tree.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

scrollbar = tk.Scrollbar(root, orient="vertical", command=result_tree.yview)
result_tree.config(yscrollcommand=scrollbar.set)
scrollbar.pack(side="right", fill="y")

result_tree.bind("<Double-1>", open_url)

bottom_frame = tk.Frame(root, bg="#333333")
bottom_frame.pack(side="bottom", fill="x", pady=10)
export_button = tk.Button(bottom_frame, text="Exportar a Excel", command=export_to_excel)
export_button.pack(side="left", padx=10)

root.mainloop()
