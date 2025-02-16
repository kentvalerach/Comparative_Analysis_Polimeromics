import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from sqlalchemy import create_engine, text
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

# 📌 Contar los registros en la base de datos para limitar paginación
def get_total_records():
    query = """
    SELECT COUNT(*) FROM biogrid_homosapiens 
    INNER JOIN rcsb_pdb 
    ON LOWER(TRIM(biogrid_homosapiens.official_symbol)) = LOWER(TRIM(rcsb_pdb.macromolecule_name));
    """
    conn = engine.connect()
    try:
        result = conn.execute(text(query)).fetchone()
        total = result[0] if result else 0
        print(f"🔹 Total registros disponibles en el JOIN: {total}")
        return total
    except Exception as e:
        print(f"🚨 Error al contar registros: {e}")
        return 0
    finally:
        conn.close()

TOTAL_RECORDS = get_total_records()
if TOTAL_RECORDS == 0:
    print("🚨 ERROR: El JOIN no encontró coincidencias.")

# 📌 Función para obtener un solo registro con paginación
def fetch_record(offset):
    query = f"""
    SELECT * FROM biogrid_homosapiens 
    INNER JOIN rcsb_pdb 
    ON LOWER(TRIM(biogrid_homosapiens.official_symbol)) = LOWER(TRIM(rcsb_pdb.macromolecule_name))
    LIMIT 1 OFFSET {offset};
    """
    conn = engine.connect()
    try:
        df = pd.read_sql_query(text(query), conn)
        print(f"✅ Datos recuperados en OFFSET {offset}:")
        print(df.head())  # Debug para verificar si hay datos
        return df
    except Exception as e:
        print(f"🚨 Error al obtener registro en OFFSET {offset}: {e}")
        return pd.DataFrame()
    finally:
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
    """Actualiza el dashboard al navegar entre registros."""
    
    # Si no hay índice actual, empieza en 0
    if current_index is None or not isinstance(current_index, str):
        current_index = 0
    else:
        try:
            current_index = int(current_index.split(": ")[1])
        except ValueError:
            current_index = 0

    # Ajustar el índice sin `combined_data`
    new_index = max(0, min(TOTAL_RECORDS - 1, current_index + (1 if next_clicks > prev_clicks else -1)))

    # Obtener el registro actual con paginación SQL
    record = fetch_record(new_index)
    if record.empty:
        return f"Current index: {new_index}", "No data available", "No data available", {}, {}

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
                x=[record.iloc[0].get("percent_solvent_content", 0)],
                y=[record.iloc[0].get("ph", 0)],
                mode='markers',
                marker={'color': 'blue', 'size': 12, 'symbol': 'star'},
                name='Selected Record'
            )
        ],
        'layout': {'title': 'Percent Solvent Content vs pH', 'xaxis': {'title': 'Percent Solvent Content'}, 'yaxis': {'title': 'pH'}}
    }

    # Gráfico 2: Relación entre `temp_k` y `molecular_weight`
    comparison_plot_2 = {
        'data': [
            go.Scattergl(
                x=[record.iloc[0].get("temp_k", 0)],
                y=[record.iloc[0].get("molecular_weight", 0)],
                mode='markers',
                marker={'color': 'green', 'size': 12, 'symbol': 'star'},
                name='Selected Record'
            )
        ],
        'layout': {'title': 'Temperature (K) vs Molecular Weight', 'xaxis': {'title': 'Temp (K)'}, 'yaxis': {'title': 'Molecular Weight'}}
    }

    return f"Current index: {new_index}", biogrid_details, rcsb_details, comparison_plot_1, comparison_plot_2

# Run the app

server = app.server


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)




