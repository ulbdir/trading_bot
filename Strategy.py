from abc import ABC, abstractmethod

class Strategy(ABC):
    
    @abstractmethod
    def __init__(self) -> None:
        pass

    @abstractmethod
    def initialise(self) -> None:
        pass
