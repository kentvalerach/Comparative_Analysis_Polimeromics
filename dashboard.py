import dash
from dash import dcc, html, Input, Output, State
import polars as pl
import plotly.graph_objs as go
import os
import psycopg2
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL is None:
    raise ValueError("No se encontró la variable de entorno DATABASE_URL. Asegúrate de configurarla en Railway.")

# Crear el engine de SQLAlchemy con configuración de pool de conexiones
engine = create_engine(DATABASE_URL, poolclass=QueuePool, pool_size=5, max_overflow=10)

try:
    print("Conectando a PostgreSQL en Railway...")
    with engine.connect() as conn:
        print("Conexión exitosa.")

        # Realizar el JOIN en SQL directamente en PostgreSQL
        join_query = """
            SELECT biogrid_homosapiens.official_symbol, 
                   biogrid_homosapiens.identifier_id, 
                   biogrid_homosapiens.identifier_type, 
                   biogrid_homosapiens.aliases,
                   rcsb_pdb.macromolecule_name, 
                   rcsb_pdb.experimental_method, 
                   rcsb_pdb.molecular_weight, 
                   rcsb_pdb.ph, 
                   rcsb_pdb.temp_k
            FROM biogrid_homosapiens
            INNER JOIN rcsb_pdb
            ON LOWER(TRIM(biogrid_homosapiens.official_symbol)) = LOWER(TRIM(rcsb_pdb.macromolecule_name))
            LIMIT 5000;
        """

        print("Ejecutando JOIN en PostgreSQL...")
        combined_data = pd.read_sql(join_query, conn)

        print(f"JOIN completado. Registros combinados: {len(combined_data)}")

        # Limitar la carga a solo el 10% de los datos después del JOIN
        if not combined_data.empty:
            combined_data = combined_data.sample(frac=0.1, random_state=42)
            print(combined_data.head(5))  # Muestra las primeras 5 filas del dataset combinado
        else:
            print("⚠️ Advertencia: No se encontraron registros en el JOIN.")

except Exception as e:
    print(f"Error al ejecutar el JOIN en PostgreSQL: {e}")

finally:
    engine.dispose()  # Cierra la conexión correctamente



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
