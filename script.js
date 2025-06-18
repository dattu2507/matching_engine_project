const ws = new WebSocket("ws://localhost:8000/ws");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "bbo") {
    document.getElementById("bbo").textContent = JSON.stringify(data.bbo, null, 2);
  }

  if (data.type === "trade") {
    const el = document.createElement("div");
    el.innerHTML = `<strong>${data.side}</strong> ${data.qty} @ ${data.price}`;
    document.getElementById("trades").prepend(el);
  }
};

document.getElementById("submitForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const side = document.getElementById("side").value;
  const type = document.getElementById("type").value;
  const price = document.getElementById("price").value;
  const qty = document.getElementById("qty").value;

  const order = {
    symbol: "BTC-USDT",
    side,
    qty: parseFloat(qty),
    order_type: type,
    price: price ? parseFloat(price) : null
  };

  const res = await fetch("/order/submit", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(order)
  });

  const result = await res.json();
  document.getElementById("order-response").textContent = JSON.stringify(result, null, 2);
});
document.querySelector("form").addEventListener("submit", async (e) => {
  e.preventDefault();

  const side = document.getElementById("side").value;
  const type = document.getElementById("type").value;
  const price = document.getElementById("price").value;
  const quantity = document.getElementById("qty").value;

const order = {
  symbol: "BTC-USDT",
  side: side.toLowerCase(),
  order_type: type.toLowerCase(),
  price: price ? parseFloat(price) : null,
  qty: parseFloat(quantity),  // ✅ Changed from 'quantity' to 'qty'
};


  const response = await fetch("/order/submit", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(order),
  });

  const result = await response.json();
  console.log(result);
});
document.getElementById("cancelForm").addEventListener("submit", async (e) => {
  e.preventDefault();

  const symbol = document.getElementById("cancel-symbol").value;
  const orderId = document.getElementById("cancel-order-id").value;

  try {
    const res = await fetch(`/order/cancel/${symbol}/${orderId}`, {
      method: "DELETE",
    });

    const result = await res.json();
    document.getElementById("cancel-response").textContent = JSON.stringify(result, null, 2);
  } catch (err) {
    document.getElementById("cancel-response").textContent = "Error cancelling order.";
    console.error(err);
  }
});
const container = document.getElementById("trades");
container.innerHTML = "";

data.forEach(trade => {
    const line = document.createElement("div");
    line.innerHTML = `<strong>${trade.aggressor_side}</strong> ${trade.qty} @ ${trade.price}`;
    container.appendChild(line);
});
