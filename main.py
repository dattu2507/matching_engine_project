from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import Literal, List, Dict
from app.matching_engine_rest import OrderBook, Order

import uuid
import asyncio
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse ,JSONResponse
from fastapi import Request
import os
import logging



# Mount the static folder


app = FastAPI()
# Setup logger
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
@app.on_event("startup")
async def start_background_broadcast():
    async def send_fake_updates():
        while True:
            await asyncio.sleep(2)  # Every 2 seconds
            await broadcast_message({
                "type": "bbo",
                "bbo": {
                    "best_bid": {"price": 100.5, "qty": 1.0},
                    "best_ask": {"price": 101.0, "qty": 1.2}
                }
            })
    asyncio.create_task(send_fake_updates())

app.mount("/static", StaticFiles(directory="static"), name="static")
# Connected WebSocket clients
connected_clients: List[WebSocket] = []

# Async broadcaster function used in OrderBook
async def broadcast_message(message: Dict):
    for client in connected_clients:
        try:
            await client.send_json(message)
        except Exception:
            pass  # Ignore broken clients

# In-memory books (inject broadcaster into each OrderBook)
books = {
    "BTC-USDT": OrderBook("BTC-USDT", broadcaster=broadcast_message)
}

class OrderRequest(BaseModel):
    symbol: str
    side: Literal["buy", "sell"]
    price: float | None = None
    qty: float
    order_type: Literal["limit", "market", "ioc", "fok"]

@app.get("/")
def home():
    return {"message": "Matching Engine with WebSocket is running"}

@app.get("/ui")
def frontend():
    return FileResponse("static/index.html")

@app.post("/order/submit")
async def submit_order(order_data: OrderRequest):
    try:
        book = books.get(order_data.symbol)
        if not book:
            raise HTTPException(404, detail="Symbol not found")

        if order_data.order_type in ["limit", "fok", "ioc"] and order_data.price is None:
            raise HTTPException(400, detail="Price required for this order type")

        order = Order(
            id=str(uuid.uuid4()),
            symbol=order_data.symbol,
            side=order_data.side,
            price=order_data.price,
            qty=order_data.qty,
            order_type=order_data.order_type
        )

        result = book.add_order(order)

        return {
            "order_id": order.id,
            "status": result["status"],
            "trades": result["trades"],  # ✅ Already dicts, no need to call to_dict
            "message": result.get("reason", "Order processed")
        }

    except Exception as e:
        logger.exception("Error in /order/submit")
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.delete("/order/cancel/{symbol}/{order_id}")
def cancel_order(symbol: str, order_id: str):
    book = books.get(symbol)
    if not book:
        raise HTTPException(404, detail="Symbol not found")
    success = book.cancel_order(order_id)
    return {"message": "Canceled" if success else "Order not found"}

@app.get("/book/bbo/{symbol}")
def get_bbo(symbol: str):
    book = books.get(symbol)
    if not book:
        raise HTTPException(404, detail="Symbol not found")
    return book.get_bbo()

@app.get("/book/depth/{symbol}")
def get_depth(symbol: str):
    book = books.get(symbol)
    if not book:
        raise HTTPException(404, detail="Symbol not found")
    return book.get_depth()

@app.get("/trades/{symbol}")
def get_trades(symbol: str):
    book = books.get(symbol)
    if not book:
        raise HTTPException(404, detail="Symbol not found")
    return book.get_recent_trades()

# WebSocket endpoint
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    connected_clients.append(websocket)
    try:
        while True:
            await websocket.receive_text()  # Keeps connection alive
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
