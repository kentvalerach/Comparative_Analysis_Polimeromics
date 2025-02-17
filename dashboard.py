import dash
from dash import dcc, html, Input, Output, State
import polars as pl
import plotly.graph_objs as go
import os

DATA_DIR = "C:/Polimeromics/data/exported_data/"
BIOGRID_PATH = os.path.join(DATA_DIR, "biogrid_homosapiens.csv")
RCSB_PATH = os.path.join(DATA_DIR, "rcsb_pdb.csv")

try:
    print("Cargando datos desde archivos locales con Polars...")
    
    # Leer los archivos CSV con Polars
    biogrid_data = pl.read_csv(BIOGRID_PATH)
    rcsb_data = pl.read_csv(RCSB_PATH)
    
    print("Datos cargados exitosamente. Realizando JOIN...")
    
    # Normalizar claves para evitar problemas de espacios y mayúsculas
    biogrid_data = biogrid_data.with_columns(pl.col("official_symbol").str.to_lowercase().str.strip())
    rcsb_data = rcsb_data.with_columns(pl.col("macromolecule_name").str.to_lowercase().str.strip())
    
    # Realizar el merge (INNER JOIN) en Polars
    combined_data = biogrid_data.join(
        rcsb_data, 
        left_on="official_symbol", 
        right_on="macromolecule_name", 
        how="inner"
    )
    
    # Limitar la carga a solo el 10% de los datos después del JOIN
    combined_data = combined_data.sample(fraction=0.1, seed=42)
    
    print(f"JOIN completado. Registros combinados: {len(combined_data)}")
    
    # Convertir a pandas para Dash
    combined_data = combined_data.to_pandas()
except Exception as e:
    print(f"Error al cargar y combinar los datos: {e}")
    combined_data = None

if combined_data is None or combined_data.empty:
    print("⚠️ Advertencia: El dataframe combinado está vacío. Revisa los archivos en la carpeta.")

# Initialize Dash app
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0),
        html.Button("Next", id='next-button', n_clicks=0),
        html.Div(id='record-index', style={'marginTop': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    html.Div([
        html.Div([
            html.H3("Comparison Graphs"),
            dcc.Graph(id='comparison-plot-1'),
            dcc.Graph(id='comparison-plot-2'),
            html.H3("BIOGRID Data"),
            html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

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
        print("❌ No hay datos disponibles en el DataFrame")
        return "No data available", "No BIOGRID data", "No RCSB data", go.Figure(), go.Figure()

    if current_index is None or isinstance(current_index, str):
        current_index = 0
    else:
        try:
            current_index = int(current_index.split(": ")[-1])
        except ValueError:
            current_index = 0

    new_index = current_index + (1 if next_clicks > prev_clicks else -1)
    new_index = max(0, min(len(combined_data) - 1, new_index))

    current_record = combined_data.iloc[new_index]
    print("Registro actual:", current_record.to_dict())

    biogrid_symbol = current_record.get('official_symbol', 'N/A')
    biogrid_id = current_record.get('unique_id_x', 'N/A')
    rcsb_entry = current_record.get('entry_id', 'N/A')
    rcsb_macro = current_record.get('macromolecule_name', 'N/A')

    biogrid_details = f"Official Symbol: {biogrid_symbol}\nUnique ID: {biogrid_id}"
    rcsb_details = f"Entry ID: {rcsb_entry}\nMacromolecule: {rcsb_macro}"

    return f"Current index: {new_index}", biogrid_details, rcsb_details, go.Figure(), go.Figure()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
