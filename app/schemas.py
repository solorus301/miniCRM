from pydantic import BaseModel
from datetime import datetime, date
from typing import List, Optional

class ClientCreate(BaseModel):
    name: str
    email: str
    phone: Optional[str] = None

class ClientResponse(ClientCreate):
    id: int
    status: str
    created_at: datetime

class OrderCreate(BaseModel):
    client_id: int
    amount: float

class OrderResponse(OrderCreate):
    id: int
    status: str
    order_date: date

class InteractionCreate(BaseModel):
    client_id: int
    type: str 
    notes: str

class ClientDetailResponse(ClientResponse):
    orders: List[OrderResponse] = []
    total_spent: float = 0
    last_interaction: Optional[date] = None



