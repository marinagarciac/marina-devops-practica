"""Cliente Python de la API REST de la Tienda Online.

Este script es independiente del servidor: no importa TiendaService ni los
modelos. Toda la comunicación se hace con peticiones HTTP usando `requests`.

Uso:
    python cliente.py                                  # usa BASE_URL por defecto
    python cliente.py --url http://192.168.1.34:8000   # API en otro equipo
"""

import argparse
import json
import sys
import time

import requests

# Dirección base de la API. Cámbiala aquí o pásala con --url.
# Para probar entre dos equipos: "http://<IP_DEL_SERVIDOR>:8000"
BASE_URL = "http://localhost:8000"

TIMEOUT = 5  # segundos


class ErrorAPI(Exception):
    """La API ha respondido con un código distinto del esperado."""


def mostrar(titulo: str, datos) -> None:
    print(f"\n=== {titulo} ===")
    print(json.dumps(datos, indent=2, ensure_ascii=False))


def comprobar(respuesta: requests.Response, esperado: int):
    """Comprueba el código de estado y devuelve el JSON de la respuesta."""
    print(f"{respuesta.request.method} {respuesta.url} -> {respuesta.status_code}")
    if respuesta.status_code != esperado:
        try:
            detalle = respuesta.json().get("detail")
        except ValueError:
            detalle = respuesta.text
        raise ErrorAPI(f"Se esperaba {esperado} y se recibió {respuesta.status_code}: {detalle}")
    return respuesta.json() if respuesta.content else None


# ----------------------------------------------------------- Llamadas a la API


def crear_usuario(nombre: str, email: str, direccion_postal: str, tipo: str = "cliente") -> dict:
    datos = {"nombre": nombre, "email": email, "tipo": tipo, "direccion_postal": direccion_postal}
    r = requests.post(f"{BASE_URL}/usuarios", json=datos, timeout=TIMEOUT)
    return comprobar(r, 201)


def listar_usuarios() -> list[dict]:
    r = requests.get(f"{BASE_URL}/usuarios", timeout=TIMEOUT)
    return comprobar(r, 200)


def obtener_usuario(usuario_id: int) -> dict:
    r = requests.get(f"{BASE_URL}/usuarios/{usuario_id}", timeout=TIMEOUT)
    return comprobar(r, 200)


def crear_producto(datos: dict) -> dict:
    r = requests.post(f"{BASE_URL}/productos", json=datos, timeout=TIMEOUT)
    return comprobar(r, 201)


def listar_productos() -> list[dict]:
    r = requests.get(f"{BASE_URL}/productos", timeout=TIMEOUT)
    return comprobar(r, 200)


def crear_pedido(cliente_id: int, items: list[dict]) -> dict:
    datos = {"cliente_id": cliente_id, "items": items}
    r = requests.post(f"{BASE_URL}/pedidos", json=datos, timeout=TIMEOUT)
    return comprobar(r, 201)


def pedidos_de_cliente(cliente_id: int) -> list[dict]:
    r = requests.get(f"{BASE_URL}/usuarios/{cliente_id}/pedidos", timeout=TIMEOUT)
    return comprobar(r, 200)


# ------------------------------------------------------------- Flujo de prueba


def main() -> int:
    print(f"Usando la API en {BASE_URL}")

    # Sufijo para que el email no se repita si el script se ejecuta varias veces
    sufijo = int(time.time())

    try:
        # 1. Crear un usuario
        usuario = crear_usuario(
            nombre="Laura Martínez",
            email=f"laura.{sufijo}@example.com",
            direccion_postal="Rúa do Príncipe 12, Vigo",
        )
        mostrar("Usuario creado", usuario)

        # 2. Consultar la lista de usuarios
        usuarios = listar_usuarios()
        mostrar(f"Usuarios registrados ({len(usuarios)})", usuarios)

        # 3. Crear varios productos (uno de cada tipo)
        nuevos = [
            {"tipo": "generico", "nombre": "Taza de cerámica", "precio": 7.5, "stock": 30},
            {"tipo": "electronico", "nombre": "Auriculares Bluetooth", "precio": 59.9, "stock": 10, "meses_garantia": 24},
            {"tipo": "ropa", "nombre": "Camiseta básica", "precio": 19.99, "stock": 50, "talla": "M", "color": "Azul"},
        ]
        creados = []
        for datos in nuevos:
            producto = crear_producto(datos)
            creados.append(producto)
            mostrar("Producto creado", producto)

        # 4. Consultar la lista de productos
        productos = listar_productos()
        mostrar(f"Productos disponibles ({len(productos)})", productos)

        # 5. Crear un pedido para el usuario
        items = [
            {"producto_id": creados[1]["id"], "cantidad": 1},
            {"producto_id": creados[2]["id"], "cantidad": 2},
        ]
        pedido = crear_pedido(usuario["id"], items)
        mostrar("Pedido creado", pedido)
        print(f"Total del pedido: {pedido['total']:.2f} €")

        # 6. Consultar los pedidos del usuario
        pedidos = pedidos_de_cliente(usuario["id"])
        mostrar(f"Pedidos de {usuario['nombre']} ({len(pedidos)})", pedidos)

        # Comprobación extra: la API rechaza un pedido sin stock suficiente
        print("\n=== Prueba de error: pedido con stock insuficiente ===")
        try:
            crear_pedido(usuario["id"], [{"producto_id": creados[1]["id"], "cantidad": 1000}])
        except ErrorAPI as e:
            print(f"Error esperado -> {e}")

    except requests.exceptions.ConnectionError:
        print(f"\nNo se pudo conectar con la API en {BASE_URL}. ¿Está el servidor en marcha?")
        return 1
    except requests.exceptions.Timeout:
        print(f"\nLa API en {BASE_URL} no respondió en {TIMEOUT} s.")
        return 1
    except ErrorAPI as e:
        print(f"\nError de la API: {e}")
        return 1

    print("\nFlujo completado correctamente.")
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Cliente de la API de la Tienda Online")
    parser.add_argument("--url", default=BASE_URL, help=f"Dirección base de la API (por defecto {BASE_URL})")
    BASE_URL = parser.parse_args().url.rstrip("/")
    sys.exit(main())
