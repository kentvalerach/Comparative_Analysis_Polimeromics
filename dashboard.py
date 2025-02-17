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
    
    # Leer los archivos CSV con Polars asegurando inferencia correcta de tipos
    biogrid_data = pl.read_csv(BIOGRID_PATH, infer_schema_length=10000, try_parse_dates=True)
    rcsb_data = pl.read_csv(RCSB_PATH, infer_schema_length=10000, try_parse_dates=True)
    
    print("Datos cargados exitosamente. Verificando datos...")
    print(f"Registros en BIOGRID: {len(biogrid_data)}")
    print(f"Registros en RCSB: {len(rcsb_data)}")

    # Asegurar que las claves de unión sean de tipo String
    biogrid_data = biogrid_data.with_columns(pl.col("official_symbol").cast(pl.Utf8).str.strip_chars().str.to_lowercase())
    rcsb_data = rcsb_data.with_columns(pl.col("macromolecule_name").cast(pl.Utf8).str.strip_chars().str.to_lowercase())

    # Convertir columnas problemáticas a Float64 antes del JOIN para evitar errores
    problematic_columns = ["number_of_water_molecules", "molecular_weight"]
    for col in problematic_columns:
        if col in rcsb_data.columns:
            rcsb_data = rcsb_data.with_columns(pl.col(col).cast(pl.Float64, strict=False))

    print("Realizando JOIN...")
    
    # Realizar el merge (INNER JOIN) en Polars
    combined_data = biogrid_data.join(
        rcsb_data, 
        left_on="official_symbol", 
        right_on="macromolecule_name", 
        how="inner"
    )
    
    # Validar que haya registros en el conjunto combinado
    if len(combined_data) == 0:
        raise ValueError("El JOIN no generó registros. Verifica los datos de entrada.")
    
    # Limitar la carga a solo el 10% de los datos después del JOIN
    combined_data = combined_data.sample(fraction=0.1, seed=42)

    print(f"JOIN completado. Registros combinados: {len(combined_data)}")
    print(combined_data.head(5))  # Muestra las primeras 5 filas del dataset combinado

except Exception as e:
    print(f"Error al cargar y combinar los datos: {e}")
    combined_data = None

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
    global combined_data  # Asegurar acceso a la variable global

    if combined_data is None or len(combined_data) == 0:
        return "No data available", "", "", {}, {}

    # Convertir a Pandas antes de usar .iloc
    combined_data_pd = combined_data.to_pandas()

    # Determinar el índice actual
    if current_index is None:
        current_index = 0
    else:
        current_index = int(current_index.split(": ")[1])

    # Ajustar el índice basado en los botones
    new_index = current_index + (1 if next_clicks > prev_clicks else -1)
    new_index = max(0, min(len(combined_data_pd) - 1, new_index))

    # Obtener el registro actual
    current_record = combined_data_pd.iloc[new_index]

    # BIOGRID details: mostrar todas las columnas
    biogrid_details = "\n".join([
        f"{col}: {current_record.get(col, 'N/A')}" for col in biogrid_data.columns
    ])

    # RCSB details: mostrar todas las columnas
    rcsb_details = "\n".join([
        f"{col}: {current_record.get(col, 'N/A')}" for col in rcsb_data.columns
    ])

    # Gráficos dinámicos con contexto y punto resaltado
    comparison_plot_1 = {
        'data': [
            {'x': combined_data_pd["percent_solvent_content"],
             'y': combined_data_pd["ph"],
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
            {'x': combined_data_pd["temp_k"],
             'y': combined_data_pd["molecular_weight"],
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

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
