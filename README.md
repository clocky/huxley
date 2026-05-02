# Huxley

A one-page [Flask](https://flask.palletsprojects.com/en/2.2.x/) app to 
dynamically show a departure board for a given railway in the United Kingdom. 

Uses the [Huxley2 API](https://huxley2.azurewebsites.net) for requests and [Bootstrap 5.2](https://getbootstrap.com) for layout.

## Install

1. ```python3 -m venv .venv && source .venv/bin/activate```
2. ```pip install -r requirements.txt```
3. Set a `DARWIN_API_KEY` in a `.env` file in the root of this project. If you don't already have one, you can request an access token via the National Rail [OpenLDBWS portal](https://realtime.nationalrail.co.uk/OpenLDBWSRegistration/Registration).

## Web

```flask run```

Opens a departure board at http://127.0.0.1:5000. Defaults to London Waterloo. Navigate to `/departures/<crs>/` for other stations.

## CLI

```python station.py -s <crs>```

Options:

| Flag | Description |
|------|-------------|
| `-s`, `--station` | CRS code of the station (e.g. `kgx`, `wat`, `pad`) |
| `-r`, `--rows` | Number of services to show (default: 10) |
| `-a`, `--arrivals` | Show arrivals instead of departures |
| `-f`, `--formation` | Show train formation (coach count, first class, toilets) |
| `-m`, `--messages` | Show NRCC messages |
| `-d`, `--debug` | Print the API URL |
