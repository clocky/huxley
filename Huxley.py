# """Read and parse information from the Huxley API for National Rail services."""
# type: ignore [call-arg]
import os
from dataclasses import dataclass
from datetime import datetime

import requests
from dateutil import parser, tz
from dotenv import load_dotenv


@dataclass
class Toilet:
    """A class to represent a toilet on a train coach."""

    status: int
    value: str

    def __init__(self, toilet: dict):
        self.status = toilet["status"]
        self.value = toilet["value"]


@dataclass
class Coach:
    """A class to represent a train coach."""

    coach_class: str
    loading: int
    loading_specified: bool
    number: str
    toilet: list

    def __init__(self, coach: dict):
        """Initialise a Coach object."""
        self.coach_class = coach["coachClass"]
        self.loading = coach["loading"]
        self.loading_specified = coach["loadingSpecified"]
        self.number = coach["number"]
        self.toilet = Toilet(coach["toilet"]) if coach["toilet"] is not None else None


@dataclass
class Formation:
    """A class to represent a train formation."""

    avg_loading: int
    avg_loading_specified: bool
    coaches: list

    def __init__(self, formation: dict):
        self.avg_loading = formation["avgLoading"]
        self.avg_loading_specified = formation["avgLoadingSpecified"]
        self.coaches = [Coach(d) for d in formation["coaches"]]


@dataclass
class Point:
    """Define a point on a route, such as a station or a platform."""

    location_name: str
    crs: str
    via: str
    future_change_to: str
    assoc_is_cancelled: bool

    def __init__(self, point: dict):
        """Initialise a point."""
        self.location_name = point["locationName"]
        self.crs = point["crs"]
        self.via = point["via"]
        self.future_change_to = point["futureChangeTo"]
        self.assoc_is_cancelled = point["assocIsCancelled"]


@dataclass
class Service:
    """Define a service, such as a train, bus or ferry."""

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
    service_id_guid: str
    service_type: int
    formation: list

    def __init__(self, service: dict):
        """Intialise a Service object."""
        self.destination = [Point(d) for d in service["destination"]]
        self.origin = [Point(o) for o in service["origin"]]
        if service["formation"] is not None:
            self.formation = Formation(service["formation"])
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
        self.service_id_guid = service["serviceIdGuid"]
        self.service_type = service["serviceType"]


class Huxley:
    """Interface to the Huxley API."""

    def __init__(self, crs):
        """Intiialise call to the API with a CRS (station code)."""
        load_dotenv()
        self.BASE_URL: str = "http://huxley2.azurewebsites.net"
        self.crs: str = crs
        self.access_token = os.getenv("DARWIN_API_KEY")
        self.response: dict = {}

    def get_data(self, endpoint: str, expand: bool, rows: int = 10):
        """Use Requests to retrieve JSON data from the Huxley API."""
        payload: dict = {"accessToken": self.access_token, "expand": expand}
        url: str = f"{self.BASE_URL}/{endpoint}/{self.crs}/{rows}"
        r = requests.get(url, params=payload)
        if r.status_code == 200:
            self.response = r.json()
        return True

    def get_departures(self, expand: bool = False, rows: int = 8):
        """Request a list of departures for a given railway station."""
        self.get_data("departures", expand=expand, rows=rows)

    def get_arrivals(self, expand: bool = False, rows: int = 8):
        """Request a list of arrivals for a given railway station."""
        self.get_data("arrivals", expand=expand, rows=rows)

    @property
    def generated_at(
        self, timezone: str = "UTC", locale: str = "Europe/London"
    ) -> datetime:
        """Create a datetime object from the generatedAt timestamp."""
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
        if self.response["trainServices"] != None:
            train_services = [Service(s) for s in self.response["trainServices"]]
        return train_services

    @property
    def bus_services(self) -> list:
        """Return a list of replacement bus services for a given station."""
        bus_services: list = []
        if self.response["busServices"] != None:
            bus_services = [Service(s) for s in self.response["busServices"]]
        return bus_services

    @property
    def ferry_services(self) -> list:
        """Return a list of ferry services for a given station."""
        ferry_services: list = []
        if self.response["ferryServices"] != None:
            ferry_services = [Service(s) for s in self.response["ferryServices"]]
        return ferry_services

    @property
    def nrcc_messages(self) -> dict:
        """Retrieve any National Rail Communication Center message for the station."""
        return self.response["nrccMessages"]

    @property
    def location_name(self) -> str:
        """Return the location name for the station."""
        location_name: str = ""
        if "locationName" in self.response:
            location_name = self.response["locationName"]
        else:
            location_name = f"Unknown location: '{self.crs}'"
        return location_name

    @property
    def are_services_available(self) -> bool:
        """Return a boolean response indicating whether services are available."""
        are_services_available: bool = False
        if "areServicesAvailable" in self.response:
            are_services_available = self.response["areServicesAvailable"]
        return are_services_available
