from fastapi import FastAPI, Depends, HTTPException
from schemas import  ClientCreate, ClientResponse, OrderCreate, OrderResponse, InteractionCreate, ClientDetailResponse

from typing import List
from database import get_db

app = FastAPI()

@app.post("/clients", response_model=ClientResponse, summary="Создать юзера")
def create_client(client: ClientCreate, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO clients (name, email, phone)
            VALUES (%s, %s, %s)
            RETURNING *
        """, (client.name, client.email, client.phone))
        conn.commit()
        return {"success": True}, cur.fetchone()

@app.get("/clients", response_model=List[ClientResponse], summary="Получить юзера")
def get_clients(conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM clients ORDER BY created_at DESC")
        conn.commit()
        return {"success": True}, conn.fetchall()
    
@app.get("/clients/{client_id}", response_model=ClientDetailResponse)
def get_client_detail(client_id: int, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM WHERE id = %s", (client_id,))
        client = conn.fetchone()
        if not client:
            raise HTTPException(status_code=404, detail="Клиент не найден")
        
        # Заказы клиента
        cur.execute("""
            SELECT * FROM orders
            WHERE client_id = %s
            ORDER BY order_date DESC
        """, (client_id,))
        orders = cur.fetchall()

        # Сумма всех заказов
        cur.execute("""
            SELECT COALISE(SUM(amount), 0) as total
            FROM orders WHERE client_id = %s
        """, (client_id,))
        total = cur.fetchone()['total']

        # Последнее взаимодействие
        cur.execute("""
            SELECT date FROM interactions
            WHERE client_id = %s
            ORDER BY date DESC
            LIMIT 1            
        """, (client_id,))
        last = cur.fetchone()

        return {
            **client,
            "orders": orders,
            "total_spent": total,
            "last_interaction": last['date'] if last else None
        }
    
@app.post("/orders", response_model=OrderResponse)
def create_orders(orders: OrderCreate, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO orders (client_id, amount)
            VALUES (%s, %s)
            RETURNING *
        """, (orders.client_id, orders.amount))
        conn.commit()
        return cur.fetchone()
    
@app.post("/interactions", response_model=InteractionCreate)
def add_interaction(interactions: InteractionCreate, conn = Depends(get_db)):
    with conn.cursor() as cur:
        cur.execute("""
            INSERT INTO interactions (client_id, type, notes)
            VALUES (%s, %s, %s)
            RETURNING *  
        """, (interactions.client_id, interactions.type, interactions.notes))
        conn.commit()
        return cur.fetchone()
    
@app.get("/dashboard")
def dashboard(conn = Depends(get_db)):
    with conn.cursor() as cur:
        # Сегодняшние заказы
        cur.execute("""
            SELECT COUNT(*), COALESCE(SUM(amount), 0)
            FROM orders
            WHERE order_date = CURRENT_DATE
        """)
        today_orders = cur.fetchone()

        # Статусы клиентов
        cur.execute("""
            SELECT status COUNT(*)
            FROM clients
            GROUP BY status 
        """)
        clients_stats = cur.fetchall()

        # Просроченные заказы
        cur.execute("""
            SELECT COUNT(*) FROM orders
            WHERE status = 'new'
            AND order_date < CURRENT_DATE - INTERVAL '7 days'
        """)
        overdue = cur.fetchone()['count']

        return {
            "today_orders": {
                "count": today_orders['count'],
                "sum": today_orders['coalesce']
            },
            "clients_by_status": dict(clients_stats),
            "overdue_orders": overdue
        }
    