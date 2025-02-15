import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
import plotly.graph_objs as go
from sqlalchemy import create_engine
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

def fetch_record(offset):
    """Consulta optimizada con JOIN en SQL para obtener un solo registro a la vez."""
    query = f"""
    SELECT * FROM biogrid_homosapiens 
    INNER JOIN rcsb_pdb 
    ON LOWER(biogrid_homosapiens.official_symbol) = LOWER(rcsb_pdb.macromolecule_name)
    LIMIT 1 OFFSET {offset};
    """
    conn = engine.connect()
    try:
        return pd.read_sql_query(query, conn)
    finally:
        conn.close()  # ✅ Cierra la conexión después de la consulta

# Inicializar Dash app
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Controles de navegación
    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0),
        html.Button("Next", id='next-button', n_clicks=0),
        html.Div(id='record-index', style={'marginTop': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Contenedor principal (2 columnas)
    html.Div([
        # Columna izquierda: Gráficos y datos de BIOGRID
        html.Div([
            html.H3("Comparison Graphs"),
            dcc.Graph(id='comparison-plot-1'),
            dcc.Graph(id='comparison-plot-2'),
            html.H3("BIOGRID Data"),
            html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

        # Columna derecha: Datos de RCSB y descripción
        html.Div([
            html.H3("RCSB Data"),
            html.Pre(id='rcsb-details', style={
                'border': '1px solid black',
                'padding': '10px',
                'overflowY': 'scroll',
                'maxHeight': '300px'
            }),
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
    """Actualiza el dashboard al navegar entre registros."""
    
    # Si no hay índice actual, empieza en 0
    current_index = 0 if current_index is None else int(current_index.split(": ")[1])

    # Ajustar el índice según el botón presionado
    new_index = max(0, current_index + (1 if next_clicks > prev_clicks else -1))

    # Obtener el registro actual con paginación SQL
    record = fetch_record(new_index)
    if record.empty:
        return f"Current index: {new_index}", "No data", "No data", {}, {}

    # BIOGRID Details
    biogrid_details = "\n".join([f"{col}: {record.iloc[0][col]}" for col in record.columns if "biogrid" in col])

    # RCSB Details
    rcsb_details = "\n".join([
        f"{col}: {record.iloc[0][col]}" if len(str(record.iloc[0][col])) < 100 else f"{col}: {str(record.iloc[0][col])[:100]}..."
        for col in record.columns if "rcsb" in col
    ])

    # Gráfico 1: Relación entre `percent_solvent_content` y `ph`
    comparison_plot_1 = {
        'data': [
            go.Scattergl(
                x=[record.iloc[0]["percent_solvent_content"]],
                y=[record.iloc[0]["ph"]],
                mode='markers',
                marker={'color': 'blue', 'size': 12, 'symbol': 'star'},
                name='Selected Record'
            )
        ],
        'layout': {
            'title': 'Percent Solvent Content vs pH',
            'xaxis': {'title': 'Percent Solvent Content'},
            'yaxis': {'title': 'pH'}
        }
    }

    # Gráfico 2: Relación entre `temp_k` y `molecular_weight`
    comparison_plot_2 = {
        'data': [
            go.Scattergl(
                x=[record.iloc[0]["temp_k"]],
                y=[record.iloc[0]["molecular_weight"]],
                mode='markers',
                marker={'color': 'green', 'size': 12, 'symbol': 'star'},
                name='Selected Record'
            )
        ],
        'layout': {
            'title': 'Temperature (K) vs Molecular Weight',
            'xaxis': {'title': 'Temp (K)'},
            'yaxis': {'title': 'Molecular Weight'}
        }
    }

    return f"Current index: {new_index}", biogrid_details, rcsb_details, comparison_plot_1, comparison_plot_2

# Ejecutar la aplicación
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
