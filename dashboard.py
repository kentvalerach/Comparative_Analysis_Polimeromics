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

# Solo traer las columnas necesarias
biogrid_query = "SELECT unique_id, official_symbol FROM biogrid_homosapiens LIMIT 1000"
rcsb_query = "SELECT unique_id, macromolecule_name, percent_solvent_content, ph, temp_k, molecular_weight FROM rcsb_pdb LIMIT 1000"

biogrid_data = get_data(biogrid_query)
rcsb_data = get_data(rcsb_query)

# Normalizar nombres de columna y limpiar datos
biogrid_data["official_symbol"] = biogrid_data["official_symbol"].str.lower().str.strip()
rcsb_data["macromolecule_name"] = rcsb_data["macromolecule_name"].str.lower().str.strip()

# Realizar un join eficiente
combined_query = """
SELECT b.unique_id AS unique_id_biogrid, r.unique_id AS unique_id_rcsb, b.official_symbol, r.macromolecule_name, 
       r.percent_solvent_content, r.ph, r.temp_k, r.molecular_weight
FROM biogrid_homosapiens b
JOIN rcsb_pdb r ON b.official_symbol = r.macromolecule_name
LIMIT 1000
"""

combined_data = get_data(combined_query)

# Inicializar Dash
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center'}),
    
    dcc.Store(id='data-store', data=combined_data.to_dict('records')),
    
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
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'}),
        
        html.Div([
            html.H3("Fluginformationen"),
            html.Pre(id='details', style={'border': '1px solid black', 'padding': '10px'})
        ], style={'width': '48%', 'display': 'inline-block', 'padding': '10px'})
    ], style={'display': 'flex', 'justifyContent': 'space-between'})
])

@app.callback(
    [Output('record-index', 'children'),
     Output('details', 'children'),
     Output('comparison-plot-1', 'figure'),
     Output('comparison-plot-2', 'figure')],
    [Input('prev-button', 'n_clicks'),
     Input('next-button', 'n_clicks')],
    [State('data-store', 'data'),
     State('record-index', 'children')]
)
def update_dashboard(prev_clicks, next_clicks, data, current_index):
    df = pd.DataFrame(data)
    if current_index is None:
        current_index = 0
    else:
        current_index = int(current_index.split(": ")[1])
    
    new_index = current_index + (1 if next_clicks > prev_clicks else -1)
    new_index = max(0, min(len(df) - 1, new_index))
    
    current_record = df.iloc[new_index]
    details = "\n".join([f"{col}: {current_record[col]}" for col in df.columns])
    
    plot1 = {
        'data': [{
            'x': df["percent_solvent_content"],
            'y': df["ph"],
            'mode': 'markers',
            'marker': {'color': 'lightblue', 'size': 8}
        }],
        'layout': {'title': 'Percent Solvent Content vs pH', 'xaxis': {'title': 'Percent Solvent Content'}, 'yaxis': {'title': 'pH'}}
    }
    
    plot2 = {
        'data': [{
            'x': df["temp_k"],
            'y': df["molecular_weight"],
            'mode': 'markers',
            'marker': {'color': 'lightgreen', 'size': 8}
        }],
        'layout': {'title': 'Temperature (K) vs Molecular Weight', 'xaxis': {'title': 'Temp (K)'}, 'yaxis': {'title': 'Molecular Weight'}}
    }
    
    return f"Current index: {new_index}", details, plot1, plot2

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)


