from enum import Enum
from datetime import datetime, timezone

class Order:
    
    class Side(Enum):
        LONG = 1
        SHORT = 2
    
    class Type(Enum):
        MARKET = 1
        LIMIT = 2

    def __init__(self, qty: float, side: Side = Side.LONG, type: Type = Type.MARKET, limit_price: float = 0) -> None:
        self.id = 0
        self.qty = qty
        self.side = side
        self.type = type
        self.limit_price = limit_price
        self.creationTime = datetime.now(timezone.utc)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, self.__class__):
            return self.id == __o.id
        elif isinstance(__o, int):
            return self.id == __o
        else:
            return False
