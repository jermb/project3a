from flask import Flask, render_template, request, url_for, flash, redirect, abort, get_flashed_messages
from graph import Graph
import graph as util

# make a Flask application object called app
app = Flask(__name__)
app.config["DEBUG"] = True

# flash the secret key to secure sessions
app.config["SECRET_KEY"] = "secret treasure"


# use the app.route() decorator to create a Flask view function called index()
@app.route('/', methods=("GET", "POST"))
def index():
    #   Create list of nasdaq stock symbols from file
    with open("nasdaq.txt", "r") as file:
        nasdaq: list = []
        for line in file.readlines():
            nasdaq.append(line.strip('\n'))


    if request.method == "POST":
        #   Retrieve values from form fields
        symbol = request.form["symbol"]
        graph_type = request.form["graphType"]
        time_series = request.form["timeSeries"]
        start_date = request.form["start"]
        end_date = request.form["end"]

        #   Validate input
        if symbol == "empty":
            flash("Symbol is required")
        elif graph_type == "empty":
            flash("Graph is required")
        elif time_series == "empty":
            flash("Time series is required")
        elif not util.check_dates(start_date, end_date):
            flash("End date cannot come before start date")
        else:
            try:
                #   Generate graph and send to html page
                graph = Graph(symbol, graph_type, time_series, start_date, end_date).create()
                return render_template('index.html', symbols=nasdaq, graph=graph)
            except ValueError:
                flash("Could not find data for this query")

    #   Render page without graph
    return render_template('index.html', symbols=nasdaq, graph=None)

if __name__ == '__main__':
    app.run(port=5005, host='0.0.0.0')

