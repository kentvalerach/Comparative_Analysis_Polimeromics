import dash
from dash import dcc, html, Input, Output, State
import pandas as pd
from sqlalchemy import create_engine
import os

# Obtener la URL de la base de datos desde las variables de entorno
DATABASE_URL = os.getenv('DATABASE_URL')

# Crear un motor SQLAlchemy
engine = create_engine(DATABASE_URL)

# Función para cargar datos bajo demanda
def load_data(page, page_size):
    offset = page * page_size
    query = f"""
    SELECT * FROM biogrid_homosapiens
    LIMIT {page_size} OFFSET {offset}
    """
    return pd.read_sql_query(query, engine)

# Tamaño de la página para la paginación
PAGE_SIZE = 100

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
    new_index = max(0, min(PAGE_SIZE - 1, new_index))

    # Load data for the current page
    current_page = new_index // PAGE_SIZE
    data = load_data(current_page, PAGE_SIZE)

    # Get the current record
    current_record = data.iloc[new_index % PAGE_SIZE]

    # BIOGRID details: show all columns
    biogrid_details = "\n".join([
        f"{col}: {current_record.get(col, 'N/A')}" for col in data.columns
    ])

    # RCSB details: show all columns with special handling for long rows
    rcsb_details = "\n".join([
        f"{col}: {current_record.get(col, 'N/A')}" if col not in ['crystal_growth_procedure', 'structure_title']
        else f"{col}: {current_record[col][:100]}..."  # Limit long rows to 100 characters
        for col in data.columns
    ])

    # Dynamic Graphs with context and highlighted point
    comparison_plot_1 = {
        'data': [
            {'x': data["percent_solvent_content"],
             'y': data["ph"],
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
            {'x': data["temp_k"],
             'y': data["molecular_weight"],
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
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)

