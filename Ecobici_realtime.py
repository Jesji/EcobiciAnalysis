#ECOBICI REAL TIME ANALYSIS
#%%
#GET DATA FROM API
import requests 
import pandas as pd

# give url and request api
url = "https://gbfs.mex.lyftbikes.com/gbfs/gbfs.json"
response = requests.get(url)

# if code is 200 transform data to json
if response.status_code == 200:
    data = response.json()
else: 
    print(f"Failed to fetch data. Status code: {response.status_code}")

# aafter reviewing json structure 
# transform data to dataframe of jsons
data_bici = pd.json_normalize(data["data"]["en"]["feeds"])

#print(data_bici['url'].values)

# caracteristicas de los datasets dados:
#1. system_information : lenguaje, dominio, startdate, timezone, caracteristicas del sistema
#2. station_status: info dinamica: [station_id, num_bikes_available, num_bikes_disabled, etc. 
#3. free_bike_status : ta vacio
#4. station_iformation: info estatica de las estaciones station_id, name, lat, lon, capacity, electri_charge_waiver, is_charging, 
#5. system_alerts: notificaiones de estaciones fuera de servicio

#Por lo tanto solo son interesantes para este analisis
# station_status y station_information
#%%
# GET DATA FROM STATUS AND INFO IN RESULTS DICT
results =  {}
names = {"station_status", "station_information"}

for a in names:
    url = data_bici.loc[data_bici["name"]== a, "url"].values[0]
    #print(url)
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            stations_data = data["data"]["stations"] 
            df_result = pd.json_normalize(stations_data)
            results[a] = df_result
            print(f"Data from '{a}' loaded succesfully")
        else:
            print(f"Failed to fetch data from '{a}'. code : {response.status_code}")
    except Exception as e:
        print(f"error while fetching '{a}': {e}")

#print(results["station_status"])

#%% 
# EXPLORE DATASETS
df_status = results["station_status"]
df_info = results["station_information"]

# merge by station id
df_whole = pd.merge(df_status, df_info, on="station_id")
#print(df_whole.sum())
df_whole

#Get indicadores to show in dashboard
tot_bikes_available = df_whole["num_bikes_available"].sum()
tot_docks_available = df_whole["num_docks_available"].sum()
#tot_bikes_disabled = df_whole["num_bikes_disabled"].sum()

#print(df_info[df_info["name"].str.contains('601')] )
#print(df_status[df_info["station_id"].str.contains('608')] )
#df_status
#print(df_info[df_info["station_id"]=='690'] )
#df_status = results.get("station_status")
#df_info = results.get("station_information")

#%%
#PLOTLY HEAT MAP
import plotly.express as px
map_ava_bike = px.density_mapbox(df_whole, lat="lat", lon="lon", z="num_bikes_available",
                        radius=20, center=dict(lat=df_whole.lat.mean(), lon=df_whole.lon.mean()),
                        zoom=11, mapbox_style="open-street-map", height=900)

#fig.show()

#%%
# SMALL GRAPHICS TO SHOW
# bar plot of available bikes 
bar_fig_bike  = px.histogram(df_whole, x="num_bikes_available", nbins=20, 
                             title="Bicicletas disponibles por estación")
#bar_fig_bike.show()

bar_fig_docks  = px.histogram(df_whole, x="num_docks_available", nbins=20, 
                             title="Puertos disponibles por estación")

#bar_fig_docks.show()
# %%
# Dash test
import dash
from dash import html, dcc
app = dash.Dash(__name__)

app.layout = html.Div(
    style={"display":"flex", "height":"100vh", "width":"90vw", 
            "flexDirection":"row","gap":"0px" ,"boxSizing":"border-box", "margin":"0"}, 
    children=[
    # left side
    html.Div(style={"width":"40%", "padding": "5px", "display": "flex", 
                    "flexDirection": "column", "gap": "1px", "boxSizing":"border-box"}, children=[
        #seccion botones
        html.Div(style={"display":"flex","flexDirection":"row", "gap":"0px"}, children=[
            #recuadro 1
            html.Div(style={"width":"20%", "backgroundColor":"#f8f9fa", "padding":"20px", "border":"1px solid #ddd", "textAlign":"left",
                            "fontSize":"20px", "boxShadow":"0px 2px 5px rgba(0,0,0,0.1)"}, children= [
                    html.Div("Total bicis disponibles", style={"fontWeight":"bold", "marginBottom":"10px"}),
                    html.Div(f"{tot_bikes_available:0.0f}") ]), 
            #recuadro 2
            html.Div(style={"width":"20%", "backgroundColor":"#f8f9fa", "padding":"20px", "border":"1px solid #ddd", "textAlign":"left",
                            "fontSize":"20px", "boxShadow":"0px 2px 5px rgba(0,0,0,0.1)"}, children= [
                    html.Div("Total puertos disponibles", style={"fontWeight":"bold", "marginBottom":"10px"}),
                    html.Div(f"{tot_docks_available:0.0f}") ])
            ]), 
        
        dcc.Graph(figure=bar_fig_bike, style={"height": "50%"}),
        dcc.Graph(figure=bar_fig_docks, style={"height":"50%"})
        ]),

    #right side
    html.Div(style={"width":"70%", "padding": "5px"}, children=[
        dcc.Graph(figure=map_ava_bike, style={"height": "100%"})
    ])
    ])

if __name__ == "__main__":
    app.run_server(debug = True)

