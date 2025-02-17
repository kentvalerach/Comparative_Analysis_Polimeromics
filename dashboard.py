import dash
from dash import dcc, html, Input, Output, State
import polars as pl
import plotly.graph_objs as go
import os
import urllib.request

DATA_DIR = "data"
COMBINED_DATA_PATH = os.path.join(DATA_DIR, "combined_data.csv")

# Crear la carpeta 'data' si no existe
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

# Verificar si el archivo no está en Railway y descargarlo desde GitHub
if not os.path.exists(COMBINED_DATA_PATH):
    github_url = "https://raw.githubusercontent.com/kentvalerach/Comparative_Analysis_Polimeromics/main/data/combined_data.csv"
    print(f"Descargando datos desde {github_url}...")
    urllib.request.urlretrieve(github_url, COMBINED_DATA_PATH)
    print("Archivo descargado exitosamente.")

# Verificar si el archivo realmente existe y mostrar su contenido
if os.path.exists(COMBINED_DATA_PATH):
    print(f"✅ Archivo encontrado: {COMBINED_DATA_PATH}")
else:
    print("❌ Error: El archivo no fue encontrado en la carpeta data/")

# Cargar los datos combinados desde el archivo preprocesado
combined_data = None
try:
    print("Cargando datos combinados desde archivo local...")
    combined_data = pl.read_csv(
        COMBINED_DATA_PATH, 
        dtypes={"identifier_id": str},  # Forzar la columna identifier_id como string
        ignore_errors=True  # Ignorar errores de conversión
    )
    print(f"Archivo combinado cargado con {len(combined_data)} registros y {len(combined_data.columns)} columnas.")
    print("Nombres de columnas disponibles en combined_data:")
    print(combined_data.columns)
    combined_data = combined_data.to_pandas()

    # Renombrar columnas para que coincidan con lo esperado por el dashboard
    rename_mapping = {
        "symbol": "official_symbol",
        "unique_i": "unique_id_x",
        "entry_id": "entry_id",
        "macromolecule": "macromolecule_name"
    }
    combined_data.rename(columns={k: v for k, v in rename_mapping.items() if k in combined_data.columns}, inplace=True)
    print("Columnas después de renombrar:", combined_data.columns.tolist())

except Exception as e:
    print(f"Error al cargar el archivo combinado: {e}")
    combined_data = None

if combined_data is None or combined_data.empty:
    print("⚠️ Advertencia: El dataframe combinado está vacío. Revisa el archivo en la carpeta data.")

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
            html.Div([
                html.H3("Biomedical and Genetic Insights"),
                html.P("The data presented in this dashboard integrates molecular interaction information (BIOGRID) "
                       "and structural details of macromolecules (RCSB PDB). This combination offers valuable insights "
                       "into the genetic and biochemical mechanisms underlying human physiology and disease."),
                html.P("Potential biomedical applications include:"),
                html.Ul([
                    html.Li("**Drug Discovery**: Identifying potential drug targets by analyzing protein structures and "
                            "their interaction patterns."),
                    html.Li("**Gene Function Analysis**: Elucidating the functional roles of genes and proteins in "
                            "biological pathways by studying interaction networks."),
                    html.Li("**Precision Medicine**: Supporting personalized therapeutic approaches by linking structural "
                            "variations to specific genetic markers.")
                ]),
                html.P("A unique aspect of this analysis is the integration of two comprehensive datasets—BIOGRID and RCSB PDB—which allows "
                       "for predictive modeling. The presence of an objective variable, **HIT**, provides a foundation for "
                       "machine learning approaches to predict key biological interactions. Additionally, the inclusion of "
                       "structural and functional information on macromolecules like **Notum** and **Furin** enhances the ability "
                       "to explore critical biochemical pathways."),
                html.P("This data-driven approach empowers researchers to uncover novel therapeutic strategies and "
                       "enhance our understanding of human biology at a molecular level by linking genetic insights with macromolecular data." 
                       "You can access the Python script in the repository https://github.com/kentvalerach/Polimeromic")
            ], style={
                'marginTop': '20px',
                'padding': '10px',
                'border': '1px solid black',
                'backgroundColor': '#f9f9f9',
                'lineHeight': '1.6'
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
    # Determine the current index
    if current_index is None:
        current_index = 0
    else:
        current_index = int(current_index.split(": ")[1])

    # Adjust the index based on button clicks
    new_index = current_index + (1 if next_clicks > prev_clicks else -1)
    new_index = max(0, min(len(combined_data) - 1, new_index))

    # Get the current record
    current_record = combined_data.iloc[new_index]

    # BIOGRID details: show all columns
    biogrid_details = "\n".join([
        f"{col}: {current_record.get(col, 'N/A')}" for col in biogrid_data.columns
    ])

    # RCSB details: show all columns with special handling for long rows
    rcsb_details = "\n".join([
        f"{col}: {current_record.get(col, 'N/A')}" if col not in ['crystal_growth_procedure', 'structure_title']
        else f"{col}: {current_record[col][:100]}..."  # Limit long rows to 100 characters
        for col in rcsb_data.columns
    ])

    # Dynamic Graphs with context and highlighted point
    comparison_plot_1 = {
        'data': [
            {'x': rcsb_data["percent_solvent_content"],
             'y': rcsb_data["ph"],
             'mode': 'markers',
             'marker': {'color': 'lightblue', 'size': 8},
             'name': 'All Records'},
            {'x': [current_record["percent_solvent_content"]],
             'y': [current_record["ph"]],
             'mode': 'markers',
             'marker': {'color': 'blue', 'size': 12, 'symbol': 'star'},
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
            {'x': rcsb_data["temp_k"],
             'y': rcsb_data["molecular_weight"],
             'mode': 'markers',
             'marker': {'color': 'lightgreen', 'size': 8},
             'name': 'All Records'},
            {'x': [current_record["temp_k"]],
             'y': [current_record["molecular_weight"]],
             'mode': 'markers',
             'marker': {'color': 'green', 'size': 12, 'symbol': 'star'},
             'name': 'Selected Record'},
        ],
        'layout': {
            'title': 'Temperature (K) vs Molecular Weight',
            'xaxis': {'title': 'Temp (K)'},
            'yaxis': {'title': 'Molecular Weight'}
        }
    }

    return f"Current index: {new_index}", biogrid_details, rcsb_details, comparison_plot_1, comparison_plot_2

# Run the app

server = app.server


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
