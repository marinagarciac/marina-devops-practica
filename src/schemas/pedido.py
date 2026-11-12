"""Esquemas Pydantic de pedidos."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from models.Pedido import Pedido


class PedidoItemCreate(BaseModel):
    """Una línea del pedido al crearlo: qué producto y cuántas unidades."""

    producto_id: str = Field(min_length=1)
    cantidad: int = Field(gt=0)


class PedidoCreate(BaseModel):
    """Datos para crear un pedido."""

    cliente_id: str = Field(min_length=1)
    items: list[PedidoItemCreate] = Field(min_length=1)

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "cliente_id": "id-del-cliente",
                    "items": [
                        {"producto_id": "id-del-producto-1", "cantidad": 2},
                        {"producto_id": "id-del-producto-2", "cantidad": 1},
                    ],
                }
            ]
        }
    )


class PedidoItemRead(BaseModel):
    """Una línea del pedido tal y como la devuelve la API."""

    producto_id: str
    nombre: str
    precio_unitario: float
    cantidad: int
    subtotal: float


class PedidoRead(BaseModel):
    """Pedido completo con fecha, cliente, total y líneas."""

    id: str
    fecha: datetime
    cliente_id: str
    cliente_nombre: str
    total: float
    items: list[PedidoItemRead]

    @classmethod
    def desde_modelo(cls, pedido: Pedido) -> "PedidoRead":
        # Pedido.productos es un diccionario {producto: cantidad}
        items = [
            PedidoItemRead(
                producto_id=producto.id,
                nombre=producto.nombre,
                precio_unitario=producto.precio,
                cantidad=cantidad,
                subtotal=round(producto.precio * cantidad, 2),
            )
            for producto, cantidad in pedido.productos.items()
        ]
        return cls(
            id=pedido.id,
            fecha=pedido.fecha,
            cliente_id=pedido.cliente.id,
            cliente_nombre=pedido.cliente.nombre,
            total=round(pedido.calcular_total(), 2),
            items=items,
        )
