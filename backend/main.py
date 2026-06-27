from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
from typing import List, Optional
import uuid

# --- 1. DATABASE SETUP (SQLAlchemy + SQLite) ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./techpro_crm.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- 2. DATABASE MODELS (Tables) ---
class ProductDB(Base):
    __tablename__ = "products"
    id = Column(String, primary_key=True, index=True)
    sku = Column(String, unique=True, index=True)
    name = Column(String)
    price = Column(Float)
    stock = Column(Integer)

class TicketDB(Base):
    __tablename__ = "tickets"
    id = Column(String, primary_key=True, index=True)
    customer_name = Column(String)
    device = Column(String)
    issue = Column(String)
    status = Column(String, default="Queue") # Queue, In Progress, Done
    price = Column(Float, default=0.0)

Base.metadata.create_all(bind=engine)

# --- 3. PYDANTIC SCHEMAS (Data Validation) ---
class Product(BaseModel):
    sku: str
    name: str
    price: float
    stock: int

class ProductResponse(Product):
    id: str
    class Config: from_attributes = True

class Ticket(BaseModel):
    customer_name: str
    device: str
    issue: str
    status: str
    price: float

class TicketResponse(Ticket):
    id: str
    class Config: from_attributes = True

# --- 4. FASTAPI APPLICATION ---
app = FastAPI(title="TechPro CRM API")

# Allow your frontend to talk to this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace "*" with your frontend's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

# --- 5. API ENDPOINTS ---

# Inventory Endpoints
@app.get("/api/products", response_model=List[ProductResponse])
def get_products(db: Session = Depends(get_db)):
    return db.query(ProductDB).all()

@app.post("/api/products", response_model=ProductResponse)
def create_product(product: Product, db: Session = Depends(get_db)):
    db_product = ProductDB(**product.dict(), id=str(uuid.uuid4()))
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

# Kanban Repair Ticket Endpoints
@app.get("/api/tickets", response_model=List[TicketResponse])
def get_tickets(db: Session = Depends(get_db)):
    return db.query(TicketDB).all()

@app.post("/api/tickets", response_model=TicketResponse)
def create_ticket(ticket: Ticket, db: Session = Depends(get_db)):
    db_ticket = TicketDB(**ticket.dict(), id=str(uuid.uuid4()))
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket

@app.put("/api/tickets/{ticket_id}/status")
def update_ticket_status(ticket_id: str, status: str, db: Session = Depends(get_db)):
    db_ticket = db.query(TicketDB).filter(TicketDB.id == ticket_id).first()
    if not db_ticket: raise HTTPException(status_code=404, detail="Ticket not found")
    db_ticket.status = status
    db.commit()
    return {"message": "Status updated successfully"}
