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
import plotly.graph_objects as go
#import datetime
#import investpy



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



def get_stockP(l_of_stocks, start = dt(2020, 1, 1), end = dt.now()):
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
    'A':'BC'
}

l_of_stocks = ['VTI', 'VEA', 'VWO', 'BND', 
                'NVDA', 'AMD', 'INTC', '0050.TW']
df_stock = get_stockP(l_of_stocks)
#df_stock_return = get_stockP_return(df_stock)

df_stock = df_stock.sort_values(by='Date', ascending=False)
#df_stock_return = df_stock_return.sort_values(by='Date', ascending=False)

app = dash.Dash('Hello World')
server = app.server

auth = dash_auth.BasicAuth(
    app,
    VALID_USERNAME_PASSWORD_PAIRS
)


app.layout = html.Div([
    dcc.Markdown('Update every 30 seconds'),
    dcc.Markdown('**Stock Ticker**'),
    dcc.Dropdown(
        id='my-dropdown',
        options=[
            {'label': 'VTI', 'value': 'VTI'},
            {'label': 'VEA', 'value': 'VEA'},
            {'label': 'VWO', 'value': 'VWO'},
            {'label': 'BND', 'value': 'BND'},
            {'label': 'NVDA', 'value': 'NVDA'},
            {'label': 'AMD', 'value': 'AMD'},
            {'label': 'INTC', 'value': 'INTC'},
            {'label': '0050', 'value': '0050.TW'},
        ],
        value='VTI'
    ), 
    dcc.Graph(id='my-indicator'),
#    html.Div(["Input1: ",dcc.Input(id='my-input1', value=1, type='number'),
#              "Input2: ",dcc.Input(id='my-input2', value=1, type='number'),
#              html.Button(id='submit-button-state', n_clicks=0, children='Submit'),
#              html.Div(id='my-output')]),   
#    html.Label('Stock Ticker'),
    dcc.DatePickerRange(
        id='my-date-picker-range',
        start_date = dt(2020, 1, 1),
        min_date_allowed=dt(2018, 1, 1),
        max_date_allowed=dt.now(),
        initial_visible_month=dt.now(),
        end_date=dt.now().date()
    ),
    html.Br(),
    dcc.Graph(id='my-graph'),
    html.Br(),
#    dcc.Graph(id='pie-chart'),
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
#    dcc.Markdown('**Percentage Change**'),
#    dash_table.DataTable(
#    id='table_return',
#    columns=[{"name": i, "id": i} for i in df_stock_return.columns],
#    data=df_stock_return.to_dict('records'),
#    page_size = 20,
#    sort_action="native"
#    ),
    dcc.Interval(
            id='interval-component',
            interval=30*1000, # in milliseconds 30sec update
            n_intervals=0
    )
], style={'width': '600'})


### Callback

#indicator
@app.callback(Output('my-indicator', 'figure'),
            [Input('my-dropdown', 'value'),
            Input('my-date-picker-range', 'start_date'),
            Input('my-date-picker-range', 'end_date'),
            Input('interval-component', 'n_intervals')])
def update_indicator(selected_dropdown_value, start_date, end_date, n):
    df = web.DataReader(
        selected_dropdown_value,
        'yahoo',
        start_date,
        end_date
        )
    stock_return = round(((df.iloc[-1,3] - df.iloc[0,3]) / df.iloc[0,3]) * 100, 2)
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        mode = "number",
        value = stock_return,
        number = {'suffix': "%"},
        domain = {'row': 0, 'column': 0}))
    fig.update_layout(
        paper_bgcolor="#EBF5FB",
        autosize=True,
        margin=dict(l=50,r=50,b=100,t=100,pad=4),
#        width=300,
#        height=300,
        grid = {'rows': 1, 'columns': 1, 'pattern': "independent"},
        template = {'data' : {'indicator': [{
                                            'title': {'text': "Return"},
                                            'mode' : "number",
                                            'delta' : {'reference': 0}
                                            }]
                             }
                    })
    return fig

""" @app.callback(
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
    return 'Output: {} (The Button has been pressed {} times)'.format(v, n_clicks) """

# Line Chart
@app.callback(Output('my-graph', 'figure'), 
            [Input('my-dropdown', 'value'),
            Input('my-date-picker-range', 'start_date'),
            Input('my-date-picker-range', 'end_date'),
            Input('interval-component', 'n_intervals')])
def update_graph(selected_dropdown_value, start_date, end_date, n):
    df = web.DataReader(
        selected_dropdown_value,
        'yahoo',
        start_date,
        end_date
    )
    return {
        'data': [{'x': df.index,'y': df.Close}],
        'layout': {'margin': {'l': 40, 'r': 0, 't': 20, 'b': 30}}
    }



""" @app.callback(Output('pie-chart', 'figure'),
            [Input('my-dropdown','value')])
def update_pie_chart(my_dropdown):
    dff = pd.DataFrame({'Stock': ['A', 'B'], 'Value': [6, 4]})

    piechart=px.pie(
            data_frame=dff,
            names='Stock',
            values='Value',
            hole=.3,
            )

    return piechart """



@app.callback(Output('table', 'data'),
            [Input('my-date-picker-range', 'start_date'),
            Input('my-date-picker-range', 'end_date'),
            Input('interval-component', 'n_intervals')])
def update_datatable(start_date, end_date, n):
    df_stock = get_stockP(l_of_stocks, start_date, end_date)
    df_stock = df_stock.sort_values(by='Date', ascending=False)
    data=df_stock.to_dict('records')
    
    return data



app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

if __name__ == '__main__':
    app.run_server(debug=True)
