# -*- coding: utf-8 -*-
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

f = open('data/20200813_060412_All.txt', 'rb')
lines = f.readlines()
ticks = []
ELW = []
hoga = []

for line in lines:
    tick = line.decode('utf-8', errors='ignore').split('[')
    if len(tick) <= 1:
        continue
    tick[0] = tick[0][:-1]
    if (tick[1][5:17] == "KRA5731BZA10") or (tick[1][5:17] == "KR4201Q83259"):
        if (tick[1][:5] == "A3034") or (tick[1][:5] == "G7034"):
            ticks.append(
                [datetime.fromtimestamp(float(tick[0])), tick[1][:5], tick[1][5:17], float(tick[1][23:28]) / 100,
                 int(tick[1][28:35])])
        if tick[1][:5] == "A3021":
            ELW.append([datetime.fromtimestamp(float(tick[0])), tick[1][:5], tick[1][5:17], int(tick[1][34:43]),
                        int(tick[1][43:53]), int(tick[1][135:144]), int(tick[1][144:153])])
        if tick[1][:5] == "B6034":
            hoga.append(
                [datetime.fromtimestamp(float(tick[0])), float(tick[1][32:37]) / 100, int(tick[1][37:44]),
                 float(tick[1][99:104]) / 100, int(tick[1][104:111])])

ticks = pd.DataFrame(ticks, columns=['Timestamp', 'TRCode', 'ProductCode', 'Price', 'volume'])
A3034, G7034 = ticks.groupby('TRCode')
A3034 = A3034[1]  # 옵션 체결
G7034 = G7034[1]  # 옵션 우선호가
# ELW
A3021 = pd.DataFrame(ELW, columns=['Timestamp', 'TRCode', 'ProductCode', 'Price', 'volume', "매도1호가", "매수1호가"])
A3021["매도1호가"] = A3021.apply(lambda x: x["매도1호가"] if x["매도1호가"] != 0 else None, axis=1)
A3021["매수1호가"] = A3021.apply(lambda x: x["매수1호가"] if x["매수1호가"] != 0 else None, axis=1)
A3021.fillna(method='ffill', inplace=True)
A3021 = A3021.iloc[1:]
hoga = pd.DataFrame(hoga, columns=['Timestamp', "매수1단계우선호가가격", "매수1단계우선호가잔량", "매도1단계우선호가가격", "매도1단계우선호가잔량"])

A3021.set_index("Timestamp", inplace=True)
hoga.set_index("Timestamp", inplace=True)

# 시장규모
account3 = []
for mkt_time, ELW_tick in A3021.iterrows():
    spread_num = ELW_tick["volume"] // 2500
    if spread_num:
        _df = hoga[hoga.index > mkt_time].iloc[0]
        mid_op_p = (_df["매수1단계우선호가가격"] + _df["매도1단계우선호가가격"]) / 2
        spread = abs(mid_op_p - (ELW_tick["매도1호가"] + ELW_tick["매수1호가"])/2)
        if (_df["매수1단계우선호가가격"] * 100 < ELW_tick["Price"]) & (_df["매도1단계우선호가가격"] * 100 > ELW_tick["Price"]):
            if abs(_df["매수1단계우선호가가격"] * 100 - ELW_tick["Price"]) > abs(
                    _df["매도1단계우선호가가격"] * 100 - ELW_tick["Price"]):
                # ELW 매수 포지션, option 매도 포지션
                account3.append([mkt_time, ELW_tick["Price"], 2500 * spread_num, mid_op_p, -spread_num, spread])
            if abs(_df["매수1단계우선호가가격"] * 100 - ELW_tick["Price"]) < abs(
                    _df["매도1단계우선호가가격"] * 100 - ELW_tick["Price"]):
                # ELW 매도 포지션, option 매수 포지션
                account3.append([mkt_time, ELW_tick["Price"], -2500 * spread_num, mid_op_p, spread_num, spread])
            if abs(_df["매수1단계우선호가가격"] * 100 - ELW_tick["Price"]) == abs(
                    _df["매도1단계우선호가가격"] * 100 - ELW_tick["Price"]):
                if _df["매수1단계우선호가잔량"] > _df["매도1단계우선호가잔량"]:
                    # ELW 매도 포지션, option 매수 포지션
                    account3.append([mkt_time, ELW_tick["Price"], -2500 * spread_num, mid_op_p, spread_num, spread])
                else:
                    # ELW 매수 포지션, option 매도 포지션
                    account3.append([mkt_time, ELW_tick["Price"], 2500 * spread_num, mid_op_p, -spread_num, spread])
        if _df["매수1단계우선호가가격"] * 100 > ELW_tick["Price"]:
            # ELW 매수 포지션, option 매도 포지션
            account3.append([mkt_time, ELW_tick["Price"], 2500 * spread_num, mid_op_p, -spread_num, spread])
        if _df["매도1단계우선호가가격"] * 100 < ELW_tick["Price"]:
            # ELW 매도 포지션, option 매수 포지션
            account3.append([mkt_time, ELW_tick["Price"], -2500 * spread_num, mid_op_p, spread_num, spread])

account3 = pd.DataFrame(account3, columns=["Timestamp", "ELW_price", "ELW_volume", "Option_price", "spread_num", "spread"])
account3["edge"] = account3.apply(
    lambda x: x["ELW_price"] - x["Option_price"] * 100 if x["spread_num"] > 0 else 100 * x["Option_price"] - x[
        "ELW_price"],
    axis=1)

account3["edge"].sum()
account3["edge"].min()
account3["edge"].max()
account3["edge"].cumsum().plot()
plt.show()
