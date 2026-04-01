from fastapi import FastAPI
from dotenv import load_dotenv

load_dotenv()

try:
	from .database import initialize_database
	from .routers import eventos, ia
except ImportError:
	from database import initialize_database
	from routers import eventos, ia

app = FastAPI()


@app.on_event("startup")
def startup():
	initialize_database()


app.include_router(eventos.router)
app.include_router(ia.router)


@app.get("/")
def root():
	return {"status": "ok"}
