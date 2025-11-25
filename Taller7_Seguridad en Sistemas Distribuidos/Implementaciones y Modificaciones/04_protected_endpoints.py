# [TALLER 7] Endpoint Público: LOGIN
@app.post("/login", response_model=Token, tags=["Autenticacion"])
async def login(form_data: LoginRequest):
    user = users_db.get(form_data.username)
    if not user or not verify_password(form_data.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Usuario o contraseña incorrectos")
    
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return {"access_token": access_token, "token_type": "bearer"}

# Endpoint Protegido: AGREGAR (POST)
@app.post("/inventory", response_model=Product, tags=["Inventario"])
async def add_product(
    product: Product, 
    current_user: dict = Depends(get_current_user) # 🔒 CANDADO DE SEGURIDAD
):
    # Lógica para guardar...
    pass

# Endpoint Protegido: ELIMINAR (DELETE)
@app.delete("/inventory/{product_id}", tags=["Inventario"])
async def delete_product(
    product_id: int,
    current_user: dict = Depends(get_current_user) # 🔒 CANDADO DE SEGURIDAD
):
    # Lógica para eliminar...
    pass
