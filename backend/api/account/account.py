import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List
from database import models, schemas, db as database
from api.auth.utils import get_current_user
from api.account.utils import (
    add_to_wishlist, remove_from_wishlist, add_to_cart, remove_from_cart, send_order_confirmation_email, send_promo_email
)
from database.schemas import OrderItemResponse, OrderResponse, Product as ProductSchema, ReferralRequest
from database.models import Product
from hashids import Hashids

hashids = Hashids(min_length=20, salt="ladimoodjenajjacibrendnabalkanu")

router = APIRouter()

#-----------------------------------#
#           USER DETAILS            #
#-----------------------------------#

@router.get("/details", response_model=schemas.User)
def get_user_details(current_user: models.User = Depends(get_current_user)):
    return current_user

@router.get("/me", response_model=schemas.User)
def get_user_me(current_user: models.User = Depends(get_current_user)):
    return current_user

#-----------------------------------#
#          ADDRESS ROUTES           #
#-----------------------------------#

@router.get("/address", response_model=schemas.Address)
def get_address(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    address = db.query(models.Address).filter(models.Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address

@router.post("/address", response_model=schemas.Address)
def add_or_update_address(address: schemas.AddressBase, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    existing_address = db.query(models.Address).filter(models.Address.user_id == current_user.id).first()
    if existing_address:
        # Update logic if an address already exists
        existing_address.street_address = address.street_address
        existing_address.city = address.city
        existing_address.state = address.state
        existing_address.postal_code = address.postal_code
        existing_address.country = address.country
        db.commit()
        db.refresh(existing_address)
        return existing_address
    else:
        # Create new address if none exists
        new_address = models.Address(**address.model_dump(), user_id=current_user.id)
        db.add(new_address)
        db.commit()
        db.refresh(new_address) 
        return new_address


@router.delete("/address", response_model=schemas.Message)
def delete_address(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    address = db.query(models.Address).filter(models.Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    db.delete(address)
    db.commit()
    return {"message": "Address deleted successfully"}

#-----------------------------------#
#         ORDER ROUTES              #
#-----------------------------------#

@router.get("/orders", response_model=List[schemas.Order])
def get_orders(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Retrieve all orders for the authenticated user, including order items
    and product details.
    """
    try:
        # Query orders with eager loading of items and their associated products
        orders = (
            db.query(models.Order)
            .filter(models.Order.user_id == current_user.id)
            .options(
                joinedload(models.Order.items)
                .joinedload(models.OrderItem.product)
                .joinedload(models.Product.category)  # Include category if needed
            )
            .all()
        )

        if not orders:
            return []  # Return an empty list instead of raising an HTTPException

        # Serialize orders into response format
        serialized_orders = [
            schemas.Order(
                id=order.id,
                user_id=order.user_id,
                status=order.status.value,
                total_price=order.total_price,
                items=[
                    schemas.OrderItem(
                        id=item.id,
                        product=schemas.Product(
                            id=item.product.id,
                            name=item.product.name,
                            description=item.product.description,  # Optional in schema
                            price=item.product.price,
                            created_at=item.product.created_at,
                            updated_at=item.product.updated_at,
                            category=schemas.Category(
                                id=item.product.category.id,
                                name=item.product.category.name
                            ) if item.product.category else None,
                        ),
                        quantity=item.quantity,
                        color=item.color,
                        size=item.size.value if hasattr(item.size, 'value') else item.size,
                        price=item.price,
                    )
                    for item in order.items
                ],
                created_at=order.created_at,
                updated_at=order.updated_at,
            )
            for order in orders
        ]

        return serialized_orders

    except Exception as e:
        # Handle unexpected errors gracefully
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred while retrieving orders: {str(e)}"
        )


@router.get("/orders/{order_id}", response_model=OrderResponse)
def get_order(order_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    numeric_order_id = hashids.decode(order_id)
    if not numeric_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")

    # Query the order with its items and the related products loaded
    order = (
        db.query(models.Order)
        .filter(models.Order.id == numeric_order_id[0], models.Order.user_id == current_user.id)
        .options(
            joinedload(models.Order.items).joinedload(models.OrderItem.product)  # Load products in items
        )
        .first()
    )

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")

    # Construct response data
    response_data = OrderResponse(
        id=hashids.encode(order.id),  # Use hashed ID in the response
        user_id=order.user_id,
        status=order.status.value if hasattr(order.status, 'value') else order.status,
        total_price=order.total_price,
        items=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product.id,
                product_name=item.product.name,
                quantity=item.quantity,
                color=item.color,
                size=item.size.value if hasattr(item.size, 'value') else item.size,
                price=item.product.price  # Use 'price' instead of 'product_price'
            ) for item in order.items
        ],
        created_at=order.created_at,
        updated_at=order.updated_at
    )
    return response_data

@router.post("/orders", response_model=schemas.PublicOrderResponse)
def create_order(
    order: schemas.OrderCreate, 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user)
):
    # Create a new order
    new_order = models.Order(
        user_id=current_user.id,
        status=order.status,
        total_price=order.total_price,
        created_at=datetime.datetime.now(),
        updated_at=datetime.datetime.now()
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)

    # Add items to the order
    for item in order.items:
        order_item = models.OrderItem(
            order_id=new_order.id,
            product_id=item.product_id,
            quantity=item.quantity,
            color=item.color,
            size=item.size,
            price=item.price  
        )
        db.add(order_item)
    db.commit()

    # Load the order with items
    order_with_items = (
        db.query(models.Order)
        .filter(models.Order.id == new_order.id)
        .options(joinedload(models.Order.items).joinedload(models.OrderItem.product))  # Load related products
        .first()
    )

    hashed_order_id = hashids.encode(new_order.id)

    # Send the order confirmation email
    try:
        send_order_confirmation_email(
            receiver_email=current_user.email,
            receiver_name=current_user.full_name, 
            order_id=new_order.id  # Use plain ID for internal communication
        )
    except Exception as e:
        print(f"Error sending order confirmation email: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail="Failed to send confirmation email."
        )

    # Build the response data
    response_data = schemas.PublicOrderResponse(
        id=hashed_order_id,  # Use hashed ID
        plain_id=new_order.id,  # Include plain integer ID
        user_id=order_with_items.user_id,
        user=None,  # Optional, or provide user details if needed
        status=order_with_items.status.value,
        total_price=order_with_items.total_price,
        items=[
            schemas.OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_name=item.product.name,
                quantity=item.quantity,
                color=item.color,
                size=item.size.value if hasattr(item.size, 'value') else item.size,
                price=item.price
            )
            for item in order_with_items.items
        ],
        created_at=order_with_items.created_at,
        updated_at=order_with_items.updated_at,
    )

    return response_data



@router.delete("/order/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def cancel_order(order_id: str, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    numeric_order_id = hashids.decode(order_id)
    if not numeric_order_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid order ID")
    order = db.query(models.Order).filter(models.Order.user_id == current_user.id, models.Order.id == numeric_order_id[0]).first()
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found")
    if order.status != schemas.OrderStatusEnum.PENDING:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Only pending orders can be canceled")
    db.delete(order)
    db.commit()
    return {"message": "Order canceled successfully"}

#-----------------------------------#
#         WISHLIST ROUTES           #
#-----------------------------------#

@router.post("/wishlist", response_model=schemas.WishlistItemRead)
def add_wishlist_item(
    item: schemas.WishlistItemCreate,
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    return add_to_wishlist(db, current_user.id, item.product_id, color=item.color, size=item.size)

@router.get("/wishlist", response_model=List[schemas.WishlistItemRead])
def get_wishlist(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user),
):
    wishlist_items = (
        db.query(models.WishlistItem)
        .join(models.Wishlist, models.WishlistItem.wishlist_id == models.Wishlist.id)
        .filter(models.Wishlist.user_id == current_user.id)
        .all()
    )
    # Return an empty list instead of raising an error
    return wishlist_items



@router.delete("/wishlist/{item_id}", response_model=schemas.Message)
def remove_wishlist_item(item_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return remove_from_wishlist(db, item_id, current_user.id)

#-----------------------------------#
#          CART ROUTES              #
#-----------------------------------#

@router.get("/cart", response_model=schemas.Cart)
def get_cart(db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        # If the user doesn't have a cart yet, create one
        cart = models.Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return cart

# update cart item
@router.put("/cart/{item_id}", response_model=schemas.CartItem)
def update_cart_item(item_id: int, cart_item: schemas.CartItem, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Fetch the user's cart
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    # Find the cart item by its ID and ensure it belongs to the cart
    item = db.query(models.CartItem).filter(
        models.CartItem.id == item_id,
        models.CartItem.cart_id == cart.id
    ).first()

    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")


    item.quantity = cart_item.quantity
    item.color = cart_item.color
    item.size = cart_item.size

    db.commit()
    db.refresh(item) 
    return item

@router.post("/cart", response_model=schemas.CartItem)
def add_cart_item(cart_item: schemas.CartItem, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    if not cart:
        cart = models.Cart(user_id=current_user.id)
        db.add(cart)
        db.commit()
        db.refresh(cart)
    return add_to_cart(db, cart.id, cart_item.product.id, cart_item.quantity, color=cart_item.color, size=cart_item.size)

@router.delete("/cart/{item_id}", response_model=schemas.Message)
def remove_cart_item(item_id: int, db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    return remove_from_cart(db, item_id, current_user.id)

@router.delete("/cart/clear", response_model=schemas.Message)
def clear_user_cart(
    db: Session = Depends(database.get_db),
    current_user: models.User = Depends(get_current_user)
):
    # Find the user's cart
    cart = db.query(models.Cart).filter(models.Cart.user_id == current_user.id).first()
    
    if not cart:
        return {"message": "Cart is already empty"}
    
    try:
        # Delete the cart associated with the user
        db.delete(cart)
        db.commit()
    except Exception as e:
        print(f"Error clearing cart: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear the cart."
        )

    return {"message": "Cart cleared successfully"}


@router.get("/products", response_model=List[ProductSchema])
def get_products(
    db: Session = Depends(database.get_db),
    category_id: int = None,
    min_price: float = None,
    max_price: float = None
):
    query = db.query(Product)
    
    # Optionally filter by category
    if category_id:
        query = query.filter(Product.category_id == category_id)
    
    # Optionally filter by price range
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    
    return query.all()

@router.get("/products/{product_id}", response_model=ProductSchema)
def get_product(product_id: int, db: Session = Depends(database.get_db)):
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product

@router.post("/add-to-newsletter", response_model=None)
def add_to_newsletter(
    email_data: schemas.NewsletterUserSchema,
    db: Session = Depends(database.get_db)
):
    existing_user = db.query(models.NewsletterUser).filter(models.NewsletterUser.email == email_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")
    new_user = models.NewsletterUser(email=email_data.email)
    db.add(new_user)
    db.commit()
    return None

@router.post("/referrals", status_code=status.HTTP_200_OK)
def send_referrals(referral_request: ReferralRequest):
    referrals = referral_request.referrals

    if not referrals:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No referrals provided.")

    # Send an email to each referral
    for referral in referrals:
        send_promo_email(referral.email, referral.name)

    return {"message": "Referral emails sent successfully."}
