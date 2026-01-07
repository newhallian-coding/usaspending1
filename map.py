import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
import numpy as np
import pandas as pd
from pathlib import Path


# -----------------------------
# Define State class
# -----------------------------
class State:
    def __init__(self, code, red=0, green=0, center=None):
        self.code = code
        self.red = red
        self.green = green
        self.center = center  # dict: {"lat": ..., "lon": ...}
        self.is_selected = False

    @property
    def combined(self):
        return self.green - self.red


# -----------------------------
# US State codes and centers
# -----------------------------
state_centers = {
    "AL": {"lat":32.8,"lon":-86.8}, "AK":{"lat":61.2,"lon":-149.9},
    "AZ": {"lat":34.2,"lon":-111.7}, "AR":{"lat":34.8,"lon":-92.3},
    "CA":{"lat":36.8,"lon":-119.4}, "CO":{"lat":39.0,"lon":-105.5},
    "CT":{"lat":41.6,"lon":-72.7}, "DE":{"lat":39.0,"lon":-75.5},
    "FL":{"lat":28.7,"lon":-82.6}, "GA":{"lat":32.5,"lon":-83.5},
    "HI":{"lat":20.7,"lon":-156.0}, "ID":{"lat":44.0,"lon":-114.0},
    "IL":{"lat":40.0,"lon":-89.0}, "IN":{"lat":39.9,"lon":-86.3},
    "IA":{"lat":42.0,"lon":-93.0}, "KS":{"lat":38.5,"lon":-98.0},
    "KY":{"lat":37.8,"lon":-85.0}, "LA":{"lat":31.0,"lon":-92.0},
    "ME":{"lat":45.3,"lon":-69.0}, "MD":{"lat":39.0,"lon":-76.7},
    "MA":{"lat":42.3,"lon":-71.8}, "MI":{"lat":44.3,"lon":-85.0},
    "MN":{"lat":46.0,"lon":-94.0}, "MS":{"lat":33.0,"lon":-89.5},
    "MO":{"lat":38.5,"lon":-92.0}, "MT":{"lat":47.0,"lon":-109.5},
    "NE":{"lat":41.5,"lon":-99.5}, "NV":{"lat":39.5,"lon":-116.0},
    "NH":{"lat":43.8,"lon":-71.5}, "NJ":{"lat":40.1,"lon":-74.7},
    "NM":{"lat":34.5,"lon":-106.0}, "NY":{"lat":43.0,"lon":-75.0},
    "NC":{"lat":35.5,"lon":-79.0}, "ND":{"lat":47.5,"lon":-100.5},
    "OH":{"lat":40.0,"lon":-82.5}, "OK":{"lat":35.5,"lon":-97.5},
    "OR":{"lat":44.0,"lon":-120.5}, "PA":{"lat":41.0,"lon":-77.5},
    "RI":{"lat":41.6,"lon":-71.5}, "SC":{"lat":33.5,"lon":-80.5},
    "SD":{"lat":44.5,"lon":-100.0}, "TN":{"lat":35.8,"lon":-86.5},
    "TX":{"lat":31.0,"lon":-100.0}, "UT":{"lat":39.5,"lon":-111.5},
    "VT":{"lat":44.0,"lon":-72.7}, "VA":{"lat":37.5,"lon":-78.5},
    "WA":{"lat":47.5,"lon":-120.5}, "WV":{"lat":38.5,"lon":-80.5},
    "WI":{"lat":44.5,"lon":-89.5}, "WY":{"lat":43.0,"lon":-107.5}
}
PARQUET_DIR = Path("usa_spending_defense")
US_STATES = [x for x in state_centers.keys()]


def aggregate_state_counts_dict():
    # Initialize dictionary with each state
    state_counts = {state: [0,0] for state in US_STATES}

    for file in PARQUET_DIR.glob("*.parquet"):
        df = pd.read_parquet(file)

        # Primary Place of Performance
        if "pop_state_code" in df.columns:
            pop_vals = df["pop_state_code"].dropna()
            pop_counts_file = pop_vals.value_counts()
            for state, count in pop_counts_file.items():
                if state in state_counts:
                    state_counts[state][0] += int(count)

        # Recipient Location
        if "recipient_location_state_code" in df.columns:
            rec_vals = df["recipient_location_state_code"].dropna()
            rec_counts_file = rec_vals.value_counts()
            for state, count in rec_counts_file.items():
                if state in state_counts:
                    state_counts[state][1] += int(count)
    return state_counts


# -----------------------------
# Initialize States
# -----------------------------
states_dict = {}
colors = aggregate_state_counts_dict()
for code, center in state_centers.items():
    red = colors[code][1]
    green = colors[code][0]
    states_dict[code] = State(
        code=code,
        red=red,
        green=green,
        center=center
    )

# -----------------------------
# Dash App Setup
# -----------------------------
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("Interactive US Contracts Map", style={"margin": "0", "padding": "6px 0"}),

    html.Div([
        html.Button("Show Completed (Red)", id="btn-red", n_clicks=0),
        html.Button("Show Offered (Green)", id="btn-green", n_clicks=0),
        html.Button("Show Combined", id="btn-redgreen", n_clicks=0),
        html.Button("Reset White", id="btn-white", n_clicks=0),
    ], style={"marginBottom": "6px"}),

    dcc.Graph(id="us-map", style={"width": "100vw", "height": "calc(100vh - 80px)"}),

    html.Div(
        id="top-states",
        style={
            "position": "absolute",
            "top": "90px",
            "right": "20px",
            "backgroundColor": "white",
            "padding": "12px",
            "border": "1px solid #ccc",
            "borderRadius": "6px",
            "width": "260px",
            "fontFamily": "Arial",
            "fontSize": "14px"
        }
    ),

    html.Div(
        id="state-info",
        style={
            "position": "absolute",
            "top": "250px",
            "right": "20px",
            "backgroundColor": "white",
            "padding": "12px",
            "border": "1px solid #ccc",
            "borderRadius": "6px",
            "width": "260px",
            "fontFamily": "Arial",
            "fontSize": "14px",
            "display": "none"  # start hidden
        }
    )

])


# -----------------------------
# Choropleth creator
# -----------------------------
def create_fig(states_list, value_type="red", color_scale="Reds"):
    """
    states_list: list of State objects
    value_type: "red", "green", or "combined_value"
    color_scale: Plotly color scale or custom [[0,color1],[1,color2]]
    """

    # Extract codes and values based on value_type
    codes = [s.code for s in states_list]

    if value_type == "red":
        values = [s.red for s in states_list]
    elif value_type == "green":
        values = [s.green for s in states_list]
    elif value_type == "combined_value":
        values = [s.combined for s in states_list]
    else:
        values = [1] * len(states_list)  # default white map

    # Create DataFrame for Plotly
    df = pd.DataFrame({"state": codes, "value": values})

    fig = px.choropleth(
        df,
        locations="state",
        locationmode="USA-states",
        color="value",
        scope="usa",
        color_continuous_scale=color_scale,
        labels={"value": "Intensity"}
    )

    # Highlight selected state(s)
    line_colors = ["black"] * len(codes)
    line_widths = [1.5] * len(codes)
    for idx, s in enumerate(states_list):
        if getattr(s, "is_selected", False):
            line_colors[idx] = "yellow"  # highlight color
            line_widths[idx] = 4

    fig.update_traces(marker_line_color=line_colors, marker_line_width=line_widths, showscale=False)

    # Optional: adjust zoom / center
    # If a state is selected, center on it
    selected_states = [s for s in states_list if getattr(s, "is_selected", False)]
    if selected_states and selected_states[0].center:
        center = selected_states[0].center
        fig.update_geos(center=center, projection_scale=2.5)
    else:
        fig.update_geos(center={"lat": 36, "lon": -96}, projection_scale=0.8)

    fig.update_layout(margin={"l": 0, "r": 0, "t": 0, "b": 0})

    return fig

# -----------------------------
# Callback
# -----------------------------
@app.callback(
    Output("us-map", "figure"),
    Output("top-states", "children"),
    Output("state-info", "children"),
    Output("state-info", "style"),
    Input("btn-red", "n_clicks"),
    Input("btn-green", "n_clicks"),
    Input("btn-redgreen", "n_clicks"),
    Input("btn-white", "n_clicks"),
    Input("us-map", "clickData")
)
def update_map(n_red, n_green, n_redgreen, n_white, clickData):
    ctx = dash.callback_context
    last_trigger = ctx.triggered[-1]["prop_id"].split(".")[0] if ctx.triggered else None

    # -----------------------
    # Reset selection & info panel by default
    # -----------------------
    for s in states_dict.values():
        s.is_selected = False

    info_panel = html.Div()
    info_style = {"display": "none"}

    # -----------------------
    # State click takes precedence
    # -----------------------
    if last_trigger == "us-map" and clickData:
        selected_code = clickData["points"][0]["location"]
        states_dict[selected_code].is_selected = True
        state_obj = states_dict[selected_code]

        info_panel = html.Div([
            html.H4(f"State: {state_obj.code}"),
            html.P(f"Awarded Contracts: {state_obj.red}"),
            html.P(f"Offered Contracts: {state_obj.green}"),
            html.P(f"Combined: {state_obj.combined}")
        ])
        info_style = {
            "position": "absolute",
            "top": "250px",
            "right": "20px",
            "backgroundColor": "white",
            "padding": "12px",
            "border": "1px solid #ccc",
            "borderRadius": "6px",
            "width": "260px",
            "fontFamily": "Arial",
            "fontSize": "14px",
            "display": "block"
        }

        return (
            create_fig(list(states_dict.values()), "red", [[0, "white"], [1, "white"]]),
            html.Div(f"Selected state: {state_obj.code}"),  # rankings panel placeholder
            info_panel,
            info_style
        )

    # -----------------------
    # Reset / White button
    # -----------------------
    if last_trigger == "btn-white":
        return (
            create_fig(list(states_dict.values()), "red", [[0, "white"], [1, "white"]]),
            html.Div("No rankings (white map)"),
            info_panel,
            info_style
        )

    # -----------------------
    # Gradient buttons
    # -----------------------
    if last_trigger == "btn-green":
        top5 = sorted(states_dict.values(), key=lambda s: s.green, reverse=True)[:5]
        panel = html.Div([
            html.H4("Top 5 Green States"),
            html.Ol([html.Li(f"{s.code}: {s.green}") for s in top5])
        ])
        return create_fig(list(states_dict.values()), "green", "Greens"), panel, info_panel, info_style

    if last_trigger == "btn-red":
        top5 = sorted(states_dict.values(), key=lambda s: s.red, reverse=True)[:5]
        panel = html.Div([
            html.H4("Top 5 Red States"),
            html.Ol([html.Li(f"{s.code}: {s.red}") for s in top5])
        ])
        return create_fig(list(states_dict.values()), "red", "Reds"), panel, info_panel, info_style

    if last_trigger == "btn-redgreen":
        for s in states_dict.values():
            s.combined_value = s.combined

        top5_green = sorted(states_dict.values(), key=lambda s: s.combined_value, reverse=True)[:5]
        top5_red = sorted(states_dict.values(), key=lambda s: s.combined_value)[:5]

        panel = html.Div([
            html.H4("Most Extreme"),
            html.Div([
                html.H5("🟢 More Offered"),
                html.Ol([html.Li(f"{s.code}: +{s.combined_value}") for s in top5_green])
            ], style={"marginBottom": "10px"}),
            html.Div([
                html.H5("🔴 More Completed"),
                html.Ol([html.Li(f"{s.code}: {s.combined_value}") for s in top5_red])
            ])
        ])

        # combined_norm = [(s.combined - min([s.combined for s in states_dict.values()])) /
        #                  (max([s.combined for s in states_dict.values()]) -
        #                   min([s.combined for s in states_dict.values()])) for s in states_dict.values()]

        return create_fig(list(states_dict.values()), "combined_value", [[0,"red"], [0.5,"white"], [1,"green"]]), panel, info_panel, info_style

    # -----------------------
    # Fallback
    # -----------------------
    return (
        create_fig(list(states_dict.values()), "red", [[0, "white"], [1, "white"]]),
        html.Div("Click a gradient button or state to see rankings"),
        info_panel,
        info_style
    )

# -----------------------------
# Run app
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)

#TODO: add top 3 most completed and awarded for each state
#TODO: add gradient on only selected state
#TODO: add live data filters
#TODO: add top cities when a state is selected