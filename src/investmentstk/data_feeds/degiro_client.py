from typing import Optional

import pandas as pd
from degiro_connector.quotecast.api import API as QuotecastAPI
from degiro_connector.quotecast.models.quotecast_pb2 import Chart
from degiro_connector.quotecast.actions.action_get_chart import ChartHelper

from investmentstk.data_feeds.data_feed import DataFeed, TimeResolution
from investmentstk.models.bar import Bar
from investmentstk.models.barset import BarSet
from investmentstk.models.price import Price
from investmentstk.persistence.requests_cache import requests_cache_configured

TIME_RESOLUTION_TO_DEGIRO_API_RESOLUTION_MAP = {
    TimeResolution.day: Chart.Interval.P1D,
    TimeResolution.week: Chart.Interval.P1W,
    TimeResolution.month: Chart.Interval.P1M,
}

TIME_RESOLUTION_TO_DEGIRO_API_TIME_RANGE_MAP = {
    TimeResolution.day: Chart.Interval.P1Y,
    TimeResolution.week:  Chart.Interval.P1Y,
    TimeResolution.month:  Chart.Interval.P10Y,
}

user_token = None


class DegiroClient(DataFeed):
    """
    THIS IS A DRAFT
    A client to retrieve data from Degiro
    """

    
    def __init__(self):
        self.quotecast_api = QuotecastAPI(user_token=user_token)
        self.last_price = None

    @requests_cache_configured()
    def retrieve_bars(
        self,
        source_id: str,
        *,
        resolution: TimeResolution = TimeResolution.day,
        instrument_type: Optional[str] = "stock",
    ) -> BarSet:
        """
        :param source_id: the internal ID used in Avanza
        :param instrument_type:
        :return: a BarSet
        """

        quotecast_api = self.quotecast_api

        # PREPARE REQUEST
        request = Chart.Request()
        request.culture = "fr-FR"
        request.period = TIME_RESOLUTION_TO_DEGIRO_API_RESOLUTION_MAP[resolution]
        request.requestid = "1"
        request.resolution = TIME_RESOLUTION_TO_DEGIRO_API_TIME_RANGE_MAP[resolution]
        request.series.append("issueid:"+source_id)
        request.tz = "Europe/Paris"

        # FETCH DATA
        chart = quotecast_api.get_chart(request=request, raw=False)

        # FORMAT DATA
        ChartHelper.format_chart(chart=chart, copy=False)
        chart_df = ChartHelper.serie_to_df(serie=chart.series[0])
        chart_df["timestamp"] = pd.to_datetime(chart_df["timestamp"], unit="s")

        bars: BarSet = set()

        for _index, row in chart_df.iterrows():
            bars.add(Bar.from_degiro(row))

        return bars

    @requests_cache_configured()
    def retrieve_asset_name(self, source_id: str, instrument_type: Optional[str] = "stock") -> str:
        """
        Retrieves the name of an asset

        :param source_id: the internal ID used in Avanza
        :param instrument_type:
        :return: the asset name (ticker)
        """

        quotecast_api = self.quotecast_api

        # SETUP REQUEST
        request = Chart.Request()
        request.culture = "fr-FR"
        request.period = Chart.Interval.P1D
        request.requestid = "1"
        request.series.append("issueid:"+source_id)
        request.tz = "Europe/Paris"

        # FETCH DATA
        chart = quotecast_api.get_chart(request=request, raw=True)
        name = chart["series"][0]["data"][0]["name"]
        symbol = chart["series"][0]["data"][0]["alfa"]

        return symbol  # Name or symbol ?

    @requests_cache_configured(hours=0.5)
    def retrieve_price(self, source_id: str, instrument_type: Optional[str] = "stock") -> Price:
        quotecast_api = self.quotecast_api

        # SETUP REQUEST
        request = Chart.Request()
        request.culture = "fr-FR"
        request.period = Chart.Interval.P1D
        request.requestid = "1"
        request.series.append("issueid:"+source_id)
        request.tz = "Europe/Paris"

        # FETCH DATA
        chart = quotecast_api.get_chart(request=request, raw=True)

        data = {
            "lastPrice": chart["series"][0]["data"][0]["lastPrice"],
            "change": self.last_price - chart["series"][0]["data"][0]["lastPrice"],
            "changePercent": self.last_price/chart["series"][0]["data"][0]["lastPrice"],  # Can't be x/0 ?
        } 

        # `changePercent` compare to which lastPrice : day, minute, last price fetched ?
        return Price(last=data["lastPrice"], change=data["change"], change_pct=data["changePercent"])
