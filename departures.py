#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CLI tool to show upcoming departures for a given railway station."""
import re

import click
from rich import box
from rich.console import Console
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


def show_departures(station, show_nrcc_messages: bool):
    """Render a Rich table of departures for a railway station."""
    console = Console(theme=BOOTSTRAP)

    table = Table(
        style="secondary",
        show_header=True,
        box=box.SIMPLE_HEAD,
        title=station.location_name,
        title_style="light on primary",
    )
    table.caption_style = "warning"
    table.add_column("Time", width=6)
    table.add_column("Destination", style="warning", width=44)
    table.add_column("Plat", justify="right", width=4)
    table.add_column("Expected", justify="right", width=10)
    table.add_column("Operator", justify="right", style="info", width=16)

    if station.train_services:
        for service in station.train_services:
            std: str = service.std.strftime("%H:%M")
            platform: str = service.platform
            operator: str = service.operator_short_name
            destination: str = parse_destinations(service)
            etd: str = parse_etd(service)
            table.add_row(std, destination, platform, etd, operator)

            if hasattr(service, "cancel_reason"):
                if service.cancel_reason is not None and service.is_cancelled is True:
                    table.add_row("", f"[secondary]{service.cancel_reason}[/secondary]")

            if hasattr(service, "delay_reason"):
                if service.delay_reason is not None and service.cancel_reason is None:
                    table.add_row("", f"[secondary]{service.delay_reason}[/secondary]")

            if hasattr(service, "formation"):
                if service.is_cancelled is False or service.delay_reason == "":
                    count: int = len(service.formation.coaches)
                    table.add_row(
                        "",
                        f"[secondary]This train is formed of {count} coaches[/secondary]",
                    )
    console.print(table)

    if show_nrcc_messages is True:
        if station.nrcc_messages is not None:
            nrcc_messages: list = parse_nrcc_messages(station.nrcc_messages)
            for message in nrcc_messages:
                console.print(
                    message,
                    highlight=False,
                    new_line_start=True,
                    style="secondary",
                    width=80,
                    justify="center",
                )


def parse_nrcc_messages(nrcc_messages: list) -> list:
    """Parse NRCC messages, stripping HTML and control characters."""
    messages: list = []
    for message in nrcc_messages:
        message["value"] = re.sub(r"<.*?>", "", message["value"])
        message["value"] = re.sub(r"(\r\n|\n|\r)", "", message["value"])
        messages.append(message["value"])
    return messages


def parse_destinations(service) -> str:
    """Show the destination of a service, including any via points."""
    destinations: list = []
    for d in service.destination:
        destination = d.location_name
        if hasattr(d, "via") and d.via is not None:
            destination = f"{d.location_name} [white]{d.via}[/white]"
        else:
            destination = d.location_name
        destinations.append(destination)
    parsed: str = ""
    match len(destinations):
        case 1:
            parsed = f"{destinations[0]}"
        case 2:
            parsed = f"{destinations[0]} and {destinations[1]}"
        case _:
            parsed = (
                "[light],[/light] ".join(destinations[:-1])
                + " [light]and[/light] "
                + destinations[-1]
            )

    return parsed


def parse_etd(service) -> str:
    """Parse the expected departure time of a service, adding color hints."""
    etd: str = service.etd
    if service.etd == "On time":
        etd = f"[success]{etd}[/success]"
    elif service.etd == "Cancelled" and service.is_cancelled is True:
        etd = f"[danger]{etd}[/danger]"
    elif service.etd != service.std:
        etd = f"[warning]{etd}[/warning]"
    return etd


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
def departures(crs, rows, show_nrcc_messages):
    """CLI tool to show departures for a railway station."""
    station = huxley.Station(crs)
    station.get_departures(expand=False, rows=rows)
    show_departures(station, show_nrcc_messages)


if __name__ == "__main__":
    departures()
