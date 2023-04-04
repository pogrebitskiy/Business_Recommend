import dash
from dash import dcc
from dash import html
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
from dash import dash_table

# Import your make_recommendations function
from recommend import make_recommendations, get_reviews

global rec_df
active_row = None

# Initialize the Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], suppress_callback_exceptions=True)

# Define the layout of the interface
app.layout = html.Div([
    html.Div([
        html.H1('Business Recommendations'),
        html.Label('Business ID'),
        dcc.Input(id='business-id', type='text', value='', placeholder='Enter a business ID'),
        html.Br(),
        html.Label('Max Distance'),
        dcc.Input(id='max-dist', type='number', value=16000),
        html.Br(),
        html.Button('Get Recommendations', id='submit-button', n_clicks=0),
    ], style={'text-align': 'center', 'width': '50%', 'padding': '20px', 'margin': 'auto'}),
    dbc.Row([
        dbc.Col(html.Div(id='business-table'), style={'padding': '20px', 'flex': '50%'}),
        dbc.Col(html.Div(id='reviews-table'), style={'padding': '20px', 'flex': '50%'})
    ], align='center', style={'display': 'flex', 'flex-direction': 'row'})

])


# callback function that will be triggered when the user clicks the submit button
@app.callback(
    Output('business-table', 'children'),
    [Input('submit-button', 'n_clicks')],
    [State('business-id', 'value'),
     State('max-dist', 'value')]
)
def update_output(n_clicks, business_id, max_dist):
    global rec_df
    if n_clicks == 0:
        return dash.no_update

    else:
        # Call the make_recommendations function with the input values
        rec_df = make_recommendations(business_id, max_dist)

        # Round off big floats
        rec_df['distance'] = rec_df['distance'].round(3)
        rec_df['recommend_score'] = rec_df['recommend_score'].round(3)

        # Hide specified columns from display
        hide = ['business_id', 'postal_code', 'latitude', 'longitude', 'state', 'average_adj_score',
                'credibility_score']

        # Build table from data
        table = dash_table.DataTable(
            id='rec-table',
            columns=[{"name": i, "id": i}
                     for i in rec_df.columns if i not in hide],
            data=rec_df.to_dict('records'),
            style_header={
                'backgroundColor': '#f5f5f5',
                'fontWeight': 'bold'
            },
            active_cell={'row': 0, 'column': 0},
            page_action='native',
            style_table={
                'height': '750px',  # set the height of the table
                'overflowY': 'scroll',  # enable vertical scrolling
                'border': 'thin lightgrey solid',
                'border-collapse': 'collapse',
                'width': '100%',
                'font-family': 'Ariel',
                'font-size': '14px'
            },
            style_cell={
                'textAlign': 'left',
                'whiteSpace': 'normal',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'maxWidth': '150px',
                'padding': '10px',
                'border': '1px solid #ddd'
            },
            style_data_conditional=[
                {
                    'if': {'state': 'selected'},
                    'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                    'border': '1px solid rgb(0, 116, 217)',
                },
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f9f9f9'
                },

            ],
            selected_cells=[],
        )

        # Return table with header
        return html.Div([html.H2('Businesses'), table])


# callback that updates the active row variable when a cell is clicked
@app.callback(
    Output('rec-table', 'style_data_conditional'),
    Input('rec-table', 'active_cell')
)
def update_active_cell(active_cell):
    global active_row
    # Gets the active row from the first table
    active_row = active_cell['row'] if active_cell else None

    # applies conditional syling
    return [
        {
            'if': {'row_index': active_row},
            'backgroundColor': 'rgba(0, 116, 217, 0.3)'
        },
        {
            'if': {'state': 'selected'},
            'backgroundColor': 'rgba(0, 116, 217, 0.3)',
            'border': 'None',
        }
    ]


# callback function that is triggered then a new row of the table is clicked
@app.callback(Output('reviews-table', 'children'),
              [Input('rec-table', 'active_cell')])
def selected_row_and_show_reviews(active_cell):
    global rec_df
    if active_cell:

        # Get the clicked business_id
        clicked_id = rec_df.iloc[active_cell['row']]['business_id']

        # Get the reviews and round the dataframe
        rev_df = get_reviews(clicked_id)
        rev_df['adjusted_score'] = rev_df['adjusted_score'].round(3)

        hide = ['funny', 'cool', 'user_id', 'business_id']

        # Build the table
        table = dash_table.DataTable(
            id='rev-table',
            columns=[{"name": i, "id": i}
                     for i in rev_df.columns if i not in hide],
            data=rev_df.to_dict('records'),
            # Establish tooltips
            tooltip_data=[
                {
                    'text': {'value': str(row['text']), 'type': 'markdown'}

                } for row in rev_df.to_dict('records')
            ],
            style_header={
                'backgroundColor': '#f5f5f5',
                'fontWeight': 'bold'
            },
            tooltip_delay=500,
            tooltip_duration=None,
            page_action='native',
            style_data={
                'height': 'auto',
                'whiteSpace': 'normal'
            },
            style_table={
                'height': '750px',  # set the height of the table
                'overflowY': 'scroll',  # enable vertical scrolling
                'border': 'thin lightgrey solid',
                'border-collapse': 'collapse',
                'width': '100%',
                'font-family': 'Ariel',
                'font-size': '14px'
            },
            css=[{
                'selector': '.dash-cell div.dash-cell-value',
                'rule': 'display: -webkit-box; '
                        '-webkit-line-clamp: 4; '
                        '-webkit-box-orient: vertical; '
                        'overflow: hidden;'
            },
                # Tooltip styling
                {'selector': '.dash-tooltip', 'rule': 'max-width: none; white-space: normal;'},
                {'selector': '.dash-table-tooltip', 'rule': 'overflow:hidden; max-width: 600px; max-height: 600px; '
                                                            'font-size: 10px;'},
                {'selector': '.tooltip', 'rule': 'z-index: 10001;!important;'}
            ],
            style_cell={
                'textAlign': 'left',
                'overflow': 'hidden',
                'textOverflow': 'ellipsis',
                'height': '70px',
                'whiteSpace': 'pre-wrap',
                'maxWidth': '150px',
                'padding': '10px',
                'border': '1px solid #ddd'
            },
            style_data_conditional=[
                {
                    'if': {'state': 'selected'},
                    'backgroundColor': 'rgba(0, 116, 217, 0.3)',
                    'border': '1px solid rgb(0, 116, 217)',
                },
                {
                    'if': {'row_index': 'odd'},
                    'backgroundColor': '#f9f9f9'
                }
            ],
        )

        # Return the table with a header
        return html.Div([html.H2('Reviews'), table])


if __name__ == '__main__':
    app.run_server(debug=False)
