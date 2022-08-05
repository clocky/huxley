# Huxley

A one-page [Flask](https://flask.palletsprojects.com/en/2.2.x/) app to 
dynamically show a departure board for a given railway in the United Kingdom. 

Uses the [Huxley2 API](https://huxley2.azurewebsites.net) for requests and [Bootstrap 5.2](https://getbootstrap.com) for layout.

## Install

1. ```python3 -m pip install -r requirements.txt```
2. Set a `DARWIN_API_KEY` in a `.env` file in the root of this project. If you don't already have one, you can request an access token via the National Rail [OpenLDBWS portal](https://realtime.nationalrail.co.uk/OpenLDBWSRegistration/Registration).
3. ```python3 -m flask run```
