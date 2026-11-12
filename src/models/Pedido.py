"""Modelo de datos para los pedidos de la tienda online."""

import uuid
from datetime import datetime
from typing import Dict

from models.Producto import Producto
from models.Usuario import Cliente


class Pedido:
    """Representa un pedido realizado por un cliente de la tienda."""

    def __init__(self, cliente: Cliente,
                 productos: Dict[Producto, int]) -> None:
        """Inicializa un pedido con un identificador único y la fecha actual.

        Args:
            cliente: Cliente que realiza el pedido.
            productos: Diccionario {producto: cantidad} solicitado.
        """
        self.id: str = str(uuid.uuid4())
        self.cliente: Cliente = cliente
        self.productos: Dict[Producto, int] = productos
        self.fecha: datetime = datetime.now()

    def calcular_total(self) -> float:
        """Calcula el importe total del pedido.

        Returns:
            La suma de precio * cantidad de todos los productos del pedido.
        """
        return sum(producto.precio * cantidad
                   for producto, cantidad in self.productos.items())

    def __str__(self) -> str:
        """Devuelve un resumen legible del pedido."""
        detalle = ", ".join(
            f"{cantidad}x {producto.nombre}"
            for producto, cantidad in self.productos.items()
        )
        fecha_str = self.fecha.strftime("%Y-%m-%d %H:%M:%S")
        return (f"Pedido [{self.id[:8]}] de {self.cliente.nombre} "
                f"el {fecha_str} -> {detalle} "
                f"| Total: {self.calcular_total():.2f}€")
