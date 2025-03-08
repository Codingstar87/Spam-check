from typing import Union
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.base import baseApi
from os import getenv
import uvicorn
from app.DB.postgress import DataBasePool
import os
from app.redis.redis import get_redis_client
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app:FastAPI) :
    await DataBasePool.setup()
    yield
    await DataBasePool.teardown()

app = FastAPI(lifespan=lifespan)

origin = "*"


app.include_router(baseApi,prefix="")

port = int(os.getenv("PORT", 8080))
host = os.getenv("HOST", "0.0.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin],
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"]
)

redis_client = get_redis_client()

if __name__ == "__main__":
    print(f"Server is running on http://{host}:{port}")
    uvicorn.run("spamChk:app", host=host, port=port, reload=True, log_level="debug")




