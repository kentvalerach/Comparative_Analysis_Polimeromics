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

    print("Datos cargados exitosamente. Realizando JOIN...")

    # Normalizar claves para evitar problemas de espacios y mayúsculas
    biogrid_data = biogrid_data.with_columns(
        pl.col("official_symbol").str.to_lowercase().str.strip()
    )
    rcsb_data = rcsb_data.with_columns(
        pl.col("macromolecule_name").str.to_lowercase().str.strip()
    )

    # Realizar el merge (INNER JOIN) en Polars
    combined_data = biogrid_data.join(
        rcsb_data, 
        left_on="official_symbol", 
        right_on="macromolecule_name", 
        how="inner"
    )

    print(f"JOIN completado. Registros combinados: {len(combined_data)}")

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

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
    



