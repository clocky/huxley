import os
from dataclasses import dataclass

import requests
import datetime
from dateutil import parser
from dotenv import load_dotenv


@dataclass
class Point:
    location_name: str
    crs: str
    via: str
    future_change_to: str
    assoc_is_cancelled: bool

    def __init__(self, point: dict):
        self.location_name = point["locationName"]
        self.crs = point["crs"]
        self.via = point["via"]
        self.future_change_to = point["futureChangeTo"]
        self.assoc_is_cancelled = point["assocIsCancelled"]


@dataclass
class Service:
    eta: str
    sta: str
    etd: str
    std: str
    is_circular_route: bool
    is_cancelled: bool
    cancel_reason: str
    delay_reason: str
    destination: list
    platform: int
    operator: str
    operator_code: str

    def __init__(self, service: dict):
        self.destination = [Point(d) for d in service["destination"]]
        self.origin = [Point(d) for d in service["origin"]]
        self.sta = service["sta"]
        self.eta = service["eta"]
        self.std = service["std"]
        self.etd = service["etd"]
        self.is_circular_route = service["isCircularRoute"]
        self.is_cancelled = service["isCancelled"]
        self.cancel_reason = service["cancelReason"]
        self.delay_reason = service["delayReason"]
        self.platform = service["platform"]
        self.operator = service["operator"]
        self.operator_code = service["operatorCode"]


class Huxley:
    def __init__(self, crs):
        load_dotenv()
        self.base_path: str = "http://huxley2.azurewebsites.net"
        self.crs: str = crs
        self.access_token = os.getenv("DARWIN_API_KEY")
        self.response: dict = {}

    def get_data(self, endpoint):
        payload: object = {"accessToken": self.access_token}
        url: str = f"{self.base_path}/{endpoint}/{self.crs}"
        r = requests.get(url, params=payload)
        self.response = r.json()
        return True

    def get_departures(self):
        self.get_data("departures")

    def get_arrivals(self):
        self.get_data("arrivals")

    @property
    def generated_at(self) -> datetime.datetime:
        return parser.parse(self.response["generatedAt"])

    @property
    def train_services(self) -> list:
        train_services = [Service(s) for s in self.response["trainServices"]]
        return train_services

    @property
    def bus_services(self) -> dict:
        return self.response["busServices"]

    @property
    def ferry_services(self) -> dict:
        return self.response["ferryServices"]

    @property
    def nrcc_messages(self) -> dict:
        return self.response["nrccMessages"]

    @property
    def location_name(self) -> str:
        return self.response["locationName"]

    @property
    def are_services_available(self) -> bool:
        return self.response["areServicesAvailable"]
