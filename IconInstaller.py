import os
import sys
import ctypes
import requests
import time
import datetime
import threading
import re
import configparser
from io import BytesIO
from PIL import Image
from tkinter import filedialog, Tk

# --- CÓDIGOS DE COLOR ANSI (MODO DARK) ---
RESET = "\033[0m"
BOLD = "\033[1m"
VERDE = "\033[92m"       
ROJO = "\033[91m"        
AMARILLO = "\033[93m"    
BLANCO = "\033[97m"      
GRIS = "\033[90m"        
CYAN = "\033[96m"

# --- CONSTANTES DE DISEÑO ---
ANCHO_VENTANA = 74       
ALTO_VENTANA = 32 
ANCHO_MARCO_H = 68       
ANCHO_TEXTO_UTIL = 66    

# --- GESTIÓN DE CONFIGURACIÓN ---
ARCHIVO_CONFIG = 'settings.ini'
ruta_iconos_cache = ""

def cargar_configuracion():
    config = configparser.ConfigParser()
    if os.path.exists(ARCHIVO_CONFIG):
        config.read(ARCHIVO_CONFIG)
        if 'DEFAULT' in config and 'RutaIconos' in config['DEFAULT']:
            return config['DEFAULT']['RutaIconos']
    return None

def guardar_configuracion(nueva_ruta):
    config = configparser.ConfigParser()
    config['DEFAULT'] = {'RutaIconos': nueva_ruta}
    with open(ARCHIVO_CONFIG, 'w') as configfile:
        config.write(configfile)
    global ruta_iconos_cache
    ruta_iconos_cache = nueva_ruta

# --- SISTEMA ---
def bloquear_redimension():
    os.system(f"mode con: cols={ANCHO_VENTANA} lines={ALTO_VENTANA}")
    hwnd = ctypes.windll.kernel32.GetConsoleWindow()
    estilo_actual = ctypes.windll.user32.GetWindowLongW(hwnd, -16)
    estilo_nuevo = estilo_actual & ~0x00010000 & ~0x00040000
    ctypes.windll.user32.SetWindowLongW(hwnd, -16, estilo_nuevo)

def reloj_titulo():
    while True:
        ahora = datetime.datetime.now().strftime("%H:%M:%S")
        ctypes.windll.kernel32.SetConsoleTitleW(f"Icon Installer - by Gen Castro  |  {ahora}")
        time.sleep(1)

def configurar_consola():
    os.system("") 
    os.system("color 0F") 
    bloquear_redimension()
    hilo = threading.Thread(target=reloj_titulo, daemon=True)
    hilo.start()

# --- DIBUJO ---
def len_visible(texto):
    ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-9:;<=>?]*[ -/]*[@-~])')
    return len(ansi_escape.sub('', str(texto)))

def borde_superior(): print(f" ╔{'═' * ANCHO_MARCO_H}╗")
def borde_inferior(): print(f" ╚{'═' * ANCHO_MARCO_H}╝")
def separador_doble(): print(f" ╠{'═' * ANCHO_MARCO_H}╣")
def separador_simple(): print(f" ╟{'─' * ANCHO_MARCO_H}╢")
def linea_vacia(): print(f" ║ {' ' * ANCHO_TEXTO_UTIL} ║")

def texto_centrado_color(texto):
    texto_puro = str(texto)
    longitud_real = len_visible(texto_puro)
    if longitud_real > ANCHO_TEXTO_UTIL:
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-9:;<=>?]*[ -/]*[@-~])')
        texto = ansi_escape.sub('', texto)[:ANCHO_TEXTO_UTIL]
        longitud_real = len(texto)
    espacios_totales = ANCHO_TEXTO_UTIL - longitud_real
    izq = espacios_totales // 2
    der = espacios_totales - izq
    print(f" ║ {' '*izq}{texto}{' '*der} ║")

def texto_izquierda_color(texto):
    longitud_real = len_visible(texto)
    der = ANCHO_TEXTO_UTIL - longitud_real
    print(f" ║ {texto}{' '*der} ║")

def encabezado_dbi():
    ahora = datetime.datetime.now()
    fecha_str = ahora.strftime("%Y-%m-%d %H:%M") 
    titulo = "ICON INSTALLER"
    firma = "by Gen Castro"
    
    espacio1 = (ANCHO_TEXTO_UTIL // 2) - len(titulo) - (len(firma) // 2)
    espacio2 = ANCHO_TEXTO_UTIL - len(titulo) - len(firma) - len(fecha_str) - espacio1
    
    borde_superior()
    print(f" ║ {BLANCO}{titulo}{RESET}{' ' * espacio1}{GRIS}{firma}{RESET}{' ' * espacio2}{fecha_str} ║")
    separador_doble()

def dibujar_interfaz(estado="Esperando...", ultimo_target="---"):
    os.system("cls")
    print("\n")
    encabezado_dbi()
    
    linea_vacia()
    texto_centrado_color(f"ESTADO: {estado}")
    linea_vacia()
    separador_simple()
    
    ruta_display = ruta_iconos_cache
    if len(ruta_display) > 40: ruta_display = "..." + ruta_display[-37:]
    
    linea_vacia()
    texto_izquierda_color(f"  ALMACEN ICONOS: {GRIS}{ruta_display}{RESET}")
    linea_vacia()
    separador_simple()

    linea_vacia()
    texto_centrado_color("ULTIMO PROCESADO:")
    texto_centrado_color(f"{BOLD}{ultimo_target}{RESET}")
    linea_vacia()
    separador_doble()
    
    linea_vacia()
    texto_izquierda_color(f"  {BOLD}OPCIONES DE ENTRADA:{RESET}")
    texto_izquierda_color("  1. Pega una URL de internet.")
    # NUEVA INSTRUCCIÓN
    texto_izquierda_color(f"  2. {CYAN}Arrastra una imagen{RESET} aquí dentro.") 
    texto_izquierda_color(f"  3. Escribe {AMARILLO}'config'{RESET} para opciones.")
    linea_vacia()
    borde_inferior()
    print("\n")

# --- LÓGICA PRINCIPAL ---
def seleccionar_carpeta(titulo_ventana="SELECCIONAR CARPETA"):
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    folder = filedialog.askdirectory(title=titulo_ventana)
    root.destroy()
    return folder

def procesar():
    global ruta_iconos_cache
    
    # 1. SETUP INICIAL
    ruta_iconos_cache = cargar_configuracion()
    
    if not ruta_iconos_cache:
        print(f"\n  {AMARILLO}[CONFIGURACIÓN INICIAL]{RESET}")
        print("  Selecciona dónde se guardarán los archivos .ico generados.")
        time.sleep(2)
        ruta = seleccionar_carpeta("SELECCIONA ALMACEN DE ICONOS")
        if ruta:
            guardar_configuracion(ruta)
        else:
            print(f"  {ROJO}Error: Ruta obligatoria.{RESET}")
            time.sleep(2)
            return

    ultimo_target = "Ninguno"
    msg_estado = f"{VERDE}Esperando Imagen (URL o Local){RESET}"

    while True:
        dibujar_interfaz(msg_estado, ultimo_target)
        try:
            print(f"  {AMARILLO}> ARRASTRA IMAGEN / PEGA URL:{RESET} ", end="")
            entrada = input().strip()
        except: break
        
        if not entrada: continue
        if entrada.lower() == 'salir': break
        
        # LIMPIEZA DE COMILLAS (Windows las pone al arrastrar)
        entrada = entrada.strip('"').strip("'")
        
        if entrada.lower() == 'config':
            msg_estado = f"{AMARILLO}Configurando...{RESET}"
            dibujar_interfaz(msg_estado, ultimo_target)
            nueva_ruta = seleccionar_carpeta("SELECCIONA NUEVO ALMACEN DE ICONOS")
            if nueva_ruta:
                guardar_configuracion(nueva_ruta)
                msg_estado = f"{VERDE}Almacén actualizado{RESET}"
            else:
                msg_estado = f"{ROJO}Cambio cancelado{RESET}"
            continue

        # --- LÓGICA HÍBRIDA (URL vs LOCAL) ---
        img = None
        
        # CASO A: Es una URL (empieza por http)
        if entrada.lower().startswith("http"):
            msg_estado = f"{AMARILLO}Descargando de internet...{RESET}"
            dibujar_interfaz(msg_estado, ultimo_target)
            try:
                headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
                response = requests.get(entrada, headers=headers, timeout=10)
                response.raise_for_status()
                img = Image.open(BytesIO(response.content))
            except Exception as e:
                msg_estado = f"{ROJO}ERROR URL: {str(e)[:25]}{RESET}"
                continue
        
        # CASO B: Es un Archivo Local (existe en el disco)
        elif os.path.exists(entrada):
            msg_estado = f"{CYAN}Cargando archivo local...{RESET}"
            dibujar_interfaz(msg_estado, ultimo_target)
            try:
                img = Image.open(entrada)
            except Exception as e:
                msg_estado = f"{ROJO}ERROR ARCHIVO: No es imagen{RESET}"
                continue
        
        # CASO C: No es nada válido
        else:
            msg_estado = f"{ROJO}Entrada no válida{RESET}"
            continue

        # --- PROCESAMIENTO COMÚN ---
        # Asegurar RGBA
        if img.mode != 'RGBA': 
            img = img.convert('RGBA')

        # SELECCION CARPETA
        msg_estado = f"{AMARILLO}Selecciona carpeta destino...{RESET}"
        dibujar_interfaz(msg_estado, ultimo_target)
        carpeta = seleccionar_carpeta("SELECCIONA LA CARPETA A PERSONALIZAR")
        
        if not carpeta:
            msg_estado = f"{ROJO}Cancelado{RESET}"
            continue
        
        nombre = os.path.basename(carpeta)
        ultimo_target = nombre[:45]

        # GUARDAR ICO
        try:
            if not os.path.exists(ruta_iconos_cache): os.makedirs(ruta_iconos_cache)
            ruta_ico = os.path.join(ruta_iconos_cache, f"{nombre}.ico")
            
            img = img.resize((256, 256), Image.LANCZOS)
            img.save(ruta_ico, format='ICO', sizes=[(256, 256)])
        except Exception as e:
             msg_estado = f"{ROJO}ERROR GUARDADO: {str(e)[:30]}{RESET}"
             continue

        # APLICAR
        try:
            ini = os.path.join(carpeta, "desktop.ini")
            if os.path.exists(ini):
                os.system(f'attrib -h -s -r "{ini}" >nul 2>&1')
                try: os.remove(ini)
                except: pass
            
            with open(ini, 'w') as f:
                f.write(f"[.ShellClassInfo]\nIconResource={ruta_ico},0\n[ViewState]\nMode=\nVid=\nFolderType=Generic")

            os.system(f'attrib +h +s "{ini}"')
            os.system(f'attrib +r "{carpeta}"')
            ctypes.windll.shell32.SHChangeNotify(0x08000000, 0x0000, None, None)
            
            msg_estado = f"{VERDE}EXITO - Icono aplicado{RESET}"
        except:
            msg_estado = f"{ROJO}ERROR DE SISTEMA{RESET}"

if __name__ == "__main__":
    try:
        configurar_consola()
        procesar()
    except: pass