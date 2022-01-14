import io
import sys
from functools import partial

import folium
import numpy as np
import pandas as pd
import requests
from geopy import GoogleV3


def get_latlon(geolocator, location_dict, place):
    if place in location_dict:
        return location_dict[place]
    else:
        location = geolocator.geocode(place)
        location_dict[place] = (location.latitude, location.longitude)
        return location.latitude, location.longitude


# Get private strings
data_url = sys.argv[1]
api_key = sys.argv[2]

locations_df = pd.read_csv("locations.csv")
locations_tuple = list(locations_df.to_records(index=False))
location_dict = {place: (lat, lon) for place, lat, lon in locations_tuple}

# Get data and remove personal info
urlData = requests.get(data_url).content
df = pd.read_csv(io.StringIO(urlData.decode("utf-8")))
df = df.drop([col for col in df.columns if col != "Hometown"], axis=1)

# Setup location name to latitude longitude functions
geolocator = GoogleV3(api_key=api_key)
vec_address_converter = np.vectorize(partial(get_latlon, geolocator, location_dict))
lat, lon = vec_address_converter(df["Hometown"].to_numpy())

# Create Map
m = folium.Map(zoom_start=15)

for coord in zip(lat, lon):
    folium.Marker(
        location=[coord[0], coord[1]], icon=folium.Icon(color="orange", icon="user")
    ).add_to(m)

m.fit_bounds(m.get_bounds())

# Save map to html
m.save("caltech26-map/index.html")

# Save downloaded locations to a CSV
updated_data = [(key, coords[0], coords[1]) for key, coords in location_dict.items()]
pd.DataFrame(updated_data, columns=["Hometown", "Latitude", "Longitude"]).to_csv(
    "locations.csv", index=False
)
