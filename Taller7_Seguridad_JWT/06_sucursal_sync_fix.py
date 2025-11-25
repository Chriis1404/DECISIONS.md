# Corrección en SucursalAPIdemo.py
@app.post("/sync-sale-history", tags=["Sincronización"])
async def sync_sale_history(notification: SaleNotificationFromCentral):
    
    # 1. Filtro Anti-Duplicados (Evita bucles infinitos si la venta es propia)
    if notification.branch_id == BRANCH_ID:
        logger.info(f"ℹ️ Historial: Venta propia omitida.")
        return {"status": "success", "message": "Venta propia omitida."}
    
    # 2. Corrección del Crash (Manejo seguro si el producto no existe localmente)
    product_name = local_inventory.get(
        notification.product_id, 
        Product(id=0, name="PRODUCTO_EXTERNO", price=0, stock=0)
    ).name
    
    # ... resto de la lógica ...
