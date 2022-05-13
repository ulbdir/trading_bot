import string


class Wallet:

    def __init__(self) -> None:
        self.tokens = {}
    
    def getBalance(self, token: string) -> float:
        result = 0
        if token in self.tokens:
            result = self.tokens[token]
        return result
    
    def setBalance(self, token: string, amount: float) -> None:
        self.tokens[token] = amount