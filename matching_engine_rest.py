from dataclasses import dataclass, field
from typing import Optional, Literal, Deque, Callable
from collections import deque
import time
import uuid
from sortedcontainers import SortedDict
from datetime import datetime, UTC
import asyncio


Side = Literal["buy", "sell"]
OrderType = Literal["market", "limit", "ioc", "fok"]

def ns_now(): return time.time_ns()


@dataclass(slots=True)
class Order:
    id: str
    symbol: str
    side: Side
    price: Optional[float] = None
    qty: float = 0
    order_type: OrderType = "limit"
    ts: int = field(default_factory=ns_now)
    remaining: float = field(init=False)

    def __post_init__(self):
        self.remaining = self.qty


@dataclass
class Trade:
    trade_id: str
    symbol: str
    price: float
    qty: float
    aggressor_side: Side
    maker_order_id: str
    taker_order_id: str
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))


class OrderBook:
    def __init__(self, symbol: str, broadcaster: Optional[Callable] = None):
        self.symbol = symbol
        self.bids = SortedDict(lambda x: -x)
        self.asks = SortedDict()
        self.orders = {}
        self.trade_log = []
        self.broadcaster = broadcaster  # async callback for WebSocket

    def _add_to_book(self, book: SortedDict, order: Order):
        if order.price not in book:
            book[order.price] = deque()
        book[order.price].append(order)
        self.orders[order.id] = order

    def _match(self, order: Order):
        trades = []
        book = self.asks if order.side == "buy" else self.bids
        is_market = order.order_type == "market"

        while order.remaining > 0 and book:
            best_price = next(iter(book))
            if not is_market:
                if (order.side == "buy" and order.price < best_price) or \
                   (order.side == "sell" and order.price > best_price):
                    break

            level = book[best_price]
            while level and order.remaining > 0:
                resting_order = level[0]
                match_qty = min(order.remaining, resting_order.remaining)
                match_price = resting_order.price

                trade = Trade(
                    trade_id=str(uuid.uuid4()),
                    symbol=self.symbol,
                    price=match_price,
                    qty=match_qty,
                    aggressor_side=order.side,
                    maker_order_id=resting_order.id,
                    taker_order_id=order.id
                )

                trades.append(trade)
                self.trade_log.append(trade)

                # 🔄 Broadcast trade update
                if self.broadcaster:
                    asyncio.create_task(self.broadcaster({
                        "type": "trade",
                        "symbol": trade.symbol,
                        "price": trade.price,
                        "qty": trade.qty,
                        "side": trade.aggressor_side,
                        "maker_order_id": trade.maker_order_id,
                        "taker_order_id": trade.taker_order_id,
                        "timestamp": trade.timestamp.isoformat()
                    }))

                order.remaining -= match_qty
                resting_order.remaining -= match_qty

                if resting_order.remaining == 0:
                    level.popleft()
                    del self.orders[resting_order.id]
                if not level:
                    del book[best_price]

        return trades

    def add_order(self, order: Order):
        if order.order_type == "fok":
            total_qty = 0
            book = self.asks if order.side == "buy" else self.bids

            for price in sorted(book.keys()):
                if not book[price]:
                    continue
                if (order.side == "buy" and order.price < price) or \
                   (order.side == "sell" and order.price > price):
                    break
                for resting in book[price]:
                    total_qty += resting.remaining
                    if total_qty >= order.qty:
                        break
                if total_qty >= order.qty:
                    break

            if total_qty < order.qty:
                return {"status": "rejected", "trades": []}

        trades = self._match(order)

        if order.remaining == 0:
            status = "filled"
        elif order.order_type == "ioc":
            status = "partial" if trades else "cancelled"
        elif order.order_type == "fok":
            status = "filled"
        elif order.order_type == "market":
            status = "partial" if trades else "unfilled"
        else:
            status = "resting"
            if order.remaining > 0 and order.order_type == "limit":
                price_level = self.bids if order.side == "buy" else self.asks
                if order.price not in price_level:
                    price_level[order.price] = deque()
                price_level[order.price].append(order)
                self.orders[order.id] = order

        # 🔄 Broadcast BBO after order matching
        if self.broadcaster:
            asyncio.create_task(self.broadcaster({
                "type": "bbo",
                "symbol": self.symbol,
                "bbo": self.get_bbo()
            }))

        return {"status": status, "trades": trades}

    def cancel_order(self, order_id: str):
        order = self.orders.get(order_id)
        if not order:
            return False
        book = self.bids if order.side == "buy" else self.asks
        book[order.price] = deque(o for o in book[order.price] if o.id != order_id)
        if not book[order.price]:
            del book[order.price]
        del self.orders[order_id]
        return True

    def _qty_at_price(self, orders_at_level):
        return sum(order.remaining for order in orders_at_level)

    def get_bbo(self):
        top_bid = self.bids.peekitem(-1)[0] if self.bids else None
        top_ask = self.asks.peekitem(0)[0] if self.asks else None

        return {
            "bids": [{"price": top_bid, "qty": self._qty_at_price(self.bids[top_bid])}] if top_bid else [],
            "asks": [{"price": top_ask, "qty": self._qty_at_price(self.asks[top_ask])}] if top_ask else []
        }

    def get_depth(self, levels: int = 5):
        return {
            "bids": [[p, sum(o.remaining for o in q)] for p, q in list(self.bids.items())[:levels]],
            "asks": [[p, sum(o.remaining for o in q)] for p, q in list(self.asks.items())[:levels]]
        }

    def get_recent_trades(self, limit=50):
        return [t.__dict__ for t in self.trade_log[-limit:]]
