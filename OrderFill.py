from datetime import datetime, timezone

from Order import Order

class OrderFill:

    def __init__(self, qty, price, fee: float, timestamp: datetime) -> None:
        self.qty = qty
        self.price = price
        self.fee = fee
        self.timestamp = timestamp
