import pandas as pd
import numpy as np
import json
import os
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output
import dash_table
from main import web_stats,trade_details,web_graph
import plotly.graph_objects as go
import plotly.express as px
from dash.exceptions import PreventUpdate
np.seterr(divide='ignore', invalid='ignore')

df = pd.DataFrame({"Total_P/L": [0],
                    "Trade_counts": [0],
                    "Return/Trade": [0],
                    "Profit_factor": [0]})
df.index = ["moving_avg_strategy"]

for files in os.listdir(os.getcwd()):
    if ".json" in files:
        file= open(os.path.join(os.getcwd(),"main.json"),"r")
        data= json.load(file)
        dataa= data["trading_parameters"]

strategies= ["Moving_Average_Strategy","upper"]

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = dash.Dash(__name__,external_stylesheets=external_stylesheets)

app.layout = html.Div(
    children=[
        html.H1("Automated Back-Testing",style={'text-align':'center','background-color': "#009999",
                                                'font-weight': 'bold'}),

        html.P("Select Strategy",style={'background-color': "#b3ffff" ,'font-weight': 'bold'}),
        dcc.Dropdown(id="Strategy_selection",
                     options=[{"label":"Moving_Average_Strategy" , "value": "Moving_Average_Strategy"} ,
                              {"label":"upper_circuit_strategy" , "value": "upper_circuit_strategy", 'disabled': True }],#for val in strategies
                     placeholder="select the strategy",style={"width": "45%"}),

        html.P("Select Moving avg no",style={'background-color': "#b3ffff" ,'font-weight': 'bold'}),
        dcc.Input(id="select_ma",type="number",placeholder="enter the number",style={"width": "20%"}),

        html.P("Strategy summary",style={'background-color': "#b3ffff" ,'font-weight': 'bold'}),
        dash_table.DataTable(id='table',
                            columns=[{"name": i, "id": i} for i in df.columns],
                            data= df.to_dict('records'),
                            style_header={'border': '1px solid black','background-color': "#ccfff5",
                                          'font-weight': 'bold'},#ccfff5
                            style_cell={'border': '1px solid grey'},
                            style_data={
                                    'whiteSpace': 'normal',
                                    'height': 'auto',
                                }
                             ),

        html.P("Stats_Graph",style={'background-color': "#b3ffff" ,'font-weight': 'bold'}),
        dcc.Graph(id="Year_wise_profit_Loss")
    ]
)

@app.callback(Output(component_id="Year_wise_profit_Loss", component_property= "figure"),
              [Input(component_id="Strategy_selection",component_property="value"),
               Input(component_id="select_ma",component_property="value")])

def update_graph(Strategy_selection,select_ma):
    #would get error bcoz we havent updates mean or any value and its trting to plot
    if Strategy_selection==None or select_ma==None :
        raise PreventUpdate
    elif Strategy_selection== "Moving_Average_Strategy":
        data_pat = dataa["data_path"]
        stats_df= pd.DataFrame(web_graph(data_path= data_pat, mavg_value=select_ma))
        fig1= px.bar(stats_df, x='Entrydate', y='returns',
                         hover_data=['Entrydate', 'returns'],
                         color= stats_df["pl_signal"],
                         color_discrete_map={
                             "Profit":"rgb(135,197,95)",
                             "Loss":"rgb(237,100,90)"
                         },
                         labels={'returns': 'profit & loss',"Entrydate":"Entry_year"}, height=600

                     )
        fig1.update_layout(title_text='2008-2018_Strategy_report')
        return fig1


@app.callback(Output(component_id="table", component_property= "data"),
              [Input(component_id="Strategy_selection", component_property="value"),
               Input(component_id="select_ma", component_property="value")])

def update_table(Strategy_selection,select_ma):
    if Strategy_selection==None or select_ma==None:
        raise PreventUpdate
    elif Strategy_selection=="Moving_Average_Strategy":
        data_path= dataa["data_path"]
        strategy_stat = web_stats(data_path,select_ma)
        columns=[{"name": i, "id": i} for i in strategy_stat.columns],
        data=strategy_stat.to_dict('records')
        return data




if __name__ =="__main__":
    app.run_server(debug=True, port=5001)