from typing import Dict, List, Optional

from models.Producto import Producto, ProductoElectronico, ProductoRopa
from models.Usuario import Usuario, Cliente, Administrador
from models.Pedido import Pedido


class TiendaService:
    """Servicio central que actúa de intermediario entre usuarios y productos."""

    def __init__(self) -> None:
        """Inicializa la tienda con los almacenes de usuarios, productos y
        pedidos vacíos."""
        self.usuarios: Dict[str, Usuario] = {}
        self.productos: Dict[str, Producto] = {}
        self.pedidos: List[Pedido] = []

    # ------------------------------------------------------------------
    # Gestión de usuarios
    # ------------------------------------------------------------------
    def registrar_usuario(self, tipo: str, nombre: str, email: str,
                           **kwargs) -> Usuario:
        """Registra un nuevo usuario en la tienda.

        Args:
            tipo: "cliente" o "administrador".
            nombre: Nombre del usuario.
            email: Correo electrónico del usuario.
            **kwargs: Atributos adicionales según el tipo. Para "cliente"
                se espera `direccion`.

        Returns:
            La instancia de usuario (Ciente o admin) creada

        Raises:
            ValueError: Si el tipo indicado no es válido.
        """
        tipo_normalizado = tipo.strip().lower()
        usuario: Usuario
        if tipo_normalizado == "cliente":
            usuario = Cliente(nombre, email, kwargs.get("direccion", ""))
        elif tipo_normalizado == "administrador":
            usuario = Administrador(nombre, email)
        else:
            raise ValueError(f"Tipo de usuario no válido: {tipo}")

        self.usuarios[usuario.id] = usuario
        return usuario

    def obtener_usuario(self, usuario_id: str) -> Optional[Usuario]:
        """Busca un usuario a partir de su identificador.

        Args:
            usuario_id: Identificador del usuario.

        Returns:
            El usuario encontrado, o None si no existe.
        """
        return self.usuarios.get(usuario_id)

    def listar_usuarios(self) -> List[Usuario]:
        """Lista todos los usuarios registrados en la tienda.

        Returns:
            Una lista con todos los usuarios.
        """
        return list(self.usuarios.values())

    # ------------------------------------------------------------------
    # Gestión de productos
    # ------------------------------------------------------------------
    def agregar_producto(self, tipo: str, nombre: str, precio: float,
                          stock: int, **kwargs) -> Producto:
        """Crea un producto de la categoría indicada y lo añade al inventario.

        Args:
            tipo: "electronico", "ropa" o "generico".
            nombre: Nombre del producto.
            precio: Precio unitario.
            stock: Cantidad inicial de stock.
            **kwargs: Atributos específicos de la subclase: `meses_garantia`
                para "electronico"; `talla` y `color` para "ropa".

        Returns:
            El producto creado y ya añadido al inventario.

        Raises:
            ValueError: Si el tipo indicado no es válido.
        """
        tipo_normalizado = tipo.strip().lower()
        producto: Producto
        if tipo_normalizado == "electronico":
            producto = ProductoElectronico(
                nombre, precio, stock, kwargs.get("meses_garantia", 12))
        elif tipo_normalizado == "ropa":
            producto = ProductoRopa(
                nombre, precio, stock,
                kwargs.get("talla", "M"), kwargs.get("color", "N/A"))
        elif tipo_normalizado == "generico":
            producto = Producto(nombre, precio, stock)
        else:
            raise ValueError(f"Tipo de producto no válido: {tipo}")

        self.productos[producto.id] = producto
        return producto

    def eliminar_producto(self, producto_id: str) -> bool:
        """Elimina un producto del inventario a partir de su identificador.

        Args:
            producto_id: Identificador del producto a eliminar.

        Returns:
            True si el producto existía y se eliminó, False en caso
            contrario.
        """
        return self.productos.pop(producto_id, None) is not None

    def listar_productos(self) -> List[Producto]:
        """Lista todos los productos disponibles en la tienda.

        Returns:
            Una lista con todos los productos del inventario.
        """
        return list(self.productos.values())

    def obtener_producto(self, producto_id: str) -> Optional[Producto]:
        """Busca un producto a partir de su identificador.

        Args:
            producto_id: Identificador del producto.

        Returns:
            El producto encontrado, o None si no existe.
        """
        return self.productos.get(producto_id)

    # ------------------------------------------------------------------
    # Gestión de pedidos
    # ------------------------------------------------------------------
    def realizar_pedido(self, usuario_id: str,
                         productos_cantidades: Dict[str, int]
                         ) -> Optional[Pedido]:
        """Genera un pedido para un cliente si existe stock suficiente.

        esto verifica primero que el usuario exista y sea un Cliente, y que haya
        stock suficiente de todos los productos solicitados. Si todo es
        correcto, descuenta las unidades del inventario y crea el pedido.

        Args:
            usuario_id: Identificador del usuario que realiza el pedido.
            productos_cantidades: Diccionario {producto_id: cantidad}.

        Returns:
            El Pedido creado, o None si el usuario no existe, no es cliente,
            algún producto no existe o no hay stock suficiente.
        """
        usuario = self.usuarios.get(usuario_id)
        if usuario is None or not isinstance(usuario, Cliente):
            return None

        productos_pedido: Dict[Producto, int] = {}
        for producto_id, cantidad in productos_cantidades.items():
            producto = self.productos.get(producto_id)
            if producto is None or not producto.hay_stock(cantidad):
                return None
            productos_pedido[producto] = cantidad

        for producto, cantidad in productos_pedido.items():
            producto.actualizar_stock(-cantidad)

        pedido = Pedido(usuario, productos_pedido)
        self.pedidos.append(pedido)
        return pedido

    def listar_pedidos_usuario(self, usuario_id: str) -> List[Pedido]:
        """Lista los pedidos de un usuario ordenados por fecha.

        Args:
            usuario_id: Identificador del usuario (cliente).

        Returns:
            Lista de pedidos del usuario ordenada de más antiguo a más
            reciente.
        """
        pedidos_usuario = [p for p in self.pedidos
                            if p.cliente.id == usuario_id]
        return sorted(pedidos_usuario, key=lambda p: p.fecha)
