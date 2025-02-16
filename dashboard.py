import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from sqlalchemy import create_engine, text
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

def get_data(query, params=None):
    """Función para obtener datos de la base de datos de forma optimizada."""
    try:
        with engine.connect() as connection:
            return pd.read_sql_query(text(query), connection, params=params)
    except Exception as e:
        print(f"Error al obtener datos: {e}")
        return pd.DataFrame()

# Consultas optimizadas para obtener datos relevantes
combined_query = """
SELECT b.*, r.*
FROM biogrid_homosapiens b
JOIN rcsb_pdb r ON b.official_symbol = r.macromolecule_name
LIMIT 1000
"""

combined_data = get_data(combined_query)

# Inicializar la aplicación Dash
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # Navegación de registros
    html.Div([
        html.Button("Previous", id='prev-button', n_clicks=0),
        html.Button("Next", id='next-button', n_clicks=0),
        html.Div(id='record-index', style={'marginTop': '10px'}),
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),

    # Contenedor principal dividido en dos columnas
    html.Div([
        # Columna izquierda: gráficos y datos BIOGRID
        html.Div([
            html.H3("Comparison Graphs"),
            dcc.Graph(id='comparison-plot-1'),
            dcc.Graph(id='comparison-plot-2'),
            html.H3("BIOGRID Data"),
            html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'}),
        ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),

        # Columna derecha: datos RCSB y análisis biomédico
        html.Div([
            html.H3("RCSB Data"),
            html.Pre(id='rcsb-details', style={
                'border': '1px solid black',
                'padding': '10px',
                'overflowY': 'scroll',
                'maxHeight': '300px'
            }),
            html.H3("Biomedical and Genetic Insights"),
            html.Div(id='biomedical-insights', style={
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
     Output('comparison-plot-2', 'figure'),
     Output('biomedical-insights', 'children')],
    [Input('prev-button', 'n_clicks'),
     Input('next-button', 'n_clicks')],
    State('record-index', 'children'),
    prevent_initial_call=True
)
def update_dashboard(prev_clicks, next_clicks, current_index):
    if current_index is None:
        new_index = 0
    else:
        new_index = int(current_index.split(": ")[1])
    
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update
    
    triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]
    if triggered_id == 'next-button':
        new_index = min(new_index + 1, len(combined_data) - 1)
    elif triggered_id == 'prev-button':
        new_index = max(new_index - 1, 0)
    
    current_record = combined_data.iloc[new_index]

    biogrid_details = "\n".join([f"{col}: {current_record[col]}" for col in combined_data.columns if col.startswith("b_")])
    rcsb_details = "\n".join([f"{col}: {current_record[col]}" for col in combined_data.columns if col.startswith("r_")])

    comparison_plot_1 = {
        'data': [
            {'x': combined_data["percent_solvent_content"],
             'y': combined_data["ph"],
             'mode': 'markers',
             'marker': {'color': 'lightblue', 'size': 8},
             'name': 'All Records'},
            {'x': [current_record["percent_solvent_content"]],
             'y': [current_record["ph"]],
             'mode': 'markers',
             'marker': {'color': 'blue', 'size': 12, 'symbol': 'star'},
             'name': 'Selected Record'},
        ],
        'layout': {'title': 'Percent Solvent Content vs pH', 'xaxis': {'title': 'Percent Solvent Content'}, 'yaxis': {'title': 'pH'}}
    }

    comparison_plot_2 = {
        'data': [
            {'x': combined_data["temp_k"],
             'y': combined_data["molecular_weight"],
             'mode': 'markers',
             'marker': {'color': 'lightgreen', 'size': 8},
             'name': 'All Records'},
            {'x': [current_record["temp_k"]],
             'y': [current_record["molecular_weight"]],
             'mode': 'markers',
             'marker': {'color': 'green', 'size': 12, 'symbol': 'star'},
             'name': 'Selected Record'},
        ],
        'layout': {'title': 'Temperature (K) vs Molecular Weight', 'xaxis': {'title': 'Temp (K)'}, 'yaxis': {'title': 'Molecular Weight'}}
    }

    return f"Current index: {new_index}", biogrid_details, rcsb_details, comparison_plot_1, comparison_plot_2, "Updated biomedical insights based on selected data."

server = app.server

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

