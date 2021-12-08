import pandas as pd
import datetime
from pandas import DataFrame
from pandas import Series
import time
import pyupbit #pip install pyupbit
import telegram #pip install python-telegram-bot
import pandas_ta as ta #pip install pandas_ta


#전략 세팅
hrs         = 4     # 4시간 또는 24시간만 가능 (4 or 24)
Swing       = 1.5   # 스윙전략 코인별 비중 (1 ~ 2)
Coins       = 50    # 거래량 상위 스크리닝 (40 ~ 100, 자연수)
Long        = 1.6   # *ATR + EMA 상방 돌파 시 진입 (1.5~2.0)
Exit        = 0     # *ATR + EMA 하방 돌파 시 매도 (0)
Elength     = 30    # EMA기준 (length,20~40)
ATRlength   = 10    # ATR 기준 (10)
Time        = 3     # 거래량 검색 시간 (컴퓨터 사양에 따라 5분이면 충분합니다.)

#코인별 세부전략
BTCSwing        = 20         # 비트 스윙 비중 (% 기준) -> Swing 값보다는 크게만 설정 가능합니다.
ETHSwing        = 15         # 이더 스윙 비중 (% 기준) -> Swing 값보다는 크게만 설정 가능합니다.
Exclusion       = ['KRW-BTC','KRW-ETH','KRW-AQT','KRW-SBD','KRW-BSV','KRW-EOS','KRW-XLM','KRW-KNC','KRW-ONT','KRW-OMG','KRW-REP','KRW-MOC','KRW-STPT','KRW-POLY','KRW-WAXP','KRW-LSK','KRW-GLM','KRW-ONG','KRW-TT','KRW-HIVE','KRW-POWR','KRW-ELF','KRW-ANKR','KRW-GAS','KRW-GRS'] 
                            # 전략에서 배제할 코인을 KRW-*** 꼴로 입력하세요. 
                            # Reference : print(pyupbit.get_tickers(fiat="KRW")) 

#매수전략
isbuymarket     = False     # True 시 전액 시장가 매수 <- 최소주문금액에 주의하세요. (True or False)
Acc             = 100000    # 분할 매수 기준 (차액이 x원 이상일 경우 지정가 분할 매수 시행) 
                            # 분할매수를 원치 않는 경우 Accdiv = 0, bid_price_div =0 으로 하거나 매수 기준을 올려주세요
                            # 최소 주문금액이 5천원 이므로, ACCqty * ACC /100 값이 5000 이상이여야 돌아갑니다.
Accdiv          = 2         # 분할매수 수 (0 또는 자연수를 입력하세요, 분할 원치 않는 경우 0을 입력하세요)
Accgap          = 0.5       # 분할매수 갭 (% 기준)
bid_price_div   = 2         # 아래호가 매수 수 (0 또는 자연수를 입력하세요, 분할 원치 않는 경우 0을 입력하세요)
Accqty          = 8         # 분할 매수 비중 (% 기준)
isbuyreorder    = False     # True 시 미체결 매수주문 재주문 (True or False) 
                            # 역분사 실행시에 꼭 False로 하세요. (역분사 미체결 주문 다시 주문합니다.)

#매도전략
issellmarket    = False     # True 시 전액 시장가 매도 <- 최소주문금액에 주의하세요. (True or False)
Dis             = 100000    # 분할 매도 기준 (차액이 x원 이상일 경우 지정가 분할 매도 시행) 
                            # 분할매도를 원치 않는 경우 Accdiv = 0, bid_price_div =0 으로 하거나 매도 기준을 올려주세요
                            # 최소 주문금액이 5천원 이므로, Disqty 기준으로 10%씩 분할하므로 최소주문금액을 확인하세요
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
iscancel        = False     # 시작 전에 미체결 주문 취소를 원하는 경우 True 로 설정 (역분사 전략에 미체결 주문 취소 주문이 있어 역분사 전략 실행 시에 주문 취소 안되게 설정해두었습니다.)
isrebalancing   = True      # 리밸런싱 전략 같이 실행 중인 경우 True 로 설정
reb_qty         = 0.5       # 리밸런싱 전략 코인당 비중 (% 기준) -> 스윙 전략과 2배 이상 차이 둘 것.
isredca         = True      # 역분사 전략 같이 실행 중인 경우 True 로 설정
Ubuntu          = True      # 구글클라우드 or 일반적인 세팅인 경우 true 로 설정하세요. 
                            # ****분할매수/매도시 파이썬 버전에 따라 orderbook 주문 오류가 날 수 있습니다. -> 이 경우 Fasle 로 설정****
Time2           = 3         # 미체결 주문 재주문 시간 (봉 시작 후)

tickers = pyupbit.get_tickers(fiat="KRW") # 업비트 원화 시장 코인 종목 확인
for ticker in Exclusion:
    tickers.remove(ticker)
Interval = "minute240" if hrs == 4 else "day"

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval=Interval, count=1)
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
    if qty > 5100 : # 최소주문금액만큼의 차액 필요
        if issellmarket:
            upbit.sell_market_order(ticker,qty/p)
            print(ticker,"시장가 매도")
        else :
            distribute(ticker,qty)

now = datetime.datetime.now()
nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S') 

Threshold       = 0.6*(upbit.get_balance_t("KRW") + upbit.get_amount('ALL'))*Swing/100
Inclusion       = []
Inclusion_new   = []

for ticker in tickers:
    p = pyupbit.get_current_price(ticker) 
    q = upbit.get_balance(ticker)
    time.sleep(0.2) #json 오류 방지 API 최대 1초에 5번까지 호출 가능
    if p*q > Threshold:
        Inclusion_new.append(ticker)

for ticker in Inclusion_new:
    Inclusion.append(ticker)
    tickers.remove(ticker)

print(nowDatetime, "감시 시작")
bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n감시 시작합니다. 스윙 전략 현재 예상 보유코인 :\n"+str(Inclusion)))

while True:
    try:
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
        start_time = get_start_time("KRW-BTC")
        end_time  = start_time + datetime.timedelta(hours=hrs)

        #매도 시작
        if (end_time - datetime.timedelta(minutes=Time) < now < end_time ) :
            k       = pd.Series(dtype='float64') #k는 값을 받아서 저장할 시리즈 변수 (pandas)
            k1      = pd.Series(dtype='float64') #k는 값을 받아서 저장할 시리즈 변수 (pandas)
            k2      = pd.Series(dtype='float64') #k는 값을 받아서 저장할 시리즈 변수 (pandas)
            print(nowDatetime,"시작")
            bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n봇 실행, 미체결 주문 취소, 자산 비중 계산, 거래량, 배수 순위 검색"))
            
            if iscancel and not isredca:
                for ticker0 in tickers: #미체결 주문 확인
                    pending = upbit.get_order(ticker0)
                    lp      = len(pending) #미체결 주문 수
                    if lp > 0 :
                        for o in range(0,lp) :
                            upbit.cancel_order(pending[o]['uuid'])

            Residual    = upbit.get_balance_t("KRW") # 예수금
            coinbalance = upbit.get_amount('ALL')    # 현재 매수금액 (평가금 아님)
            total       = Residual + coinbalance     # 총액
            qty         = int(total * Swing / 100)       # 스윙전략 매수금
            BTCqty      = int(total * BTCSwing / 100)    # 비트스윙전략 매수금
            ETHqty      = int(total * ETHSwing / 100)    # 이더스윙전략 매수금
            Rebqty      = int(total * reb_qty / 100) if isrebalancing else 0

            now = datetime.datetime.now()
            nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')

            for ticker in tickers: #candidate 의 거래량 상위 결정, 가장 최근 봉 거래금액
                df          = pyupbit.get_ohlcv(ticker,interval=Interval,count=1)
                v           = float(df['value'][0])
                k1[ticker]  = float(v) #float 타입으로 변환해준다

            l           = k1.sort_values(ascending=False) 
            vsup1       = l[0:Coins]
            # vinf1       = l[Coins:len(l)]

            for b in range(0,Coins) : # 거래량 상위종목만 매수 조건에 포함
                ticker2=vsup1.index[b]
                df2 = pyupbit.get_ohlcv(ticker2,interval=Interval)
                df2['ema'] = ta.ema(df2["close"], length=Elength)
                df2['atr'] = ta.atr(df2['high'],df2['low'],df2['close'],ATRlength)
                
                if str(df2['ema'][len(df2)-1]) == "None": # 최근 상장 코인 배제 (ema값 없음)
                    v = 0
                else :
                    # Multiplier 계산 (ATR 기준)
                    multi = float(df2['close'][len(df2)-1]-df2['ema'][len(df2)-1])/float(df2['atr'][len(df2)-1])
                    multi_shift = float(df2['close'][len(df2)-2]-df2['ema'][len(df2)-2])/float(df2['atr'][len(df2)-2])
                    # 채널 상방 돌파 확인
                    if multi > Long and multi_shift < Long :
                        p = df2['close'][len(df2)-1]
                        q = upbit.get_balance(ticker2)
                        v = multi
                    else :
                        v = 0
                k[ticker2] = float(v)
                print(ticker2,v)
                time.sleep(0.2) # 1초당 5회 조회 제한 -> 'NoneType' object is not subscriptable

            for ticker2 in Inclusion:
                df2 = pyupbit.get_ohlcv(ticker2,interval="minute240")
                df2['ema'] = ta.ema(df2["close"], length=Elength)
                df2['atr'] = ta.atr(df2['high'],df2['low'],df2['close'],ATRlength)
                if str(df2['ema'][len(df2)-1]) == "None":
                    v = 0
                else :
                    multi = float(df2['close'][len(df2)-1]-df2['ema'][len(df2)-1])/float(df2['atr'][len(df2)-1])
                    multi_shift = float(df2['close'][len(df2)-2]-df2['ema'][len(df2)-2])/float(df2['atr'][len(df2)-2])
                    #보유 종목은 하향 돌파하는지만 확인
                    if multi < Exit and multi_shift > Exit :
                        p = df2['close'][len(df2)-1] 
                        q = upbit.get_balance(ticker2)
                        if p * q > Rebqty *1.5 : # 현재 보유중인 경우에만 매도
                            v = multi
                        else :
                            v = 0
                    else :
                        v = 0
                k[ticker2] = float(v)
                print(ticker2,v)
                time.sleep(0.2)
            
            l       = k.sort_values(ascending=False) #거래량 상위
            cond    = l > 0
            Out     = l < 0
            l_plus  = l[cond]
            ExCoins = min(len(l_plus), Coins)
            vsup2   = l_plus[0:ExCoins] 
            l_minus = l[Out]

            now = datetime.datetime.now()
            nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
            bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n아래 항목 매수 대기중\n"+str(vsup2)+"\n아래 항목 매도 대기중\n"+str(l_minus)))

            while (end_time - datetime.timedelta(minutes=Time) < now < end_time):
                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                time.sleep(10)
                print("\n[" + nowDatetime + "] 봉 시작시간까지 대기중 ")

            bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n상방 채널 돌파 "+str(ExCoins)+"항목 보유 여부 확인 시작 및 매수"))

            for b in range(0,ExCoins) :
                ticker3=vsup2.index[b]
                q=upbit.get_balance(ticker3)
                if ticker3 == "KRW-BTC":
                    buyorder(ticker3,BTCqty)
                    k2[ticker3] = float(BTCqty)
                elif ticker3 == "KRW-ETH":
                    buyorder(ticker3,ETHqty) 
                    k2[ticker3] = float(ETHqty)
                else :
                    buyorder(ticker3,qty)
                    k2[ticker3] = float(qty)
                print(ticker3,"스윙 추가")
                Inclusion.append(ticker3) #스윙 보유 전략 list 추가
                tickers.remove(ticker3) #candidate list 배제

            now = datetime.datetime.now()
            nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
            bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n하방 채널 돌파 "+str(len(l_minus))+"항목 매도 시작"))

            for s in range(0,len(l_minus)) :
                ticker4 = l_minus.index[s]
                p       = pyupbit.get_current_price(ticker4)
                q       = upbit.get_balance(ticker4)
                sellorder(ticker4,p*q - Rebqty)
                k2[ticker4] = float(0)
                Inclusion.remove(ticker4) #스윙 보유 전략 list 배제
                tickers.append(ticker4) #candidate list 추가

            now = datetime.datetime.now()
            nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
            start_time = get_start_time("KRW-BTC")

            bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n분할매수/매도 주문 종료\n"+str(k2)))

            if isbuyreorder or issellreorder :
                while (start_time < now < start_time + datetime.timedelta(minutes=Time2)):
                    now = datetime.datetime.now()
                    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                    time.sleep(10)
                    print("\n[" + nowDatetime + "] 미체결 주문 재 주문 시간까지 대기중 ")

                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n미체결 주문 재청산"))
                
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

            print(nowDatetime, "스윙 종료")
            bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 스윙]\n완료, 다음 매매 시간까지 대기중"))


    # 예외 처리
    except Exception as e:
        print(e)

    # 10초 기다림
    time.sleep(10)