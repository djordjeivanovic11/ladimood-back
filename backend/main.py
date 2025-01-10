from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import models, db as database
from api.auth import auth
from api.account import account


app = FastAPI()


models.Base.metadata.create_all(bind=database.engine)


origins = [
    "http://localhost:3000", 

]


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(account.router, prefix="/api/account", tags=["account"])

