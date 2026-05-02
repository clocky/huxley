"""Read and parse information from the Huxley API for National Rail services."""
import json
import os
from datetime import datetime, time
from typing import Any

import requests
from dateutil import parser, tz
from dotenv import load_dotenv
from dataclasses import dataclass

from .codes import OPERATOR_CODES

load_dotenv()


@dataclass
class Toilet:
    """A class to represent a toilet on a train coach."""

    status: int
    value: str

    def __init__(self, toilet: dict[str, Any]) -> None:
        """Initialise a toilet object."""
        self.status = toilet["status"]
        self.value = toilet["value"]


@dataclass
class Coach:
    """A class to represent a train coach."""

    number: str
    coach_class: str
    toilet: Toilet | None
    loading: int = 0
    loading_specified: bool = False

    def __init__(self, coach: dict[str, Any]) -> None:
        """Initialise a Coach object."""
        self.coach_class = coach["coachClass"]
        self.loading = coach["loading"]
        self.loading_specified = coach["loadingSpecified"]
        self.number = coach["number"]
        self.toilet = (
            Toilet(coach["toilet"]) if coach.get("toilet") is not None else None
        )


@dataclass
class Formation:
    """A class to represent a train formation."""

    avg_loading: int
    avg_loading_specified: bool
    coaches: list[Coach] | None = None

    def __init__(self, formation: dict[str, Any]) -> None:
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
    via: str | None
    future_change_to: str | None
    assoc_is_cancelled: bool

    def __init__(self, destination: dict[str, Any]) -> None:
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
    destination: list[Destination]
    origin: list[Destination]
    detach_front: bool
    operator: str
    operator_code: str
    service_id_guid: str
    service_type: int
    is_early: bool = False
    is_delayed: bool = False
    cancel_reason: str | None = None
    delay_reason: str | None = None
    formation: Formation | None = None
    eta: time | str | None = None
    sta: time | None = None
    etd: time | str | None = None
    std: time | None = None
    platform: str | None = None

    def __init__(self, service: dict[str, Any]) -> None:
        """Initialise a Service object."""
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
        if self.operator_code in OPERATOR_CODES:
            return OPERATOR_CODES[self.operator_code]
        return f"[{self.operator_code}] {self.operator}"


@dataclass
class Station:
    """Interface to the Huxley API."""

    BASE_URL: str
    board: str | None = None

    def __init__(self, crs: str) -> None:
        """Initialise call to the API with a CRS (station code)."""
        self.BASE_URL = "http://huxley2.azurewebsites.net"
        self.crs: str = crs
        self.access_token: str | None = os.getenv("DARWIN_API_KEY")
        self.response: dict[str, Any] = {}
        self.url: str = ""

    def get_data(
        self, endpoint: str, expand: bool = False, rows: int = 10, local: bool = False
    ) -> bool:
        """Use Requests to retrieve JSON data from the Huxley API."""
        if not local:
            payload: dict[str, Any] = {"accessToken": self.access_token, "expand": expand}
            url: str = f"{self.BASE_URL}/{endpoint}/{self.crs}/{rows}"
            r = requests.get(url, params=payload)
            self.url = r.url
            if r.status_code == 200:
                self.response = r.json()
                return True
            else:
                return False
        else:
            self.response = {}
            try:
                with open(f"./data/{self.crs}.json") as f:
                    self.response = json.load(f)
                return True
            except FileNotFoundError:
                return False

    def get_departures(self, expand: bool = False, rows: int = 8, local: bool = False) -> None:
        """Request a list of departures for a given railway station."""
        self.board = "departures"
        self.get_data("departures", expand=expand, rows=rows, local=local)

    def get_arrivals(self, expand: bool = False, rows: int = 8, local: bool = False) -> None:
        """Request a list of arrivals for a given railway station."""
        self.board = "arrivals"
        self.get_data("arrivals", expand=expand, rows=rows, local=local)

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
    def train_services(self) -> list[Service]:
        """Return a list of train services for a given station."""
        if self.response.get("trainServices") is not None:
            return [Service(s) for s in self.response["trainServices"]]
        return []

    @property
    def bus_services(self) -> list[Service]:
        """Return a list of replacement bus services for a given station."""
        if self.response.get("busServices") is not None:
            return [Service(s) for s in self.response["busServices"]]
        return []

    @property
    def ferry_services(self) -> list[Service]:
        """Return a list of ferry services for a given station."""
        if self.response.get("ferryServices") is not None:
            return [Service(s) for s in self.response["ferryServices"]]
        return []

    @property
    def nrcc_messages(self) -> list[dict[str, Any]]:
        """Retrieve any National Rail Communication Center message for the station."""
        if self.response.get("nrccMessages") is not None:
            result: list[dict[str, Any]] = self.response["nrccMessages"]
            return result
        return []

    @property
    def location_name(self) -> str:
        """Return the location name for the station."""
        if self.response.get("locationName") is not None:
            name: str = self.response["locationName"]
            return name
        return f"Unknown location: '{self.crs}'"

    @property
    def are_services_available(self) -> bool:
        """Return a boolean response indicating whether services are available."""
        if self.response.get("areServicesAvailable") is not None:
            available: bool = self.response["areServicesAvailable"]
            return available
        return False
