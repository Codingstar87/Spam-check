import traceback
from ..DB.postgress import DB
from ..DB.postgressModel import TableNameEnum
from passlib.context import CryptContext
    


async def handle_domain(domain, db_pool):
    try:
        data = await DB.get_attr(TableNameEnum.DOMAINS, domain, db_pool)
        
        if data:
            await DB.update_attr(TableNameEnum.DOMAINS, domain, {"seen": data.seen + 1}, db_pool=db_pool)
            return {
                "code": 200,
                "domain": domain,
                "disposable": data.disposable,
                "publicDomain": data.publicDomain,
                "suspicious": data.suspicious
            }
    
        try:
            with open("publicDomain.text", "r") as file:
                public_domains = {line.strip() for line in file}
        except Exception as e:
            traceback.print_exc()
            return {"code": 500, "error": "Failed to read public domains file"}
        if domain in public_domains:
            return {
                "code": 200,
                "domain": domain,
                "disposable": False,
                "publicDomain": True,
                "suspicious": False
            }
        data = await DB.get_attr(TableNameEnum.NEW_DOMAINS, domain, db_pool)

        if data:
            await DB.update_attr(TableNameEnum.NEW_DOMAINS, domain, {"seen": data.seen + 1}, db_pool=db_pool)
        else:
            await DB.insert_attr(TableNameEnum.NEW_DOMAINS, {"domain": domain, "seen": 1}, db_pool=db_pool)

        return {
            "code": 200,
            "domain": domain,
            "disposable": False,
            "publicDomain": False,
            "suspicious": False
        }

    except Exception as e:
        traceback.print_exc()
        return {"code": 500, "error": str(e)}



async def handle_add_domain(data, db_pool):
    try:
        domain = data.domain  
        existing_domain = await DB.get_attr(TableNameEnum.DOMAINS, domain, db_pool)

        if not existing_domain:
            with open("publicDomain.text", "r") as file:
                public_domains = {line.strip() for line in file}

            if domain in public_domains:
                return {"code": 200, "domain": domain, "disposable": False, "publicDomain": True, "suspicious": False}
            else:
                await DB.insert_attr(TableNameEnum.DOMAINS, {"domain": domain}, db_pool=db_pool)

            return {"code": 200, "domain": domain, "message": "Domain added "}

    except Exception as e:
        traceback.print_exc()
        return {"code": 500, "error": str(e)}




async def handle_signup(request, data, db_pool):
    try:
        email = data.email
        domain = email.split("@")[1]
        
        domain_data = await DB.get_attr(TableNameEnum.DOMAINS, domain, db_pool)
        if domain_data:
            return {"code": 400, "error": "The email is a spam email. Please check the email."}
        
        if await DB.get_attr(TableNameEnum.USERS, email, db_pool):
            return {"code": 400, "error": "Email already exists"}
        
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        hashed_password = pwd_context.hash(data.password)
        
        userdata = {
            "username": data.username,
            "email": email,
            "password": hashed_password,
            "role": data.role 
        }
        
        user_id = await DB.insert_attr(TableNameEnum.USERS, userdata, db_pool)
        
        if user_id and user_id is not None:  
            return {"code": 201, "message": "User registered successfully"}
        else:
            return {"code": 500, "error": "Internal server error. Could not register user."}
        
    except Exception as e:
        traceback.print_exc()
        return {"code": 500, "error": str(e)}





async def handle_login(request, data, db_pool):
    user_data = await DB.get_attr(TableNameEnum.USERS, data.email, db_pool)

    if not user_data:
        return {"code": 400, "error": "Invalid email"}

    if isinstance(user_data, dict):
        hashed_password = user_data.get("password")
    else:
        hashed_password = getattr(user_data, "password", None)

    if not hashed_password:
        return {"code": 400, "error": "Invalid user data"}

    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    if not pwd_context.verify(data.password, hashed_password):
        return {"code": 400, "error": "Invalid password"}

    return {"code": 200, "message": "Login successful"}