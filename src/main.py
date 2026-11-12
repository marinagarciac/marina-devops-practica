"""Punto de entrada de la aplicación y capa de exposición del servicio.

Define los endpoints de la API REST, que reciben las peticiones HTTP, validan
los datos con los esquemas Pydantic y delegan la lógica en TiendaService.

Ejecución:
    uvicorn main:app --reload                      (solo este equipo)
    uvicorn main:app --host 0.0.0.0 --port 8000    (accesible desde la red local)
"""

from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware

from models.Usuario import Cliente
from schemas import (
    PedidoCreate,
    PedidoRead,
    ProductoCreate,
    ProductoRead,
    UsuarioCreate,
    UsuarioRead,
)
from Services.Tienda_service import TiendaService

app = FastAPI(
    title="Tienda Online API",
    description="API REST de la tienda online construida sobre TiendaService.",
    version="1.0.0",
)

# Permite que el frontend (abierto desde otro origen, p. ej. file:// o
# http://localhost:5500) pueda hacer peticiones a la API desde el navegador.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Única instancia del servicio: todos los clientes trabajan sobre los mismos datos
tienda = TiendaService()


def get_tienda() -> TiendaService:
    """Dependencia que proporciona el servicio de la tienda a cada endpoint."""
    return tienda


def buscar_cliente(servicio: TiendaService, cliente_id: str) -> Cliente:
    """Devuelve el cliente o lanza 404 si no existe / 400 si no es cliente."""
    usuario = servicio.obtener_usuario(cliente_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe ningún usuario con id {cliente_id}")
    if not isinstance(usuario, Cliente):
        raise HTTPException(status.HTTP_400_BAD_REQUEST, f"El usuario {cliente_id} no es un cliente")
    return usuario


@app.get("/", tags=["General"])
def raiz():
    return {"mensaje": "API de la Tienda Online", "documentacion": "/docs"}


# ------------------------------------------------------------------ Usuarios


@app.post(
    "/usuarios",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Usuarios"],
    responses={400: {"description": "Datos no válidos"}, 409: {"description": "Email ya registrado"}},
)
def crear_usuario(datos: UsuarioCreate, servicio: TiendaService = Depends(get_tienda)):
    email = datos.email.strip().lower()
    if any(u.email.lower() == email for u in servicio.listar_usuarios()):
        raise HTTPException(status.HTTP_409_CONFLICT, f"Ya existe un usuario con el email '{datos.email}'")
    try:
        usuario = servicio.registrar_usuario(
            datos.tipo, datos.nombre.strip(), email, direccion=datos.direccion_postal
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return UsuarioRead.desde_modelo(usuario)


@app.get("/usuarios", response_model=list[UsuarioRead], tags=["Usuarios"])
def listar_usuarios(servicio: TiendaService = Depends(get_tienda)):
    return [UsuarioRead.desde_modelo(u) for u in servicio.listar_usuarios()]


@app.get(
    "/usuarios/{usuario_id}",
    response_model=UsuarioRead,
    tags=["Usuarios"],
    responses={404: {"description": "Usuario no encontrado"}},
)
def obtener_usuario(usuario_id: str, servicio: TiendaService = Depends(get_tienda)):
    usuario = servicio.obtener_usuario(usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe ningún usuario con id {usuario_id}")
    return UsuarioRead.desde_modelo(usuario)


# ----------------------------------------------------------------- Productos


@app.post(
    "/productos",
    response_model=ProductoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Productos"],
    responses={400: {"description": "Datos no válidos"}},
)
def crear_producto(datos: ProductoCreate, servicio: TiendaService = Depends(get_tienda)):
    # Atributos específicos de cada tipo, que agregar_producto recibe por kwargs
    extra = {}
    if datos.tipo == "electronico":
        extra["meses_garantia"] = datos.meses_garantia
    elif datos.tipo == "ropa":
        extra["talla"] = datos.talla.strip()
        extra["color"] = datos.color.strip()

    try:
        producto = servicio.agregar_producto(
            datos.tipo, datos.nombre.strip(), datos.precio, datos.stock, **extra
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    return ProductoRead.desde_modelo(producto)


@app.get("/productos", response_model=list[ProductoRead], tags=["Productos"])
def listar_productos(servicio: TiendaService = Depends(get_tienda)):
    return [ProductoRead.desde_modelo(p) for p in servicio.listar_productos()]


@app.get(
    "/productos/{producto_id}",
    response_model=ProductoRead,
    tags=["Productos"],
    responses={404: {"description": "Producto no encontrado"}},
)
def obtener_producto(producto_id: str, servicio: TiendaService = Depends(get_tienda)):
    producto = servicio.obtener_producto(producto_id)
    if producto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe ningún producto con id {producto_id}")
    return ProductoRead.desde_modelo(producto)


@app.delete(
    "/productos/{producto_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    tags=["Productos"],
    responses={404: {"description": "Producto no encontrado"}},
)
def eliminar_producto(producto_id: str, servicio: TiendaService = Depends(get_tienda)):
    if not servicio.eliminar_producto(producto_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe ningún producto con id {producto_id}")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ------------------------------------------------------------------- Pedidos


@app.post(
    "/pedidos",
    response_model=PedidoRead,
    status_code=status.HTTP_201_CREATED,
    tags=["Pedidos"],
    responses={
        400: {"description": "Stock insuficiente o el usuario no es un cliente"},
        404: {"description": "Cliente o producto no encontrado"},
    },
)
def crear_pedido(datos: PedidoCreate, servicio: TiendaService = Depends(get_tienda)):
    # 1. El cliente existe y es de tipo Cliente
    buscar_cliente(servicio, datos.cliente_id)

    # 2. Agrupar cantidades por si un mismo producto aparece en varias líneas
    cantidades: dict[str, int] = {}
    for item in datos.items:
        cantidades[item.producto_id] = cantidades.get(item.producto_id, 0) + item.cantidad

    # 3. Cada producto existe y tiene stock suficiente
    for producto_id, cantidad in cantidades.items():
        producto = servicio.obtener_producto(producto_id)
        if producto is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, f"No existe ningún producto con id {producto_id}")
        if not producto.hay_stock(cantidad):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"Stock insuficiente para '{producto.nombre}' "
                f"(disponible: {producto.stock}, solicitado: {cantidad})",
            )

    # 4. Crear el pedido con la lógica de TiendaService (descuenta el stock).
    #    realizar_pedido devuelve None si alguna comprobación falla.
    pedido = servicio.realizar_pedido(datos.cliente_id, cantidades)
    if pedido is None:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "No se ha podido realizar el pedido")
    return PedidoRead.desde_modelo(pedido)


@app.get(
    "/usuarios/{cliente_id}/pedidos",
    response_model=list[PedidoRead],
    tags=["Pedidos"],
    responses={
        400: {"description": "El usuario no es un cliente"},
        404: {"description": "Cliente no encontrado"},
    },
)
def pedidos_de_cliente(cliente_id: str, servicio: TiendaService = Depends(get_tienda)):
    buscar_cliente(servicio, cliente_id)
    return [PedidoRead.desde_modelo(p) for p in servicio.listar_pedidos_usuario(cliente_id)]


if __name__ == "__main__":
    import uvicorn

    # host="0.0.0.0" acepta conexiones de otros equipos de la red local
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
