import getopt
import sys
import subprocess
import requests
import time
from getmac import get_mac_address

OUI_DATABASE_FILE = 'manuf.txt'

def obtener_datos_por_ip(ip, database):
    try:
        mac = get_mac_address(ip=ip)
        if mac:
            vendor, elapsed_time = solicitudDB(mac)
            return mac, vendor, elapsed_time
        else:
            return None, f"Error: No se pudo obtener la dirección MAC para la IP: {ip}", 0
    except Exception as e:
        return None, str(e), 0

def obtener_datos_por_mac(mac, database):
    vendor, elapsed_time = solicitudDB(mac)
    return mac, vendor, elapsed_time

def mostrar_tabla_arp():
    try:
        arp_table = subprocess.check_output(["arp", "-a"], universal_newlines=True)
        print(arp_table)
    except subprocess.CalledProcessError:
        print("No se pudo obtener la tabla ARP.")
    except FileNotFoundError:
        print("El comando 'arp' no está disponible en tu sistema.")

def solicitudDB(mac):
    api_url = f"https://api.maclookup.app/v2/macs/{mac}"

    try:
        start_time = time.time()
        response = requests.get(api_url, timeout=5)
        end_time = time.time()
        elapsed_time = end_time - start_time

        if response.status_code == 200:
            data = response.json()
            vendor = data.get('company', 'No se encontró información')
            return vendor, elapsed_time
        else:
            error_message = f"Error en la solicitud a la API. Código de estado: {response.status_code}"
            if response.status_code == 404:
                error_message += " (No se encontró información para la dirección MAC proporcionada)"
            return error_message, elapsed_time

    except requests.exceptions.Timeout:
        return "Tiempo de espera agotado al conectar con la API", elapsed_time
    except requests.exceptions.RequestException as e:
        return str(e), elapsed_time
    except Exception as e:
        # Bloque general para capturar cualquier excepción no manejada
        return f"Error inesperado: {str(e)}", 0

def main(argv):
    ip = None
    mac = None
    show_arp = False

    try:
        opts, args = getopt.getopt(argv, "hi:m:", ["ip=", "mac=", "arp", "help"])

    except getopt.GetoptError:
        print("Uso: python OUILookup.py --ip <IP> --mac <MAC> --arp [--help]")
        sys.exit(2)

    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("Uso: python OUILookup.py --ip <IP> --mac <MAC> --arp [--help]")
            print("--ip: IP del host a consultar.")
            print("--mac: MAC address a consultar.")
            print("--arp: Muestra la tabla ARP.")
            sys.exit()

        if opt in ("-i", "--ip"):
            ip = arg

        if opt in ("-m", "--mac"):
            mac = arg

        if opt == "--arp":
            show_arp = True

    if show_arp:
        mostrar_tabla_arp()
    elif ip:
        mac, vendor, elapsed_time = obtener_datos_por_ip(ip, OUI_DATABASE_FILE)
        if mac:
            if "Error" in vendor:
                print(f"Error: {vendor}")
            else:
                print(f"IP address: {ip}")
                print(f"MAC address: {mac}")
                print(f"Fabricante: {vendor}")
                print(f"Tiempo de respuesta: {elapsed_time} segundos")
        else:
            print(f"Error: {vendor}")
    elif mac:
        mac, vendor, elapsed_time = obtener_datos_por_mac(mac, OUI_DATABASE_FILE)
        if "Error" in vendor:
            print(f"Error: {vendor}")
        else:
            print(f"MAC address: {mac}")
            print(f"Fabricante: {vendor}")
            print(f"Tiempo de respuesta: {elapsed_time} segundos")
    else:
        print("Debe proporcionar una opción válida (--ip, --mac, --arp, o --help.")

if __name__ == "__main__":
    main(sys.argv[1:])