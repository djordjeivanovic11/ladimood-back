from fastapi import HTTPException, status # type: ignore
from sqlalchemy.orm import Session 
from database import models
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage

# Fetch user address by user ID
def get_user_address(db: Session, user_id: int):
    address = db.query(models.Address).filter(models.Address.user_id == user_id).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address

# Fetch user orders by user ID
def get_user_orders(db: Session, user_id: int):
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found")
    return orders

# Fetch user's wishlist by user ID
def get_user_wishlist(db: Session, user_id: int):
    wishlist = db.query(models.WishlistItem).join(models.Wishlist).filter(models.Wishlist.user_id == user_id).all()
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return wishlist

# Fetch user's cart by user ID
def get_user_cart(db: Session, user_id: int):
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return cart

# Fetch cart item by cart ID and product ID
def get_cart_item(db: Session, cart_id: int, product_id: int):
    cart_item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id, models.CartItem.product_id == product_id).first()
    return cart_item

# Add product to user's wishlist
def add_to_wishlist(db: Session, user_id: int, product_id: int, color: str, size: str):
    # Check if the user already has a wishlist
    wishlist = db.query(models.Wishlist).filter(models.Wishlist.user_id == user_id).first()

    # If no wishlist exists for the user, create one
    if not wishlist:
        wishlist = models.Wishlist(user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)

    # Check if the item is already in the wishlist
    existing_item = db.query(models.WishlistItem).filter(
        models.WishlistItem.product_id == product_id,
        models.WishlistItem.wishlist_id == wishlist.id  # Check if it's in the user's wishlist
    ).first()

    if existing_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already in wishlist")

    # Add the wishlist item with color and size
    wishlist_item = models.WishlistItem(
        product_id=product_id,
        wishlist_id=wishlist.id,  # Use the user's wishlist ID
        color=color,  # Ensure color is passed here
        size=size     # Ensure size is passed here
    )
    db.add(wishlist_item)
    db.commit()
    db.refresh(wishlist_item)
    return wishlist_item

# Remove product from user's wishlist
def remove_from_wishlist(db: Session, wishlist_item_id: int, user_id: int):
    wishlist_item = db.query(models.WishlistItem).filter(
        models.WishlistItem.id == wishlist_item_id,
        models.WishlistItem.wishlist.has(user_id=user_id)
    ).first()
    if not wishlist_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist item not found")
    db.delete(wishlist_item)
    db.commit()
    return {"message": "Item removed from wishlist"}

# Add product to user's cart
def add_to_cart(db: Session, cart_id: int, product_id: int, quantity: int, color: str, size: str):
    cart_item = models.CartItem(
        cart_id=cart_id,
        product_id=product_id,
        quantity=quantity,
        color=color,  
        size=size     
    )
    db.add(cart_item)
    db.commit()
    db.refresh(cart_item)
    return cart_item


# Remove item from user's cart
def remove_from_cart(db: Session, cart_item_id: int, user_id: int):
    cart_item = db.query(models.CartItem).filter(
        models.CartItem.id == cart_item_id,
        models.CartItem.cart.has(user_id=user_id)
    ).first()
    if not cart_item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart item not found")
    db.delete(cart_item)
    db.commit()
    return {"message": "Item removed from cart"}

def clear_cart(db: Session, user_id: int):
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")

    # Delete all items from the user's cart
    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"message": "Cart cleared successfully"}

def send_promo_email(receiver_email: str, receiver_name: str):
    # Use environment variables for credentials
    sender_email = "djordjeivanovic65@gmail.com"
    sender_password = "owlj ddmq zjce gues"

    subject = "Your friend recommended Ladimood!"

    template_path = "templates/promo_email.html"

    # Load the HTML template
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Error reading email template: {e}")
        raise Exception("Failed to read email template.")

    # Replace placeholder with the receiver's name
    html_content = html_content.replace('{{ receiver_name }}', receiver_name)

    # Create the root message
    msg_root = MIMEMultipart('alternative')
    msg_root['Subject'] = subject
    msg_root['From'] = sender_email
    msg_root['To'] = receiver_email

    # Attach the HTML content
    msg_html = MIMEText(html_content, 'html')
    msg_root.attach(msg_html)

    # Send the email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg_root.as_string())
        print(f"Email sent successfully to {receiver_email}")
    except Exception as e:
        print(f"Failed to send email to {receiver_email}: {e}")
        raise Exception("Failed to send email.")
    

def send_order_confirmation_email(receiver_email: str, receiver_name: str, order_id: int):
    sender_email = "djordjeivanovic65@gmail.com"
    sender_password = "owlj ddmq zjce gues"

    subject = f"Order Confirmation - Order #{order_id}"

    template_path = "templates/order_confirmation_email.html"

    # Load the HTML template
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Error reading email template: {e}")
        raise Exception("Failed to read email template.")

    # Replace placeholders with actual values
    html_content = html_content.replace('{{ receiver_name }}', receiver_name)
    html_content = html_content.replace('{{ order_id }}', str(order_id))

    # Create the root message
    msg_root = MIMEMultipart('alternative')
    msg_root['Subject'] = subject
    msg_root['From'] = sender_email
    msg_root['To'] = receiver_email

    # Attach the HTML content
    msg_html = MIMEText(html_content, 'html')
    msg_root.attach(msg_html)

    # Send the email
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg_root.as_string())
        print(f"Order confirmation email sent successfully to {receiver_email}")
    except Exception as e:
        print(f"Failed to send order confirmation email to {receiver_email}: {e}")
        raise Exception("Failed to send email.")
