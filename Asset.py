import datetime
import time
import ccxt
import pyupbit
import telegram

# 텔레그램 봇
bot = telegram.Bot(token="5018511910:AAH63St5u0GB8m5WvjOyksAGeRPMWP8NZ2A")
chat_id = "5027533498"
bot.sendMessage(chat_id=chat_id, text="매 15분마다 잔고 업데이트 및 신고점 & 저점시에 메시지 전송합니다") # 메세지 보내기

#업비트
price = pyupbit.get_current_price
access = "VSNMzyDIyAgHzhpk6Najyo6DahZbLGT8xYnEpWd3"
secret = "uvSS9zdcRPc22JkxPbYtLMbeGlb5vcbuahzxxeNa"
upbit = pyupbit.Upbit(access, secret)

# 바이낸스
exchange = ccxt.binance()
exchange.apiKey = ''
exchange.secret = ''
balance = exchange.fetch_balance(params={"type": "future"})

업비트H = 30000000
업비트L = 30000000
바이낸스H = 20000000
바이낸스L = 20000000
바이낸스UH = 17000
바이낸스UL = 17000
전체H = 50000000
전체L = 50000000
Time = 15
update = 900 #seconds (업데이트간 간격)
전체MDD = 0
업비트MDD = 0
바이낸스MDD = 0

while True:
    try:
        def get_start_time(ticker):
            """시작 시간 조회"""
            df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
            start_time = df.index[0]
            return start_time

        now = datetime.datetime.now()
        start_time = get_start_time("KRW-BTC")
        end_time1 = start_time + datetime.timedelta(hours=8) # 업비트 시장 시작 시간 + 8시간, 5시
        end_time2 = end_time1 + datetime.timedelta(hours=8) # 업비트 시장 시작 시간 + 16시간, 다음날 1시
        end_time3 = end_time2 + datetime.timedelta(hours=8) # 업비트 시장 시작 시간 + 24시간, 다음날 9시

        # 역분사 시에 잠시 멈춤
        while (end_time1 - datetime.timedelta(minutes=Time) < now < end_time1 + datetime.timedelta(minutes=Time) ) or (end_time2 - datetime.timedelta(minutes=Time) < now < end_time2 + datetime.timedelta(minutes=Time) ) or (end_time3 - datetime.timedelta(minutes=Time) < now < end_time3 + datetime.timedelta(minutes=Time)) :
            now = datetime.datetime.now()
            time.sleep(180)

        quity = 0
        df    = upbit.get_balances()
        COINS = len(df)

        for s in range(0,COINS) :
            if str(df[s]['currency']) == 'KRW' :
                quity += float(df[s]['balance']) + float(df[s]['locked'])
            elif (str(df[s]['unit_currency']) == 'KRW') and (float(df[s]['avg_buy_price']) > 0) :
                quity += (float(df[s]['balance']) + float(df[s]['locked'] )) * pyupbit.get_current_price(str(df[s]['unit_currency'])+"-"+str(df[s]['currency']))

        업비트잔고 = quity

        #바이낸스 평가금 확인 (USDT/KRW 기준)


        ticker = exchange.fetch_ticker('BTC/USDT')
        바이낸스잔고 = float(balance['total']['USDT'])
        USDT = price("KRW-BTC")/ticker['close']
        바이낸스KRW잔고 = 바이낸스잔고*USDT
        전체잔고 = 바이낸스KRW잔고 + 업비트잔고
        
        # 메세지 보내기  
        nowh = int(now.strftime('%H'))
        nowm = int(now.strftime('%M'))
        nowf = now.strftime('%Y-%m-%d %H:%M') 

        전체H = max(전체H, 전체잔고)
        전체L = min(전체L, 전체잔고)
        전체DD = 100-전체잔고/전체H * 100
        전체MDD = max(전체DD, 전체MDD)

        업비트H = max(업비트H, 업비트잔고)
        업비트L = min(업비트L, 업비트잔고)
        업비트DD = 100-업비트잔고/업비트H * 100
        업비트MDD = max(업비트DD, 업비트MDD)

        바이낸스H = max(바이낸스H, 바이낸스KRW잔고)
        바이낸스L = min(바이낸스L, 바이낸스KRW잔고)
        바이낸스DD = 100-바이낸스KRW잔고/바이낸스H * 100
        바이낸스MDD = max(바이낸스DD, 바이낸스MDD)

        바이낸스UH = max(바이낸스UH, 바이낸스잔고)
        바이낸스UL = min(바이낸스UL, 바이낸스잔고)
        MSG = nowf+"\n업비트 : "+str(format(int(업비트잔고),',d'))+"원 (DD: "+str(int(업비트DD*100)/100)+"%)"+"\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT, DD: "+str(int(바이낸스DD*100)/100)+"%)"+"\n전체 : "+str(format(int(전체잔고),',d'))+"원 (DD: "+str(int(전체DD*100)/100)+"%)"
        #매 4시간 마다 전송하는 메시지
        MSG2 = "업비트 MDD :"+str(int(업비트MDD*100)/100)+"%\n 바이낸스 MDD:"+str(int(바이낸스MDD*100)/100)+"%\n 전체 MDD:"+str(int(전체MDD*100)/100)+"%"
        #MDD 달성시에 전송하는 메시지

        if 전체H == 전체잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 전체 잔고 신고점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
        elif 전체L == 전체잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 전체 잔고 신저점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
            bot.sendMessage(chat_id=chat_id, text=MSG2)
        elif 업비트H == 업비트잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 업비트 잔고 신고점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
        elif 업비트L == 업비트잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 업비트 잔고 신저점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
            bot.sendMessage(chat_id=chat_id, text=MSG2)
        elif 바이낸스H == 바이낸스KRW잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 바이낸스 잔고 신고점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
        elif 바이낸스L == 바이낸스KRW잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 바이낸스 잔고 신저점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
            bot.sendMessage(chat_id=chat_id, text=MSG2)
        elif 바이낸스UH == 바이낸스잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 바이낸스 잔고(USDT) 신고점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
        elif 바이낸스UL == 바이낸스잔고 :
            bot.sendMessage(chat_id=chat_id, text=nowf+" 바이낸스 잔고(USDT) 신저점 달성\n업비트 : "+str(format(int(업비트잔고),',d'))+"원\n바이낸스 : "+str(format(int(바이낸스KRW잔고),',d'))+"원 ("+str('{:0,.2f}'.format(바이낸스잔고))+"USDT)\n전체 : "+str(format(int(전체잔고),',d'))+"원")
            bot.sendMessage(chat_id=chat_id, text=MSG2)
        elif (int((nowh -1)/4) == (nowh -1)/4) and (nowm < 25) : 
            bot.sendMessage(chat_id=chat_id, text=MSG)

    # 예외 처리
    except Exception as e:
        print(e)

    # 10분 기다림
    time.sleep(update)
