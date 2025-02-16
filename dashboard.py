import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from sqlalchemy import create_engine
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

def fetch_data(limit=100, offset=0):
    """Carga solo una porción de los datos desde la base de datos."""
    try:
        biogrid_query = f"""
            SELECT * FROM biogrid_homosapiens 
            LIMIT {limit} OFFSET {offset}
        """
        rcsb_query = f"""
            SELECT * FROM rcsb_pdb 
            LIMIT {limit} OFFSET {offset}
        """
        
        biogrid_data = pd.read_sql_query(biogrid_query, engine)
        rcsb_data = pd.read_sql_query(rcsb_query, engine)
        
        # Normalizar columnas en SQL en lugar de Pandas
        biogrid_data["official_symbol"] = biogrid_data["official_symbol"].str.lower().str.strip()
        rcsb_data["macromolecule_name"] = rcsb_data["macromolecule_name"].str.lower().str.strip()
        
        if 'sequence' in rcsb_data.columns:
            rcsb_data = rcsb_data.drop(columns=['sequence'])
        
        combined_data = biogrid_data.merge(
            rcsb_data,
            left_on="official_symbol",
            right_on="macromolecule_name",
            how="inner"
        ).reset_index(drop=True)
        
        return combined_data
    except Exception as e:
        print(f"Error al cargar los datos: {e}")
        return pd.DataFrame()

# Inicializar Dash
app = dash.Dash(__name__)
server = app.server  # Exponer el servidor Flask

def layout():
    return html.Div([
        html.H1("Comparative Analysis Dashboard", style={'textAlign': 'center'}),
        
        # Almacenamiento del índice actual
        dcc.Store(id='current-index', data=0),
        
        html.Div([
            html.Button("Previous", id='prev-button', n_clicks=0),
            html.Button("Next", id='next-button', n_clicks=0),
            html.Div(id='record-index', style={'marginTop': '10px'}),
        ], style={'textAlign': 'center'}),
        
        html.Div([
            html.Div([
                html.H3("BIOGRID Data"),
                html.Pre(id='biogrid-details', style={'border': '1px solid black', 'padding': '10px'})
            ], style={'width': '45%', 'float': 'left', 'padding': '10px'}),
            
            html.Div([
                html.H3("RCSB Data"),
                html.Pre(id='rcsb-details', style={'border': '1px solid black', 'padding': '10px'})
            ], style={'width': '45%', 'float': 'right', 'padding': '10px'})
        ], style={'display': 'flex'}),
    ])

def register_callbacks(app):
    @app.callback(
        [Output('record-index', 'children'),
         Output('biogrid-details', 'children'),
         Output('rcsb-details', 'children'),
         State('current-index', 'data')],
        [Input('prev-button', 'n_clicks'),
         Input('next-button', 'n_clicks')]
    )
    def update_dashboard(prev_clicks, next_clicks, current_index):
        new_index = max(0, min(current_index + (1 if next_clicks > prev_clicks else -1), 99))
        
        # Obtener datos de forma paginada
        combined_data = fetch_data(limit=1, offset=new_index)
        if combined_data.empty:
            return "No Data", "", ""
        
        current_record = combined_data.iloc[0]
        
        biogrid_details = "\n".join([f"{col}: {current_record.get(col, 'N/A')}" for col in combined_data.columns if col.startswith("biogrid")])
        rcsb_details = "\n".join([f"{col}: {current_record.get(col, 'N/A')}" for col in combined_data.columns if col.startswith("rcsb")])
        
        return f"Current index: {new_index}", biogrid_details, rcsb_details

app.layout = layout
register_callbacks(app)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)




