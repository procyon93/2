import pandas as pd
import datetime
from pandas import DataFrame
from pandas import Series
import time
import pyupbit #pip install pyupbit
import telegram #pip install python-telegram-bot
import pandas_ta as ta #pip install pandas_ta

#전략 세팅 (8시간)
hrs             = 8      # 매 8시간마다 실행 (4의 배수만 넣어주세요. 최대 24시간)
reb_qty         = 0.6    # 리밸런싱 전략 코인당 비중 (% 기준)
Coins           = 25     # 동일가중 매수 코인 수
basic           = 10     # 하락 여부 상관 없이, 포함시킬 코인 수
limit           = 10     # 익절/손절 라인 (%)
Elength         = 30     # EMA기준 (length, 30봉)
Time            = 8      # 거래량 검색 시간 -> 컴퓨터 사양 고려
Time2           = 4      # 매도 시작시간 #Time보다 작아야함
Out             = 15     # out of market 시에 몇 % 씩 팔지
Out2            = 20     # EMA 밑으로 떨어지면 몇 % 씩 팔지

#매수전략
isbuymarket     = False     # 전액 시장가 매수 <- 최소주문금액에 주의하세요. (True or False)
Acc             = 100000    # 분할 매수 기준 (x원 이상일 경우 지정가 분할 매수 시행)
                            # 최소 주문금액이 5천원 이므로, ACCqty * ACC /100 값이 5000 이상이여야 돌아갑니다.
Accdiv          = 2         # 분할매수 수 (0 또는 자연수를 입력하세요, 분할 원치 않는 경우 0을 입력하세요)
Accgap          = 0.5       # 분할매수 갭 (% 기준)
bid_price_div   = 2         # 아래호가 매수 수 (0 또는 자연수를 입력하세요, 분할 원치 않는 경우 0을 입력하세요)
Accqty          = 8         # 분할 매수 비중 (% 기준)
isbuyreorder    = False     # 미체결 매수주문 재주문 (True or False) 
                            # 역분사 실행시에 꼭 False로 하세요. (역분사 미체결 주문 다시 주문합니다.)

#매도전략
issellmarket    = False     # 전액 시장가 매도 <- 최소주문금액에 주의하세요. (True or False)
Dis             = 100000    # 분할 매도 기준 (x원 이상일 경우 지정가 분할 매수 시행)
                            # 최소 주문금액이 5천원 이므로, Disqty 기준으로 10%씩 분할하므로 6만원이상이 좋습니다.
Disdiv          = 0         # 분할 매도 수 (0 또는 자연수를 입력하세요, 분할 원치 않는 경우 0을 입력하세요)
Disgap          = 0.5       # 분할 매도 갭 (% 기준)
ask_price_div   = 1         # 윗호가 매도 수 (0 또는 자연수를 입력하세요, 분할 원치 않는 경우 0을 입력하세요)
Disqty          = 15        # 분할 매도 비중 (% 기준)
issellreorder   = False     # 미체결 매도주문 재주문 (True or False), 3전략 중 하나에서만 실행하세요. (보통 역분사에서 실행하는 게 좋습니다)

#업비트 API 설정
access = "VSNMzyDIyAgHzhpk6Najyo6DahZbLGT8xYnEpWd3"
secret = "uvSS9zdcRPc22JkxPbYtLMbeGlb5vcbuahzxxeNa"
upbit  = pyupbit.Upbit(access, secret)

#텔레그램 봇 설정
bot     = telegram.Bot(token="5018511910:AAH63St5u0GB8m5WvjOyksAGeRPMWP8NZ2A")
chat_id = "5027533498"

#기타 설정 및 타 전략 설정
isswing         = True      # 스윙 전략 같이 실행 중인 경우 True 로 설정
Swing           = 1.5       # 스윙전략 코인별 비중 (1 ~ 2)
isredca         = True      # 역분사 전략 같이 실행 중인 경우 True 로 설정
Ubuntu          = True      # 구글클라우드 or 일반적인 세팅인 경우 true 로 설정하세요. 
                            # ****분할매수/매도시 파이썬 버전에 따라 orderbook 주문 오류가 날 수 있습니다. -> 이 경우 Fasle 로 설정****
Time3           = 20        # 미체결 주문 재주문 시간 (봉 시작 후)

tickers = pyupbit.get_tickers(fiat="KRW") # 업비트 원화 시장 코인 종목 확인
k1      = pd.Series(dtype='float64') #k는 값을 받아서 저장할 시리즈 변수 (pandas)
k       = pd.Series(dtype='float64') #k는 값을 받아서 저장할 시리즈 변수 (pandas)

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def accumulate(ticker,qty): 
    # qty 값이 맞춰서 추가 분할 매수   
    p     = pyupbit.get_current_price(ticker) #현재가
    q     = upbit.get_balance(ticker)
    if qty - p*q > Acc :
        orderbook = pyupbit.get_orderbook(ticker) #호가 불러오기
        bids_asks = orderbook['orderbook_units'] if Ubuntu else orderbook[0]['orderbook_units']
        for s in range(0, bid_price_div) :
            ticN  = float(bids_asks[s]['bid_price']) #아랫호가
            upbit.buy_limit_order(ticker,ticN,Accqty/100 * (qty/ticN-q))
            time.sleep(0.125) # 1초당 8회 주문 제한
        for s2 in range(0,Accdiv) :
            gapN = pyupbit.get_tick_size(p * (1-Accgap*s2/100)) # 현재가 - gap *s2 만큼의 값
            upbit.buy_limit_order(ticker,gapN,Accqty/100*(qty/gapN-q)) 
            time.sleep(0.125) # 1초당 8회 주문 제한
        ticP  = float(bids_asks[0]['ask_price'])            #윗호가
        p     = pyupbit.get_current_price(ticker)           #현재가
        x     = (1 - (bid_price_div + Accdiv) * Accqty/100)/2
        upbit.buy_limit_order(ticker,p,x*(qty/p-q))       # 남은 절반은 현재가에 매수
        upbit.buy_limit_order(ticker,ticP,x*(qty/ticP-q)) # 남은 절반는 윗호가에 매수
        print(ticker,"현재가 기준으로 분할 매수")
        time.sleep(0.125) # 1초당 8회 주문 제한
    else :
        upbit.buy_limit_order(ticker,p,qty/p-q)
        print(ticker,"현재가에 지정가 매수")

def buyorder(ticker,qty):
    p     = pyupbit.get_current_price(ticker) #현재가
    q     = upbit.get_balance(ticker)
    if qty - 5100 > p*q: # 최소주문금액만큼의 차액 필요
        if isbuymarket:
            upbit.buy_market_order(ticker,qty-p*q)
            print(ticker,"시장가 매수")
        else :
            accumulate(ticker,qty)

def distribute(ticker,qty): 
    # qty 값만큼 추가 분할 매도   
    q     = upbit.get_balance(ticker)
    p     = pyupbit.get_current_price(ticker) 
    if p*q - qty > Dis :
        orderbook = pyupbit.get_orderbook(ticker) #호가 불러오기
        bids_asks = orderbook['orderbook_units'] if Ubuntu else orderbook[0]['orderbook_units']
        for s in range(0, ask_price_div) :
            ticP  = float(bids_asks[s]['ask_price']) #윗호가
            upbit.sell_limit_order(ticker,ticP,Disqty/100 * (qty/ticP))
            time.sleep(0.125) # 1초당 8회 주문 제한
        for s2 in range(0,Accdiv) :
            gapP = pyupbit.get_tick_size(p * (1+Disgap*s2/100)) # 현재가 + gap *s2 만큼의 값
            upbit.sell_limit_order(ticker,gapP,Disqty/100*(qty/gapP)) 
            time.sleep(0.125) # 1초당 8회 주문 제한
        ticN  = float(bids_asks[0]['bid_price'])            #아랫호가
        p     = pyupbit.get_current_price(ticker)           #현재가
        x     = (1 - (ask_price_div + Disdiv) * Disqty/100)/2
        upbit.sell_limit_order(ticker,p,x*(qty/p-q))       # 남은 절반은 현재가에 매도
        upbit.sell_limit_order(ticker,ticN,x*(qty/ticN-q)) # 남은 절반은 윗호가에 매도
        print(ticker,"현재가 기준으로 분할 매도")
        time.sleep(0.125) # 1초당 8회 주문 제한
    else :
        p     = pyupbit.get_current_price(ticker) 
        upbit.sell_limit_order(ticker,p,q)
        print(ticker,"현재가에 지정가 매도")

def sellorder(ticker,qty):
    p     = pyupbit.get_current_price(ticker) 
    if qty > 5100 : # 최소주문금액만큼의 금액 필요
        if issellmarket:
            upbit.sell_market_order(ticker,qty/p)
            print(ticker,"시장가 매도")
        else :
            distribute(ticker,qty)

now = datetime.datetime.now()
nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S') 
print(nowDatetime, "감시 시작")
bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n감시 시작합니다"))

while True:
    try:
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
        start_time = get_start_time("KRW-BTC")              

        #매도 시작
        for s in range(0,int(24/hrs)) :
            end_time  = start_time + datetime.timedelta(hours=hrs*(s+1))        
            if (end_time - datetime.timedelta(minutes=Time) < now < end_time ) :
                print(nowDatetime,"시작")
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n봇 실행, 자산 비중 계산, 거래량 순위 검색"))

                Residual    = upbit.get_balance_t("KRW") # 예수금
                coinbalance = upbit.get_amount('ALL') # 매수금액 (평가금 아님)
                total   = Residual + coinbalance  # 총액
                minimum = total * reb_qty / 100 # 동일가중 매수 최소금

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                print(nowDatetime,"최소 금액", str(minimum), "기본 자산 수", str(Coins))
                print(nowDatetime,"일부 익절 기준가", str(minimum*(1+limit/100)), "추가 매수 기준가", str(minimum*(1-limit/100)))

                for ticker in tickers: #거래량 상위 결정, 최근 4시간 거래금액
                    df       = pyupbit.get_ohlcv(ticker,interval="minute240",count=1)
                    v        = float(df['value'][0])
                    k1[ticker] = float(v) #float 타입으로 변환해준다
                    l1          = k1.sort_values(ascending=False) 
                    time.sleep(0.2) # 1초당 5회 조회 제한 -> 'NoneType' object is not subscriptable
                
                for a in range(0,len(l1)) :
                    ticker2=l1.index[a]
                    df2 = pyupbit.get_ohlcv(ticker2,interval="minute240")
                    df2['ema'] = ta.ema(df2["close"], length=Elength)
                    if a < basic +1 : #상위 x개 종목은 항상 매수
                        v = float(df2['value'][len(df2)-1])
                    elif str(df2['ema'][len(df2)-1]) == "None":
                        v = 0
                    else :
                        v = (3*float(df2['volume'][len(df2)-1])
                        +2*float(df2['volume'][len(df2)-2])
                        +float(df2['volume'][len(df2)-3]))*float(df2['close'][len(df2)-1]-df2['ema'][len(df2)-1])
                    k[ticker2] = float(v)
                    print(ticker2,v)
                    time.sleep(0.2) # 1초당 5회 조회 제한 -> 'NoneType' object is not subscriptable
                
                l       = k.sort_values(ascending=False) #거래량 상위
                cond    = l > 0
                l_plus  = l[cond]                
                ExCoins = min(len(l_plus), Coins)
                vsup2   = l_plus[0:ExCoins] 
                vinf2   = l[ExCoins:len(l)]

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n거래량 검색 완료 리밸런싱 대기중\n"+str(vsup2)))

                while (end_time - datetime.timedelta(minutes=Time) < now < end_time- datetime.timedelta(minutes=Time2)):
                    now = datetime.datetime.now()
                    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                    time.sleep(10)
                    print(nowDatetime, "매수 대기 중")

                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n거래량 상위 "+str(ExCoins)+"항목 비중 조절 시작"))

                for b in range(0,ExCoins) :
                    ticker3=vsup2.index[b]
                    p=pyupbit.get_current_price(ticker3)
                    q=upbit.get_balance(ticker3)
                    time.sleep(0.2) # 1초당 5회 조회 제한 -> 'NoneType' object is not subscriptable
                    print(b, ticker3, "현재 종가",str(p), "현재 평가금",str(p*q) )
                    
                    if p*q > minimum * Swing * (1-limit/100) / reb_qty and isswing : # 평가금 > 최소금액 * (손절가 / 최소 비중) 
                        df3 = pyupbit.get_ohlcv(ticker3,interval="minute240",count=2)
                        Up  = float(df3['close'][1])/float(df3['open'][0]) # Up * (1 -limit/100) * minimum < p * q < Up * (1 + limit/100) * minimum 따라서, Up * (1 + limit/100) * minimum > minimum * Swing * (1-limit/100) / reb_qty
                        if Up > Swing * (1-limit/100) / (1+limit/100) / reb_qty :
                            p=pyupbit.get_current_price(ticker3)
                            upbit.sell_limit_order(ticker3,p,q*( 1 - 1/Up))
                            print(ticker3,"상승분 매도")
                        else :
                            print(ticker3,"자산 전체 유지")

                    else :                    
                        if p*q > minimum * (1+limit/100):  # 평가금 > 최소금액 * 익절라인 -> 일부 익절
                            p=pyupbit.get_current_price(ticker3)
                            upbit.sell_limit_order(ticker3,p,q-minimum/p)
                            print(ticker3,"기본 금액 제외 매도") 

                        elif p*q < minimum * (1-limit/100) : # 평가금 < 최소금액 * 손절라인 -> 추가 매수
                            if p*q < minimum * 0.5 : #매수량이 많은 경우, 분할 매수
                                accumulate(ticker3,minimum)

                            else: #매수량이 적은 경우
                                p=pyupbit.get_current_price(ticker3)
                                upbit.buy_limit_order(ticker3,p,minimum/p-q)
                                print(ticker3,"기본 금액에 맞춰 추가 매수")

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n거래량 하위 "+str(len(l)-ExCoins)+"항목 매도 시작"))

                for s in range(0,len(l)-ExCoins) :
                    ticker4=vinf2.index[s]
                    p = pyupbit.get_current_price(ticker4) # 종가
                    q = upbit.get_balance(ticker4) # 수량
                    print(s, ticker4, "현재 종가",str(p), "현재 평가금",str(p*q) )

                    if q > 0 :
                        if p*q > minimum * Swing * (1-limit/100) / reb_qty and isswing : #swing 전략만큼 상승한 경우
                            df4 = pyupbit.get_ohlcv(ticker4,interval="minute240",count=2)
                            Up4 = float(df4['close'][1])/float(df4['open'][0]) # Up * (1 -limit/100) * minimum < p * q < Up * (1 + limit/100) * minimum 따라서, Up * (1 + limit/100) * minimum > minimum * (1-limit/100) / reb_qty
                            if Up4 > Swing * (1-limit/100) / (1+limit/100) / reb_qty : #상승분이 큰 경우(스윙전략이 애초에 아닌 경우) -> 매도
                                p = pyupbit.get_current_price(ticker4)
                                if s < len(l_plus) - ExCoins :
                                    upbit.sell_limit_order(ticker4,p,Out*minimum/(100*p))
                                    print(ticker4,"Out of market : 자산 최소 금액 * ",str(Out),"% 매도")
                                else :
                                    upbit.sell_limit_order(ticker4,p,Out2*minimum/(100*p)) 
                                    print(ticker4,"EMA 하단 : 자산 최소 금액 * ",str(Out2),"% 매도")
                            else :
                                print(ticker4,"스윙 전략, 자산 유지")

                        else :
                            if p*q - Out2/100 * minimum < 5100  : #매도 금액 이후 5천원이 남는 경우 -> 전체 매도
                                p = pyupbit.get_current_price(ticker4)
                                if p*q > 5000 :
                                    upbit.sell_limit_order(ticker4,p,q)
                                    print(ticker4,"자산 전체 매도")
                            else :
                                p = pyupbit.get_current_price(ticker4)
                                if s < len(l_plus) - ExCoins : #EMA가 종가 아래인 경우
                                    upbit.sell_limit_order(ticker4,p,Out*minimum/(100*p))
                                    print(ticker4,"Out of market : 자산 최소 금액 * ",str(Out),"% 매도")
                                else : #EMA가 종가 위인 경우
                                    upbit.sell_limit_order(ticker4,p,Out2*minimum/(100*p))      
                                    print(ticker4,"EMA 하단 : 자산 최소 금액 * ",str(Out2),"% 매도")                          
                                        
                    time.sleep(0.2) # 1초당 5회 조회 제한 -> 'NoneType' object is not subscriptable

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                print(nowDatetime, "리밸런싱 종료")
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n리밸런싱 종료"))

                while (end_time - datetime.timedelta(minutes=Time2) < now < end_time) :
                    now = datetime.datetime.now()
                    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                    time.sleep(60)

                if isbuyreorder or issellreorder :

                    while (start_time < now < start_time + datetime.timedelta(minutes=Time3)):
                        now = datetime.datetime.now()
                        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                        time.sleep(10)
                        print("\n[" + nowDatetime + "] 미체결 주문 재 주문 시간까지 대기중 ")

                    bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n미체결 주문 재청산"))
                    
                    for ticker3 in tickers:
                        pending3 = upbit.get_order(ticker3)
                        lp3=len(pending3)
                        print(ticker3,lp3)
                        if lp3 > 0 :
                            for o3 in range(0,lp3) :
                                if ( str(pending3[o3]['side']) == 'bid' ) and ( str(pending3[o3]['state']) == 'wait' ) and isbuyreorder :
                                    upbit.cancel_order(pending3[o3]['uuid'])
                                    ticP = pyupbit.get_tick_size(pyupbit.get_current_price(ticker3) * 1.1)
                                    upbit.buy_limit_order(ticker3, ticP, float(pending3[o3]['remaining_volume']))

                                elif ( str(pending3[o3]['side']) == 'ask' ) and ( str(pending3[o3]['state']) == 'wait' ) and issellreorder :
                                    upbit.cancel_order(pending3[o3]['uuid'])
                                    ticP = pyupbit.get_tick_size(pyupbit.get_current_price(ticker3) * 0.9)
                                    upbit.sell_limit_order(ticker3, ticP, float(pending3[o3]['remaining_volume']))

                print(nowDatetime, "리밸런싱 종료")
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 리밸런싱]\n완료, 다음 매매 시간까지 대기중"))

                tickers=pyupbit.get_tickers(fiat="KRW") 

    # 예외 처리
    except Exception as e:
        print(e)

    # 10초 기다림
    time.sleep(10)
       