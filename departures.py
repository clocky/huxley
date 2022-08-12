from Huxley import Huxley
from rich import print
from rich.console import Console
from rich.table import Table
from rich.theme import Theme

bootstrap = Theme(
    {
        "success": "#198754",
        "warning": "#ffc107",
        "danger": "#dc3545",
        "info": "#0dcaf0",
        "light": "#f8f9fa",
        "dark": "#212529",
        "secondary": "#6c757d",
    }
)


def show_departures(station):
    console = Console(theme=bootstrap)
    table = Table(style="dark")
    table.add_column("Time", width=6)
    table.add_column("Destination", style="warning", width=40)
    table.add_column("Plat", justify="right", width=4)
    table.add_column("Expected", justify="right", width=9)
    table.add_column("Operator", justify="right", style="info", width=24)
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
                    destination = f"{destination} [secondary]{d.via}[/secondary]"

        if service.etd == "On time":
            etd = f"[success]{etd}[/success]"
        elif service.etd == "Cancelled" and service.is_cancelled is True:
            etd = f"[danger]{etd}[/danger]"
        elif service.etd != service.std:
            etd = f"[warning]{etd}[/warning]"

        table.add_row(std, destination, platform, etd, operator)
    console.print(table)


if __name__ == "__main__":
    station = Huxley("wok")
    station.get_departures(expand=False, rows=10)
    show_departures(station)
