def create_receipt(sale):

    return {
        "sale_id": sale.id,
        "customer": sale.customer.name,
        "product": sale.product.name,
        "price": float(sale.price),
        "expiration": str(
            sale.expires_at
        )
    }
