# marina-devops-practica

**Autora:** Marina García

Repositorio de la Práctica 3 de Arquitectura del Software. Parte del código de
la Práctica 2 y lo usa para practicar control de versiones con Git y GitHub
(ramas, commits y Pull Requests) y la contenerización con Docker.

## Descripción de la aplicación

**Tienda Online – API REST con FastAPI.** Aplicación Python que gestiona
usuarios (clientes y administradores), productos (genéricos, electrónicos y de
ropa) y pedidos. La lógica de negocio de `TiendaService` se expone como API REST
con FastAPI y se consume desde tres clientes: la documentación interactiva
Swagger (`/docs`), un cliente Python con `requests` y un frontend web.

## Estructura

```text
marina-devops-practica/
├── src/                        Aplicación FastAPI (servidor)
│   ├── models/                 Clases de dominio de la Práctica 1
│   │   ├── __init__.py
│   │   ├── Producto.py         Producto, ProductoElectronico, ProductoRopa
│   │   ├── Usuario.py          Usuario, Cliente, Administrador
│   │   └── Pedido.py           Pedido
│   ├── Services/
│   │   ├── __init__.py
│   │   └── Tienda_service.py   TiendaService (lógica de negocio)
│   ├── schemas/                Parte 1: esquemas Pydantic
│   │   ├── usuario.py          UsuarioCreate, UsuarioRead
│   │   ├── producto.py         ProductoCreate, ProductoRead
│   │   └── pedido.py           PedidoItemCreate, PedidoCreate, PedidoItemRead, PedidoRead
│   └── main.py                 Parte 2: endpoints (punto de entrada)
├── requirements.txt            Dependencias del servidor
├── cliente/                    Práctica 2 parte 2 – Parte 1: cliente Python
│   ├── cliente.py
│   └── requirements.txt
└── frontend/                   Práctica 2 parte 2 – Parte 3: frontend web
    ├── index.html
    ├── styles.css
    └── app.js
```

Las tres partes están separadas: el cliente y el frontend no importan nada del
servidor y se comunican con él solo mediante HTTP.

### Cambios sobre la Práctica 1

Se reutilizan las clases de dominio y `TiendaService` tal cual. Solo se han
añadido a `TiendaService` tres métodos de consulta que la API necesita:

- `obtener_usuario(usuario_id)` para `GET /usuarios/{usuario_id}`.
- `listar_usuarios()` para `GET /usuarios`.
- `obtener_producto(producto_id)` para `GET /productos/{producto_id}`.

`realizar_pedido` devuelve `None` sin indicar el motivo del fallo. Por eso el
endpoint `POST /pedidos` comprueba antes el cliente, los productos y el stock,
para poder responder con el código y el mensaje adecuados (404 o 400).

## Puesta en marcha

Requiere Python 3.10 o superior.

```bash
python -m pip install -r requirements.txt
cd src
uvicorn main:app --reload
```

- API: <http://localhost:8000>
- Documentación interactiva (Swagger): <http://localhost:8000/docs>

Los datos se guardan en memoria: se pierden al reiniciar el servidor.

## Endpoints

| Método | Ruta | Descripción | Respuestas |
| --- | --- | --- | --- |
| POST | `/usuarios` | Crea un usuario (cliente o administrador) | 201, 409 email repetido, 422 datos no válidos |
| GET | `/usuarios` | Lista los usuarios | 200 |
| GET | `/usuarios/{usuario_id}` | Devuelve un usuario | 200, 404 |
| POST | `/productos` | Crea un producto genérico, electrónico o de ropa | 201, 422 |
| GET | `/productos` | Lista los productos | 200 |
| GET | `/productos/{producto_id}` | Devuelve un producto | 200, 404 |
| DELETE | `/productos/{producto_id}` | Elimina un producto | 204, 404 |
| POST | `/pedidos` | Crea un pedido | 201, 400 stock insuficiente o no es cliente, 404 cliente/producto inexistente, 422 |
| GET | `/usuarios/{cliente_id}/pedidos` | Pedidos de un cliente | 200, 400 no es cliente, 404 |

Los errores siempre tienen el formato `{"detail": ...}`.

### Validaciones de los esquemas

- **UsuarioCreate**: el email debe tener un formato válido, el `tipo` es
  `cliente` o `administrador`, y los clientes deben indicar `direccion_postal`.
- **ProductoCreate**: `precio > 0` y `stock >= 0`. Según el `tipo`:
  `electronico` exige `meses_garantia`; `ropa` exige `talla` y `color`; y no se
  admiten atributos que no correspondan al tipo.
- **PedidoCreate**: al menos una línea, con `cantidad > 0` en cada una.
- **POST /pedidos** comprueba, por este orden, que el cliente existe y es de
  tipo `Cliente`, que cada producto existe y que hay stock suficiente. Si un
  producto aparece en varias líneas, se suman sus cantidades antes de comprobar
  el stock. Si algo falla no se descuenta nada.

Ejemplos de cuerpo para las peticiones:

```json
POST /usuarios
{"nombre": "Ana Pérez", "email": "ana@example.com", "tipo": "cliente", "direccion_postal": "Calle Mayor 1, Madrid"}

POST /productos
{"tipo": "electronico", "nombre": "Portátil 14''", "precio": 899.99, "stock": 10, "meses_garantia": 24}
{"tipo": "ropa", "nombre": "Camiseta básica", "precio": 14.99, "stock": 50, "talla": "M", "color": "Blanco"}

POST /pedidos
{"cliente_id": "<id del cliente>", "items": [{"producto_id": "<id del producto>", "cantidad": 2}]}
```

---

## Práctica 2 parte 2

### Parte 1 – Cliente Python con `requests`

Con la API en marcha, desde otra terminal:

```bash
cd cliente
python -m pip install -r requirements.txt
python cliente.py
```

El script crea un usuario, lista los usuarios, crea tres productos (uno de cada
tipo), lista los productos, crea un pedido para el usuario y consulta sus
pedidos. Para terminar, comprueba que la API rechaza un pedido sin stock
suficiente (400).

Cada llamada pasa por la función `comprobar()`, que verifica el código HTTP
esperado (201 o 200) y devuelve el JSON de la respuesta, o lanza un error con
el `detail` que devuelve la API.

La dirección de la API se define en una sola línea al principio del script:

```python
BASE_URL = "http://localhost:8000"
```

También se puede cambiar sin editar el código:
`python cliente.py --url http://192.168.1.34:8000`.

### Parte 2 – Comunicación entre dos equipos

**Equipo servidor** (ejecuta la API):

1. Averiguar su IP local. En Windows, con `ipconfig` (campo «Dirección IPv4»
   del adaptador Wi-Fi o Ethernet, p. ej. `192.168.1.34`). En macOS/Linux, con
   `ipconfig getifaddr en0` o `hostname -I`.
2. Arrancar el servidor para que acepte conexiones de otros equipos de la red:

   ```bash
   cd src
   uvicorn main:app --host 0.0.0.0 --port 8000
   ```

   (o `python main.py`, que ya usa `host="0.0.0.0"`).

   Con `--host 0.0.0.0` el servidor escucha en todas las interfaces de red. Con
   el valor por defecto (`127.0.0.1`) solo responde a peticiones del propio
   equipo (`localhost`).
3. Si Windows lo pregunta, permitir el acceso a Python en el cortafuegos para
   **redes privadas**. Si no aparece el aviso, se puede abrir el puerto en una
   PowerShell de administrador:

   ```powershell
   New-NetFirewallRule -DisplayName "FastAPI 8000" -Direction Inbound -Protocol TCP -LocalPort 8000 -Action Allow -Profile Private
   ```

**Equipo cliente**:

1. Ejecutar el cliente apuntando a la IP del servidor:

   ```bash
   python cliente.py --url http://192.168.1.34:8000
   ```

   o cambiar `BASE_URL = "http://192.168.1.34:8000"` en `cliente.py`.
2. Abrir en el navegador `http://192.168.1.34:8000/docs` y comprobar que se ve
   la documentación de la API remota.
3. Comprobar que los datos creados desde el cliente aparecen en `/docs` del
   servidor (y al revés), y que en la terminal de uvicorn aparecen las
   peticiones con la IP del equipo cliente.

**`localhost` frente a IP**: `localhost` (127.0.0.1) siempre se refiere al
propio equipo, así que desde el segundo ordenador `http://localhost:8000` no
llega a la API del compañero. Para acceder a un servicio de otro equipo hay que
usar su dirección IP en la red local.

### Parte 3 – Frontend web

Con la API en marcha, servir la carpeta `frontend`:

```bash
cd frontend
python -m http.server 5500
```

y abrir <http://localhost:5500>. También funciona abriendo `index.html`
directamente con doble clic.

En la cabecera de la página hay un campo **Servidor API** para cambiar la
dirección de la API (por defecto `http://localhost:8000`). Para usar la API de
un compañero basta con escribir `http://<su IP>:8000` y pulsar **Conectar**.

Funcionalidades:

- **Productos**: listado, creación (los campos cambian según el tipo) y borrado.
- **Usuarios**: listado y creación.
- **Pedidos**: creación de un pedido con una o varias líneas y consulta de los
  pedidos de un cliente.

#### Cómo se hacen las peticiones a la API (`app.js`)

- **`pedir(metodo, ruta, cuerpo)`** es la única función que habla con la API.
  Usa `fetch(BASE_URL + ruta)`; si hay cuerpo, lo envía como JSON con la
  cabecera `Content-Type: application/json`. Después comprueba
  `respuesta.ok` (código 2xx). Si la respuesta es correcta, devuelve el JSON
  (o `null` en el 204 del DELETE). Si no, lanza un error con el código HTTP y
  el `detail` que devuelve FastAPI.
- **El objeto `api`** tiene un método por endpoint, y cada línea indica el
  endpoint que usa:

  | Función | Endpoint |
  | --- | --- |
  | `api.listarProductos()` | `GET /productos` |
  | `api.crearProducto(datos)` | `POST /productos` |
  | `api.eliminarProducto(id)` | `DELETE /productos/{producto_id}` |
  | `api.listarUsuarios()` | `GET /usuarios` |
  | `api.crearUsuario(datos)` | `POST /usuarios` |
  | `api.crearPedido(datos)` | `POST /pedidos` |
  | `api.pedidosDeCliente(id)` | `GET /usuarios/{cliente_id}/pedidos` |

- **Procesamiento de las respuestas**: las funciones `pintarProductos()`,
  `pintarUsuarios()` y `consultarPedidos()` recorren el JSON recibido y generan
  las filas de las tablas. Si la API devuelve un error, se muestra en el aviso
  rojo de la parte superior.
- **CORS**: como el frontend se sirve desde otro origen (puerto 5500 o
  `file://`), `main.py` añade `CORSMiddleware` para que el navegador permita
  esas peticiones.

### Comprobación final

Con la API en marcha, los tres clientes trabajan sobre los mismos datos:

1. `python cliente.py` crea usuarios, productos y un pedido.
2. En `/docs`, `GET /productos` muestra esos productos con el stock ya
   descontado.
3. En el frontend aparecen los mismos usuarios, productos y pedidos, y lo que
   se cree desde el frontend se ve después en `/docs` y en el cliente Python.
