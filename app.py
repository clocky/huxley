"""One-page Flask app to retrieve and render departures for a given station."""
from flask import Flask, redirect, url_for, render_template
from Huxley import Huxley

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def default():
    """Return a default main page."""
    return redirect(url_for("departures", crs="wat"))


@app.route("/departures/<string:crs>/")
@app.route("/departures/<string:crs>/<int:rows>")
def departures(crs=None, rows=10):
    """Render a departure board for the given station."""
    station = Huxley(crs)
    station.get_departures(expand=False, rows=rows)
    return render_template("departures.jinja2", station=station)
