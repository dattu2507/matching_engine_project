# ⚡ Cryptocurrency Matching Engine

A high-performance, real-time cryptocurrency matching engine built with Python and FastAPI. This engine supports various order types, real-time WebSocket updates, REST APIs for order submission, and a clean, responsive frontend for user interaction.

---

## 📌 Features

- Support for **limit**, **market**, **IOC**, and **FOK** order types
- Real-time **Best Bid/Offer (BBO)** and **Trade** updates via WebSocket
- REST API for submitting and canceling orders
- Matching logic with price-time priority
- In-memory order book with efficient data structures
- Order validation and error handling
- Order cancellation support
- Trade logging with timestamps
- Simple and intuitive frontend UI

---

## ⚙️ Tech Stack

- **Backend**: Python, FastAPI
- **Frontend**: HTML, CSS, JavaScript (vanilla)
- **Real-time**: WebSockets
- **Testing**: `pytest`
- **Logging**: Python `logging` module

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/crypto-matching-engine.git
cd crypto-matching-engine
2. Install dependencies
pip install -r requirements.txt
3. Run the FastAPI server
uvicorn main:app --reload
4. Access the Frontend
Open your browser and go to:
http://127.0.0.1:8000

🧪 API Endpoints
Submit Order

POST /order/submit
Payload:

json

{
  "symbol": "BTC-USDT",
  "side": "buy",
  "order_type": "limit",
  "price": 30000,
  "qty": 1.5
}
Response:

json

{
  "order_id": "uuid",
  "status": "filled",
  "trades": [...],
  "message": "Order processed"
}
Cancel Order

POST /order/cancel
Payload:

json
Copy
Edit
{
  "symbol": "BTC-USDT",
  "order_id": "uuid"
}
Response:


{
  "status": "cancelled",
  "message": "Order successfully cancelled"
}
🔁 WebSocket Streams
Endpoint
bash
Copy
Edit
/ws/stream
Stream Types
bbo: Best Bid/Offer update

trade: New trade execution
🧩 Order Types
Type	         Description
limit	         Matches or rests at the specified price
market	       Executes against best available prices
ioc	           Immediate or Cancel (partial or full immediately)
fok	           Fill or Kill (full immediately or reject)

🧪 Testing
Run unit tests for core matching logic:


pytest tests/
Example test:


def test_basic_limit_match():
    book = OrderBook("BTC-USDT")
    buy_order = Order(id="1", symbol="BTC-USDT", side="buy", price=30000, qty=1.0, order_type="limit")
    sell_order = Order(id="2", symbol="BTC-USDT", side="sell", price=30000, qty=1.0, order_type="limit")

    book.add_order(sell_order)
    result = book.add_order(buy_order)

    assert result["status"] == "filled"
    assert len(result["trades"]) == 1
📊 Performance Goals
✅ Match and process >1000 orders/second in-memory

✅ Broadcast real-time market data with minimal latency

✅ Maintain state consistency and integrity under load

📁 Project Structure
php

.
├── main.py                # FastAPI application
├── order_book.py          # Core matching logic
├── models.py              # Order and Trade dataclasses
├── static/
│   ├── style.css
│   └── script.js
├── templates/
│   └── index.html
├── tests/
│   └── test_matching.py
└── README.md
✅ Future Improvements
Persistent storage with Redis or PostgreSQL

User authentication and balance checks

Support for multiple trading pairs

Historical trade analytics

UI enhancements and order history tab

🙌 Author
Developed by [Your Name]

Feel free to contribute or suggest improvements.

📄 License
MIT License



---

Let me know if you’d like this in a downloadable `.md` or `.docx` file, or if you want a visual preview or enhancements (like diagrams or badges).








