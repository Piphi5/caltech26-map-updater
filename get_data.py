import io
import sys
from functools import partial

import folium
import numpy as np
import pandas as pd
import requests
from folium.plugins import MarkerCluster
from geopy import GoogleV3


def get_latlon(geolocator, location_dict, place):
    if place in location_dict:
        return location_dict[place]
    else:
        location = geolocator.geocode(place)
        if not pd.isna(location):
            location_dict[place] = (location.latitude, location.longitude)
            return location.latitude, location.longitude
        else:
            return np.nan, np.nan

def format_info(info):
    if pd.isna(info):
        return ""
    else:
        return info


def generate_popup(name, insta, snap, discord, other):
    return folium.Popup(
        html=f"""<b>Name:</b><br>
                                {format_info(name)}<br><br>
                                <b>Instagram:</b><br>
                                {format_info(insta)}<br><br>
                                <b>Snapchat:</b><br>
                                {format_info(snap)}<br><br>
                                <b>Discord:</b><br>
                                {format_info(discord)}<br><br>
                                <b>Other:</b><br>
                                {format_info(other)}<br><br>""",
        max_width=300,
    )


# Get private strings
data_url = sys.argv[1]
api_key = sys.argv[2]
map_directory = sys.argv[3]

locations_df = pd.read_csv("locations.csv")
locations_tuple = list(locations_df.to_records(index=False))
location_dict = {place: (lat, lon) for place, lat, lon in locations_tuple}

# Get data and remove personal info
urlData = requests.get(data_url).content
df = pd.read_csv(io.StringIO(urlData.decode("utf-8")))

# Raise Exception if charged price may get too large
# 200 transactions = $1 (Max limit)
if len(set(df["Hometown"]) ^ set(location_dict.keys())) >= 200:
    raise Exception("Too many places to process.")

# Setup location name to latitude longitude functions
geolocator = GoogleV3(api_key=api_key)
vec_address_converter = np.vectorize(partial(get_latlon, geolocator, location_dict))
latitudes, longitudes = vec_address_converter(df["Hometown"].to_numpy())

# Create Map
m = folium.Map(zoom_start=15)
marker_cluster = MarkerCluster().add_to(m)

for lat, lon, name, insta, snap, discord, commited, other in zip(
    latitudes,
    longitudes,
    df["Name"],
    df["Instagram"],
    df["Snapchat"],
    df["Discord"],
    df["Commited? (Y/N)"],
    df["Other"],
):
    if pd.isna(lat) or pd.isna(lon):
        continue
    icon = "user"
    if type(commited) is str and commited:
        if "Y" in commited:
            icon = "ok-sign"
        elif "N" in commited:
            icon = "question-sign"

    folium.Marker(
        location=[lat, lon],
        icon=folium.Icon(color="orange", icon=icon),
        popup=generate_popup(name, insta, snap, discord, other),
    ).add_to(marker_cluster)

m.fit_bounds(m.get_bounds())

# Save map to html
m.save(f"caltech26-map/{map_directory}/index.html")

# Save downloaded locations to a CSV
updated_data = [(key, coords[0], coords[1]) for key, coords in location_dict.items()]
pd.DataFrame(updated_data, columns=["Hometown", "Latitude", "Longitude"]).to_csv(
    "locations.csv", index=False
)
