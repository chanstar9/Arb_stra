# -*- coding: utf-8 -*-
from datetime import datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

f = open('data/20200813_060412_All.txt', 'rb')
lines = f.readlines()
ticks = []
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
            ticks.append([datetime.fromtimestamp(float(tick[0])), tick[1][:5], tick[1][5:17], int(tick[1][34:43]),
                          int(tick[1][43:53])])
        if tick[1][:5] == "B6034":
            hoga.append([datetime.fromtimestamp(float(tick[0])), float(tick[1][32:37]) / 100, int(tick[1][37:44]),
                         float(tick[1][44:49]) / 100, int(tick[1][49:56]), float(tick[1][56:61]) / 100,
                         int(tick[1][61:68]),
                         float(tick[1][68:73]) / 100, int(tick[1][73:80]), float(tick[1][80:85]) / 100,
                         int(tick[1][85:92]),
                         float(tick[1][99:104]) / 100, int(tick[1][104:111]), float(tick[1][111:116]) / 100,
                         int(tick[1][116:123]),
                         float(tick[1][123:128]) / 100, int(tick[1][128:135]), float(tick[1][135:140]) / 100,
                         int(tick[1][140:147]),
                         float(tick[1][147:152]) / 100, int(tick[1][152:159])])

ticks = pd.DataFrame(ticks, columns=['Timestamp', 'TRCode', 'ProductCode', 'Price', 'volume'])
A3021, A3034, G7034 = ticks.groupby('TRCode')
A3034 = A3034[1]  # 옵션 체결
G7034 = G7034[1]  # 옵션 우선호가
A3021 = A3021[1]  # ELW

hoga = pd.DataFrame(hoga, columns=['Timestamp', "매수1단계우선호가가격", "매수1단계우선호가잔량", "매수2단계우선호가가격", "매수2단계우선호가잔량",
                                   "매수3단계우선호가가격", "매수3단계우선호가잔량", "매수4단계우선호가가격", "매수4단계우선호가잔량",
                                   "매수5단계우선호가가격", "매수5단계우선호가잔량", "매도1단계우선호가가격", "매도1단계우선호가잔량",
                                   "매도2단계우선호가가격", "매도2단계우선호가잔량", "매도3단계우선호가가격", "매도3단계우선호가잔량",
                                   "매도4단계우선호가가격", "매도4단계우선호가잔량", "매도5단계우선호가가격", "매도5단계우선호가잔량"])

A3021.set_index("Timestamp", inplace=True)
hoga.set_index("Timestamp", inplace=True)

account = []
for mkt_time, ELW in A3021.iterrows():
    if ELW["volume"] >= 2500:
        _df = hoga[hoga.index > mkt_time]
        if (_df.iloc[0]["매수1단계우선호가가격"] < ELW["Price"]) & (_df.iloc[0]["매도1단계우선호가가격"] > ELW["Price"]):
            if abs(_df.iloc[0]["매수1단계우선호가가격"] - ELW["Price"]) > abs(_df.iloc[0]["매도1단계우선호가가격"] - ELW["Price"]):
                # ELW 매수 포지션, option 매도 포지션
                account.append([mkt_time, ELW["Price"], 2500, _df.iloc[0]["매수1단계우선호가가격"], -1])
            if abs(_df.iloc[0]["매수1단계우선호가가격"] - ELW["Price"]) < abs(_df.iloc[0]["매도1단계우선호가가격"] - ELW["Price"]):
                # ELW 매도 포지션, option 매수 포지션
                account.append([mkt_time, ELW["Price"], -2500, _df.iloc[0]["매도1단계우선호가가격"], 1])
            if abs(_df.iloc[0]["매수1단계우선호가가격"] - ELW["Price"]) == abs(_df.iloc[0]["매도1단계우선호가가격"] - ELW["Price"]):
                if _df.iloc[0]["매수1단계우선호가잔량"] > _df.iloc[0]["매도1단계우선호가잔량"]:
                    # ELW 매도 포지션, option 매수 포지션
                    account.append([mkt_time, ELW["Price"], -2500, _df.iloc[0]["매도1단계우선호가가격"], 1])
                else:
                    # ELW 매수 포지션, option 매도 포지션
                    account.append([mkt_time, ELW["Price"], 2500, _df.iloc[0]["매수1단계우선호가가격"], -1])
        if _df.iloc[0]["매수1단계우선호가가격"] > ELW["Price"]:
            # ELW 매수 포지션, option 매도 포지션
            account.append([mkt_time, ELW["Price"], 2500, _df.iloc[0]["매수1단계우선호가가격"], -1])
        if _df.iloc[0]["매도1단계우선호가가격"] < ELW["Price"]:
            # ELW 매도 포지션, option 매수 포지션
            account.append([mkt_time, ELW["Price"], -2500, _df.iloc[0]["매도1단계우선호가가격"], 1])

# 정산
account = pd.DataFrame(account, columns=["Timestamp", "ELW_price", "ELW_volume", "Option_price", "Option_volume"])
account["balance"] = account.apply(
    lambda x: (190 - x["ELW_price"]) * x["ELW_volume"] - (x["ELW_price"] * x["ELW_volume"]) * 0.00015 +
              250000 * (1.88 - x["Option_price"]) * x["Option_volume"] - 195 * (x["Option_price"] * x["Option_volume"]),
    axis=1)

account["balance"].sum()
account["balance"].min()
account["balance"].max()
account["balance"].cumsum().plot()
plt.show()

# 계약수 N배
account2 = []
spread_num = 2
for mkt_time, ELW in A3021.iterrows():
    if ELW["volume"] >= 2500 * spread_num:
        _df = hoga[hoga.index > mkt_time].iloc[0]
        if (_df["매수1단계우선호가가격"] < ELW["Price"]) & (_df["매도1단계우선호가가격"] > ELW["Price"]):
            if abs(_df["매수1단계우선호가가격"] - ELW["Price"]) > abs(_df["매도1단계우선호가가격"] - ELW["Price"]):
                # ELW 매수 포지션, option 매도 포지션
                price_arr = _df[["매수1단계우선호가가격", "매수2단계우선호가가격", "매수3단계우선호가가격", "매수4단계우선호가가격", "매수5단계우선호가가격"]].values
                volume_arr = _df[["매수1단계우선호가잔량", "매수2단계우선호가잔량", "매수3단계우선호가잔량", "매수4단계우선호가잔량", "매수5단계우선호가잔량"]].values
                volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                account2.append([mkt_time, ELW["Price"], 2500 * spread_num, amt / spread_num, -spread_num])
            if abs(_df["매수1단계우선호가가격"] - ELW["Price"]) < abs(_df["매도1단계우선호가가격"] - ELW["Price"]):
                # ELW 매도 포지션, option 매수 포지션
                price_arr = _df[["매도1단계우선호가가격", "매도2단계우선호가가격", "매도3단계우선호가가격", "매도4단계우선호가가격", "매도5단계우선호가가격"]].values
                volume_arr = _df[["매도1단계우선호가잔량", "매도2단계우선호가잔량", "매도3단계우선호가잔량", "매도4단계우선호가잔량", "매도5단계우선호가잔량"]].values
                volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                account2.append([mkt_time, ELW["Price"], -2500 * spread_num, amt / spread_num, spread_num])
            if abs(_df["매수1단계우선호가가격"] - ELW["Price"]) == abs(_df["매도1단계우선호가가격"] - ELW["Price"]):
                if _df["매수1단계우선호가잔량"] > _df["매도1단계우선호가잔량"]:
                    # ELW 매도 포지션, option 매수 포지션
                    price_arr = _df[["매도1단계우선호가가격", "매도2단계우선호가가격", "매도3단계우선호가가격", "매도4단계우선호가가격", "매도5단계우선호가가격"]].values
                    volume_arr = _df[["매도1단계우선호가잔량", "매도2단계우선호가잔량", "매도3단계우선호가잔량", "매도4단계우선호가잔량", "매도5단계우선호가잔량"]].values
                    volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                    volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                    amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                    account2.append([mkt_time, ELW["Price"], -2500 * spread_num, amt / spread_num, spread_num])
                else:
                    # ELW 매수 포지션, option 매도 포지션
                    price_arr = _df[["매수1단계우선호가가격", "매수2단계우선호가가격", "매수3단계우선호가가격", "매수4단계우선호가가격", "매수5단계우선호가가격"]].values
                    volume_arr = _df[["매수1단계우선호가잔량", "매수2단계우선호가잔량", "매수3단계우선호가잔량", "매수4단계우선호가잔량", "매수5단계우선호가잔량"]].values
                    volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                    volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                    amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                    account2.append([mkt_time, ELW["Price"], 2500 * spread_num, amt / spread_num, -spread_num])
        if _df["매수1단계우선호가가격"] > ELW["Price"]:
            # ELW 매수 포지션, option 매도 포지션
            price_arr = _df[["매수1단계우선호가가격", "매수2단계우선호가가격", "매수3단계우선호가가격", "매수4단계우선호가가격", "매수5단계우선호가가격"]].values
            volume_arr = _df[["매수1단계우선호가잔량", "매수2단계우선호가잔량", "매수3단계우선호가잔량", "매수4단계우선호가잔량", "매수5단계우선호가잔량"]].values
            volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
            volume_arr[-1] = spread_num - volume_arr[:-1].sum()
            amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
            account2.append([mkt_time, ELW["Price"], 2500 * spread_num, amt / spread_num, -spread_num])
        if _df["매도1단계우선호가가격"] < ELW["Price"]:
            # ELW 매도 포지션, option 매수 포지션
            price_arr = _df[["매도1단계우선호가가격", "매도2단계우선호가가격", "매도3단계우선호가가격", "매도4단계우선호가가격", "매도5단계우선호가가격"]].values
            volume_arr = _df[["매도1단계우선호가잔량", "매도2단계우선호가잔량", "매도3단계우선호가잔량", "매도4단계우선호가잔량", "매도5단계우선호가잔량"]].values
            volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
            volume_arr[-1] = spread_num - volume_arr[:-1].sum()
            amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
            account2.append([mkt_time, ELW["Price"], -2500 * spread_num, amt / spread_num, spread_num])

account2 = pd.DataFrame(account2, columns=["Timestamp", "ELW_price", "ELW_volume", "Option_price", "Option_volume"])
account2["balance"] = account2.apply(
    lambda x: (190 - x["ELW_price"]) * x["ELW_volume"] - (x["ELW_price"] * x["ELW_volume"]) * 0.00015 +
              250000 * (1.88 - x["Option_price"]) * x["Option_volume"] - 195 * (x["Option_price"] * x["Option_volume"]),
    axis=1)

account2["balance"].sum()
account2["balance"].min()
account2["balance"].max()
account2["balance"].cumsum().plot()
plt.show()

# 계약수 N배
account3 = []
spread_num = 3
for mkt_time, ELW in A3021.iterrows():
    if ELW["volume"] >= 2500 * spread_num:
        _df = hoga[hoga.index > mkt_time].iloc[0]
        if (_df["매수1단계우선호가가격"] < ELW["Price"]) & (_df["매도1단계우선호가가격"] > ELW["Price"]):
            if abs(_df["매수1단계우선호가가격"] - ELW["Price"]) > abs(_df["매도1단계우선호가가격"] - ELW["Price"]):
                # ELW 매수 포지션, option 매도 포지션
                price_arr = _df[["매수1단계우선호가가격", "매수2단계우선호가가격", "매수3단계우선호가가격", "매수4단계우선호가가격", "매수5단계우선호가가격"]].values
                volume_arr = _df[["매수1단계우선호가잔량", "매수2단계우선호가잔량", "매수3단계우선호가잔량", "매수4단계우선호가잔량", "매수5단계우선호가잔량"]].values
                volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                account3.append([mkt_time, ELW["Price"], 2500 * spread_num, amt / spread_num, -spread_num])
            if abs(_df["매수1단계우선호가가격"] - ELW["Price"]) < abs(_df["매도1단계우선호가가격"] - ELW["Price"]):
                # ELW 매도 포지션, option 매수 포지션
                price_arr = _df[["매도1단계우선호가가격", "매도2단계우선호가가격", "매도3단계우선호가가격", "매도4단계우선호가가격", "매도5단계우선호가가격"]].values
                volume_arr = _df[["매도1단계우선호가잔량", "매도2단계우선호가잔량", "매도3단계우선호가잔량", "매도4단계우선호가잔량", "매도5단계우선호가잔량"]].values
                volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                account3.append([mkt_time, ELW["Price"], -2500 * spread_num, amt / spread_num, spread_num])
            if abs(_df["매수1단계우선호가가격"] - ELW["Price"]) == abs(_df["매도1단계우선호가가격"] - ELW["Price"]):
                if _df["매수1단계우선호가잔량"] > _df["매도1단계우선호가잔량"]:
                    # ELW 매도 포지션, option 매수 포지션
                    price_arr = _df[["매도1단계우선호가가격", "매도2단계우선호가가격", "매도3단계우선호가가격", "매도4단계우선호가가격", "매도5단계우선호가가격"]].values
                    volume_arr = _df[["매도1단계우선호가잔량", "매도2단계우선호가잔량", "매도3단계우선호가잔량", "매도4단계우선호가잔량", "매도5단계우선호가잔량"]].values
                    volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                    volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                    amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                    account3.append([mkt_time, ELW["Price"], -2500 * spread_num, amt / spread_num, spread_num])
                else:
                    # ELW 매수 포지션, option 매도 포지션
                    price_arr = _df[["매수1단계우선호가가격", "매수2단계우선호가가격", "매수3단계우선호가가격", "매수4단계우선호가가격", "매수5단계우선호가가격"]].values
                    volume_arr = _df[["매수1단계우선호가잔량", "매수2단계우선호가잔량", "매수3단계우선호가잔량", "매수4단계우선호가잔량", "매수5단계우선호가잔량"]].values
                    volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
                    volume_arr[-1] = spread_num - volume_arr[:-1].sum()
                    amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
                    account3.append([mkt_time, ELW["Price"], 2500 * spread_num, amt / spread_num, -spread_num])
        if _df["매수1단계우선호가가격"] > ELW["Price"]:
            # ELW 매수 포지션, option 매도 포지션
            price_arr = _df[["매수1단계우선호가가격", "매수2단계우선호가가격", "매수3단계우선호가가격", "매수4단계우선호가가격", "매수5단계우선호가가격"]].values
            volume_arr = _df[["매수1단계우선호가잔량", "매수2단계우선호가잔량", "매수3단계우선호가잔량", "매수4단계우선호가잔량", "매수5단계우선호가잔량"]].values
            volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
            volume_arr[-1] = spread_num - volume_arr[:-1].sum()
            amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
            account3.append([mkt_time, ELW["Price"], 2500 * spread_num, amt / spread_num, -spread_num])
        if _df["매도1단계우선호가가격"] < ELW["Price"]:
            # ELW 매도 포지션, option 매수 포지션
            price_arr = _df[["매도1단계우선호가가격", "매도2단계우선호가가격", "매도3단계우선호가가격", "매도4단계우선호가가격", "매도5단계우선호가가격"]].values
            volume_arr = _df[["매도1단계우선호가잔량", "매도2단계우선호가잔량", "매도3단계우선호가잔량", "매도4단계우선호가잔량", "매도5단계우선호가잔량"]].values
            volume_arr = volume_arr[:np.argmin(np.where(volume_arr.cumsum() >= spread_num)) + 1]
            volume_arr[-1] = spread_num - volume_arr[:-1].sum()
            amt = (price_arr[:len(volume_arr)] * volume_arr).sum()
            account3.append([mkt_time, ELW["Price"], -2500 * spread_num, amt / spread_num, spread_num])

account3 = pd.DataFrame(account3, columns=["Timestamp", "ELW_price", "ELW_volume", "Option_price", "Option_volume"])
account3["balance"] = account3.apply(
    lambda x: (190 - x["ELW_price"]) * x["ELW_volume"] - (x["ELW_price"] * x["ELW_volume"]) * 0.00015 +
              250000 * (1.88 - x["Option_price"]) * x["Option_volume"] - 195 * (x["Option_price"] * x["Option_volume"]),
    axis=1)

account3["balance"].sum()
account3["balance"].min()
account3["balance"].max()
account3["balance"].cumsum().plot()
plt.show()

account.set_index("Timestamp", inplace=True)
account2.set_index("Timestamp", inplace=True)
account3.set_index("Timestamp", inplace=True)

test = account[["balance"]].cumsum()
test["balance2"] = account2["balance"].cumsum()

aa = account[["Timestamp", "balance"]].merge(account2[["Timestamp", "balance"]], on="Timestamp", how="outer")
aa = pd.merge(aa, account3, on=["Timestamp"], how="outer")
aa = aa[["balance_x", "balance_y", "balance"]].cumsum()
aa.fillna(method='ffill', inplace=True)
aa.plot()
plt.show()

cnt = 0
j = 0
for i in account["Timestamp"].values:
    if i in account2["Timestamp"].values:
        cnt += 1
    else:
        j += 1
