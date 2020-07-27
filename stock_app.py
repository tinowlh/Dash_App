import dash
import dash_table
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import dash_auth

import pandas as pd
from pandas_datareader import data as web
from datetime import datetime as dt


#import plotly.io as pio
#pio.templates.default = "plotly_dark"





def get_stockP(l_of_stocks, start = dt(2018, 1, 1), end = dt.now()):
    df_stock = web.DataReader(l_of_stocks, 'yahoo', start, end)
    df_stock = df_stock.loc[:, df_stock.columns.get_level_values(0).isin({'Close'})]
    df_stock.columns =df_stock.columns.droplevel()
    df_stock = df_stock.reset_index('Date')
    df_stock['Date'] = df_stock['Date'].dt.date
    return df_stock


l_of_stock = ['VTI', 'VEA', 'VWO']
df_stock = get_stockP(l_of_stock)








# Keep this out of source code repository - save in a file or a database

VALID_USERNAME_PASSWORD_PAIRS = {
    'hello': 'world',
    'world':'hello'
}

l_of_stock = ['TSLA', 'NVDA', 'AMD', 'INTL', 'VTI']
df_stock = get_stockP(l_of_stock)

app = dash.Dash('Hello World')
server = app.server

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)



app.layout = html.Div([
    html.Label('Stock Ticker'),
    #dcc.Markdown('**Stock Ticker**'),
    dcc.Dropdown(
        id='my-dropdown',
        options=[
            {'label': 'TESLA', 'value': 'TSLA'},
            {'label': 'NVIDIA', 'value': 'NVDA'},
            {'label': 'AMD', 'value': 'AMD'},
            {'label': 'INTEL', 'value': 'INTL'},
            {'label': 'VTI', 'value': 'VTI'},
        ],
        value='TSLA'
    ), 
    html.Br(),
    dcc.Graph(id='my-graph'),
    html.Br(),
    dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df_stock.columns],
    data=df_stock.to_dict('records'),
    page_size = 30,
    sort_action="native"
    )
], style={'width': '600'})


@app.callback(Output('my-graph', 'figure'), [Input('my-dropdown', 'value')])
def update_graph(selected_dropdown_value):
    df = web.DataReader(
        selected_dropdown_value,
        'yahoo',
        dt(2018, 1, 1),
        dt.now()
    )
    return {
        'data': [{
            'x': df.index,
            'y': df.Close
        }],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }

app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

if __name__ == '__main__':
    app.run_server()