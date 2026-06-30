from fastapi import FastAPI

app = FastAPI(title="Psychology Tarot AI System")

@app.get("/")
async def root():
    return {
        "status": "online",
        "message": "Psychology Tarot AI System Core Operating Successfully"
    }