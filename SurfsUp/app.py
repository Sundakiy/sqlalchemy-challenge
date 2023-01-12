#Part 2: Design Your Climate App
#Design Flask API based on the queries developed in Part 1

# 1. Import dependencies for the APP
import numpy as np
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(autoload_with=engine)
# Define references to the tables
measurement = Base.classes.measurement
station = Base.classes.station

#Start at the homepage.
#Create an app/Flask set up
app = Flask(__name__)

#1  List all the available routes.
@app.route("/")
def home():
    print("Server requested climate app home page...")
    return (
        f"Welcome to the Hawaii Climate App!<br/>"
        f"----------------------------------<br/>"
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/start_date<br/>"
        f"/api/v1.0/start_date/end_date<br/>"
        f"<br>"
        f"Note: Replace 'start_date' and 'end_date' with your query dates. Format for querying is 'YYYY-MM-DD'"
    )

#2. /api/v1.0/precipitation
#Convert the query results from your precipitation analysis (i.e. retrieve only the last 12 months of data) to a dictionary using date as the key and prcp as the value.

@app.route("/api/v1.0/precipitation")
def precipitation():
    print("Server requested climate app precipitation page...")

    # --- create a session from Python to the database ---
    session = Session(engine)

    # --- perform a query to retrieve all the date and precipitation values ---
    prcp_data = session.query(measurement.date, measurement.prcp).all()

    # --- close the session ---
    session.close()

    # --- convert the query results to a dictionary using date as the key and prcp as the value ---
    prcp_dict = {} 
    for date, prcp in prcp_data:
        prcp_dict[date] = prcp
    
    # Return the JSON representation of your dictionary.
    return jsonify(prcp_dict)


@app.route("/api/v1.0/stations")
def stations():
    print("Server requested climate app station data...")

    # --- create a session from Python to the database ---
    session = Session(engine)
    
    # --- perform a query to retrieve all the station data ---
    results = session.query(station.id, station.station, station.name).all()

    # --- close the session ---
    session.close()

    # --- create a list of dictionaries with station info using for loop---
    list_stations = []

    for st in results:
        station_dict = {}

        station_dict["id"] = st[0]
        station_dict["station"] = st[1]
        station_dict["name"] = st[2]

        list_stations.append(station_dict)

    # Return a JSON list of stations from the dataset.
    return jsonify(list_stations)


@app.route("/api/v1.0/tobs")
def tobs():
    print("Server reuested climate app temp observation data ...")

    # --- create a session from Python to the database ---
    session = Session(engine)

    # Query the dates and temperature observations of the most active station for the last year of data.

    # --- identify the most active station ---
    most_active_station = session.query(measurement.station, func.count(measurement.station)).\
                                        order_by(func.count(measurement.station).desc()).\
                                        group_by(measurement.station).\
                                        first()[0]

    # --- identify the last date, convert to datetime and calculate the start date (12 months from the last date) ---
    last_date = session.query(measurement.date).order_by(measurement.date.desc()).first()[0]
    format_str = '%Y-%m-%d'
    last_dt = dt.datetime.strptime(last_date, format_str)
    date_oneyearago = last_dt - dt.timedelta(days=365)

    # --- build query for tobs with above conditions ---
    most_active_tobs = session.query(measurement.date, measurement.tobs).\
                                    filter((measurement.station == most_active_station)\
                                            & (measurement.date >= date_oneyearago)\
                                            & (measurement.date <= last_dt)).all()

    # --- close the session ---
    session.close()

    # Return a JSON list of temperature observations (TOBS) for the previous year.
    return jsonify(most_active_tobs)

@app.route("/api/v1.0/<start>")
def temps_from_start(start):
    # Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start or start-end range.
    # When given the start only, calculate TMIN, TAVG, and TMAX for all dates greater than and equal to the start date.

    print(f"Server requested climate app daily normals from {start}...")

    # --- create a function to calculate the daily normals given a certain start date (datetime object in the format "%Y-%m-%d") ---
    def daily_normals(start_date):

        # --- create a session from Python to the database ---
        session = Session(engine)   

        sel = [measurement.date, func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)]
        return session.query(*sel).filter(func.strftime("%Y-%m-%d", measurement.date) >= func.strftime("%Y-%m-%d", start_date)).group_by(measurement.date).all()

        # --- close the session ---
        session.close()

    try:
        # --- convert the start date to a datetime object for validating and error handling ---
        start_date = dt.datetime.strptime(start, "%Y-%m-%d")

        # --- call the daily_normals function to calculate normals from the start date and save the result ---
        results = daily_normals(start_date)
        normals=[]

        # --- create a for loop to go through row and calculate daily normals ---
        for temp_date, tmin, tavg, tmax in results:

            # --- create an empty dictionary and store results for each row ---
            temps_dict = {}
            temps_dict["Date"] = temp_date
            temps_dict["T-Min"] = tmin
            temps_dict["T-Avg"] = tavg
            temps_dict["T-Max"] = tmax

            # --- append each result's dictionary to the normals list ---
            normals.append(temps_dict)

        # --- return the JSON list of normals ---
        return jsonify(normals)

    except ValueError:
        return "Please enter a start date in the format 'YYYY-MM-DD'"
    

@app.route("/api/v1.0/<start>/<end>")
def temps_between(start, end):
#When given the start and the end date, calculate the TMIN, TAVG, and TMAX for dates between the start and end date inclusive.

    print(f"Server requested climate app daily normals from {start} to {end}...")

    # --- create a function to calculate the daily normals given certain start and end dates (datetime objects in the format "%Y-%m-%d") ---
    def daily_normals(start_date, end_date):

        # --- create a session from Python to the database ---
        session = Session(engine)   

        sel = [measurement.date, func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)]
        return session.query(*sel).filter(func.strftime("%Y-%m-%d", measurement.date) >= func.strftime("%Y-%m-%d", start_date)).\
                                   filter(func.strftime("%Y-%m-%d", measurement.date) <= func.strftime("%Y-%m-%d", end_date)).\
                                    group_by(measurement.date).all()

        # --- close the session ---
        session.close()

    try:
        # --- convert the start date to a datetime object for validating and error handling ---
        start_date = dt.datetime.strptime(start, "%Y-%m-%d")
        end_date = dt.datetime.strptime(end, "%Y-%m-%d")

        # --- call the daily_normals function to calculate normals from the start date and save the result ---
        results = daily_normals(start_date, end_date)
        normals=[]

        # --- create a for loop to go through row and calculate daily normals ---
        for temp_date, tmin, tavg, tmax in results:

            # --- create an empty dictionary and store results for each row ---
            temps_dict = {}
            temps_dict["Date"] = temp_date
            temps_dict["T-Min"] = tmin
            temps_dict["T-Avg"] = tavg
            temps_dict["T-Max"] = tmax

            # --- append each result's dictionary to the normals list ---
            normals.append(temps_dict)

        # --- return the JSON list of normals ---
        return jsonify(normals)

    except ValueError:
        return "Please enter dates in the following order and format: 'start_date/end_date' i.e. 'YYYY-MM-DD'/'YYYY-MM-DD'"

# Define main behavior
if __name__ == "__main__":
    app.run(debug=True)
