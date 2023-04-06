from typing import Union
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
import psycopg
from datetime import datetime, date, timedelta
import os
from pydantic import validator
from pydantic import ValidationError
from passlib.hash import pbkdf2_sha256
from jose import JWTError, jwt

SECRET_KEY = "3cb260cf64fd0180f386da0e39d6c226137fe9abf98b738a70e4299e4c2afc93"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class Perc(BaseModel):
    value: float
    percent: float

class User(BaseModel):
    username: str
    password: str

    @validator('username')
    def username_validation(cls, v):
        if ' ' in v:
            raise ValueError('username contains space')
        return v
    
    @validator('password')
    def password_validation(cls, v):
        if ('!' or '&' or '$' or '%') not in v:
            raise ValueError('password should contain one of the following symbols: !,&,$,%')
        return v
    
DB_DSN = os.environ.get("DB_DSN")

app = FastAPI()

def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def authenticate_user(username: str, password: str, hashed_password):
    if not username:
        return False
    if not pbkdf2_sha256.verify(password, hashed_password):
        return False
    user = {username:password}
    return user

@app.on_event("startup")
async def startup_event():
    with psycopg.connect(DB_DSN) as conn:

    # Open a cursor to perform database operations
        with conn.cursor() as cur:

        # Execute a command: this creates a new table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS percents_data (
                    added FLOAT (50) NOT NULL,
                    subtracted FLOAT (50) NOT NULL,
                    percent FLOAT (50) NOT NULL,
                    time TIMESTAMP)
                """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    username VARCHAR (100) NOT NULL,
                    password VARCHAR (100) NOT NULL,
                    JWT VARCHAR (100))
                """)
     
@app.post("/add_user")
async def add_user(item: User):

    hashed_password = pbkdf2_sha256.hash(item.password)

    with psycopg.connect(DB_DSN) as conn:

        with conn.cursor() as cur:

            cur.execute(
            "INSERT INTO users (username, password) VALUES (%s, %s)",
            (item.username,hashed_password)
            )
                
    pass

@app.post("/authenticate_user")
async def authenticate_user(item: User):

    with psycopg.connect(DB_DSN) as conn:

        with conn.cursor() as cur:
            hashed_password = cur.execute(
                "SELECT password FROM users WHERE username = '%s'",
                (item.username))

    user = authenticate_user(item.username, item.password, hashed_password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": item.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}
       

@app.post("/calculate_percents")
async def create_item(item: Perc):
    if item.percent < 0:
        return {"message": "try positive value"}
    else:
        sum = item.value + item.percent*item.value/100
        sub = item.value - item.percent*item.value/100
        per = item.percent*item.value/100
        item_dict_result = [{"added":sum, "subtracted":sub, "percent":per }]

    now = datetime.now()

    with psycopg.connect(DB_DSN) as conn:

        with conn.cursor() as cur:
            cur.execute(
            "INSERT INTO percents_data (added, subtracted, percent, time) VALUES (%s, %s, %s, %s)",
            (item_dict_result["added"], item_dict_result["subtracted"], item_dict_result["percent"], now))


    return item_dict_result



        