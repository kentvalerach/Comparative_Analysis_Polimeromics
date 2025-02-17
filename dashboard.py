import dash
from dash import dcc, html, Input, Output, State
import polars as pl
import plotly.graph_objs as go
import os

# Definir rutas de los archivos en la carpeta data/
BIOGRID_PATH = "data/biogrid_homosapiens.csv"
RCSB_PATH = "data/rcsb_pdb.csv"

# Cargar los datos desde los archivos en lugar de la base de datos
try:
    print("Cargando datos desde archivos locales...")

    # Leer los archivos CSV con Polars
    biogrid_data = pl.read_csv(BIOGRID_PATH)
    rcsb_data = pl.read_csv(RCSB_PATH)

    print(f"BIOGRID Data: {len(biogrid_data)} registros cargados.")
    print(f"RCSB Data: {len(rcsb_data)} registros cargados.")

    # Ver primeras filas de los datasets para depuración
    print("BIOGRID Data Sample:")
    print(biogrid_data.head())
    print("RCSB Data Sample:")
    print(rcsb_data.head())

    print("Normalizando claves...")
    
    # Normalizar claves para evitar problemas de espacios y mayúsculas
    biogrid_data = biogrid_data.with_columns(
        pl.col("official_symbol").str.to_lowercase().str.strip()
    )
    rcsb_data = rcsb_data.with_columns(
        pl.col("macromolecule_name").str.to_lowercase().str.strip()
    )

    print("Realizando JOIN...")

    # Realizar el merge (INNER JOIN) en Polars
    combined_data = biogrid_data.join(
        rcsb_data, 
        left_on="official_symbol", 
        right_on="macromolecule_name", 
        how="inner"
    )

    print(f"JOIN completado. Registros combinados: {len(combined_data)}")
    
    # Verificar contenido de los datos combinados
    print("Combined Data Sample:")
    print(combined_data.head())

except Exception as e:
    print(f"Error al cargar y combinar los datos: {e}")
    combined_data = None

# Convertir el dataframe de Polars a Pandas si tiene datos
if combined_data is not None and len(combined_data) > 0:
    combined_data = combined_data.to_pandas()
else:
    print("Advertencia: El dataframe combinado está vacío. Revisa los datos de entrada y las claves de combinación.")

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
        # Left column: Graphs and BIOGRID data
        html.Div([
            html.H3("Comparison Graphs"),
            dcc.Graph(id='comparison-plot-1'),
            dcc.Graph(id='comparison-plot-2'),
            html.H3("BIOGRID Data"),
            html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

        # Right column: RCSB data and insights
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
    rcsb_details = f"Entry ID: {current_record['entry_id']}\nMacromolecule: {current_record['macromolecule_name']}"

    return f"Current index: {new_index}", biogrid_details, rcsb_details, {}, {}

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

    



