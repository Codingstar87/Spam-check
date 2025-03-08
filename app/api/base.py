from fastapi import APIRouter,Request
from pydantic import BaseModel,Field, EmailStr
from fastapi import Depends
from app.DB.postgress import DataBasePool
from app.api.domain import handle_domain, handle_add_domain, handle_signup , handle_login
from typing import Union
from starlette.requests import Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.api.checkmail import buy_plan ,check_email , check_plan


baseApi = APIRouter(prefix="",tags=["api"])



class New_Domain(BaseModel):
    domain :str
    disposable:bool = Field(default=False)
    publicDomain:bool = Field(default= False)
    suspicious:bool = Field(default=False)

@baseApi.get("/domain/{domain}")
async def domain (domain, db_pool = Depends(DataBasePool.get_pool)):
    return await handle_domain(domain,db_pool)

@baseApi.post("/add_domain")
async def add_domain( data: New_Domain, db_pool=Depends(DataBasePool.get_pool)):
    return await handle_add_domain(data, db_pool)



class SINGUP(BaseModel):
    username: str
    email: str
    password:str
    role :str
 

class LOGIN(BaseModel):
    email: str
    password:str

@baseApi.post("/signup")
async def signup(request: Request, data: SINGUP, db_pool=Depends(DataBasePool.get_pool)):
    return await handle_signup(request, data, db_pool)

@baseApi.post("/login")
async def login(request: Request, data: LOGIN, db_pool=Depends(DataBasePool.get_pool)):
    return await handle_login(request, data, db_pool)




class PlanPurchase(BaseModel):
    email: EmailStr
    plan: Union[int, str]

@baseApi.post("/planpurchase")
async def buy_plan_endpoint(plan: PlanPurchase, db_pool=Depends(DataBasePool.get_pool)):
    return await buy_plan(plan, db_pool)


@baseApi.get("/check-plan/{email}")
async def check_plan_endpoint(email: EmailStr, db_pool=Depends(DataBasePool.get_pool)):
    return await check_plan(email, db_pool)

class CheckEmail(BaseModel):
    api_key : str
    emails : list[EmailStr] = []
    domains : list[str] = []


limiter = Limiter(key_func=get_remote_address)



@baseApi.post('/check-email')
async def check_email_endpoint(data: CheckEmail, db_pool=Depends(DataBasePool.get_pool) ):
    return await check_email(data , db_pool)
