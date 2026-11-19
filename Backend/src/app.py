from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
)

@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/api/wishlist")
async def add_to_wishlist(request: Request):
    data = await request.json()
    print("WISHLIST ITEM:", data)
    return {"received": True}