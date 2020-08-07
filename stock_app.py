import dash
import dash_table
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_auth

import pandas as pd
from pandas_datareader import data as web
from datetime import datetime as dt
import numpy as np

import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio #themes

#import datetime
#import investpy

#pio.templates

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


def get_cum_return(l_of_stocks, start = dt(2020, 1, 1), end = dt.now()):
    df = web.DataReader(l_of_stocks, 'yahoo', start, end)
    df = df.loc[:, df.columns.get_level_values(0).isin({'Close'})]
    df.columns =df.columns.droplevel()
    df_daily_return = df.pct_change()
    df_daily_cum_return = (1 + df_daily_return).cumprod()
    df_daily_cum_return = df_daily_cum_return.reset_index('Date')
    #df_daily_cum_return['Date'] = df_daily_cum_return['Date'].dt.date
    df_unpivot = df_daily_cum_return.melt(id_vars='Date',
                         var_name= 'Stock/ETF', 
                         value_name='CumReturn')
    return df_unpivot




# Keep this out of source code repository - save in a file or a database

VALID_USERNAME_PASSWORD_PAIRS = {
    'hello': 'world',
    'A':'BC'
}

#import csv
df_stockls = pd.read_csv('stocklist.csv')

# df for table
l_of_stocks = df_stockls['value'].tolist()
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


app.layout = html.Div(
    children=[
        dcc.Markdown('Update every 30 seconds',style={'textAlign': 'right'}),
        dcc.Markdown('**Stock Ticker**'),
        html.Div(
                children=[
                    html.Div(
                        dcc.Dropdown(
                        id='my-dropdown',
                        options= df_stockls[['value', 'label']].to_dict('records'),
                        value='VTI'
                                ) #, style={'display':'inline-block', 'width': '50%'}
                            ),
                    html.Div(
                        dcc.DatePickerRange(
                            id='my-date-picker-range',
                            display_format='YYYY-MM-DD',
                            start_date = dt(2019, 1, 1),
                            min_date_allowed=dt(2018, 1, 1),
                            max_date_allowed=dt.now(),
                            initial_visible_month=dt(2019, 1, 1),
                            end_date=dt.now().date()
                                        )
                                    #, style={'display':'inline-block', 'width': '50%'}
                              )
                         ]
                  ),
        dcc.Graph(id='my-indicator'),
    #    html.Div(["Input1: ",dcc.Input(id='my-input1', value=1, type='number'),
    #              "Input2: ",dcc.Input(id='my-input2', value=1, type='number'),
    #              html.Button(id='submit-button-state', n_clicks=0, children='Submit'),
    #              html.Div(id='my-output')]),   
    #    html.Label('Stock Ticker'),
        dcc.Graph(id='my-graph'),
        html.Br(),
        html.Div(
                children=[
                    html.Div(
                        html.Label(["Benchmark",
                            dcc.Dropdown(
                            id='dropdown_benchmark1',
                            options= df_stockls[df_stockls['benchmark'] == 'Y'][['value', 'label']].to_dict('records'),
                            value='VOO'
                                    )])
                            ,style={'display':'inline-block', 'width': '50%'}
                            ),
                     html.Div(
                        html.Label(["Stock/ETF",
                            dcc.Dropdown(
                            id='dropdown_benchmark2',
                            options= df_stockls[df_stockls['benchmark'] == 'N'][['value', 'label']].to_dict('records'),
                            value='0050.TW'
                                    )])
                            ,style={'display':'inline-block', 'width': '50%'}
                            )
                        ] , style={'background-color':'#C0C0C0',
                                   'font-family':'georgia'}
                 ),        
        dcc.Graph(id='graph-benchmark'),
    #    dcc.Graph(id='pie-chart'),
        html.Br(),
        dcc.Markdown('**Stock Price**'),
        dash_table.DataTable(
        id='table',
        columns=[{"name": i, "id": i} for i in df_stock.columns],
        data=df_stock.to_dict('records'),
        page_size = 20,
 #       style_as_list_view=True,
        sort_action="native",
        style_header={'backgroundColor': 'rgb(224, 224, 224)',
                      'fontWeight': 'bold'}
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
            ], style={'width': 'auto'})


### Callback ###

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

    ttl_return = (df.iloc[-1,3] - df.iloc[0,3]) / df.iloc[0,3]
    annualized_return = ((1 + ttl_return) ** (365/ len(df))) -1
    sr_return = df['Close'].pct_change()
    volatility = sr_return.std() * np.sqrt(250)
    sharpe_ratio = (annualized_return - 0) / volatility # risk-free rate = 0
    
    fig = go.Figure()
    fig.add_trace(go.Indicator(
        title = {'text': "Total Return"},    
        mode = "number",
        value = round(ttl_return * 100,2),
        number = {'suffix': "%"},
        domain = {'row': 0, 'column': 0}))
    
    fig.add_trace(go.Indicator(
        title = {'text': "Annualized Return"},   
        mode = "number",
        value = round(annualized_return * 100,2),
        number = {'suffix': "%"},
        domain = {'row': 0, 'column': 1}))
    
    fig.add_trace(go.Indicator(
        title = {'text': "Sharpe Ratio"},   
        mode = "number",
        value = round(sharpe_ratio,2),
        domain = {'row': 0, 'column': 2}))
    
    fig.update_layout(
        paper_bgcolor="#EBF5FB",
        autosize=True,
        margin=dict(l=60,r=60,b=60,t=60,pad=4),
#        width=300,
        height=200,
        grid = {'rows': 1, 'columns': 3, 'pattern': "independent"},
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

    fig = go.Figure()
    fig.add_trace(
    go.Scatter(x=list(df.index), y=list(df['Close'])))
   
    # update_layout
    fig.update_layout(
        height=500,
        template='plotly_white',
    ) 

    

    return fig


# Line Chart (Benchmark)
@app.callback(Output('graph-benchmark', 'figure'), 
            [Input('dropdown_benchmark1', 'value'),
            Input('dropdown_benchmark2', 'value'),
            Input('my-date-picker-range', 'start_date'),
            Input('my-date-picker-range', 'end_date'),
            Input('interval-component', 'n_intervals')])
def update_graph_bmrk(dropdown_bmak1_value, dropdown_bmak2_value, start_date, end_date, n):
    ls = [dropdown_bmak1_value, dropdown_bmak2_value]
    df = get_cum_return(ls, start_date, end_date)
    df['Stock/ETF'] = df['Stock/ETF'].str.replace('VOO', 'VOO (S&P 500)')
    fig = px.line(df, x="Date", y="CumReturn", color='Stock/ETF',
                 title="Cumulative Return"
                 )
    fig.update_layout(height=500, template='plotly_dark')           
    return fig


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


# Table
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
