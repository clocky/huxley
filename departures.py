from rich import print
from rich.console import Console
from rich.table import Table
from Huxley import Huxley

if __name__ == "__main__":
    station = Huxley("gtw")
    station.get_departures()

    departures = Table(title=station.location_name)
    departures.add_column("Time")
    departures.add_column("Destination")
    departures.add_column("Platform")
    departures.add_column("Status", justify="right")

    if station.are_services_available:
        for service in station.train_services:
            for destination in service.destination:
                departures.add_row(
                    str(service.std), destination.location_name, service.etd
                )
                if service.is_cancelled:
                    departures.add_row(None, service.cancel_reason)
                if service.etd == "Delayed":
                    departures.add_row(None, service.delay_reason)

        console = Console()
        console.print(departures)
