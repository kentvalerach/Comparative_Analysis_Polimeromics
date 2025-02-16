import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from sqlalchemy import create_engine
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

try:
    # Usar la base de datos con `chunksize` para reducir uso de memoria
    biogrid_query = "SELECT official_symbol, unique_id FROM biogrid_homosapiens"
    rcsb_query = "SELECT macromolecule_name, unique_id, percent_solvent_content, ph, temp_k, molecular_weight FROM rcsb_pdb"

    # Leer los datos en lotes más pequeños
    biogrid_data = pd.read_sql_query(biogrid_query, engine)
    rcsb_data = pd.read_sql_query(rcsb_query, engine)

    print("Datos cargados exitosamente.")

    # Convertir claves de merge a minúsculas y quitar espacios
    biogrid_data["official_symbol"] = biogrid_data["official_symbol"].str.lower().str.strip()
    rcsb_data["macromolecule_name"] = rcsb_data["macromolecule_name"].str.lower().str.strip()

    # Realizar el merge en chunks para evitar gran uso de RAM
    combined_data = biogrid_data.merge(rcsb_data, left_on="official_symbol", right_on="macromolecule_name", how="inner")

    print(f"Merged {len(combined_data)} records.")

except Exception as e:
    print(f"Error al cargar los datos: {e}")
    biogrid_data = None
    rcsb_data = None
    combined_data = None

# Mantener estructura original
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Navegación por registros
    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0),
        html.Button("Next", id='next-button', n_clicks=0),
        html.Div(id='record-index', style={'marginTop': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        html.Div([
            html.H3("BIOGRID Data"),
            html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

        html.Div([
            html.H3("RCSB Data"),
            html.Pre(id='rcsb-details', style={'border': '1px solid black', 'padding': '10px'}),
        ], style={'width': '45%', 'float': 'right', 'padding': '10px'}),
    ], style={'display': 'flex'}),

    html.Div([
        html.H3("Comparison Graphs"),
        dcc.Graph(id='comparison-plot-1'),
        dcc.Graph(id='comparison-plot-2'),
    ], style={'width': '80%', 'margin': 'auto'}),
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

    biogrid_details = f"Official Symbol: {current_record['official_symbol']}\nUnique ID: {current_record['unique_id_x']}"
    rcsb_details = f"Macromolecule: {current_record['macromolecule_name']}\nUnique ID: {current_record['unique_id_y']}"

    # Gráficos optimizados
    comparison_plot_1 = {
        'data': [
            {'x': combined_data["percent_solvent_content"],
             'y': combined_data["ph"],
             'mode': 'markers',
             'marker': {'color': 'lightblue', 'size': 6},
             'name': 'All Records'},
            {'x': [current_record["percent_solvent_content"]],
             'y': [current_record["ph"]],
             'mode': 'markers',
             'marker': {'color': 'red', 'size': 10, 'symbol': 'star'},
             'name': 'Selected Record'},
        ],
        'layout': {
            'title': 'Percent Solvent Content vs pH',
            'xaxis': {'title': 'Percent Solvent Content'},
            'yaxis': {'title': 'pH'}
        }
    }

    comparison_plot_2 = {
        'data': [
            {'x': combined_data["temp_k"],
             'y': combined_data["molecular_weight"],
             'mode': 'markers',
             'marker': {'color': 'lightgreen', 'size': 6},
             'name': 'All Records'},
            {'x': [current_record["temp_k"]],
             'y': [current_record["molecular_weight"]],
             'mode': 'markers',
             'marker': {'color': 'red', 'size': 10, 'symbol': 'star'},
             'name': 'Selected Record'},
        ],
        'layout': {
            'title': 'Temperature (K) vs Molecular Weight',
            'xaxis': {'title': 'Temp (K)'},
            'yaxis': {'title': 'Molecular Weight'}
        }
    }

    return f"Current index: {new_index}", biogrid_details, rcsb_details, comparison_plot_1, comparison_plot_2

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)



