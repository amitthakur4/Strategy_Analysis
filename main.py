import numpy as np
import pandas as pd
import json
import os
from utils import reading_components
from tqdm import tqdm
import plotly.express as px
from tabulate import tabulate


#reading json from class reading_components
config_reader= reading_components()
filename= os.path.basename(__file__).split(".")[0] + ".json"
json_data=config_reader.config_json(filename)



def moving_average_df(data_path : str, mavg_value: int):
    """
    :param data_path:  close price data path to be give through json
    :param mavg_value: the moving average number you want to apply on your dataset through json
    :return: Dataframe
    """
    cls= reading_components()
    close_price_data= cls.read_files(data_path)
    mavg_df= close_price_data.rolling(window = int(mavg_value)).mean()
    return close_price_data, mavg_df


# def stats_df(data_path, mavg_value):
#     close_pr_df, moving_avg_df= moving_average_df(data_path,int(mavg_value))
#     Trade_call = []
#     entry_data = []
#     exit_data = []
#
#     for i in tqdm(close_pr_df.columns[1:]):
#         Trade_call.clear()
#         for j in range(close_pr_df.shape[0]):
#             if len(Trade_call) == 0:
#                 if (moving_avg_df.loc[j, i] < close_pr_df.loc[j, i]) & (j != close_pr_df.shape[0] - 1):  #
#                     entry_data.append(dict(stock=i, entry_date=str(close_pr_df.iloc[j, 0]),
#                                            entry_value=close_pr_df.loc[j, [i]][0]))
#                     Trade_call.append(1)
#                 else:
#                     continue
#             else:
#                 if (moving_avg_df.loc[j, i] > close_pr_df.loc[j, i]):
#                     exit_data.append(dict(exit_date=str(close_pr_df.iloc[j, 0]),
#                                           exit_value=close_pr_df.loc[j, [i]][0],
#                                           ))
#                     Trade_call.clear()
#                 else:
#                     if (j == (close_pr_df.shape[0] - 1)) & (len(Trade_call) > 0):
#                         exit_data.append(dict(exit_date=str(close_pr_df.iloc[j, 0]),
#                                               exit_value=close_pr_df.loc[j, [i]][0]
#                                               ))
#                     else:
#                         continue
#     stats= pd.concat([pd.DataFrame(entry_data), pd.DataFrame(exit_data)],axis=1).reset_index(drop=True)
#     stats.iloc[:,[1,3]]=stats.iloc[:,[1,3]].apply(pd.to_datetime, errors="coerce" )
#     # stats["days_traded"]= (stats.exit_date - stats.entry_date).dt.days
#     stats["P_&_L"]= stats.exit_value - stats.entry_value
#     return stats

flag = True #Initial value
def checkAndInvert(x):
    """
    :param x: Series [ will read the column of dataframe and reaarge exmpl .. 1st it will look for true and then false ,
                     b4 true everything would be nan, and after false it will again look at true and repeat else nan
    :return: Series
    """
    global flag #Using the global value, because we need the previous states
    if x == flag:
        #If the flag matches then invert and return the same value
        flag = False if flag==True else True
        return x
    #if the flag does not match then return NAN
    return np.nan


def trade_details(data_path, mavg_value):
    """
    :param data_path: String [ path of the close value dataframe]
    :param mavg_value: dataframe [ moving average calculated dataframe ]
    :return: dataframe
    """
    close_pr_df, moving_avg_df = moving_average_df(data_path, int(mavg_value))
    moving_avg_df= pd.concat([pd.DataFrame(close_pr_df.iloc[:,0],columns=["TRADING_DATE"]),moving_avg_df.iloc[:,:]],axis=1)
    close_pr_df = close_pr_df.set_index('TRADING_DATE')
    close_pr_df.fillna(0,inplace=True)
    moving_avg_df = moving_avg_df.set_index('TRADING_DATE')


    mask = close_pr_df > moving_avg_df
    mask.iloc[-1,:] = False
    mask.iloc[-1,:]=mask.iloc[-1,:].fillna(False)
    for col in mask.columns:
        flag = True  # Initialise the global value back to True
        mask[col] = mask[col].apply(checkAndInvert)
    mask.to_dict(orient='list')

    #taking out entry and exit stats and and combining them
    entry=  close_pr_df[mask == True].stack().reset_index(name="Entry_value").\
            rename(columns={"level_1": "stock", "TRADING_DATE": "Entrydate"})#.sort_values("Entrydate").reset_index(drop=True)
    entry["Entrydate"]=pd.to_datetime(entry["Entrydate"])
    entry= entry.sort_values(["stock","Entrydate"]).reset_index(drop=True)

    exit = close_pr_df[mask == False].stack().reset_index(name="Exit_value"). \
        rename(columns={"level_1": "exit_stock", "TRADING_DATE": "Exitdate"})  # .sort_values("Exitdate").reset_index(drop=True)
    exit["Exitdate"] = pd.to_datetime(exit["Exitdate"])
    exit = exit.sort_values(["exit_stock", "Exitdate"]).reset_index(drop=True)
    
    stats=pd.concat([entry,exit],axis=1)
    stats["returns"]= round(stats["Exit_value"]-stats["Entry_value"],2)
    return stats

def web_stats(path, mvng_avg):
    stat_file= trade_details(data_path=path , mavg_value=mvng_avg)
    a=stat_file.loc[stat_file["returns"] > 0, ["returns"]].sum().values
    b=stat_file.loc[stat_file["returns"] <= 0, ["returns"]].sum().values

    pt_factor_value = round(list(a/abs(b))[0],2)

    strategy_stats = pd.DataFrame({"Total_P/L": [np.nansum(stat_file["returns"])],
                                   "Trade_counts": stat_file.shape[0],
                                   "Return/Trade": [round(stat_file["returns"].mean(), 2)],
                                   "Profit_factor": [pt_factor_value]})
    strategy_stats["Total_P/L"]=strategy_stats["Total_P/L"].astype(float).round(2)
    strategy_stats.index = ["moving_avg_strategy"]
    return strategy_stats


def web_graph(data_path,mavg_value):
    trade_details_df =trade_details(data_path,mavg_value)
    yr_wise_pnl = trade_details_df.loc[:, ["Entrydate", "returns"]]
    yr_wise_pnl["Entrydate"] = yr_wise_pnl["Entrydate"].dt.year
    yr_wise_pnl = yr_wise_pnl.groupby(["Entrydate"]).aggregate({"returns": sum}).reset_index()
    yr_wise_pnl["Entrydate"]=yr_wise_pnl["Entrydate"].astype(dtype=object)
    yr_wise_pnl["returns"]= yr_wise_pnl["returns"].astype(float).round(2)
    yr_wise_pnl["pl_signal"] = pd.DataFrame(np.where(yr_wise_pnl["returns"] > 0, "Profit", "Loss"))
    return yr_wise_pnl


if __name__ == '__main__':
    path=json_data["data_path"]
    mavg= json_data["moving_avg_day"]
    trade_details_df=web_graph( path,mavg )

#     pt_factor_value= round(list(trade_details_df.loc[trade_details_df["returns"] > 0, ["returns"]].sum().values / abs(
#         trade_details_df.loc[trade_details_df["returns"] <= 0, ["returns"]].sum().values))[0],2)
#
#     strategy_stats= pd.DataFrame({"Total_P/L":[np.nansum(trade_details_df["returns"])],
#                           "Trade_counts": trade_details_df.shape[0],
#                           "Return/Trade":[round(trade_details_df["returns"].mean(),2)],
#                           "Profit_factor":[pt_factor_value]})
#     strategy_stats.index=["moving_avg_strategy"]
#     print(tabulate(strategy_stats,headers='keys'))
#
#     yr_wise_pnl=trade_details_df.loc[:,["Entrydate","returns"]]
#     yr_wise_pnl["Entrydate"] = yr_wise_pnl["Entrydate"].dt.year
#     yr_wise_pnl=round(yr_wise_pnl.groupby(["Entrydate"]).aggregate({"returns":sum}).reset_index(),2)
#
#     if json_data["watch_plot"]==True:
#         fig = px.bar(yr_wise_pnl, x='Entrydate', y='returns',
#                      hover_data=['Entrydate', 'returns'], color='returns',
#                      labels={'returns': 'profit & loss',"Entrydate":"Entry_year"}, height=600)
#         fig.update_layout(title_text='2008-2018_Strategy_report')
#         fig.show()
#     else:
#         pass
#
#
#


    #     fig = go.Figure(data=[go.Scatter(x=yr_wise_pnl['Entrydate'], y=yr_wise_pnl['returns'])])
    #     fig.update_layout(
    #              title={
    #             'text': "Year_wise_PnL",
    #             'y': 0.9,
    #             'x': 0.5,
    #             'xanchor': 'center',
    #             'yanchor': 'top'})
    #     fig.show()
    # else:
    #     pass






