from fastapi.responses import JSONResponse
import time ,traceback
from sqlmodel import Session,SQLModel,create_engine,select,func
from typing import Optional
from app import variable
from .postgressModel import TableNameEnum, DOMAINS, PLANS, BLOCKLIST, USERS, NEW_DOMAINS




def send_json_response(message : str, status : int, body : dict ) -> dict:

    return JSONResponse(
        content= {"message":message, "status":status, "body":body},
        status_code = status
    )

class UninitializedDatabasepoolError(Exception):
    def __init__(self,message = "The database connection pool has not been properly initialized.Please ensure setup is called "):
        self.message = message
        super().__init__(self.message)


class DataBasePool:
    _db_pool : Session = None
    _engine = None

    @classmethod
    async def initDB(cls):
        initDB(cls._engine)

    @classmethod
    async def  getEngine(cls):
        return cls._engine
    
    @classmethod
    async def setup(cls, timeout: Optional[float] = None):
        if cls._engine is not None:
            initDB(cls._engine)
        else:
            cls._engine = create_engine(
                variable.DATABASE_URL, 
                pool_size=20, 
                pool_pre_ping=True, 
                pool_recycle=60
            )
            initDB(cls._engine)
            cls._timeout = timeout
            with Session(cls._engine) as session :
                 cls._db_pool = session
    
    @classmethod
    async def get_pool(cls) -> Session:
        if cls._db_pool == None :
            raise UninitializedDatabasepoolError()
        return cls._db_pool
    
    @classmethod
    async def teardown(cls):
        print("closing databse connection")
        if not cls._db_pool :
            raise UninitializedDatabasepoolError()
        cls._db_pool.close()
        print("Database connection closed")



def initDB(_engine):
    try :
        SQLModel.metadata.create_all(_engine)

    except :
        traceback.print_exc()
        print(f"Error in creating tables")


class DB :
    def __init__(self):
        pass
    
    @classmethod
    async def get_attr(cls, dbClassNam : TableNameEnum, data, db_pool):
        if dbClassNam == TableNameEnum.DOMAINS:
            statement = select(DOMAINS).where(DOMAINS.domain == data)
            table = db_pool.exec(statement).first()
        elif dbClassNam == TableNameEnum.BLOCKLIST:
            statement = select(BLOCKLIST).where(BLOCKLIST.domain == data)
            table = db_pool.exec(statement).first()
        elif dbClassNam == TableNameEnum.NEW_DOMAINS:
            statement = select(NEW_DOMAINS).where(NEW_DOMAINS.domain == data)
            table = db_pool.exec(statement).first()
        elif dbClassNam == TableNameEnum.USERS:
            statement = select(USERS).where(USERS.email == data)
            table = db_pool.exec(statement).first()
        elif dbClassNam == TableNameEnum.PLANS:
            if "@" in data:
                statement = select(PLANS).where(PLANS.email == data)
            else:
                statement = select(PLANS).where(PLANS.api_key == data)
            table = db_pool.exec(statement).first()
        return table
    
    @classmethod
    async def calculate_domains(self,domain, db_pool):
        statement  = select(func.count()).select_from(DOMAINS).where(DOMAINS.domain == domain)
        table_count = db_pool.exec(statement).one()
        return table_count
    
    @classmethod
    async def update_attr(cls, dbClassNam : TableNameEnum, data, db_pool ):
        try:
            table = None
            if dbClassNam == TableNameEnum.DOMAINS :
                satement = select(DOMAINS).where(DOMAINS.domain == data)
                table = db_pool.exec(satement).first()
            elif dbClassNam == TableNameEnum.BLOCKLIST :
                satement = select(BLOCKLIST).where(BLOCKLIST.domain == data)
                table = db_pool.exec(satement).first()
            elif dbClassNam == TableNameEnum.NEW_DOMAINS :
                satement = select(NEW_DOMAINS).where(NEW_DOMAINS.domain == data)
                table = db_pool.exec(satement).first()
            elif dbClassNam == TableNameEnum.PLANS:
                satement = select(PLANS).where(PLANS.api_key == data["api_key"])

            if not table:
                return False

            for key, value in data.items():
                setattr(table, key, value)
            db_pool.commit()
        except Exception as e :
            if isinstance(db_pool,Session):
                db_pool.rollback()
            
            traceback.print_exc()
            return False
        
    @classmethod
    async def insert_attr(cls, db_classNam : TableNameEnum, data, db_pool):
        try:
            if db_classNam == TableNameEnum.USERS :
                data = USERS(**data)
            elif db_classNam == TableNameEnum.DOMAINS:
                data = DOMAINS(**data)
            elif db_classNam == TableNameEnum.BLOCKLIST:
                data = BLOCKLIST(**data)
            elif db_classNam == TableNameEnum.NEW_DOMAINS:
                data = NEW_DOMAINS(**data)
            elif db_classNam == TableNameEnum.PLANS :
                data = PLANS(**data)
            else :
                return False
            db_pool.add(data)
            db_pool.commit()
            db_pool.refresh(data)

            return True, data

        except Exception as e :
            db_pool.rollback()
            traceback.print_exc()
            return False ,None