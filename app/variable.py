from os import getenv
from dotenv import load_dotenv

load_dotenv(override=True)

DATABASE_URL = getenv("DATABASE_URL","")