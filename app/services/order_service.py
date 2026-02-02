from decimal import Decimal
from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.dependencies.get_date import get_date_range
from app.models.order import Order
from app.models.order_product import OrderProduct
from app.models.product import Product

ALLOWED_STATUSES = {"pending", "completed", "delivered", "canceled"}


def get_orders(db: Session, range_name: str = "week"):
    start, end = get_date_range(range_name)

    return (
        db.query(Order)
        .options(
            joinedload(Order.products),
            joinedload(Order.user),
        )
        .filter(Order.created_at >= start, Order.created_at <= end)
        .order_by(Order.id.desc())
        .all()
    )


def create_order(db: Session, user_id, data):
    if not data.items:
        raise HTTPException(status_code=400, detail="Items is empty")

    order = Order(
        user_id=user_id,
        status="pending",
        payment_method=data.payment_method,
        shipping_address=data.shipping_address,
        notes=data.notes,
        phone=data.phone,
        location=data.location,
        total_price=Decimal("0.00"),
    )

    db.add(order)
    db.flush()  

    total = Decimal("0.00")

    for item in data.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product not found: {item.product_id}"
            )

        price = Decimal(str(product.price))
        qty = int(item.quantity)
        line_total = price * qty
        total += line_total

        db.add(
            OrderProduct(
                order_id=order.id,
                product_id=product.id,
                price=price,
                quantity=qty,
                total_price=line_total,
                # snapshot fields
                name=product.name,
                image=product.image,
                weight=product.weight,
                description=product.description,
                rating=None,
            )
        )

    order.total_price = total

    db.commit()

    # ✅ MUHIM: user va products bilan qaytarsin (joinedload bilan)
    order = (
        db.query(Order)
        .options(
            joinedload(Order.products),
            joinedload(Order.user),
        )
        .filter(Order.id == order.id)
        .first()
    )
    return order

def get_my_orders(db: Session, user_id):
    return (
        db.query(Order)
        .options(
            joinedload(Order.products),
            joinedload(Order.user), 
        )
        .filter(Order.user_id == user_id)
        .order_by(Order.id.desc())
        .all()
    )

def get_order_for_user(db: Session, order_id: int, user_id):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.products),
            joinedload(Order.user),  
        )
        .filter(Order.id == order_id, Order.user_id == user_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order

def update_order_status(db: Session, order_id: int, new_status: str, user):
    order = (
        db.query(Order)
        .options(
            joinedload(Order.products),
            joinedload(Order.user),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    roles = set(user.roles or [])

    if new_status == "completed":
        if not roles.intersection({"admin", "chef"}):
            raise HTTPException(status_code=403, detail="Only admin or chef can complete")
        if order.status != "pending":
            raise HTTPException(status_code=400, detail="Only pending -> completed")

    elif new_status == "delivered":
        if not roles.intersection({"admin", "waiter"}):
            raise HTTPException(status_code=403, detail="Only admin or waiter can deliver")
        if order.status != "completed":
            raise HTTPException(status_code=400, detail="Only completed -> delivered")

    elif new_status == "pending":
        raise HTTPException(status_code=400, detail="Cannot set back to pending")

    else:
        raise HTTPException(status_code=400, detail="Invalid status")

    order.status = new_status
    db.commit()

    db.refresh(order)
    return order

def get_all_order_products(db: Session):
    return db.query(OrderProduct).order_by(OrderProduct.id.desc()).all()


def get_product_stats(db: Session, range_name: str = "week"):
    start, end = get_date_range(range_name)

    rows = (
        db.query(
            OrderProduct.product_id.label("product_id"),
            OrderProduct.name.label("name"),
            func.sum(OrderProduct.quantity).label("units"),
            func.sum(OrderProduct.total_price).label("revenue"),
        )
        .join(Order, Order.id == OrderProduct.order_id)
        .filter(Order.created_at >= start, Order.created_at <= end)
        .group_by(OrderProduct.product_id, OrderProduct.name)
        .order_by(func.sum(OrderProduct.total_price).desc())
        .all()
    )

    return [
        {
            "product_id": r.product_id,
            "name": r.name,
            "units": int(r.units or 0),
            "revenue": float(r.revenue or 0),
        }
        for r in rows
    ]



ACTIVE_STATUSES = {"pending", "completed"} 

def get_dashboard_kpis(db: Session, range_name: str = "week"):
    start, end = get_date_range(range_name)

    total_revenue = (
        db.query(func.coalesce(func.sum(OrderProduct.total_price), 0))
        .join(Order, Order.id == OrderProduct.order_id)
        .filter(Order.created_at >= start, Order.created_at <= end)
        .scalar()
    )

    total_products_units = (
        db.query(func.coalesce(func.sum(OrderProduct.quantity), 0))
        .join(Order, Order.id == OrderProduct.order_id)
        .filter(Order.created_at >= start, Order.created_at <= end)
        .scalar()
    )

    active_orders = (
        db.query(func.count(Order.id))
        .filter(Order.created_at >= start, Order.created_at <= end)
        .filter(Order.status.in_(ACTIVE_STATUSES))
        .scalar()
    )

    return {
        "total_revenue": float(total_revenue or 0),
        "total_products": int(total_products_units or 0),
        "active_orders": int(active_orders or 0),
    }
