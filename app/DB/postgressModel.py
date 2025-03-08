from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import (Column,Integer,String,Boolean,ForeignKey,func,BigInteger)
from typing import Optional,List
import time



class TableNameEnum(str,Enum) :
    USERS = "users"
    # COLLECT = "collect"
    DOMAINS = "domains"
    # PROVIDERS = "providers"
    # PROVIDERS_DOMAINS = "providers_domains"
    PLANS = "plan"
    # EMAILS = "emails"
    BLOCKLIST = "blocklist"
    SESSION = "session"
    NEW_DOMAINS = "new_domain"

class DOMAINS(SQLModel,table = True):
    id : int = Field(primary_key=True)
    domain :str = Field(unique=True)
    disposable: bool = Field(default=False)
    publicDomain : bool = Field(default=False)
    suspicious : bool = Field(default=False)
    seen :int = Field(default=0, sa_column=Column(Integer,default=0))
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))
    updated_at: Optional[int] = Field(default=0, sa_column=Column(Integer, onupdate=func.extract("epoch", func.now())))

class NEW_DOMAINS(SQLModel, table=True):
    id: int = Field(primary_key=True)
    domain: str = Field(unique=True)
    # provider: str = Field(default="")
    disposable: bool = Field(default=False)
    publicDomain: bool = Field(default=False)
    suspicious: bool = Field(default=False)
    seen: int = Field(default=0, sa_column=Column(Integer, default=0))
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))
    updated_at: Optional[int] = Field(default=0, sa_column=Column(Integer, onupdate=func.extract("epoch", func.now())))

class BLOCKLIST(SQLModel, table = True):
    id : int = Field(primary_key=True)
    username : str 
    domain : str 
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))
    updated_at: Optional[int] = Field(default=0, sa_column=Column(Integer, onupdate=func.extract("epoch", func.now())))


class SESSION(SQLModel,table = True):
    id :int = Field(primary_key=True)
    username : str
    role : str
    ip : Optional[str]
    browser : Optional[str]
    os : Optional[str]
    created_at: Optional[int] = Field(default_factory=lambda: int(time.time()))
    updated_at: Optional[int] = Field(default=0, sa_column=Column(Integer, onupdate=func.extract("epoch", func.now())))

class USERS(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True)
    email: str = Field(index=True)  
    password: str
    role: str
    sbs_id: Optional[int] = Field(default=None, foreign_key="plans.id", nullable=True) 
    created_at: int = Field(default_factory=lambda: int(time.time()), sa_column=Column(BigInteger))
    updated_at: Optional[int] = Field(
        default=0,
        sa_column=Column(BigInteger, onupdate=func.extract("epoch", func.now()))
    )

class PLANS(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    email: str = Field(index=True)  
    api_key: Optional[str] = Field(default="", nullable=True)
    plan: Optional[int] = Field(default=0)
    rate_limit: Optional[int] = Field(default=1)
    paid_amount: Optional[float] = Field(default=0.00, nullable=True)
    used: Optional[int] = Field(default=0)
    remaining: Optional[int] = Field(default=0)
    created_at: int = Field(default_factory=lambda: int(time.time()), sa_column=Column(BigInteger))
    expired_at: int = Field(default_factory=lambda: int(time.time() + (30 * 24 * 60 * 60)), sa_column=Column(BigInteger))
    # refund_amount: Optional[float] = Field(default=0.00, nullable=True)





