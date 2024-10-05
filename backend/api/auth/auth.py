from fastapi import APIRouter, Depends, Cookie, HTTPException, status, Body
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from datetime import timedelta
from database import models, schemas, db as database 
from . import utils
from database.schemas import ForgotPasswordRequest
from datetime import datetime
from jwt import PyJWTError
from api.auth.utils import get_current_user

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


@router.post("/register", response_model=schemas.User)
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
   # Check if the email is already registered
    db_user = db.query(models.User).filter(models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed_password = utils.get_password_hash(user.password)
    
    default_role_id = 2  
    
    # Create the user
    db_user = models.User(
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        phone_number=user.phone_number,
        is_active=True,
        role_id=default_role_id,  
        created_at=datetime.now(),  
        updated_at=datetime.now()  
    )
    
    # Add and commit the user to the database
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


# Login route
@router.post("/login", response_model=schemas.Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    # OAuth2PasswordRequestForm uses 'username' field by default, which we are treating as email
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    
    if not user or not utils.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(data={"sub": user.email}, expires_delta=access_token_expires)
    refresh_token = utils.create_refresh_token(data={"sub": user.email})

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.post("/token/refresh", response_model=schemas.Token)
def refresh_access_token(refresh_token: str = Body(...), db: Session = Depends(database.get_db), current_user: models.User = Depends(get_current_user)):
    # Decode the refresh token
    try:
        payload = utils.decode_token(refresh_token)
    except PyJWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    # Ensure it's a refresh token
    if payload.get("token_type") != "refresh":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token type")

    # Get email (subject) from the token
    email = payload.get("sub")
    if not email:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload")

    # Fetch the user from the database
    user = db.query(models.User).filter(models.User.email == email).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Create a new access token
    access_token_expires = timedelta(minutes=utils.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = utils.create_access_token(data={"sub": user.email, "token_type": "access"}, expires_delta=access_token_expires)
    
    return {"access_token": access_token, "token_type": "bearer"}


# Change password route
@router.post("/change-password", response_model=schemas.Message)
def change_password(
    current_password: str = Body(...), 
    new_password: str = Body(...), 
    db: Session = Depends(database.get_db), 
    current_user: models.User = Depends(get_current_user) 
):
    if not utils.verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect current password")
    
    current_user.hashed_password = utils.get_password_hash(new_password)
    db.commit()
    
    return {"message": "Password changed successfully"}



@router.post("/forgot-password", response_model=schemas.Message)
def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.email == request.email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    reset_token = utils.create_reset_token(data={"sub": user.email})
    utils.send_reset_email(email=user.email, token=reset_token)
    
    return {"message": "If this email is registered, you will receive instructions to reset your password."}

@router.post("/reset-password", response_model=schemas.Message)
def reset_password(token: str = Body(...), new_password: str = Body(...), db: Session = Depends(database.get_db)):
    email = utils.verify_reset_token(token)
    if email is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid or expired token")

    user = db.query(models.User).filter(models.User.email == email).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    user.hashed_password = utils.get_password_hash(new_password)
    db.commit()

    return {"message": "Password reset successfully"}

@router.post("/logout", response_model=schemas.Message)
def logout(
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(database.get_db)
):
    return {"message": "Logout successful"}