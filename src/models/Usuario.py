"""Modelo de datos para los usuarios de la tienda online."""

import uuid


class Usuario:
    """Clase base que representa a cualquier persona que usa la tienda."""

    def __init__(self, nombre: str, email: str) -> None:
        """Inicializa un usuario con un identificador único autogenerado.

        Args:
            nombre: Nombre del usuario.
            email: Correo electrónico del usuario.
        """
        self.id: str = str(uuid.uuid4())
        self.nombre: str = nombre
        self.email: str = email

    def is_admin(self) -> bool:
        """Indica si el usuario tiene privilegios de administrador.

        Returns:
            False por defecto para un usuario genérico.
        """
        return False

    def __str__(self) -> str:
        return f"[{self.id[:8]}] {self.nombre} ({self.email})"


class Cliente(Usuario):
    """Usuario de tipo cliente, con dirección postal de envío."""

    def __init__(self, nombre: str, email: str, direccion: str) -> None:
        """Inicializa un cliente.

        Args:
            nombre: Nombre del cliente
            email: correo electrónico del cliente
            direccion: Dirección postal del cliente.
        """
        super().__init__(nombre, email)
        self.direccion: str = direccion

    def __str__(self) -> str:
        """Devuelve una representación legible incluyendo la dirección."""
        return f"{super().__str__()} | Direccion: {self.direccion}"


class Administrador(Usuario):
    """Usuario de tipo administrador, gestor de la tienda."""

    def is_admin(self) -> bool:
        """Indica que este usuario sí tiene privilegios de administrador.

        Returns:
            True siempre, ya que es un administrador.
        """
        return True

    def __str__(self) -> str:
        """Devuelve una representación legible indicando el rol."""
        return f"{super().__str__()} | Rol: Administrador"
