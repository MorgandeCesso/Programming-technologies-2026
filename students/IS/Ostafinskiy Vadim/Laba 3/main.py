from fastapi import FastAPI
from api.controller import router

app = FastAPI(title="Workshop RAG")
app.include_router(router)
