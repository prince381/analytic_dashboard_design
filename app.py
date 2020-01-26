import pandas as pd
import numpy as np
import plotly as py
import plotly.graph_objs as go
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input,Output


file = 'https://raw.githubusercontent.com/prince381/marketing_dashboard_design/master/data%20_files/Sample%20-%20Superstore.csv'
file2 = 'https://raw.githubusercontent.com/prince381/marketing_dashboard_design/master/data%20_files/state-abbrevs.csv'
states = pd.read_csv(file2)
states.columns = ['State','State-abbreviation']
data = pd.read_csv(file)

state_tup = []
stts = states.State.values
abbrvs = states['State-abbreviation'].values
dt_states = data.State.unique()

for i in range(len(stts)):
    state_tup.append((stts[i],abbrvs[i]))
    
st_abbrvs = {}
for st in dt_states:
    if st in stts:
        for i,j in state_tup:
            if st == i:
                st_abbrvs.setdefault(st,j)
            else:
                continue
    else:
        st_abbrvs.setdefault(st,'None')
        
data['State-abbreviation'] = data.State.map(st_abbrvs)


columns_to_drop = ['Row ID','Order ID','Customer ID','Customer Name',
                  'Segment','Country','City','Postal Code','Product ID',
                   'Product Name','Ship Mode']
data = data.drop(columns_to_drop,axis=1)

data['Order Date'] = pd.to_datetime(data['Order Date'])
data['Ship Date'] = pd.to_datetime(data['Ship Date'])

years = []

for dt in data['Order Date']:
    years.append(dt.strftime('%Y'))
    
data['Year'] = years
data = data.drop('Ship Date',axis=1)
data.State = data.State.str.strip()

market_data = data.copy()


def filter_data(data_frame,category='all',year='all'):
    if category == 'all' and year == 'all':
        data = data_frame
    elif category == 'all' and year != 'all':
        data = data_frame[data_frame.Year==year]
    elif category != 'all' and year == 'all':
        data = data_frame[data_frame.Category==category]
    else:
        data = data_frame[(data_frame.Category==category)&(data_frame.Year==year)]
    return data

def mkt_summary(df):
    data = df[['Year','Sales','Quantity','Profit']].groupby('Year').sum()
    data = data.T
    data = data.reset_index()
    data.columns = ['Metric','2014','2015','2016','2017']
    data['Pct_change'] = np.round(((data['2017'] - data['2016']) / data['2016'])*100,2)
    data = np.round(data,2)
    sales = (data.iloc[0,-2:][0],data.iloc[0,-2:][1])
    quantity = (data.iloc[1,-2:][0],data.iloc[1,-2:][1])
    profit = (data.iloc[2,-2:][0],data.iloc[2,-2:][1])
    discount = df[['Year','Discount']].groupby('Year').mean().T
    discount = np.round(discount['2017'][0],2)
    return sales,profit,quantity,discount


def sales_profit_scatter(dframe):
    data = dframe[['Order Date','Sales','Profit']].set_index('Order Date')
    data = data.resample('M').sum()
    traces = []
    colors = ['brown','grey']
    for cols,color in zip(data.columns,colors):
        xdata = data.index
        ydata = data[cols].values
        name = cols
        traces.append(go.Scatter(x=xdata,
                                y=ydata,
                                name=name,
                                mode='lines',
                                marker={'size':5,
                                        'color':color,
                                       'line':{'width':.2}}))
    layout = go.Layout(height=240,
                      xaxis={'showgrid':False,
                            'title':'<b>Period</b>',
                            'titlefont':{
                                'family':'Helvetica',
                                'size':14
                            }},
                      yaxis={'title':'<b>Amount $</b>',
                            'titlefont':{
                                'family':'Helvetica',
                                'size':14
                            }},
                      margin={'l':40,'r':35,'b':45,'t':35}
                      )
    return traces,layout


def quantity_scatter(data_frame):
    data = data_frame[['Order Date','Quantity']].set_index('Order Date')
    data = data.resample('M').sum()
    xdata = data.index
    ydata = data.values.reshape(1,-1)[0]
    trace = [go.Scatter(x=xdata,
                       y=ydata,
                       mode='lines',
                       marker={'size':5,
                               'color':'brown',
                               'line':{'width':.2}
                              })
            ]
    layout = go.Layout(height=240,
                      xaxis={'showgrid':False,
                            'title':'<b>Period</b>',
                            'titlefont':{
                                'family':'Helvetica',
                                'size':14
                            }},
                      yaxis={'title':'<b>Quantity sold</b>',
                            'titlefont':{
                                'family':'Helvetica',
                                'size':14
                            }},
                      margin={'l':55,'r':35,'b':45,'t':35}
                      )
    return trace,layout

def quantity_pie(data_frame):
    data = data_frame[['Region','Quantity']].groupby('Region').sum()
    labels = data.index
    vals = data.values.reshape(1,-1)[0]
    pie_chart = [
        go.Pie(labels=labels,
              values=vals,
              hole=.5,
              marker={'line':{'width':.2},
                     'colors':['brown','lightgrey','darkorange']})
    ]
    layout = go.Layout(height=240,
                      margin={'l':55,'r':35,'b':45,'t':35})
    return pie_chart,layout



def choro_map(d_frame,metric):
    state_data = d_frame[['State',
                          'State-abbreviation',metric]].groupby(['State',
                                                                         'State-abbreviation']).sum()
    state_data = state_data.reset_index()
    locations = state_data['State-abbreviation'].values
    z_data = state_data[metric].values
    text = state_data.State.values
    ch_map = [
        go.Choropleth(locations=locations,
                     locationmode='USA-states',
                     z=z_data,
                     autocolorscale=False,
                     colorscale='YlOrRd',
                     colorbar={'tickprefix':'$'},
                     text=text)
    ]
    layout = go.Layout(height=240,
                      margin={'l':5,
                              'r':5,
                              'b':5,
                              't':5},
                      geo={'scope':'usa',
                          'projection':{'type':'albers usa'},
                          'showframe':False})
    return ch_map,layout

def text_prefix_color(num):
    if num < 0:
        return '-','red'
    else:
        return '+','lightgreen'




app = dash.Dash(__name__)

server = app.server

app.title = 'Marketting Dashboard'

app.layout = html.Div(id='parent-div',children=[
    html.Div(className='main-container',children=[
        html.Div(children=[
            html.H4('King\'s Man Home, School, and Office Accessories Supplies Limited')
        ],className='curved border'),
        html.Div(className='row',
                 style={'margin-left':20,
                       'margin-right':20},
                 children=[
                    dcc.RadioItems(id='item-type',
                                  options=[
                                      {'label':'All products','value':'all'},
                                      {'label':'Furniture','value':'Furniture'},
                                      {'label':'Office Supplies','value':'Office Supplies'},
                                      {'label':'Technology','value':'Technology'}
                                  ],
                                  value='all',
                                  labelStyle={'display':'inline-block'},
                                  style={'float':'left'}),
                     html.A([html.Button('Contact designer',className='pill')],
                            href='https://twitter.com/iam_kwekhu',
                           style={'float':'right'})
                 ]),
        html.Div(id='first-child-div',
                 className='row',
                 style={'margin-left':20,
                       'margin-right':20,
                       'margin-top':15}),
        html.Br(),
        html.Div(className='row',
                style={'margin-left':20,
                       'margin-right':20,
                       'margin-top':15},
                children=[
                    html.Div(id='choro-container',
                            className='five columns',
                            children=[
                                html.Div(children=[
                                    html.P('Peformance by state',style={'fontWeight':'bold',
                                                                       'float':'left'}),
                                    dcc.RadioItems(id='metric',
                                                  options=[
                                                      {'label':i,'value':i} for i in ['Sales','Profit',
                                                                                     'Quantity']
                                                  ],
                                                  labelStyle={'display':'inline-block'},
                                                  value='Sales',
                                                  style={'float':'right'})
                                      
                                ]),
                                html.Br(),
                                html.Div(children=[
                                    dcc.Graph(id='usa-map')
                                ])
                            ]),
                    html.Div(id='sales-profit',
                            className='seven columns',
                            children=[
                                html.P('Business performance',style={'fontWeight':'bold'}),
                                dcc.Graph(id='sales-n-profit')
                            ])
                ]),
        html.Br(),
        html.Div(className='row',
                style={'margin-left':20,
                       'margin-right':20,
                       'margin-top':15},
                children=[
                    html.Div(id='pie-container',
                            className='five columns',
                            children=[
                                html.P('Products purchased by Regions',style={'fontWeight':'bold'}),
                                dcc.Graph(id='quantity-pie')
                            ]),
                    html.Div(id='quantity-scatter-plot',
                            className='seven columns',
                            children=[
                                html.P('Quantity of products sold over the years',
                                      style={'fontWeight':'bold'}),
                                dcc.Graph(id='quantity-scatter')
                            ])
                ]),
        html.Br()
        ])
])

@app.callback(Output('first-child-div','children'),
              [Input('item-type','value')])
def summary_content(item):
    sales,profit,quantity,discount = mkt_summary(filter_data(market_data,category=item))
    total_sales = np.abs(sales[0])
    pct_sales = np.abs(sales[1])
    total_rev = profit[0]
    pct_rev = profit[1]
    total_quant = np.abs(quantity[0])
    pct_quant = np.abs(quantity[1])
    avg_disc = discount
    
    
    content = [
             html.Div(id='total-sales',
                      className='three columns',
                      children=[
                          html.P('Annual Sales',style={'fontWeight':'bold'}),
                          html.Hr(),
                          html.P('$ {}'.format(total_sales),
                                style={'color':'brown',
                                      'fontSize':20,
                                      'textAlign':'center'}),
                          html.P('{} {}% from last year'.format(text_prefix_color(pct_sales)[0],
                                                                pct_sales),
                                style={'color':text_prefix_color(pct_sales)[1],
                                      'fontWeight':'bold',
                                      'textAlign':'center'})
                      ]),
             html.Div(id='total-revenue',
                      className='three columns',
                      children=[
                          html.P('Total Revenue',style={'fontWeight':'bold'}),
                          html.Hr(),
                          html.P('$ {}'.format(total_rev),
                                style={'color':'brown',
                                      'fontSize':20,
                                      'textAlign':'center'}),
                          html.P('{} {}% from last year'.format(text_prefix_color(pct_rev)[0],
                                                                np.abs(pct_rev)),
                                style={'color':text_prefix_color(pct_rev)[1],
                                      'fontWeight':'bold',
                                      'textAlign':'center'})
                      ]),
             html.Div(id='total-products',
                      className='three columns',
                      children=[
                          html.P('Total items sold',style={'fontWeight':'bold'}),
                          html.Hr(),
                          html.P('{}'.format(total_quant),
                                style={'color':'brown',
                                      'fontSize':20,
                                      'textAlign':'center'}),
                          html.P('{} {}% from last year'.format(text_prefix_color(pct_quant)[0],
                                                                pct_quant),
                                style={'color':text_prefix_color(pct_quant)[1],
                                      'fontWeight':'bold',
                                      'textAlign':'center'})
                      ]),
             html.Div(id='avg-discount',
                      className='three columns',
                      children=[
                          html.P('Average discount',style={'fontWeight':'bold'}),
                          html.Hr(),
                          html.P('{}%'.format(avg_disc*100),
                                style={'color':'brown',
                                      'fontSize':20,
                                      'textAlign':'center'}),
                          html.P('on {} products'.format(item),
                                 style={'color':'lightgreen',
                                        'fontWeight':'bold',
                                      'textAlign':'center'})
                      ])
        ]
    
    return content

@app.callback(Output('usa-map','figure'),
             [Input('metric','value'),
             Input('item-type','value')])
def render_map(metric,category):
    data_frame = filter_data(market_data,category,'2017')
    data,layout = choro_map(data_frame,metric)
    return {'data':data,'layout':layout}

@app.callback(Output('sales-n-profit','figure'),
             [Input('item-type','value')])
def scatter_plot(item):
    dff = filter_data(market_data,item)
    data,layout = sales_profit_scatter(dff)
    return {'data':data,'layout':layout}

@app.callback(Output('quantity-scatter','figure'),
             [Input('item-type','value')])
def quantity_plot(item):
    dff = filter_data(market_data,item)
    data,layout = quantity_scatter(dff)
    return {'data':data,'layout':layout}

@app.callback(Output('quantity-pie','figure'),
             [Input('item-type','value')])
def quantity_pie_plot(item):
    dff = filter_data(market_data,item,'2017')
    data,layout = quantity_pie(dff)
    return {'data':data,'layout':layout}


if __name__ == '__main__':
    app.run_server(debug=False)