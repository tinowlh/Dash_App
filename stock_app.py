import dash
import dash_table
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_auth

import pandas as pd
from pandas_datareader import data as web
from datetime import datetime as dt

import plotly.express as px
#import datetime
#import investpy

#import plotly.io as pio
#pio.templates.default = "plotly_dark"


#### Investing.com: Stock Price
#def get_stock_price (stock, from_date, to_date, country= 'united states'):
#
#    df = investpy.get_stock_historical_data(stock= stock,
#                                        country= country,
#                                        from_date= from_date,
#                                        to_date= to_date)
#    df = df[['Close']]
#    df = df.rename(columns = {'Close':'{stock}'.format(stock=stock)})
#    df = df.reset_index('Date')
#    df['Date'] = df['Date'].dt.date
##    df.index = pd.to_datetime(df.index)
#
##    df.index = df.index.strftime("%G") + df.index.strftime("%V")
##    df = df.groupby(df.index).mean()
#
#    return df
#
#
#today = datetime.date.today()
#fr_date = '01/01/2018'
#today = today.strftime("%d/%m/%Y") # dd/mm/YY
#
#
#
#df = get_stock_price(stock= '2376', country= 'taiwan',
#                                    from_date= fr_date,
#                                    to_date= today)



def get_stockP(l_of_stocks, start = dt(2018, 1, 1), end = dt.now()):
    df_stock = web.DataReader(l_of_stocks, 'yahoo', start, end)
    df_stock = df_stock.loc[:, df_stock.columns.get_level_values(0).isin({'Close'})]
    df_stock.columns =df_stock.columns.droplevel()
    df_stock = df_stock.reset_index('Date').round(2)
    df_stock['Date'] = df_stock['Date'].dt.date
    return df_stock

def get_stockP_return(df_stock):
    df_stock = df_stock.set_index('Date')
    df_stock_return = df_stock.pct_change().round(4)
    df_stock_return = df_stock_return.reset_index('Date')
    return df_stock_return




# Keep this out of source code repository - save in a file or a database

VALID_USERNAME_PASSWORD_PAIRS = {
    'hello': 'world',
    'world':'hello'
}

l_of_stocks = ['VT', 'BND', '0050.TW']
df_stock = get_stockP(l_of_stocks)
df_stock_return = get_stockP_return(df_stock)

df_stock = df_stock.sort_values(by='Date', ascending=False)
df_stock_return = df_stock_return.sort_values(by='Date', ascending=False)

app = dash.Dash('Hello World')
server = app.server

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)


app.layout = html.Div([
    html.Iframe(
        id='my-static',
        src='/assets/test_pic.png',
        height=200,
        width='100%',
        style={'border': 'none', 'margin-top': 50}
    ),
    html.Div(["Input1: ",dcc.Input(id='my-input1', value=1, type='number'),
              "Input2: ",dcc.Input(id='my-input2', value=1, type='number'),
              html.Button(id='submit-button-state', n_clicks=0, children='Submit'),
              html.Div(id='my-output')]),
    html.Br(),          
    #html.Label('Stock Ticker'),
    dcc.Markdown('**Stock Ticker**'),
    dcc.Dropdown(
        id='my-dropdown',
        options=[
            {'label': 'VT', 'value': 'VT'},
            {'label': 'BND', 'value': 'BND'},
            {'label': '0050', 'value': '0050.TW'},
        ],
        value='VT'
    ), 
    html.Br(),
    dcc.Graph(id='my-graph'),
    html.Br(),
    dcc.Graph(id='pie-chart'),
    html.Br(),
    dcc.Markdown('**Stock Price**'),
    dash_table.DataTable(
    id='table',
    columns=[{"name": i, "id": i} for i in df_stock.columns],
    data=df_stock.to_dict('records'),
    page_size = 20,
    sort_action="native"
    ),
    html.Br(),
    dcc.Markdown('**Percentage Change**'),
    dash_table.DataTable(
    id='table_return',
    columns=[{"name": i, "id": i} for i in df_stock_return.columns],
    data=df_stock_return.to_dict('records'),
    page_size = 20,
    sort_action="native"
    ),
    dcc.Interval(
            id='interval-component',
            interval=10*1000, # in milliseconds 
            n_intervals=0
    )
], style={'width': '600'})

@app.callback(
    Output(component_id='my-output', component_property='children'),
    [Input('submit-button-state', 'n_clicks')],
    [State('my-input1', 'value'),
    State('my-input2', 'value')]
)
def update_output_div(n_clicks, input_value1, input_value2):
    if input_value1 == None:
        input_value1 = 0 
    if input_value2 == None:
        input_value2 = 0 
    v = (input_value1 - input_value2) * 100
    return 'Output: {} (The Button has been pressed {} times)'.format(v, n_clicks)


@app.callback(Output('my-graph', 'figure'), 
            [Input('my-dropdown', 'value'),
            Input('interval-component', 'n_intervals')])
def update_graph(selected_dropdown_value, n):
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



@app.callback(Output('pie-chart', 'figure'),
            [Input('my-dropdown','value')])
def update_pie_chart(my_dropdown):
    dff = pd.DataFrame({'Stock': ['A', 'B'], 'Value': [6, 4]})

    piechart=px.pie(
            data_frame=dff,
            names='Stock',
            values='Value',
            hole=.3,
            )

    return (piechart)



@app.callback(Output('table', 'data'),
            [Input('interval-component', 'n_intervals')])
def update_datatable(n):
    df_stock = get_stockP(l_of_stocks)
    df_stock = df_stock.sort_values(by='Date', ascending=False)
    data=df_stock.to_dict('records')
    
    return data



app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

if __name__ == '__main__':
    app.run_server(debug=True)
