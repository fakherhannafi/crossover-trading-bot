# In[1]:


# I have covered this script in my previous video!


# In[2]:

import pandas as pd
from binance.client import Client
from binance import BinanceSocketManager
import numpy as np
import asyncio
# In[5]:
API_KEY = '<enter_api_key>'
API_SECRET = '<enter_api_secret>'

client = Client(API_KEY, API_SECRET)


ST = 7
LT = 25
pair = 'ADAUSDT'


def gethistoricals(symbol, LT):
    df = pd.DataFrame(client.get_historical_klines(
        symbol, '1d', str(LT) + 'days ago  UTC', '1 day ago UTC'))
    closes = pd.DataFrame(df[4])
    closes.columns = ['Close']
    closes['ST'] = closes.Close.rolling(ST-1).sum()
    closes['LT'] = closes.Close.rolling(LT-1).sum()
    closes.dropna(inplace=True)
    return closes


historicals = gethistoricals(pair, LT)
print(historicals)


def liveSMA(hist, live):
    liveST = (hist['ST'].values + live.Price.values)/ST
    liveLT = (hist['LT'].values + live.Price.values)/LT
    return liveST, liveLT


def createframe(msg):
    df = pd.DataFrame([msg])
    df = df.loc[:, ['s', 'E', 'p']]
    df.columns = ['symbol', 'Time', 'Price']
    df.Price = df.Price.astype(float)
    df.Time = pd.to_datetime(df.Time, unit='ms')
    return df


async def main(coin, qty, SL_limit, open_position=False):
    bm = BinanceSocketManager(client)
    ts = bm.trade_socket(coin)
    async with ts as tscm:
        while True:
            res = await tscm.recv()
            if res:
                frame = createframe(res)
                print(frame)
                livest, livelt = liveSMA(historicals, frame)
                if livest > livelt and not open_position:
                    order = client.create_order(
                        symbol=coin, side='BUY', type='MARKET', quantity=qty)
                    print(order)
                    buyprice = float(order['fills'][0]['price'])
                    open_position = True
                if open_position:
                    if frame.Price[0] < buyprice * SL_limit or frame.Price[0] > 1.02 * buyprice:
                        order = client.create_order(
                            symbol=coin, side='SELL', type='MARKET', quantity=qty)
                        print(order)
                        loop.stop()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(pair, 50, 0.98))
