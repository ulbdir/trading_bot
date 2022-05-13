from enum import Enum
from datetime import datetime, timezone
import math

from Market import Market

class Order:
    
    class Side(Enum):
        BUY = 1
        SELL = 2
    
    class Type(Enum):
        MARKET = 1
        LIMIT = 2

    def __init__(self, market:Market, qty: float, side: Side = Side.BUY, type: Type = Type.MARKET, limit_price: float = 0) -> None:
        self.id = "0"
        self.market = market
        self.qty = qty
        self.side = side
        self.type = type
        self.limit_price = limit_price
        self.creationTime = datetime.now(timezone.utc)
        self.fills = []

    def qty_filled(self) -> float:
        result: float = 0
        for fill in self.fills:
            result += fill.qty
        return result
    
    def is_filled(self) -> bool:
        return math.isclose(self.qty, self.qty_filled())

    def __str__(self) -> str:
        return "[id: " + str(self.id) + ", market: " + str(self.market) + ", qty: " + str(self.qty) + ", side: " + str(self.side) + ", type: " + str(self.type) + ", limit: " + str(self.limit_price) + "]"

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, self.__class__):
            return self.id == __o.id
        elif isinstance(__o, int):
            return self.id == __o
        else:
            return False
