import string


class Market:
    def __init__(self, base: string, quote: string = None) -> None:
        self.base_currency = base

        if quote is None:
            self.is_spot = False
        else:
            self.quote_currency = quote
            self.is_spot = True
    
    def get_market(self) -> string:
        if self.is_spot:
            return self.base_currency + "/" + self.quote_currency
        else:
            return self.base_currency
    
    def __str__(self) -> str:
        return self.get_market()