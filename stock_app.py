# dash
import dash
import dash_table
from dash.dependencies import Input, Output, State
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_auth

# plot
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import plotly.io as pio #themes


# data
import pandas as pd
from pandas_datareader import data as web
from datetime import datetime as dt
import numpy as np

# machine learning
from sklearn.cluster import KMeans

# cache
from flask_caching import Cache


###### Initialize app ######
app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
app.title = 'Stock Analysis' #web tab title
server = app.server

# Flask cache
cache = Cache(app.server, config={
    'CACHE_TYPE': 'filesystem',
    'CACHE_DIR': 'cache-directory'
})


###### Authentication ######
# Keep this out of source code repository when it's in production - save in a file or a database
#VALID_USERNAME_PASSWORD_PAIRS = {
#    'hello': 'world',
#    'world':'hello'
#}

#auth = dash_auth.BasicAuth(
#    app,
#    VALID_USERNAME_PASSWORD_PAIRS
#)



TIMEOUT = 60

class ImportData():
    
    def __init__(self, l_of_stocks, start=dt(2020, 1, 1), end=dt.now()):
        self.l_of_stocks = l_of_stocks
        self.start = start
        self.end = end

    @cache.memoize(timeout=TIMEOUT)
    def get_stockV_raw(self):
        # data preparation
        df = web.DataReader(self.l_of_stocks, 'yahoo', self.start, self.end)
        df = df.loc[:, df.columns.get_level_values(0).isin({'Volume'})]
        df.columns =df.columns.droplevel()
        return df

    @cache.memoize(timeout=TIMEOUT)
    def get_stockP_raw(self):
        # data preparation
        df = web.DataReader(self.l_of_stocks, 'yahoo', self.start, self.end)
        df = df.loc[:, df.columns.get_level_values(0).isin({'Close'})].round(2)
        df.columns =df.columns.droplevel()
        return df
    
    
class Preprocess(ImportData):

    def __init__(self, l_of_stocks, start=dt(2020, 1, 1), end=dt.now()):
        super().__init__(l_of_stocks, start, end)

    def get_stockP_add_date(self):
        df = super().get_stockP_raw()
        df = df.reset_index('Date')
        df['Date'] = df['Date'].dt.date
        return df
    
    def get_stockP_return(self):
        df = self.get_stockP_add_date()
        df = df.set_index('Date')
        df = df.pct_change().round(4)
        df = df.reset_index('Date')
        return df

    def get_cum_return(self):
        df = super().get_stockP_raw()
        df_daily_return = df.pct_change()
        df_daily_cum_return = (1 + df_daily_return).cumprod()
        df_daily_cum_return = df_daily_cum_return.reset_index('Date')
        df_daily_cum_return = df_daily_cum_return.round(4)
        #df_daily_cum_return['Date'] = df_daily_cum_return['Date'].dt.date
        df_unpivot = df_daily_cum_return.melt(id_vars='Date',
                            var_name= 'Stock/ETF', 
                            value_name='CumReturn')
        return df_unpivot

    def get_annualizedReturn(self):
        df = super().get_stockP_raw()
        ttl_return = (df.iloc[-1] - df.iloc[0]) / df.iloc[0]
        df_ttl_return = ttl_return.to_frame(name="TTLReturn")
        df_annualized_return = ((1 + df_ttl_return) ** (365 / len(df))) -1 
        df_annualized_return = df_annualized_return.rename(columns={"TTLReturn": "AnnReturn"})
        return df_annualized_return
    
    def get_volatility(self):
        df = super().get_stockP_raw()
        df_return = df.pct_change()
        sr_volatility = df_return.std() * np.sqrt(250)
        df_volatility = sr_volatility.to_frame(name="Volatility")
        return df_volatility
    
    # @cache.memoize(timeout=TIMEOUT)
    def get_df_cluster(self):
        df_annualized_return = self.get_annualizedReturn()
        df_volatility = self.get_volatility()
        
        # merge
        df_cluster = pd.merge(df_annualized_return, 
                            df_volatility, 
                            left_index=True, right_index = True)
        df_cluster = round(df_cluster, 4)                      
        df_cluster = df_cluster.reset_index()
        
        return df_cluster


###### Data preprocess ######
# import csv
df_stockls = pd.read_csv('stocklist.csv')
df_stockls = df_stockls[~df_stockls['value'].isin(['NVDA', 'BND'])]

# df for table
l_of_stocks = df_stockls['value'].tolist()
l_cluster = df_stockls['value'].tolist()
l_cluster.remove('0050.TW')

pp = Preprocess(l_of_stocks)
df_stock = pp.get_stockP_add_date()
df_stock = df_stock.sort_values(by='Date', ascending=False)

# df_stock_return = pp.get_stockP_return()
#df_stock_return = df_stock_return.sort_values(by='Date', ascending=False)



###### UI LAYOUT ######
### SIDEBAR ###

# the style arguments for the sidebar.
SIDEBAR_STYLE = {
    'position': 'fixed',
    'top': 0,
    'left': 0,
    'bottom': 0,
    'width': '20%',
    'padding': '20px 10px',
    'color': '#ffffff',
    'background-color': '#3498DB'
}


TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#191970',
    'background-color': '#ffffff'
}



# sidebar controls
controls = dbc.FormGroup(
    [
     
        dcc.Markdown('Stock/ETF'),
        dcc.Dropdown(
            id='my-dropdown',
            options= df_stockls[['value', 'label']].to_dict('records'),
            value='VOO',
            style= {'color':'#000000'}
                ), 
        html.Br(),
        dcc.Markdown('Date'),
        dcc.DatePickerRange(
            id='my-date-picker-range',
            display_format='YYYY-MM-DD',
            start_date = dt(2020, 1, 1),
            min_date_allowed=dt(2018, 1, 1),
            max_date_allowed=dt.now(),
            initial_visible_month=dt(2020, 1, 1),
            end_date=dt.now().date()
                        ),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        dcc.Markdown('Cumulative Return Benchmark'),
        dcc.Dropdown(
            id='dropdown_benchmark1',
            options= df_stockls[df_stockls['benchmark'] == 'Y'][['value', 'label']].to_dict('records'),
            value='VOO',
            style= {'color':'#000000'}
                ),
        html.Br(),
        dcc.Markdown('Cumulative Return Stock/ETF'),        
        dcc.Dropdown(
            id='dropdown_benchmark2',
            options= df_stockls[df_stockls['benchmark'] == 'N'][['value', 'label']].to_dict('records'),
            value='0050.TW',
            style= {'color':'#000000'}
                ),
        html.Br(),
        html.Br(),
        html.Br(),
        html.Br(),
        dcc.Markdown('K-means Cluster Count'),
        dbc.Input(id="cluster-count", type="number", value=3, min=2, max=5, step=1),
        html.Br(),
        dbc.Button(
            "Generate Clusters !", 
            id="button-clustering", 
            color="primary",
            # outline=True,
            className="mr-1"
            )
        
    ]
)



sidebar = html.Div(
    [
        #html.H2('Parameters', style=TEXT_STYLE),
        #html.Hr(),
        controls
    ],
    style=SIDEBAR_STYLE,
)



### CONTENT ###

# the style arguments for the main content page.
CONTENT_STYLE = {
    'margin-left': '25%',
    'margin-right': '5%',
    'padding': '20px 10p'
}


CARD_TEXT_STYLE = {
    'textAlign': 'center',
    'color': '#0074D9'
}


content_first_row = dbc.Row(
    [
        dbc.Col(dcc.Graph(id='my-indicator'), md=12)
    ]
)

content_second_row = dbc.Row(
    [
        dbc.Col(
            dcc.Loading(
                id="loading-line-bar-chart",
                type="dot",
                children= dcc.Graph(id='my-line-bar-chart')
                ), 
            md=12)
    ]
)


content_third_row = dbc.Row(
    [

        dbc.Col(
            dcc.Loading(
                id="loading-benchmark",
                type="dot",
                children=dcc.Graph(id='graph-benchmark')
                ), 
                md=12)
    ]
)


content_fourth_row = dbc.Row(
    [
        dbc.Col(
            dcc.Loading(
                id="loading-cluster",
                type="dot",
                children=dcc.Graph(id='graph-cluster')
                ),
                md=12),
    ]
)


content_fifth_row = dbc.Row(
    [
        dbc.Col(
            dash_table.DataTable(
            id='table',
            columns=[{"name": i, "id": i} for i in df_stock.columns],
            data=df_stock.to_dict('records'),
            page_size = 20,
    #       style_as_list_view=True,
    #       fixed_rows={'headers': True},
            sort_action="native",
            style_header={'backgroundColor': 'rgb(224, 224, 224)',
                        'fontWeight': 'bold'}
            ),
         md=12
        ) 
    ]
)



content = html.Div(
    [
        dcc.Markdown('Update every 5 mins',style={'textAlign': 'right'}),
        html.H2('Stock Analysis Dashboard', style=TEXT_STYLE),
        html.Hr(),
        content_first_row,
        html.Br(),
        content_second_row,
        html.Br(),
        content_third_row,
        html.Br(),
        content_fourth_row,
        #dbc.Spinner(html.Div(id="graph-cluster")),
        html.Br(),
        content_fifth_row,
        dcc.Interval(
                id='interval-component',
                interval=5*60*1000, # in milliseconds 5min update
                n_intervals=0
                    )
    ],
    style=CONTENT_STYLE
)


app.layout = html.Div([sidebar, content])



###### Callback ######

# indicator
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
        margin=dict(l=40,r=40,b=40,t=50,pad=4),
        height=130,
        grid = {'rows': 1, 'columns': 3, 'pattern': "independent"},
        template = {'data' : {'indicator': [{
                                            'title': {'text': "Return"},
                                            'mode' : "number",
                                            'delta' : {'reference': 0}
                                            }]
                             }
                    })
    return fig


# Line Bar Chart
@app.callback(Output('my-line-bar-chart', 'figure'), 
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

    # Create figure with secondary y-axis
    #fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig = make_subplots(
                    rows=2, cols=1, 
                    shared_xaxes=True, 
                    vertical_spacing=0.05
                    )

    fig.add_trace(
    go.Scatter(x=list(df.index), y=list(df['Close']), name="Price"),
    row=1, col=1
    )


    fig.add_trace(
    go.Bar(x=list(df.index), y=list(df['Volume']), name="Volume"),
    row=2, col=1
    )
   
    # update_layout
    fig.update_layout(
        title='Stock Price & Volume',
        height=600,
        template='plotly_dark',
    ) 

    ## Set y-axes titles
    #fig.update_yaxes(title_text="<b>Price</b>", secondary_y=False)
    #fig.update_yaxes(title_text="<b>Volume</b>", secondary_y=True)

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
    df = Preprocess(ls, start_date, end_date).get_cum_return()
    df['Stock/ETF'] = df['Stock/ETF'].str.replace('VOO', 'VOO (S&P 500)')
    fig = px.line(df, x="Date", y="CumReturn", color='Stock/ETF',
                 title="Comparing Cumulative Return"
                 )
    fig.update_layout(height=600, 
            template='plotly_dark')           
    return fig


# clustering
@app.callback(Output('graph-cluster', 'figure'),
            [Input("button-clustering", "n_clicks")],
            [State('my-dropdown', 'value'),
            State("cluster-count", "value")])
def update_clustering(n_clicks, selected_dropdown_value, n_clusters):
    # data preparation
    df_cluster = Preprocess(l_cluster).get_df_cluster()
    df = df_cluster.loc[:, ['AnnReturn', 'Volatility']]
    
    #K-means Clustering
    # minimal input validation, make sure there's at least two clusters
    km = KMeans(n_clusters=max(n_clusters, 2))
    km.fit(df.values)
    df_cluster["cluster"] = km.labels_
    centers = km.cluster_centers_
    
    
    #data points
    data = [
        go.Scatter(
            x=df_cluster.loc[df_cluster.cluster == c, 'AnnReturn'],
            y=df_cluster.loc[df_cluster.cluster == c, 'Volatility'],
            mode="markers",
            marker={"size": 12},
            name="Cluster{}".format(c),
            text=df_cluster.loc[df_cluster.cluster == c, 'Symbols']
            
        )
        for c in range(n_clusters)
    ]
    
    
    # centers
    data.append(
        go.Scatter(
            x=centers[:, 0],
            y=centers[:, 1],
            mode="markers",
            marker={"color": "#000", "size": 8, "symbol": "diamond"},
            name="Cluster centers",
        )
    )
    
    layout = {"xaxis": {"title": 'Annualized Return'}, "yaxis": {"title": 'Volatility (Risk)'}}

    fig = go.Figure(data=data, layout=layout)

    fig.update_layout(height=600,
        title = 'K-means Clustering',
        template='plotly')    
    
    return fig
    


# Table
@app.callback(Output('table', 'data'),
            [Input('my-date-picker-range', 'start_date'),
            Input('my-date-picker-range', 'end_date'),
            Input('interval-component', 'n_intervals')])
def update_datatable(start_date, end_date, n):
    df_stock = Preprocess(l_of_stocks, start_date, end_date).get_stockP_add_date()
    df_stock = df_stock.sort_values(by='Date', ascending=False)
    data=df_stock.to_dict('records')
    
    return data



#app.css.append_css({'external_url': 'https://codepen.io/chriddyp/pen/bWLwgP.css'})

if __name__ == '__main__':
    app.run_server(debug=True) 
    # app.run_server(host='0.0.0.0', port=9000) # local
