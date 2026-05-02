#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI tool to show upcoming departures for a given railway station."""
# TODO: Show bus and ferry replacement services (only train_services are rendered)
# TODO: Show currentOrigins/currentDestinations when a service is diverted or short-formed
# TODO: Show adhocAlerts (e.g. "No toilet facilities on this service")
# TODO: Handle filterLocationCancelled for filtered queries (e.g. WAT to WOK)
# TODO: Show service length from top-level field when detailed formation is unavailable
import html
import re
from datetime import time
from typing import Any

import click
from rich import box
from rich.console import Console
from rich.padding import Padding
from rich.table import Table
from rich.theme import Theme

import huxley

BOOTSTRAP = Theme(
    {
        "success": "#198754",
        "warning": "#ffc107",
        "light": "#f8f9fa",
        "info": "#0dcaf0",
        "primary": "#0d6efd",
        "danger": "#dc3545",
        "dark": "#212529",
        "secondary": "#6c757d",
    }
)


def show_board(station: huxley.Station, show_nrcc_messages: bool, show_formation: bool) -> None:
    """Render a Rich table of departures for a railway station."""
    console = Console(theme=BOOTSTRAP)
    direction: str = "Destination" if station.board == "departures" else "Origin"
    title_suffix: str = "Departures" if station.board == "departures" else "Arrivals"
    title: str = f"{station.location_name}: {title_suffix}"

    table = Table(
        style="secondary",
        show_header=True,
        box=box.SIMPLE_HEAD,
        title=title,
        title_style="primary",
        pad_edge=False,
        show_lines=False,
    )
    table.caption_style = "warning"

    table.add_column("Time", width=6)
    table.add_column(direction, style="warning", width=45)
    table.add_column("Plat", justify="right", width=4)
    table.add_column("Expected", justify="right", width=9)
    table.add_column("Operator", justify="right", style="info", width=16)

    if station.train_services:
        for service in station.train_services:
            st: str = ""
            if service.std:
                st = service.std.strftime("%H:%M")
            elif service.sta:
                st = service.sta.strftime("%H:%M")
            platform: str = parse_platform(service)
            operator: str = service.operator_short_name

            location: str = parse_station(service)

            et: str = parse_et(service)

            if service.is_cancelled and service.cancel_reason is not None:
                location += f"\n[secondary]{service.cancel_reason}[/secondary]"
            elif service.delay_reason is not None:
                location += f"\n[secondary]{service.delay_reason}[/secondary]"

            if show_formation:
                if service.formation is not None and service.is_cancelled is False:
                    formation: str = parse_formation(service)
                    if formation:
                        location += f"\n[light]{formation}[/light]"

            table.add_row(st, location, platform, et, operator)

    console.print(table)

    if show_nrcc_messages and station.nrcc_messages:
        parsed_messages: list[str] = parse_nrcc_messages(station.nrcc_messages)
        for message in parsed_messages:
            console.print(
                Padding(message, (0, 16)),
                highlight=False,
                style="info",
                width=94,
                justify="center",
            )


def parse_formation(service: huxley.Service) -> str:
    """Parse the formation of a service, adding color hints."""
    diagram: str = ""
    if service.formation is not None and service.formation.coaches is not None:
        if service.is_cancelled is False or service.delay_reason == "":
            diagram += "◢"
            coaches: int = len(service.formation.coaches)
            for coach in service.formation.coaches:
                carriage = "■" if coach.toilet and coach.toilet.status == 1 else "◻"
                tint = "primary" if coach.coach_class == "First" else "light"
                diagram = diagram + f"[{tint}]{carriage}[/{tint}]"
            diagram = diagram + f" {coaches}"
    return diagram


def parse_nrcc_messages(nrcc_messages: list[dict[str, Any]]) -> list[str]:
    """Parse NRCC messages, stripping HTML and control characters."""
    messages: list[str] = []
    for message in nrcc_messages:
        text: str = re.sub(r"<.*?>", "", message["value"])
        text = re.sub(r"(\r\n|\n|\r)", "", text)
        text = html.unescape(text)
        messages.append(text)
    return messages


def parse_station(service: huxley.Service) -> str:
    """Show the origin or destination of a service, including any via points."""
    stations: list[str] = []
    source: str = "destination" if service.std is not None else "origin"
    for d in getattr(service, source):
        if d.via is not None:
            location = f"{d.location_name} [white]{d.via}[/white]"
        else:
            location = d.location_name
        stations.append(location)

    match len(stations):
        case 1:
            return stations[0]
        case 2:
            return f"{stations[0]} [secondary]and[/secondary] {stations[1]}"
        case _:
            return (
                "[secondary],[/secondary] ".join(stations[:-1])
                + " [secondary]and[/secondary] "
                + stations[-1]
            )


def parse_et(service: huxley.Service) -> str:
    """Parse the expected departure time of a service, adding color hints."""
    attr = "etd" if service.etd is not None else "eta"
    value = getattr(service, attr)
    if value is None:
        return "[white]\u2014[/white]"
    if value == "On time":
        tag = "success"
    elif value == "Delayed":
        tag = "warning"
    elif value == "Cancelled" and service.is_cancelled:
        tag = "danger"
    elif isinstance(value, time) and value != service.std:
        tag = "warning"
    else:
        tag = "white"
    return f"[{tag}]{value}[/{tag}]"


def parse_platform(service: huxley.Service) -> str:
    """Return the platform number, or a dash if not available."""
    return service.platform if service.platform is not None else "-"


@click.command()
@click.option(
    "-s",
    "--station",
    "crs",
    required=True,
    type=str,
    default="kgx",
    help="CRS code of the station",
)
@click.option(
    "-r",
    "--rows",
    type=int,
    show_default=True,
    default=10,
    help="Number of rows of services to retrieve",
)
@click.option(
    "-m",
    "--messages",
    "show_nrcc_messages",
    type=bool,
    is_flag=True,
    default=False,
    help="Show NRCC messages for the station",
)
@click.option(
    "-f",
    "--formation",
    "show_formation",
    type=bool,
    is_flag=True,
    default=False,
    help="Show formation of each train service",
)
@click.option(
    "-l",
    "--local",
    type=bool,
    is_flag=True,
    default=False,
    help="Use local JSON data for debugging",
)
@click.option(
    "-d",
    "--debug",
    type=bool,
    is_flag=True,
    default=False,
    help="Show API response for debugging",
)
@click.option(
    "-a",
    "--arrivals",
    is_flag=True,
    default=False,
    help="Show arrivals instead of departures",
)
def main(crs: str, arrivals: bool, rows: int, show_nrcc_messages: bool, show_formation: bool, local: bool, debug: bool) -> None:
    """Show upcoming departures or arrivals for a given railway station."""
    station = huxley.Station(crs)
    if arrivals:
        station.get_arrivals(expand=False, rows=rows, local=local)
    else:
        station.get_departures(expand=False, rows=rows, local=local)
    show_board(station, show_nrcc_messages, show_formation)
    if debug:
        print(station.url)


if __name__ == "__main__":
    main()
