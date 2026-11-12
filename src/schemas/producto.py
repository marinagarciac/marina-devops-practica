"""Esquemas Pydantic de productos."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from models.Producto import Producto, ProductoElectronico, ProductoRopa

TipoProducto = Literal["generico", "electronico", "ropa"]


class ProductoCreate(BaseModel):
    """Datos para crear un producto. Los atributos extra dependen del tipo."""

    tipo: TipoProducto = "generico"
    nombre: str = Field(min_length=1, max_length=100)
    precio: float = Field(gt=0)
    stock: int = Field(ge=0)
    # Solo electrónicos
    meses_garantia: int | None = Field(default=None, ge=0)
    # Solo ropa
    talla: str | None = Field(default=None, min_length=1, max_length=10)
    color: str | None = Field(default=None, min_length=1, max_length=30)

    @model_validator(mode="after")
    def validar_atributos_por_tipo(self):
        if self.tipo == "electronico":
            if self.meses_garantia is None:
                raise ValueError("Los productos electrónicos requieren 'meses_garantia'")
            if self.talla is not None or self.color is not None:
                raise ValueError("Los productos electrónicos no tienen 'talla' ni 'color'")
        elif self.tipo == "ropa":
            if self.talla is None or self.color is None:
                raise ValueError("Los productos de ropa requieren 'talla' y 'color'")
            if self.meses_garantia is not None:
                raise ValueError("Los productos de ropa no tienen 'meses_garantia'")
        else:
            if any(v is not None for v in (self.meses_garantia, self.talla, self.color)):
                raise ValueError(
                    "Los productos genéricos no admiten 'meses_garantia', 'talla' ni 'color'"
                )
        return self

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {"tipo": "generico", "nombre": "Taza", "precio": 7.5, "stock": 30},
                {"tipo": "electronico", "nombre": "Portátil 14''", "precio": 899.99, "stock": 10, "meses_garantia": 24},
                {"tipo": "ropa", "nombre": "Camiseta básica", "precio": 14.99, "stock": 50, "talla": "M", "color": "Blanco"},
            ]
        }
    )


class ProductoRead(BaseModel):
    """Datos de un producto que devuelve la API."""

    id: str
    tipo: TipoProducto
    nombre: str
    precio: float
    stock: int
    meses_garantia: int | None = None
    talla: str | None = None
    color: str | None = None

    @classmethod
    def desde_modelo(cls, producto: Producto) -> "ProductoRead":
        datos = {
            "id": producto.id,
            "nombre": producto.nombre,
            "precio": producto.precio,
            "stock": producto.stock,
        }
        if isinstance(producto, ProductoElectronico):
            return cls(**datos, tipo="electronico", meses_garantia=producto.meses_garantia)
        if isinstance(producto, ProductoRopa):
            return cls(**datos, tipo="ropa", talla=producto.talla, color=producto.color)
        return cls(**datos, tipo="generico")
