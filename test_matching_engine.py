import pytest
from app.matching_engine_rest import OrderBook, Order
import uuid

@pytest.fixture
def order_book():
    return OrderBook("BTC-USDT")

def create_order(symbol, side, qty, price, order_type="limit"):
    return Order(
        id=str(uuid.uuid4()),
        symbol=symbol,
        side=side,
        qty=qty,
        price=price,
        order_type=order_type
    )

def test_cancel_order(order_book):
    order = create_order("BTC-USDT", "buy", 1.0, 100)
    order_book.add_order(order)

    canceled = order_book.cancel_order(order.id)
    assert canceled
    assert order.id not in order_book.orders

def test_get_bbo_and_depth(order_book):
    order_book.add_order(create_order("BTC-USDT", "buy", 2.0, 100))
    order_book.add_order(create_order("BTC-USDT", "sell", 2.0, 105))

    bbo = order_book.get_bbo()
    assert bbo["bids"][0]["price"] == 100
    assert bbo["asks"][0]["price"] == 105

    depth = order_book.get_depth()
    assert depth["bids"][0][0] == 100
    assert depth["asks"][0][0] == 105

def test_market_order_matching():
    book = OrderBook("BTC-USDT")

    # Add some resting limit sell orders (liquidity)
    book.add_order(Order(id="s1", symbol="BTC-USDT", side="sell", price=100, qty=2, order_type="limit"))
    book.add_order(Order(id="s2", symbol="BTC-USDT", side="sell", price=101, qty=3, order_type="limit"))

    # Submit a market buy order for qty=4
    result = book.add_order(Order(id="b1", symbol="BTC-USDT", side="buy", price=0, qty=4, order_type="market"))

    assert result["status"] == "filled"
    assert len(result["trades"]) == 2  # Filled across two price levels

    assert result["trades"][0].price == 100
    assert result["trades"][0].qty == 2
    assert result["trades"][1].price == 101
    assert result["trades"][1].qty == 2

    # Check remaining depth
    depth = book.get_depth()
    assert float(depth["asks"][0][0]) == 101
    assert float(depth["asks"][0][1]) == 1  # 3 - 2 = 1 left at 101

def test_limit_order_matching():
    book = OrderBook("BTC-USDT")

    # Submit a limit buy order that rests on the book
    result = book.add_order(Order(id="b1", symbol="BTC-USDT", side="buy", price=99, qty=5, order_type="limit"))

    assert result["status"] == "resting"
    assert result["trades"] == []
    assert book.get_bbo()["bids"][0] == {"price": 99, "qty": 5}

def test_ioc_order():
    book = OrderBook("BTC-USDT")

    # Add a resting limit sell order
    book.add_order(Order(id="s1", symbol="BTC-USDT", side="sell", price=100, qty=3, order_type="limit"))

    # Submit IOC buy order
    result = book.add_order(Order(id="b1", symbol="BTC-USDT", side="buy", price=101, qty=5, order_type="ioc"))

    assert result["status"] == "partial"
    assert len(result["trades"]) == 1
    assert result["trades"][0].price == 100
    assert result["trades"][0].qty == 3

    # IOC order should not leave anything resting
    assert book.get_bbo()["bids"] == []

def test_fok_order():
    book = OrderBook("BTC-USDT")

    # Add a small resting sell order
    book.add_order(Order(id="s1", symbol="BTC-USDT", side="sell", price=100, qty=3, order_type="limit"))

    # FOK buy order with quantity > what's available
    result = book.add_order(Order(id="b1", symbol="BTC-USDT", side="buy", price=101, qty=5, order_type="fok"))

    assert result["status"] == "rejected"
    assert result["trades"] == []

    bbo = book.get_bbo()
    assert "asks" in bbo
    assert len(bbo["asks"]) > 0
    assert bbo["asks"][0] == {"price": 100, "qty": 3}

