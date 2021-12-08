import datetime
import time
import ccxt
import pyupbit
import telegram
import sys
import ChatBotModel


def asset(bot, update):
    now = datetime.datetime.now()
    nowf = now.strftime('%Y-%m-%d %H:%M') 
    refresh.sendMessage(nowf+" 잔고 검색 중")
    
    #업비트
    access = ""
    secret = ""
    upbit  = pyupbit.Upbit(access, secret)
    price  = pyupbit.get_current_price

    quity = 0
    df=upbit.get_balances()
    COINS = len(df)

    for s in range(0,COINS) :
        if str(df[s]['currency']) == 'KRW' :
            quity += float(df[s]['balance']) + float(df[s]['locked'])
        elif (str(df[s]['unit_currency']) == 'KRW') and (float(df[s]['avg_buy_price']) > 0) :
            quity += (float(df[s]['balance']) + float(df[s]['locked'] )) * float(pyupbit.get_current_price(str(df[s]['unit_currency'])+"-"+str(df[s]['currency'])))

    업비트잔고 = quity

    #바이낸스
    exchange = ccxt.binance()
    exchange.apiKey = ''
    exchange.secret = ''
    balance = exchange.fetch_balance(params={"type": "future"})

    ticker = exchange.fetch_ticker('BTC/USDT')
    바이낸스잔고 = float(balance['total']['USDT'])
    USDT = price("KRW-BTC")/ticker['close']
    바이낸스KRW잔고 = 바이낸스잔고*USDT
    전체잔고 = 바이낸스KRW잔고 + 업비트잔고
    nowf = now.strftime('%Y-%m-%d %H:%M') 
    T = nowf+"\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원"
    refresh.sendMessage(T)

def proc_stop(bot, update):
    refresh.sendMessage('봇 종료')
    refresh.stop()

refresh = ChatBotModel.Botupdate()
refresh.add_handler('update', asset)
refresh.add_handler('stop', proc_stop)
refresh.start()