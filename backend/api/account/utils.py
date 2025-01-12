from fastapi import HTTPException, status # type: ignore
from sqlalchemy.orm import Session 
from database import models
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import dotenv

dotenv.load_dotenv()

EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

def get_user_address(db: Session, user_id: int):
    address = db.query(models.Address).filter(models.Address.user_id == user_id).first()
    if not address:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Address not found")
    return address

def get_user_orders(db: Session, user_id: int):
    orders = db.query(models.Order).filter(models.Order.user_id == user_id).all()
    if not orders:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="No orders found")
    return orders

def get_user_wishlist(db: Session, user_id: int):
    wishlist = db.query(models.WishlistItem).join(models.Wishlist).filter(models.Wishlist.user_id == user_id).all()
    if not wishlist:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Wishlist not found")
    return wishlist

def get_user_cart(db: Session, user_id: int):
    cart = db.query(models.Cart).filter(models.Cart.user_id == user_id).first()
    if not cart:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cart not found")
    return cart

def get_cart_item(db: Session, cart_id: int, product_id: int):
    cart_item = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id, models.CartItem.product_id == product_id).first()
    return cart_item

def add_to_wishlist(db: Session, user_id: int, product_id: int, color: str, size: str):
    wishlist = db.query(models.Wishlist).filter(models.Wishlist.user_id == user_id).first()
    if not wishlist:
        wishlist = models.Wishlist(user_id=user_id)
        db.add(wishlist)
        db.commit()
        db.refresh(wishlist)

    existing_item = db.query(models.WishlistItem).filter(
        models.WishlistItem.product_id == product_id,
        models.WishlistItem.wishlist_id == wishlist.id 
    ).first()

    if existing_item:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Item already in wishlist")

    wishlist_item = models.WishlistItem(
        product_id=product_id,
        wishlist_id=wishlist.id, 
        color=color,  
        size=size    
    )
    db.add(wishlist_item)
    db.commit()
    db.refresh(wishlist_item)
    return wishlist_item

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

    db.query(models.CartItem).filter(models.CartItem.cart_id == cart.id).delete()
    db.commit()
    return {"message": "Cart cleared successfully"}

def send_promo_email(receiver_email: str, receiver_name: str):
    sender_email = EMAIL
    sender_password = PASSWORD

    subject = "Your friend recommended Ladimood!"

    template_path = "templates/promo_email.html"

    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Error reading email template: {e}")
        raise Exception("Failed to read email template.")

    html_content = html_content.replace('{{ receiver_name }}', receiver_name)

    msg_root = MIMEMultipart('alternative')
    msg_root['Subject'] = subject
    msg_root['From'] = sender_email
    msg_root['To'] = receiver_email

    msg_html = MIMEText(html_content, 'html')
    msg_root.attach(msg_html)

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

    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            html_content = file.read()
    except Exception as e:
        print(f"Error reading email template: {e}")
        raise Exception("Failed to read email template.")

    html_content = html_content.replace('{{ receiver_name }}', receiver_name)
    html_content = html_content.replace('{{ order_id }}', str(order_id))

    msg_root = MIMEMultipart('alternative')
    msg_root['Subject'] = subject
    msg_root['From'] = sender_email
    msg_root['To'] = receiver_email

    msg_html = MIMEText(html_content, 'html')
    msg_root.attach(msg_html)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg_root.as_string())
        print(f"Order confirmation email sent successfully to {receiver_email}")
    except Exception as e:
        print(f"Failed to send order confirmation email to {receiver_email}: {e}")
        raise Exception("Failed to send email.")
