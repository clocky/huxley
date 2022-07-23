from flask import Flask, render_template
from Huxley import Huxley

app = Flask(__name__)
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"


@app.route("/departures/<string:crs>")
@app.route("/departures/<string:crs>/<int:rows>")
def departures(crs=None, rows=10):
    station = Huxley(crs)
    station.get_departures(expand=False, rows=rows)
    return render_template("departures.jinja2", station=station)
