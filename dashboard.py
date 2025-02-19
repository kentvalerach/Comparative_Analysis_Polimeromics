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
            dcc.Graph(id='comparison-plot-2'),
            html.Div([
                html.H3("BIOGRID_Homosapiens Data"),
                html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
            ], style={'border': '1px solid black', 'padding': '10px', 'marginTop': '20px'})
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),
        
        # Right column: RCSB data and insights
        html.Div([
            html.Div([
                html.H3("RCSB_PDB Data"),
                html.Pre(id='rcsb-details', style={'border': '1px solid black', 'padding': '10px', 'overflowY': 'scroll', 'maxHeight': '300px'}),
            ], style={'border': '1px solid black', 'padding': '10px', 'marginTop': '20px'}),
            
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
                html.P("This is an independent Bioinformatics study by Kent Valera Chirinos.  "
                "The project combines data from two main sources: BIOGRID a database focused on molecular interactions," 
                " in particular genes and proteins relevant to Homo sapiens. RCSB PDB a repository of structural and biophysical" 
                " data on macromolecules, including proteins and nucleic acids. You can access the scripts and data"),
                html.A(" Kent Valera Chirinos, Repository" , href="https://github.com/kentvalerach"),           
            ], style={'border': '1px solid black', 'padding': '10px', 'marginTop': '20px'})
        ], style={'width': '45%', 'float': 'right', 'padding': '10px'})
    ], style={'display': 'flex', 'justifyContent': 'space-between'})
])
# Callback para actualizar datos
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

    # Ajustar correctamente el índice de navegación
    if next_clicks > prev_clicks:
        new_index = min(len(combined_data) - 1, current_index + 1)  # Avanzar con "Next"
    elif prev_clicks > next_clicks:
        new_index = max(0, current_index - 1)  # Retroceder con "Previous"
    else:
        new_index = current_index  # Mantenerse en el mismo índice si no se presiona nada

    current_record = combined_data.iloc[new_index]

    biogrid_details = "\n".join([f"{col}: {current_record[col]}" for col in combined_data.columns[:8]])
    rcsb_details = "\n".join([f"{col}: {current_record[col]}" for col in combined_data.columns[9:]])

    return f"Current index: {new_index}", biogrid_details, rcsb_details


# Callbacks para actualizar graficos
@app.callback(
    [Output('comparison-plot-1', 'figure'),
     Output('comparison-plot-2', 'figure')],
    [Input('prev-button', 'n_clicks'),
     Input('next-button', 'n_clicks')],
    [State('record-index', 'children')]
)
def update_graphs(prev_clicks, next_clicks, current_index):
    if combined_data is None or combined_data.empty:
        return go.Figure(), go.Figure()

    if current_index is None:
        current_index = 0
    else:
        current_index = int(current_index.split(": ")[1])

    new_index = max(0, min(len(combined_data) - 1, current_index + (1 if next_clicks > prev_clicks else -1)))
    current_record = combined_data.iloc[new_index]

    # Gráfico 1: Molecular Weight vs pH
    figure1 = go.Figure()

    # Agregar todos los puntos en color verde claro
    figure1.add_trace(go.Scatter(
        x=combined_data['molecular_weight'],
        y=combined_data['ph'],
        mode='markers',
        marker=dict(size=8, color='lightgreen', symbol='circle'),
        name="All Data"
    ))

    # Agregar el punto seleccionado con un sombreado en estrella (verde más oscuro)
    figure1.add_trace(go.Scatter(
        x=[current_record['molecular_weight']],
        y=[current_record['ph']],
        mode='markers',
        marker=dict(size=14, color='darkgreen', symbol='star'),
        name="Selected Data"
    ))

    figure1.update_layout(
        title='Molecular Weight vs pH',
        xaxis_title='Molecular Weight',
        yaxis_title='pH',
        plot_bgcolor='white'  # Quitar el fondo azul cuadriculado
    )

    # Gráfico 2: Temperature vs Molecular Weight
    figure2 = go.Figure()

    # Agregar todos los puntos en color azul claro
    figure2.add_trace(go.Scatter(
        x=combined_data['temp_k'],
        y=combined_data['molecular_weight'],
        mode='markers',
        marker=dict(size=8, color='lightblue', symbol='circle'),
        name="All Data"
    ))

    # Agregar el punto seleccionado con un sombreado en estrella (azul más oscuro)
    figure2.add_trace(go.Scatter(
        x=[current_record['temp_k']],
        y=[current_record['molecular_weight']],
        mode='markers',
        marker=dict(size=14, color='blue', symbol='star'),
        name="Selected Data"
    ))

    figure2.update_layout(
        title='Temperature vs Molecular Weight',
        xaxis_title='Temperature (K)',
        yaxis_title='Molecular Weight',
        plot_bgcolor='white'  # Quitar el fondo azul cuadriculado
    )

    return figure1, figure2


server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)
