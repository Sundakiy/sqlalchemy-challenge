import numpy as np

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func, distinct

from flask import Flask, jsonify

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")

# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)

# Save reference to the table
measurement = Base.classes.measurement
station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)



@app.route("/")
def welcome():
    print("Server requested climate app welcome page...")
    return (
        f"Welcome to the Hawaii Climate App!<br/>"
        f"----------------------------------------------<br/>"
        f"Available Routes for Hawaii Weather Data:<br/><br>"
        f"Precipitation measurement over the last 12 months: /api/v1.0/precipitation<br>"
        f"A list of stations and their respective station numbers: /api/v1.0/stations<br>"
        f"Temperature observations at the most active station over the previous 12 months: /api/v1.0/tobs<br>"
        f"Enter a start date (yyyy-mm-dd) to retrieve the minimum, maximum, and average temperatures for all dates after the specified date: /api/v1.0/<start><br>"
        f"Enter both a start and end date (yyyy-mm-dd) to retrieve the minimum, maximum, and average temperatures for that date range: /api/v1.0/<start>/<end><br>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """# create precipitation route of last 12 months of precipitation data"""
    # Query and summarize daily precipitation across all stations for the last year of available data
    
    recent_prcp = session.query(str(measurement.date), measurement.prcp)\
    .filter(measurement.date > '2016-08-22')\
    .filter(measurement.date <= '2017-08-23')\
    .order_by(measurement.date).all()

    # convert results to a dictionary with date as key and prcp as value
    prcp_dict = dict(recent_prcp)

    # return json list of dictionary
    return jsonify(prcp_dict)

@app.route("/api/v1.0/stations")
def stations():
    # Create our session (link) from Python to the DB
    session = Session(engine)

    """Return a list of all the active Weather stations in Hawaii"""
    # Return a list of active weather stations in Hawaii
    sel = [measurement.station]
    active_stations = session.query(*sel).\
        group_by(measurement.station).all()
    session.close()

    # Return a dictionary with the date as key and the daily precipitation total as value
    # Convert list of tuples into normal list and return the JSonified list
    list_of_stations = list(np.ravel(active_stations)) 
    return jsonify(list_of_stations)

@app.route("/api/v1.0/tobs")
def tobs():
    # Create our session (link) from Python to the DB
    session = Session(engine)
    # Query the last 12 months of temperature observation data for the most active station
    start_date = '2016-08-23'
    sel = [measurement.date, 
        measurement.tobs]
    station_temps = session.query(*sel).\
            filter(measurement.date >= start_date, measurement.station == 'USC00519281').\
            group_by(measurement.date).\
            order_by(measurement.date).all()

    session.close()

    # Return a dictionary with the date as key and the daily temperature observation as value
    observation_dates = []
    temperature_observations = []

    for date, observation in station_temps:
        observation_dates.append(date)
        temperature_observations.append(observation)
    
    most_active_tobs_dict = dict(zip(observation_dates, temperature_observations))

    return jsonify(most_active_tobs_dict)

@app.route("/api/v1.0/trip/<start_date>")
@app.route("/api/v1.0/trip/<start_date>/<end_date>")
def trip1(start_date=None, end_date=None):
    # Calculate minimum, average and maximum temperatures for the range of dates starting with start date.
   

    session = Session(engine)

    if not end_date:
        query_result = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).all()
    else:
         query_result = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start_date).filter(measurement.date <= end_date).all()

    session.close()
    temps = list(np.ravel(query_result))
    return jsonify(temps)


if __name__ == '__main__':
    app.run(debug=True)