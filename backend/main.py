from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import models, db as database
from api.auth import auth
from api.account import account


app = FastAPI()

# Create the database tables
models.Base.metadata.create_all(bind=database.engine)

# Allow CORS for frontend communication
origins = [
    "http://localhost:3000", 
    # Add other allowed origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include the authentication router
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(account.router, prefix="/api/account", tags=["account"])

