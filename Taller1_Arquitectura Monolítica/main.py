from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, List

app = FastAPI(title="EcoMarket Monolito v1")

# Modelo de datos
class Product(BaseModel):
    id: Optional[int] = None
    name: str
    price: float
    stock: int

# Base de datos en memoria
inventory = [
    {"id": 1, "name": "Manzanas", "price": 2.5, "stock": 100},
    {"id": 2, "name": "Pan", "price": 1.5, "stock": 50}
]

@app.get("/")
def root():
    return {"message": "Bienvenido a EcoMarket v1"}

@app.get("/products", response_model=List[dict])
def get_products():
    return inventory

@app.get("/products/{product_id}")
def get_product(product_id: int):
    for p in inventory:
        if p["id"] == product_id:
            return p
    raise HTTPException(status_code=404, detail="Producto no encontrado")

@app.post("/products", status_code=201)
def add_product(product: Product):
    new_id = len(inventory) + 1
    new_prod = product.dict()
    new_prod["id"] = new_id
    inventory.append(new_prod)
    return new_prod

@app.put("/products/{product_id}")
def update_product(product_id: int, updated_product: Product):
    for index, p in enumerate(inventory):
        if p["id"] == product_id:
            inventory[index] = updated_product.dict()
            inventory[index]["id"] = product_id # Mantener ID original
            return inventory[index]
    raise HTTPException(status_code=404, detail="Producto no encontrado para actualizar")

@app.delete("/products/{product_id}", status_code=204)
def delete_product(product_id: int):
    for index, p in enumerate(inventory):
        if p["id"] == product_id:
            inventory.pop(index)
            return
    raise HTTPException(status_code=404, detail="Producto no encontrado para eliminar")
