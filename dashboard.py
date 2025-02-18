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
    SELECT biogrid_homosapiens.official_symbol, biogrid_homosapiens.identifier_id,
           biogrid_homosapiens.identifier_type, biogrid_homosapiens.aliases,
           rcsb_pdb.macromolecule_name, rcsb_pdb.experimental_method,
           rcsb_pdb.molecular_weight, rcsb_pdb.ph, rcsb_pdb.temp_k
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
if combined_data is not None:
    combined_data = combined_data.sample(frac=0.1, random_state=42)
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
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px', 'color': '#2c3e50'}),
    
    # Record navigation
    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0, style={'backgroundColor': '#3498db', 'color': 'white', 'border': 'none', 'padding': '10px 20px', 'marginRight': '10px'}),
        html.Button("Next", id='next-button', n_clicks=0, style={'backgroundColor': '#2ecc71', 'color': 'white', 'border': 'none', 'padding': '10px 20px'}),
        html.Div(id='record-index', style={'marginTop': '10px', 'color': '#34495e', 'fontWeight': 'bold'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Main container split into two columns
    html.Div([
        html.Div([
            html.H3("Comparison Graphs", style={'color': '#16a085'}),
            dcc.Graph(id='comparison-plot-1'),
            dcc.Graph(id='comparison-plot-2'),
            html.H3("BIOGRID Data", style={'color': '#e67e22'}),
            html.Pre(id='biogrid-details', style={'border': '1px solid #e67e22', 'padding': '10px', 'backgroundColor': '#fdf2e9'}),
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

        html.Div([
            html.H3("RCSB Data", style={'color': '#8e44ad'}),
            html.Pre(id='rcsb-details', style={
                'border': '1px solid #8e44ad',
                'padding': '10px',
                'overflowY': 'scroll',
                'maxHeight': '300px',
                'backgroundColor': '#f4ecf7'
            }),
        ], style={'width': '45%', 'float': 'right', 'padding': '10px'}),
    ], style={'display': 'flex', 'justifyContent': 'space-between'}),
])

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
