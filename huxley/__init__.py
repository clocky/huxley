"""Read and parse information from the Huxley API for National Rail services."""
# type: ignore [call-arg]
import json
import os
from datetime import datetime, time
from typing import List, Optional, Union

import requests
from dateutil import parser, tz
from dotenv import load_dotenv
from pydantic.dataclasses import dataclass

from .codes import OPERATOR_CODES


@dataclass
class Toilet:
    """A class to represent a toilet on a train coach."""

    status: int
    value: str

    def __init__(self, toilet: dict):
        """Initialise a toilet object."""
        self.status = toilet["status"]
        self.value = toilet["value"]


@dataclass
class Coach:
    """A class to represent a train coach."""

    number: str
    coach_class: str
    toilet: Optional[Toilet]
    loading: int = 0
    loading_specified: bool = False

    def __init__(self, coach: dict):
        """Initialise a Coach object."""
        self.coach_class = coach["coachClass"]
        self.loading = coach["loading"]
        self.loading_specified = coach["loadingSpecified"]
        self.number = coach["number"]
        self.toilet = (
            Toilet(coach["toilet"]) if coach.get("toilet") is not None else None
        )


@dataclass
class Point:
    """A class to represent a calling point on a service."""

    location_name: str
    crs: str
    st: time
    et: time | str
    at: time
    is_cancelled: bool
    length: int
    detach_front: bool
    formation: str
    adhoc_alerts: str


@dataclass
class Formation:
    """A class to represent a train formation."""

    avg_loading: int
    avg_loading_specified: bool
    coaches: Optional[List[Coach]] = None

    def __init__(self, formation: dict):
        """Define a train formation, including the coaches."""
        self.avg_loading = formation["avgLoading"]
        self.avg_loading_specified = formation["avgLoadingSpecified"]
        if formation.get("coaches") is not None:
            self.coaches = [Coach(d) for d in formation["coaches"]]


@dataclass
class Destination:
    """Define a point on a route, such as a station or a platform."""

    location_name: str
    crs: str
    via: Optional[str]
    future_change_to: Optional[str]
    assoc_is_cancelled: bool

    def __init__(self, destination: dict):
        """Initialise a point."""
        self.location_name = destination["locationName"]
        self.crs = destination["crs"]
        self.via = destination["via"]
        self.future_change_to = destination["futureChangeTo"]
        self.assoc_is_cancelled = destination["assocIsCancelled"]


@dataclass
class Service:
    """Define a service, such as a train, bus or ferry."""

    is_circular_route: bool
    is_cancelled: bool
    is_reverse_formation: bool
    destination: List[Destination]
    detach_front: bool
    operator: str
    operator_code: str
    service_id_guid: str
    service_type: int
    is_early: bool = False
    is_delayed: bool = False
    cancel_reason: Optional[str] = None
    delay_reason: Optional[str] = None
    formation: Optional[Formation] = None
    eta: Optional[Union[time, str]] = None
    sta: Optional[time] = None
    etd: Optional[Union[time, str]] = None
    std: Optional[time] = None
    platform: Optional[str] = None

    def __init__(self, service: dict):
        """Intialise a Service object."""
        self.destination = [Destination(d) for d in service["destination"]]
        self.origin = [Destination(o) for o in service["origin"]]

        if service.get("formation") is not None:
            self.formation = Formation(service["formation"])

        if service.get("eta") not in [None, "On time", "Delayed", "Cancelled"]:
            self.eta = datetime.strptime(service["eta"], "%H:%M").time()
        else:
            self.eta = service["eta"]

        if service.get("sta") is not None:
            self.sta = datetime.strptime(service["sta"], "%H:%M").time()

        if service.get("std") is not None:
            self.std = datetime.strptime(service["std"], "%H:%M").time()

        if service.get("etd") not in [None, "On time", "Delayed", "Cancelled"]:
            self.etd = datetime.strptime(service["etd"], "%H:%M").time()
        else:
            self.etd = service["etd"]

        self.is_circular_route = service["isCircularRoute"]
        self.is_cancelled = service["isCancelled"]
        self.is_reverse_formation = service["isReverseFormation"]
        self.cancel_reason = service["cancelReason"]
        self.delay_reason = service["delayReason"]
        self.detach_front = service["detachFront"]
        self.platform = service["platform"]
        self.operator = service["operator"]
        self.operator_code = service["operatorCode"]
        self.service_id_guid = service["serviceIdGuid"]
        self.service_type = service["serviceType"]

    @property
    def operator_short_name(self) -> str:
        """Return the friendly name of the operator."""
        short_name: str = ""

        if self.operator_code in OPERATOR_CODES:
            short_name = OPERATOR_CODES[self.operator_code]
        else:
            short_name = f"[{self.operator_code}] {self.operator}"
        return short_name


@dataclass
class Station:
    """Interface to the Huxley API."""

    BASE_URL: str
    board: str = None

    def __init__(self, crs):
        """Intiialise call to the API with a CRS (station code)."""
        load_dotenv()
        self.BASE_URL = "http://huxley2.azurewebsites.net"
        self.crs: str = crs
        self.access_token = os.getenv("DARWIN_API_KEY")
        self.response: dict = {}
        self.url: str = ""

    def get_data(
        self, endpoint: str, expand: bool = False, rows: int = 10, local: bool = False
    ) -> bool:
        """Use Requests to retrieve JSON data from the Huxley API."""
        if not local:
            self.payload: dict = {"accessToken": self.access_token, "expand": expand}
            self.endpoint: str = f"{self.BASE_URL}/{endpoint}/{self.crs}/{rows}"
            r = requests.get(self.endpoint, params=self.payload)
            self.url = r.url
            if r.status_code == 200:
                self.response = r.json()
                return True
            else:
                return False
        else:
            self.response = {}
            try:
                self.response = json.load(open(f"./data/{self.crs}.json"))
                return True
            except FileNotFoundError:
                return False

    def get_departures(self, expand: bool = False, rows: int = 8, local: bool = False):
        """Request a list of departures for a given railway station."""
        self.board = "departures"
        self.get_data("departures", expand=expand, rows=rows, local=local)

    def get_arrivals(self, expand: bool = False, rows: int = 8, local: bool = False):
        """Request a list of arrivals for a given railway station."""
        self.board = "arrivals"
        self.get_data("arrivals", expand=expand, rows=rows)

    @property
    def generated_at(self) -> datetime:
        """Create a datetime object from the generatedAt timestamp."""
        timezone: str = "UTC"
        locale: str = "Europe/London"
        generated_at: datetime = datetime.now()
        if "generatedAt" in self.response:
            generated_at = (
                parser.parse(self.response["generatedAt"])
                .replace(tzinfo=tz.gettz(timezone))
                .astimezone(tz.gettz(locale))
            )
        return generated_at

    @property
    def train_services(self) -> list:
        """Return a list of train services for a given station."""
        train_services: list = []
        if self.response.get("trainServices") is not None:
            train_services = [Service(s) for s in self.response["trainServices"]]
        return train_services

    @property
    def bus_services(self) -> list:
        """Return a list of replacement bus services for a given station."""
        bus_services: list = []
        if self.response.get("busServices") is not None:
            bus_services = [Service(s) for s in self.response["busServices"]]
        return bus_services

    @property
    def ferry_services(self) -> list:
        """Return a list of ferry services for a given station."""
        ferry_services: list = []
        if self.response.get("ferryServices") is not None:
            ferry_services = [Service(s) for s in self.response["ferryServices"]]
        return ferry_services

    @property
    def nrcc_messages(self) -> dict:
        """Retrieve any National Rail Communication Center message for the station."""
        nrcc_messages: dict = {}
        if self.response.get("nrccMessages") is not None:
            nrcc_messages = self.response["nrccMessages"]
        return nrcc_messages

    @property
    def location_name(self) -> str:
        """Return the location name for the station."""
        location_name: str = ""
        if self.response.get("locationName") is not None:
            location_name = self.response["locationName"]
        else:
            location_name = f"Unknown location: '{self.crs}'"
        return location_name

    @property
    def are_services_available(self) -> bool:
        """Return a boolean response indicating whether services are available."""
        are_services_available: bool = False
        if self.response.get("areServicesAvailable") is not None:
            are_services_available = self.response["areServicesAvailable"]
        return are_services_available
