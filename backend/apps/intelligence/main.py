# Entrypoint for intelligence API
from fastapi import FastAPI

app = FastAPI(title="LLM Intelligence Layer")

@app.get("/")
def read_root():
    return {"message": "Intelligence layer is running"}
