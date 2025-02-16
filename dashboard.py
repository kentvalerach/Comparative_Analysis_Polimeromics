import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from sqlalchemy import create_engine
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

# Consulta SQL optimizada con JOIN directo para reducir carga en RAM
query = """
SELECT 
    b.*, 
    r.* 
FROM biogrid_homosapiens AS b
INNER JOIN rcsb_pdb AS r
ON LOWER(TRIM(b.official_symbol)) = LOWER(TRIM(r.macromolecule_name))
"""

try:
    # Cargar datos por partes en lugar de todo a la vez
    combined_data = pd.read_sql_query(query, engine, chunksize=1000)  # Cargar en fragmentos
    combined_data = pd.concat(combined_data, ignore_index=True)  # Unir fragmentos
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
])

@app.callback(
    [Output('record-index', 'children'),
     Output('biogrid-details', 'children'),
     Output('rcsb-details', 'children')],
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

    biogrid_details = "\n".join([f"{col}: {current_record.get(col, 'N/A')}" for col in combined_data.columns if col.startswith("b_")])
    rcsb_details = "\n".join([f"{col}: {current_record.get(col, 'N/A')}" for col in combined_data.columns if col.startswith("r_")])

    return f"Current index: {new_index}", biogrid_details, rcsb_details

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

