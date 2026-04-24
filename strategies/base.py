from abc import ABC, abstractmethod

from data.models import TradeSignal
from data.store import DataStore


class BaseStrategy(ABC):
    """
    All strategies implement this interface.
    evaluate() is called on every new candle close.
    """

    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    def evaluate(self, store: DataStore) -> TradeSignal: ...
