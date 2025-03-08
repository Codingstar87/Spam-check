from datetime import timedelta,datetime
import traceback
import uuid
from fastapi import HTTPException
from ..DB.postgress import DB
from ..DB.postgressModel import TableNameEnum,PLANS
from ..redis.redis import get_redis_client
from sqlalchemy.exc import IntegrityError


PLAN_RATE_LIMITS = {
    200000: 5,
    500000: 15,
    1500000: 25,
    3500000: 50,
    
}
EXPIRATION_TIME = int(timedelta(days=30).total_seconds())

async def buy_plan(plan, db_pool):
    try:
        email = plan.email
        selected_plan = plan.plan  
        
        rate_limits = {
            200000: 5,
            500000: 15,
            1500000: 25,
            3500000: 50
        }

       
        if selected_plan == "free":
            selected_plan = 1000 
            rate_limit = 1
        elif selected_plan in rate_limits:
            rate_limit = rate_limits[selected_plan]
        else:
            raise HTTPException(status_code=400, detail="Invalid plan selected.")
        
        existing_email = await DB.get_attr(TableNameEnum.PLANS, email, db_pool)
        
        if existing_email:
            formatted_created_at = datetime.fromtimestamp(existing_email.created_at).strftime("%Y-%m-%d %H:%M:%S")
            formatted_expired_at = datetime.fromtimestamp(existing_email.expired_at).strftime("%Y-%m-%d %H:%M:%S")
            api_key = existing_email.api_key if existing_email.api_key else 'no api_key please take a plan'
            
            return {"message": {
                "email": existing_email.email,
                "plan": existing_email.plan,
                "api_key": api_key,
                "used": existing_email.used,
                "remaining": existing_email.remaining,
                "created": formatted_created_at,
                "expired_at": formatted_expired_at,
                "rate_limit": PLAN_RATE_LIMITS.get(existing_email.plan, 1)  
            }}
        else:
            api_key = str(uuid.uuid4())
            rate_limit = PLAN_RATE_LIMITS.get(selected_plan, 1)
            remaining_emails = 1000 if selected_plan == "free" else selected_plan
            
            await DB.insert_attr(
                TableNameEnum.PLANS, 
                {"email": email, "api_key": api_key, "plan": selected_plan, "remaining": remaining_emails, "rate_limit": rate_limit},
                db_pool=db_pool
            )


            redis_client = get_redis_client()
            if redis_client:
                redis_client.set(api_key, rate_limit, EXPIRATION_TIME)
            return {
                "message": "Plan purchase processed successfully and data stored in Redis",
                "api_key": api_key,
                "rate_limit": rate_limit,
                "expires_in": EXPIRATION_TIME
            }
        
    except:
        traceback.print_exc()
        return None




async def check_plan(email, db_pool):
    existing_email = await DB.get_attr(TableNameEnum.PLANS, email, db_pool)
        
    if existing_email:
        formatted_created_at = datetime.utcfromtimestamp(existing_email.created_at).strftime("%Y-%m-%d %H:%M:%S") if isinstance(existing_email.created_at, int) else existing_email.created_at.strftime("%Y-%m-%d %H:%M:%S")
        formatted_expired_at = datetime.utcfromtimestamp(existing_email.expired_at).strftime("%Y-%m-%d %H:%M:%S") if isinstance(existing_email.expired_at, int) else existing_email.expired_at.strftime("%Y-%m-%d %H:%M:%S")
        api_key = existing_email.api_key if existing_email.api_key else 'no api_key, please take a plan'
        

        return {
            "message": {
                "email": existing_email.email,
                "plan": existing_email.plan,
                "api_key": api_key,
                "used": existing_email.used,
                "remaining": existing_email.remaining,
                "created": formatted_created_at,
                "expired_at": formatted_expired_at
            }
        }
    else:
        return {"message": "No plan found for the given email."}





async def check_email( data, db_pool):
    api_key = data.api_key
    domains = data.domains
    emails = data.emails

    if not api_key:
        raise HTTPException(status_code=400, detail="API key is required.")

    check_key = await DB.get_attr(TableNameEnum.PLANS, api_key, db_pool)
    count = check_key.rate_limit 
    # print(count)

    if not check_key:
        raise HTTPException(status_code=400, detail="Invalid API key.")
    
    if not emails and not domains:
        raise HTTPException(status_code=400, detail="Please provide either some emails or domains to check.")

    domain_list = []
    for d in domains :
        domain_list.append(d)
    for b in emails :
        extracted_domain = b.split('@')[-1]
        domain_list.append(extracted_domain)
    

    if len(domain_list) > count:
        raise HTTPException(status_code=400, detail=f"You cannot check more than {count} emails or domains at a time.")

    #
    redis_client = get_redis_client()
    redis_key = f"rate_limit:{api_key}"
    rate_limit =  redis_client.get(api_key) 
    if rate_limit is None:
        raise HTTPException(status_code=500, detail="Rate limit not found in Redis.")

    # print(rate_limit)
    rate_limit = int(rate_limit)  

    redis_count_key = f"rate_count:{api_key}"
    current_count =  redis_client.get(redis_count_key)

    
    
    print("current_count",current_count)
    if current_count is None:
        redis_client.set(redis_count_key, 0, ex=60)
        current_count = 0
    else:
        current_count = int(current_count)

    remaining_checks = rate_limit - current_count

    if len(domain_list) > remaining_checks:
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit exceeded: You can check {remaining_checks} more emails this second."
        )
    redis_client.incrby(redis_count_key, len(domain_list))


    #
    public_domains = set()
    try:
        with open("publicDomain.text", "r") as file:
            public_domains = {line.strip() for line in file}
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail="Public domain file not found.")
    
    public_domains_found = []
    spam_domains = []
    not_spam_domains = []

    for domain in domain_list:
        if domain in public_domains:
            public_domains_found.append(domain)
            continue 
        domain_data = await DB.get_attr(TableNameEnum.DOMAINS, domain, db_pool)
        if domain_data:
            spam_domains.append(domain)
        else:
            existing_domain = await DB.get_attr(TableNameEnum.NEW_DOMAINS, domain, db_pool)
            not_spam_domains.append(domain)
            if not existing_domain:
                try:
                    await DB.insert_attr(TableNameEnum.NEW_DOMAINS, {"domain": domain}, db_pool=db_pool)
                except IntegrityError:
                    print(f"Domain {domain} already exists in new_domains. Skipping insertion.")

    total_limit = check_key.plan 
    used = check_key.used
    remaining_limit = check_key.remaining
    total_checks = len(domain_list)
    if total_checks == 0:
        raise HTTPException(status_code=400, detail="Please provide either some emails or domains to check.")

    new_used = used + total_checks
    new_remaining_limit = remaining_limit - total_checks
    if new_used > total_limit:
        raise HTTPException(status_code=400, detail="Exceeded total limit for checking emails/domains.")
    try:
 
        await DB.update_attr(
            TableNameEnum.PLANS,
            {"api_key": api_key, "used": new_used, "remaining": new_remaining_limit},
            db_pool=db_pool  
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating plan data: {str(e)}")

    return {
        "Public Domains": public_domains_found,
        "Spam Domains": spam_domains,
        "Not Spam Domains": not_spam_domains,
        "total_limit": total_limit,
        "used": new_used,
        "remaining": new_remaining_limit
    }
