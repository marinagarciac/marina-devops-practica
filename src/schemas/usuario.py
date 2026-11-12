"""Esquemas Pydantic de usuarios."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.Usuario import Usuario


class UsuarioCreate(BaseModel):
    """Datos que envía el cliente para crear un usuario."""

    nombre: str = Field(min_length=1, max_length=100)
    email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", max_length=150)
    tipo: Literal["cliente", "administrador"] = "cliente"
    direccion_postal: str | None = Field(default=None, max_length=200)

    @model_validator(mode="after")
    def cliente_requiere_direccion(self):
        if self.tipo == "cliente" and not (self.direccion_postal and self.direccion_postal.strip()):
            raise ValueError("Los clientes deben indicar una dirección postal")
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "nombre": "Ana Pérez",
                    "email": "ana@example.com",
                    "tipo": "cliente",
                    "direccion_postal": "Calle Mayor 1, Madrid",
                }
            ]
        }
    )


class UsuarioRead(BaseModel):
    """Datos de un usuario que devuelve la API."""

    id: str
    nombre: str
    email: str
    es_admin: bool

    @classmethod
    def desde_modelo(cls, usuario: Usuario) -> "UsuarioRead":
        return cls(
            id=usuario.id,
            nombre=usuario.nombre,
            email=usuario.email,
            es_admin=usuario.is_admin(),
        )
