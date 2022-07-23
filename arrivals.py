from rich import print
from rich.console import Console
from rich.table import Table
from Huxley import Huxley

if __name__ == "__main__":
    station = Huxley("wat")
    station.get_arrivals()
    arrivals = Table(title=station.location_name, box=None)
    arrivals.add_column()
    arrivals.add_column()
    arrivals.add_column()
    arrivals.add_column(justify="right")

    if station.are_services_available:
        for service in station.train_services:
            for origin in service.origin:
                if service.eta != "On time":
                    eta = f"Exp {service.eta}"
                else:
                    eta = service.eta
                arrivals.add_row(origin.location_name, service.sta, service.platform, eta)
                if service.is_cancelled:
                    arrivals.add_row(service.cancel_reason)
                if service.eta == "Delayed":
                    arrivals.add_row(None, service.delay_reason)

        console = Console()
        console.print(arrivals)
