import dash
from dash import dcc, html, Input, Output, State
import polars as pl
import plotly.graph_objs as go
import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("No se encontró la variable de entorno DATABASE_URL")

# Conectar a PostgreSQL en Railway
engine = create_engine(DATABASE_URL)

try:
    print("Conectando a PostgreSQL en Railway...")
    conn = engine.connect()
    print("Conexión exitosa.")
except Exception as e:
    print(f"Error al conectar a PostgreSQL: {e}")
    exit()

# Realizar el JOIN en SQL directamente en PostgreSQL
join_query = """
    SELECT biogrid_homosapiens.*, rcsb_pdb.*
    FROM biogrid_homosapiens
    INNER JOIN rcsb_pdb
    ON LOWER(TRIM(biogrid_homosapiens.official_symbol)) = LOWER(TRIM(rcsb_pdb.macromolecule_name))
    LIMIT 5000
"""

try:
    print("Ejecutando JOIN en PostgreSQL...")
    combined_data = pd.read_sql(join_query, conn)
    print(f"JOIN completado. Registros combinados: {len(combined_data)}")
except Exception as e:
    print(f"Error al ejecutar el JOIN en PostgreSQL: {e}")
    combined_data = None

# Limitar la carga a solo el 10% de los datos después del JOIN
if combined_data is not None and not combined_data.empty:
    combined_data = combined_data.sample(frac=0.1, random_state=42).reset_index(drop=True)
    print(combined_data.head(5))  # Muestra las primeras 5 filas del dataset combinado

if combined_data is None or combined_data.empty:
    print("⚠️ Error: combined_data está vacío en Dash.")
else:
    print(f"✅ Datos disponibles en Dash: {len(combined_data)} registros.")

# Cerrar conexión
conn.close()

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Record navigation
    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0),
        html.Button("Next", id='next-button', n_clicks=0),
        html.Div(id='record-index', style={'marginTop': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Main container split into two columns
    html.Div([
        html.Div([
            html.H3("Comparison Graphs"),
            dcc.Graph(id='comparison-plot-1'),
            dcc.Graph(id='comparison-plot-2')
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

        html.Div([
            html.Div([
                html.H3("BIOGRID_Homosapiens Data"),
                html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
            ], style={'border': '1px solid black', 'padding': '10px', 'marginBottom': '10px'}),

            html.Div([
                html.H3("RCSB_PDB Data"),
                html.Pre(id='rcsb-details', style={'border': '1px solid black', 'padding': '10px', 'overflowY': 'scroll', 'maxHeight': '300px'}),
            ], style={'border': '1px solid black', 'padding': '10px'})
        ], style={'width': '45%', 'float': 'right', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'space-between'}),
])

@app.callback(
    [Output('record-index', 'children'),
     Output('biogrid-details', 'children'),
     Output('rcsb-details', 'children')],
    [Input('prev-button', 'n_clicks'),
     Input('next-button', 'n_clicks')],
    [State('record-index', 'children')]
)
def update_data(prev_clicks, next_clicks, current_index):
    if combined_data is None or combined_data.empty:
        return "No data available", "", ""

    if current_index is None:
        current_index = 0
    else:
        current_index = int(current_index.split(": ")[1])
    
    new_index = current_index + (1 if next_clicks > prev_clicks else -1)
    new_index = max(0, min(len(combined_data) - 1, new_index))
    
    current_record = combined_data.iloc[new_index]
    
    biogrid_details = "\n".join([f"{col}: {current_record[col]}" for col in combined_data.columns[:6]])
    rcsb_details = "\n".join([f"{col}: {current_record[col]}" for col in combined_data.columns[7:]])

    return f"Current index: {new_index}", biogrid_details, rcsb_details

@app.callback(
    [Output('comparison-plot-1', 'figure'),
     Output('comparison-plot-2', 'figure')],
    [Input('prev-button', 'n_clicks'),
     Input('next-button', 'n_clicks')]
)
def update_graphs(prev_clicks, next_clicks):
    if combined_data is None or combined_data.empty:
        return go.Figure(), go.Figure()

    figure1 = go.Figure(data=[go.Scatter(x=combined_data['molecular_weight'], y=combined_data['ph'], mode='markers')])
    figure1.update_layout(title='Molecular Weight vs pH', xaxis_title='Molecular Weight', yaxis_title='pH')
    
    figure2 = go.Figure(data=[go.Scatter(x=combined_data['temp_k'], y=combined_data['molecular_weight'], mode='markers')])
    figure2.update_layout(title='Temperature vs Molecular Weight', xaxis_title='Temperature (K)', yaxis_title='Molecular Weight')

    return figure1, figure2

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
