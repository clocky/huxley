#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI tool to show upcoming departures for a given railway station."""
import re

import click
import html
from datetime import datetime, time
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


def show_board(station, show_nrcc_messages: bool, show_formation: bool):
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

            # If the cancel reason is not empty, add it to the destination.
            if hasattr(service, "cancel_reason"):
                if service.is_cancelled is True and service.cancel_reason is not None:
                    location += f"\n[secondary]{service.cancel_reason}[/secondary]"

            # If the delay reason is not empty, add it to the destination.
            if hasattr(service, "delay_reason"):
                if service.delay_reason is not None and service.cancel_reason is None:
                    location += f"\n[secondary]{service.delay_reason}[/secondary]"

            # If formation exists, add it to the table.
            if show_formation:
                if service.formation is not None and service.is_cancelled is False:
                    formation: str = parse_formation(service)
                    # Only add the formation if it's not an empty string.
                    if formation:
                        location += f"\n[light]{formation}[/light]"

            # Add everything to the table
            table.add_row(st, location, platform, et, operator)

    console.print(table)

    if show_nrcc_messages is True:
        if station.nrcc_messages is not None:
            nrcc_messages: list = parse_nrcc_messages(station.nrcc_messages)
            for message in nrcc_messages:
                console.print(
                    Padding(message, (0, 16)),
                    highlight=False,
                    style="info",
                    width=94,
                    justify="center",
                )


def parse_formation(service) -> str:
    """Parse the formation of a service, adding color hints."""
    diagram: str = ""
    carriage: str = "■"
    if service.formation.coaches is not None:
        if service.is_cancelled is False or service.delay_reason == "":
            diagram += "◢"
            coaches: int = len(service.formation.coaches)
            for coach in service.formation.coaches:
                carriage = "■" if coach.toilet and coach.toilet.status == 1 else "◻"
                tint = "primary" if coach.coach_class == "First" else "light"
                diagram = diagram + f"[{tint}]{carriage}[/{tint}]"
            diagram = diagram + f" {coaches}"
    return diagram


def parse_nrcc_messages(nrcc_messages: list) -> list:
    """Parse NRCC messages, stripping HTML and control characters."""
    messages: list = []
    for message in nrcc_messages:
        message["value"] = re.sub(r"<.*?>", "", message["value"])
        message["value"] = re.sub(r"(\r\n|\n|\r)", "", message["value"])
        message["value"] = html.unescape(message["value"])
        messages.append(message["value"])
    return messages


def parse_station(service) -> str:
    """Show the origin or destination of a service, including any via points."""
    stations: list = []
    source: str = "destination" if service.std is not None else "origin"
    for d in getattr(service, source):
        location = d.location_name
        if hasattr(d, "via") and d.via is not None:
            location = f"{d.location_name} [white]{d.via}[/white]"
        else:
            location = d.location_name
        stations.append(location)
    parsed: str = ""

    match len(stations):
        case 1:
            parsed = f"{stations[0]}"
        case 2:
            parsed = f"{stations[0]} [secondary]and[/secondary] {stations[1]}"
        case _:
            parsed = (
                "[secondary],[/secondary] ".join(stations[:-1])
                + " [secondary]and[/secondary] "
                + stations[-1]
            )

    return parsed


def parse_et(service) -> str:
    """Parse the expected departure time of a service, adding color hints."""
    estimated_time: str = ""
    tag: str = "white"
    property: str = "etd" if service.etd is not None else "eta"
    if getattr(service, property) == "On time":
        tag = "success"
    elif getattr(service, property) == "Delayed":
        tag = "warning"
    elif getattr(service, property) == "Cancelled" and service.is_cancelled is True:
        tag = "danger"
    elif getattr(service, property) == None:
        tag = "white"
        et = "—"
    elif getattr(service, property) != service.std:
        tag = "warning"
        et = getattr(service, property).strftime("%H:%M")
    estimated_time = f"[{tag}]{getattr(service, property)}[/{tag}]"
    return estimated_time


def parse_platform(service) -> str:
    platform: str = ""
    match service.platform:
        case None:
            platform = "-"
        case _:
            platform = service.platform
    return platform


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
def main(crs, arrivals, rows, show_nrcc_messages, show_formation, local, debug):
    if arrivals:
        arrival_board(crs, rows, show_nrcc_messages, show_formation, local, debug)
    else:
        departure_board(crs, rows, show_nrcc_messages, show_formation, local, debug)


def departure_board(crs, rows, show_nrcc_messages, show_formation, local, api):
    """CLI tool to show departures for a railway station."""
    station = huxley.Station(crs)
    station.get_departures(expand=False, rows=rows, local=local)
    show_board(station, show_nrcc_messages, show_formation)
    if api:
        print(station.url)


def arrival_board(crs, rows, show_nrcc_messages, show_formation, local, api):
    """CLI tool to show arrivals for a railway station."""
    station = huxley.Station(crs)
    station.get_arrivals(expand=False, rows=rows, local=local)
    show_board(station, show_nrcc_messages, show_formation)
    if api:
        print(station.url)


if __name__ == "__main__":
    main()
