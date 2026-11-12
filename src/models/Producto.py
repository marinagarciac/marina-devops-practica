"""Modelo de datos para los productos de la tienda online."""

import uuid


class Producto:
    """Clase base que representa un producto genérico de la tienda."""

    def __init__(self, nombre: str, precio: float, stock: int) -> None:
        """Inicializa un producto con un identificador único autogenerado.

        Args:
            nombre: Nombre del producto.
            precio: Precio unitario del producto.
            stock: Cantidad de unidades disponibles.
        """
        self.id: str = str(uuid.uuid4())
        self.nombre: str = nombre
        self.precio: float = precio
        self.stock: int = stock

    def hay_stock(self, cantidad: int) -> bool:
        """Comprueba si hay stock suficiente para la cantidad solicitada.

        Args:
            cantidad: Unidades que se desean comprobar.

        Returns:
            True si el stock disponible es mayor o igual a la cantidad.
        """
        return self.stock >= cantidad

    def actualizar_stock(self, cantidad: int) -> None:
        """Actualiza el stock del producto.

        Args:
            cantidad: Unidades a añadir (positivo, reposición) o restar
                (negativo, compra) del stock actual.

        Raises:
            ValueError: Si la operación deja el stock en un valor negativo.
        """
        nuevo_stock = self.stock + cantidad
        if nuevo_stock < 0:
            raise ValueError("El stock no puede quedar en un valor negativo.")
        self.stock = nuevo_stock

    def __str__(self) -> str:
        """Devuelve una representación legible del producto."""
        return (f"[{self.id[:8]}] {self.nombre} - {self.precio:.2f}€ "
                f"(stock: {self.stock})")


class ProductoElectronico(Producto):
    """Producto electrónico, con meses de garantía adicionales."""

    def __init__(self, nombre: str, precio: float, stock: int,
                 meses_garantia: int) -> None:
        """Inicializa un producto electrónico.

        Args:
            nombre: Nombre del producto.
            precio: Precio unitario.
            stock: Cantidad de unidades disponibles.
            meses_garantia: Meses de garantía del producto.
        """
        super().__init__(nombre, precio, stock)
        self.meses_garantia: int = meses_garantia

    def __str__(self) -> str:
        """Devuelve una representación legible incluyendo la garantía."""
        return f"{super().__str__()} | Garantía: {self.meses_garantia} meses"


class ProductoRopa(Producto):
    """Producto de ropa, con talla y color."""

    def __init__(self, nombre: str, precio: float, stock: int,
                 talla: str, color: str) -> None:
        """Inicializa un producto de ropa.

        Args:
            nombre: Nombre del producto.
            precio: Precio unitario.
            stock: Cantidad de unidades disponibles.
            talla: Talla del producto (p.ej. "S", "M", "L").
            color: Color del producto.
        """
        super().__init__(nombre, precio, stock)
        self.talla: str = talla
        self.color: str = color

    def __str__(self) -> str:
        """Devuelve una representación legible incluyendo talla y color."""
        return f"{super().__str__()} | Talla: {self.talla}, Color: {self.color}"
