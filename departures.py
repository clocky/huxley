#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import click
from rich import box
from rich.console import Console
from rich.table import Table
from rich.theme import Theme

from Huxley import Huxley

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


def show_departures(station):
    console = Console(theme=BOOTSTRAP)

    table = Table(
        style="secondary",
        show_header=True,
        box=box.SIMPLE_HEAD,
        title=station.location_name,
        title_style="warning",
    )
    table.caption_style = "warning"
    table.add_column("Time", width=6)
    table.add_column("Destination", style="warning", width=40)
    table.add_column("Plat", justify="right", width=4)
    table.add_column("Expected", justify="right", width=9)
    table.add_column("Operator", justify="right", style="info")

    for service in station.train_services:
        std: str = service.std
        etd: str = service.etd
        platform: str = service.platform
        operator: str = service.operator
        destination: str = ""
        via: str = ""

        for d in service.destination:
            destination = d.location_name
            if hasattr(d, "via"):
                if d.via is not None:
                    destination = f"{destination} [white]{d.via}[/white]"

        if service.etd == "On time":
            etd = f"[success]{etd}[/success]"
        elif service.etd == "Cancelled" and service.is_cancelled is True:
            etd = f"[danger]{etd}[/danger]"
        elif service.etd != service.std:
            etd = f"[warning]{etd}[/warning]"

        table.add_row(std, destination, platform, etd, operator)

        if hasattr(service, "cancel_reason"):
            if service.cancel_reason is not None and service.is_cancelled is True:
                table.add_row("", f"[secondary]{service.cancel_reason}[/secondary]")

        if hasattr(service, "delay_reason"):
            if service.delay_reason is not None and service.cancel_reason is None:
                table.add_row("", f"[secondary]{service.delay_reason}[/secondary]")
    console.print(table)


@click.command()
@click.option("--crs", help="CRS Code")
@click.option("--rows", default=12, help="Number of rows")
def departures(crs, rows):
    station = Huxley(crs)
    station.get_departures(expand=False, rows=rows)
    show_departures(station)


if __name__ == "__main__":
    departures()
