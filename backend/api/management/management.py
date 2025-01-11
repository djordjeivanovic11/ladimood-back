from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from database import models, schemas, db as database
import dotenv
import os

dotenv.load_dotenv()

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS"))
RESET_TOKEN_EXPIRE_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRE_MINUTES"))

router = APIRouter()

def to_order_response(db_order: models.Order, db: Session) -> schemas.OrderResponse:
    # Fetch the user associated with the order
    db_user = db.query(models.User).filter(models.User.id == db_order.user_id).first()

    # Fetch the address associated with the user
    db_address = db.query(models.Address).filter(models.Address.user_id == db_order.user_id).first()

    # Construct the User schema object (or None if user doesn't exist)
    user_schema = None
    if db_user:
        user_schema = schemas.User(
            id=db_user.id,
            email=db_user.email,
            full_name=db_user.full_name,
            phone_number=db_user.phone_number,
            is_active=db_user.is_active,
            role=db_user.role,  # if you'd like to load the role from DB as well
            created_at=db_user.created_at,
            updated_at=db_user.updated_at,
        )

    # Construct the address dictionary (or None if address doesn't exist)
    address_dict = None
    if db_address:
        address_dict = {
            "street_address": db_address.street_address,
            "city": db_address.city,
            "state": db_address.state,
            "postal_code": db_address.postal_code,
            "country": db_address.country,
        }

    # Construct the OrderResponse
    return schemas.OrderResponse(
        id=db_order.id,
        user_id=db_order.user_id,
        user=user_schema,
        status=db_order.status.value,
        total_price=db_order.total_price,
        created_at=db_order.created_at,
        updated_at=db_order.updated_at,
        items=[
            schemas.OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                color=item.color,
                size=item.size.value,
                price=item.price,
            )
            for item in db_order.items
        ],
        address=address_dict,
    )


@router.get("/sales", response_model=List[schemas.SalesRecord])
def get_sales_records(db: Session = Depends(database.get_db)):
    sales_records = db.query(models.SalesRecord).all()
    if not sales_records:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No sales records found"
        )
    return sales_records



@router.get("/orders", response_model=List[schemas.OrderResponse])
def get_all_orders_with_address(db: Session = Depends(database.get_db)):
    """
    Get all orders along with user details, addresses, and order items.
    """
    orders = db.query(models.Order).all()
    if not orders:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="No orders found"
        )
    return [to_order_response(order, db) for order in orders]



@router.get("/orders/{order_id}", response_model=schemas.OrderResponse)
def get_single_order(order_id: int, db: Session = Depends(database.get_db)):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )
    return to_order_response(order, db)



@router.put("/orders/{order_id}/status", response_model=schemas.OrderResponse)
def update_order_status(
    order_id: int,
    request: schemas.UpdateStatusRequest,
    db: Session = Depends(database.get_db)
):
    """
    Updates the status of an order and logs the change if necessary.
    """
    # Fetch the order
    order = db.query(models.Order).filter(models.Order.id == order_id).first()

    if not order:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Order with ID {order_id} not found"
        )

    # Validate the status
    if request.status not in schemas.OrderStatusEnum.__members__.values():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid order status: {request.status}. Allowed statuses are: {list(schemas.OrderStatusEnum.__members__.keys())}",
        )

    # Update the order's status
    order.status = request.status
    db.commit()
    db.refresh(order)

    # Return the updated order
    return to_order_response(order, db)
