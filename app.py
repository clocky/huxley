"""One-page Flask app to retrieve and render departures for a given station."""
from flask import Flask, render_template
from Huxley import Huxley

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def hello_world():
    """Return a default main page."""
    return "<p>Hello, World!</p>"


@app.route("/departures/<string:crs>/")
@app.route("/departures/<string:crs>/<int:rows>")
def departures(crs=None, rows=10):
    """Render a departure board for the given station."""
    station = Huxley(crs)
    station.get_departures(expand=False, rows=rows)
    return render_template("departures.jinja2", station=station)
