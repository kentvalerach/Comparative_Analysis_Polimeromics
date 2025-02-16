import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.express as px
from sqlalchemy import create_engine
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

# Consulta SQL optimizada con JOIN directo
query = """
SELECT 
    b.official_symbol, 
    b.unique_id AS unique_id_biogrid, 
    r.macromolecule_name, 
    r.unique_id AS unique_id_rcsb,
    r.percent_solvent_content, 
    r.ph, 
    r.temp_k, 
    r.molecular_weight
FROM biogrid_homosapiens AS b
INNER JOIN rcsb_pdb AS r
ON LOWER(TRIM(b.official_symbol)) = LOWER(TRIM(r.macromolecule_name))
"""

try:
    # Cargar datos con chunksize para evitar uso excesivo de RAM
    combined_data = pd.read_sql_query(query, engine)
    print("Datos combinados cargados exitosamente.")
except Exception as e:
    print(f"Error al cargar los datos combinados: {e}")
    combined_data = None

# Inicializar la app de Dash
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center'}),

    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0),
        html.Button("Next", id='next-button', n_clicks=0),
        html.Div(id='record-index', style={'marginTop': '10px'}),
    ], style={'textAlign': 'center'}),

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
    if current_index is None:
        current_index = 0
    else:
        current_index = int(current_index.split(": ")[1])

    new_index = current_index + (1 if next_clicks > prev_clicks else -1)
    new_index = max(0, min(len(combined_data) - 1, new_index))

    current_record = combined_data.iloc[new_index]

    biogrid_details = f"Official Symbol: {current_record['official_symbol']}\nUnique ID: {current_record['unique_id_biogrid']}"
    rcsb_details = f"Macromolecule: {current_record['macromolecule_name']}\nUnique ID: {current_record['unique_id_rcsb']}"

    # Crear gráficos con Plotly Express
    fig1 = px.scatter(combined_data, x="percent_solvent_content", y="ph",
                      title="Percent Solvent Content vs pH",
                      labels={'percent_solvent_content': 'Percent Solvent Content', 'ph': 'pH'})
    fig1.add_scatter(x=[current_record["percent_solvent_content"]],
                     y=[current_record["ph"]],
                     mode='markers', marker=dict(color='red', size=12), name="Selected Record")

    fig2 = px.scatter(combined_data, x="temp_k", y="molecular_weight",
                      title="Temperature (K) vs Molecular Weight",
                      labels={'temp_k': 'Temperature (K)', 'molecular_weight': 'Molecular Weight'})
    fig2.add_scatter(x=[current_record["temp_k"]],
                     y=[current_record["molecular_weight"]],
                     mode='markers', marker=dict(color='red', size=12), name="Selected Record")

    return f"Current index: {new_index}", biogrid_details, rcsb_details, fig1, fig2

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)


