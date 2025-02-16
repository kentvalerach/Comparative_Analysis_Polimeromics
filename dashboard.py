import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
import os

# Definir la ruta del archivo CSV
DATA_PATH = "data/combined_data.csv"

# Cargar los datos desde el CSV en lugar de la base de datos
try:
    print("Cargando datos combinados desde archivo local...")
    combined_data = pd.read_csv(DATA_PATH)
    print(f"Archivo cargado con {len(combined_data)} registros.")
except Exception as e:
    print(f"Error al cargar el archivo de datos: {e}")
    combined_data = None

# Inicializar la app de Dash
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0),
        html.Button("Next", id='next-button', n_clicks=0),
        html.Div(id='record-index', style={'marginTop': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        html.Div([
            html.H3("BIOGRID Data"),
            html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
            html.H3("RCSB Data"),
            html.Pre(id='rcsb-details', style={'border': '1px solid black', 'padding': '10px'}),
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

        html.Div([
            html.H3("Comparison Graphs"),
            dcc.Graph(id='comparison-plot-1'),
            dcc.Graph(id='comparison-plot-2'),
        ], style={'width': '45%', 'float': 'right', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'space-between'}),
])

@app.callback(
    [Output('record-index', 'children'),
     Output('biogrid-details', 'children'),
     Output('rcsb-details', 'children'),
     Output('comparison-plot-1', 'figure'),
     Output('comparison-plot-2', 'figure')],
    [Input('prev-button', 'n_clicks'),
     Input('next-button', 'n_clicks')],
    [State('record-index', 'children')]
)
def update_dashboard(prev_clicks, next_clicks, current_index):
    if combined_data is None or combined_data.empty:
        return "No data available", "No BIOGRID data", "No RCSB data", {}, {}

    if current_index is None:
        current_index = 0
    else:
        current_index = int(current_index.split(": ")[1])

    new_index = current_index + (1 if next_clicks > prev_clicks else -1)
    new_index = max(0, min(len(combined_data) - 1, new_index))

    current_record = combined_data.iloc[new_index]

    biogrid_details = f"Official Symbol: {current_record['official_symbol']}\nUnique ID: {current_record['unique_id']}"
    rcsb_details = f"Entry ID: {current_record['entry_id']}\nMacromolecule: {current_record['ligand_name']}"

    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=combined_data["percent_solvent_content"], 
        y=combined_data["ph"],
        mode='markers',
        marker=dict(color='lightblue', size=6),
        name='All Records'
    ))
    fig1.add_trace(go.Scatter(
        x=[current_record["percent_solvent_content"]],
        y=[current_record["ph"]],
        mode='markers',
        marker=dict(color='red', size=12, symbol='star'),
        name="Selected Record"
    ))
    fig1.update_layout(title='Percent Solvent Content vs pH', xaxis_title='Percent Solvent Content', yaxis_title='pH')

    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(
        x=combined_data["temp_k"], 
        y=combined_data["molecular_weight"],
        mode='markers',
        marker=dict(color='lightgreen', size=6),
        name='All Records'
    ))
    fig2.add_trace(go.Scatter(
        x=[current_record["temp_k"]],
        y=[current_record["molecular_weight"]],
        mode='markers',
        marker=dict(color='red', size=12, symbol='star'),
        name="Selected Record"
    ))
    fig2.update_layout(title='Temperature (K) vs Molecular Weight', xaxis_title='Temp (K)', yaxis_title='Molecular Weight')

    return f"Current index: {new_index}", biogrid_details, rcsb_details, fig1, fig2

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)


