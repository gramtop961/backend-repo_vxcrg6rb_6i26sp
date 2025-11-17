import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional

from database import create_document, get_documents
from schemas import Product

app = FastAPI(title="NESMERDI API", description="Backend for NESMERDI luxury men's underwear brand website")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"brand": "NESMERDI", "message": "Welcome to the NESMERDI API"}

@app.get("/api/hello")
def hello():
    return {"message": "Hello from the backend API!"}

@app.get("/test")
def test_database():
    """Test endpoint to check if database is available and accessible"""
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }
    
    try:
        from database import db
        
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Configured"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️  Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️  Available but not initialized"
            
    except ImportError:
        response["database"] = "❌ Database module not found (run enable-database first)"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"
    
    import os
    response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
    response["database_name"] = "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set"
    
    return response

# Simple product seeding endpoint (idempotent) to add demo items
class SeedResponse(BaseModel):
    inserted: int

@app.post("/api/seed", response_model=SeedResponse)
async def seed_products():
    """Insert a small curated set of NESMERDI products if the collection is empty"""
    existing = get_documents("product", limit=1)
    if existing:
        return {"inserted": 0}
    demo_products: List[Product] = [
        Product(
            title="SilkTouch Brief",
            description="Ultra-soft premium modal blend with seamless comfort.",
            price=39.0,
            category="brief",
            sizes=["S","M","L","XL"],
            colors=["Onyx Black","Ivory","Deep Navy"],
            featured=True
        ),
        Product(
            title="AeroFlex Trunk",
            description="Breathable micro-mesh with sculpted support.",
            price=42.0,
            category="trunk",
            sizes=["S","M","L","XL"],
            colors=["Carbon","Cobalt"],
            featured=True
        ),
        Product(
            title="Heritage Boxer",
            description="Classic cut with modern tailoring and plush waistband.",
            price=45.0,
            category="boxer",
            sizes=["M","L","XL"],
            colors=["Charcoal","Snow"],
            featured=False
        ),
    ]

    inserted = 0
    for p in demo_products:
        create_document("product", p)
        inserted += 1
    return {"inserted": inserted}

# Public product list endpoint
class ProductOut(BaseModel):
    title: str
    description: Optional[str]
    price: float
    category: str
    sizes: List[str]
    colors: List[str]
    featured: bool

@app.get("/api/products", response_model=List[ProductOut])
async def list_products():
    docs = get_documents("product")
    result: List[ProductOut] = []
    for d in docs:
        result.append(ProductOut(
            title=d.get("title"),
            description=d.get("description"),
            price=float(d.get("price", 0)),
            category=d.get("category", "underwear"),
            sizes=list(d.get("sizes", [])),
            colors=list(d.get("colors", [])),
            featured=bool(d.get("featured", False))
        ))
    return result

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
