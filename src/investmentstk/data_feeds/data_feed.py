from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from investmentstk.models.barset import BarSet
from investmentstk.models.price import Price


class TimeResolution(str, Enum):
    day = "day"
    week = "week"
    month = "month"


class DataFeed(ABC):
    """
    Abstract class that every data feed client should implement.

    Individual instances be created by a factory method in `models/source.py`
    """

    @abstractmethod
    def retrieve_bars(
        self, source_id: str, *, resolution: TimeResolution = TimeResolution.day, instrument_type: Optional[str] = None
    ) -> BarSet:
        """
        Retrieves bars. For now, very simple implementation and not flexible at all
        (in terms of time range and periodicity).


        :param source_id: the ID for the asset in the source
        :param resolution: the time resolution (day, week, month)
        :param instrument_type: the type of instrument
        :return: a BarSet
        """

    @abstractmethod
    def retrieve_asset_name(self, source_id: str, instrument_type: Optional[str] = None) -> str:
        """
        Retrieves the asset name.

        :param source_id: the ID for the asset in the source
        :param instrument_type: the type of instrument
        :return: the name of the asset
        """

    @abstractmethod
    def retrieve_price(self, source_id: str, instrument_type: Optional[str] = "stock") -> Price:
        """
        Retrieves the last price (and % variation) of an asset.

        :param source_id: the ID for the asset in the source
        :param instrument_type: the type of instrument
        :return: a Price object
        """
