import pyupbit 
import pandas as pd
import datetime
from pandas import DataFrame
from pandas import Series
import time
import telegram

#업비트 API 설정
access = "VSNMzyDIyAgHzhpk6Najyo6DahZbLGT8xYnEpWd3"
secret = "uvSS9zdcRPc22JkxPbYtLMbeGlb5vcbuahzxxeNa"
upbit  = pyupbit.Upbit(access, secret)

#텔레그램 봇 설정
bot     = telegram.Bot(token="5018511910:AAH63St5u0GB8m5WvjOyksAGeRPMWP8NZ2A")
chat_id = "5027533498"

#전략 세팅 (8시간)
hrs             = 8         # 매 8시간마다 실행 (4의 배수만 넣어주세요. 최대 24시간)
ratio           = 2         # 역분사 비중 (%)
division        = 30        # 역분사 기본 분할 수 
Coins           = 15        # 역분사 코인수 (상위 거래량 순)
gap             = 1         # 첫번째 매수가 갭
pricegap        = 1         # 매수가 간 간격
ischangediv     = True      # 가변 분할
issellmarket    = False     # True 시 전액 시장가 매도 , False 시에 지정가 매도 (True or False) 
isBTCETH        = False     # True 시에 BTC, ETH 등 100만원 이상의 코인도 포함, False 시에는 미체결 주문 매도대상 아니며 역분사 코인에도 배제됨
issellreorder   = True      # True 시에 분할 주문 완료 후에 미체결 매도 주문을 취소하고 낮은 가격으로 재주문함
istic           = True      # True 시에 한 호가당 0.2% 이상인 경우 배제, 
                            # False 시에는 모든 코인 포함 (XRP, TRX 등 슬리피지가 큰 코인 포함될 가능성 있습니다)

                            # 주의사항 **분할수 크고, 비중 및 자본금 적고, 코인수 많은 경우에 최소주문금액이 안되는 경우 5100원으로 주문을 체결합니다 **

Time   = 15 # 미체결 취소 및 매도 시작 시간 ex) 15 -> 0:45, 8:45, 16:45부터 매도 시작
            # 미체결 전체 일괄 취소가 안되고, 업비트는 각각의 미체결 주문에 대하여 하나하나 취소하여야 하므로 오래걸립니다.
            # 컴퓨터 사양 고려, 봉 시작 전에 미체결 취소 및 매도를 마무리 하려면 대략적으로 분할수 * 코인 수 * 1초 정도의 시간이 걸림
            # ex) 30분할 + 가변분할 * 15종목 -> 10분정도 걸리며, 다른 전략도 같이 돌린다면 그 전에 매도 되야 하므로 충분히 15분정도 잡으면 됩니다.
            # ex) 20분할 + 가변분할 * 8 종목 -> 5-6분 정도 걸림, 다른 전략이 없으면 4-5 정도로 잡으면 됩니다
            # 잘 모르겠으면 처음에는 역분사 코인수만큼 입력하면 됩니다.

#타전략 세팅 설정 
isswing         = True   # 스윙전략 같이 실행 중인 경우 True 로 설정 -> True 시에 Swing % 정도의 코인은 candidate에서 배제됩니다.
Swing           = 1.5    # 스윙전략 코인별 비중 (1 ~ 2)
limit           = 10     # 익절/손절 라인 (%)

isrebalancing   = True   # 리밸런싱 전략 같이 실행 중인 경우 True 로 설정 -> True 시에 reb_qty % 정도의 코인은 candidate에 포함됩니다
reb_qty         = 0.5    # 리밸런싱 전략 코인당 비중 (% 기준)

maxDivision = (100-gap)/pricegap # 최대 분할 수
tickers     = pyupbit.get_tickers(fiat="KRW") # 업비트 원화 시장
k           = pd.Series(dtype='float64') #k는 값을 받아서 저장할 시리즈 변수

def get_start_time(ticker):
    """시작 시간 조회"""
    df = pyupbit.get_ohlcv(ticker, interval="day", count=1)
    start_time = df.index[0]
    return start_time

def sellorder(ticker,p,q):
    if issellmarket:
        upbit.sell_market_order(ticker,q)
        time.sleep(0.125)
        q = upbit.get_balance(ticker)
        if q>0: #최소 금액 부족으로 인하여 주문 안나간 경우 현재가 *95% 가격으로 시장가 매도
            upbit.sell_limit_order(pyupbit.get_tick_size(0.95*p),q)
    else:
        upbit.sell_limit_order(ticker,p,q)

now = datetime.datetime.now()
nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S') 
start_time = get_start_time("KRW-BTC") # 업비트 시장 시작 시간
print(nowDatetime, "감시 시작")
print(start_time, "감시 기준")

Residual = upbit.get_balance_t("KRW")

bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 역분사]\n감시 시작합니다"))

while True:
    try:
        now = datetime.datetime.now()
        nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
        start_time = get_start_time("KRW-BTC")              

        #매도 시작
        for s in range(0,int(24/hrs)) :
            end_time  = start_time + datetime.timedelta(hours=hrs*(s+1))        
            if (end_time - datetime.timedelta(minutes=Time) < now < end_time  ) :
                print(nowDatetime,"시작")
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 역분사]\n봇 실행"))

                ExResidual  = Residual
                Residual    = upbit.get_balance(ticker="KRW") # 예수금
                coinbalance = upbit.get_amount('ALL') # 매수금액 (평가금 아님)
                tailtotal = upbit.get_balance_t("KRW") - Residual
                total   = Residual + coinbalance + tailtotal # 총액
                minimum = total * reb_qty / 100 # 동일가중 매수 최소금

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                print(nowDatetime,"자본금",str(total),"주문 가능 금액",str(Residual+tailtotal), "최소 금액", str(minimum))

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 역분사]\n미체결 주문 취소 및 매도 시작"))
                
                for ticker2 in tickers: #거래량 상위 결정, 최근 16시간 거래금액
                    df       = pyupbit.get_ohlcv(ticker2,interval="minute240",count=4)  
                    q        = upbit.get_balance(ticker2)
                    pending2 = upbit.get_order(ticker2)
                    lp2      = len(pending2) #미체결 주문 수
                    p        = float(df['close'][3])
                    v        = float(df['value'][0]) + float(df['value'][1]) + float(df['value'][2]) + float(df['value'][3])

                    if isBTCETH or p < 1000000 :
                        if q == 0 :
                            v1=v
                            print(ticker2,"보유 수량 없음, Candidate")
                            if lp2 > 0 :
                                for o in range(0,lp2) :
                                    upbit.cancel_order(pending2[o]['uuid'])

                        else:
                            if isswing or isrebalancing : 
                                Open16  = float(df['open'][0]) # 16시간 전 시가 (가변 분할수 계산을 위한)
                                Low16   = min(float(df['low'][0]),float(df['low'][1])) # 16시간~8시간 전 저가 (가변 분할수 계산을 위한)
                                d16     = int((1-(Low16/Open16))*100 ) if ischangediv else 0
                                xdivision16 = min(division+d16, maxDivision)
                                                        
                                Open8   = float(df['open'][2]) # 8시간 전 시가 (가변 분할수 계산을 위한)
                                Low8    = min(float(df['low'][2]),float(df['low'][3])) # 전 저가 (가변 분할수 계산을 위한)
                                done    = min(int((Open8-Low8)*100/Open8),xdivision16) # 분할 중 체결량
                                notdone = xdivision16 - done # 분할 중 미체결량
                                
                                if lp2 > 0 :
                                    tails = 0 # 미체결 금액
                                    for o in range(0,lp2) :
                                        upbit.cancel_order(pending2[o]['uuid'])
                                        tail = float(pending2[o]['remaining_volume'])*float(pending2[o]['price'])
                                        tails += tail
                                    now = datetime.datetime.now()
                                    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                                    print(ticker2, "미체결 주문 취소, 취소 금액 :",str(tails))
                                    
                                    sell = tails * xdivision16 / lp2 - tails if ( tails < (ratio * total * lp2 /100 /division) and xdivision16 > lp2 ) else 0 # 체결 금액
                                    buy = sell + tails

                                    print(ticker2, "예상 체결 금액 :",str(sell))

                                    if notdone > 0 : 
                                        if p*q > Swing * minimum * (1-limit/100) / reb_qty : # 평가금 > 최소금액 * (손절가 / 최소 비중) -> 예상 체결분만 매도
                                            if sell > 5000 :
                                                p=pyupbit.get_current_price(ticker2)
                                                sellorder(ticker2,p,min(q,sell/p))
                                                print(ticker2,"체결분 매도")

                                                q=upbit.get_balance(ticker2) #체결분 매도 후 남은 금액으로 판단
                                                if p*q > Swing * (1-limit/100) * total /100 :
                                                    v1=0
                                                    print(ticker2,"not Candidate")
                                                else:
                                                    v1=v
                                                    print(ticker2,"Candidate")
                                            else :
                                                print(ticker2,"자산 전체 유지")
                                                print(ticker2,"not Candidate")
                                                v1=0              
                                        else :
                                            v1=v
                                            if sell > 5100 :
                                                if p*q-sell < 5100 : #체결분 매도 후 남은 금액이 5100원 이하가 되는 경우 전액 매도
                                                    p=pyupbit.get_current_price(ticker2)
                                                    sellorder(ticker2,p,q)
                                                    print(ticker2,"전량 매도")
                                                    print(ticker2,"Candidate")
                                                else : #그렇지 않은 경우 체결분만 매도
                                                    p=pyupbit.get_current_price(ticker2)
                                                    sellorder(ticker2,p,min(q,sell/p))
                                                    print(ticker2,"체결분 매도")
                                                    print(ticker2,"Candidate")

                                    else : # 오류
                                        print(ticker2,"Candidate")
                                        v1=v

                                else :
                                    print(ticker2,"미체결 주문 없음")

                                    if p*q > minimum * (1+limit/100) and isswing : #평가금 > 최소금액 * (손절가 / 최소 비중)
                                        if notdone > 0 : # 자산 유지
                                            print(ticker2,"스윙 전략 유지")
                                            print(ticker2,"not Candidate")
                                            v1=0
                                        else : #전부 체결되었을 경우
                                            p=pyupbit.get_current_price(ticker2)
                                            if p*q-buy < 5100 : #체결분 매도 후 남은 금액이 5100원 이하가 되는 경우 전액 매도
                                                p=pyupbit.get_current_price(ticker2)
                                                sellorder(ticker2,p,q)
                                                print(ticker2,"전량 매도")
                                                print(ticker2,"Candidate")
                                            else : #그렇지 않은 경우 체결분만 매도
                                                p=pyupbit.get_current_price(ticker2)
                                                sellorder(ticker2,p,buy/p)
                                                print(ticker2,"체결 금액 매도")
                                                print(ticker2,"Candidate") 
                                            v1=v
                                    else : #스윙 전략 포함 아님
                                        print(ticker2,"Candidate")
                                        v1=v
                            else:
                                sellorder(ticker2,p,q)
                                print(ticker2,"전량 매도")
                                print(ticker2,"Candidate")
                                v1=v
                                if lp2 > 0 :
                                    for o in range(0,lp2) :
                                        upbit.cancel_order(pending2[o]['uuid'])
                    else :
                        v1 = 0
                                
                    if istic and ((1000< p <2500) or (100< p <500) or (10< p <50) or (1< p <5) or (0.1< p <0.5) or (p <0.05)) : 
                        # 호가 단위 0.2% 이하
                        v2=0
                    else :
                        v2=v1
                    k[ticker2] = float(v2) #float 타입으로 변환해준다
                    l          = k.sort_values(ascending=False) 
                    vsup       = l[0:Coins] #  호가단위 0.2 % 인 종목 중 거래량 상위

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                print(nowDatetime, "매도 종료, 호가단위 0.2 % 인 종목 중 거래량 상위 목록")

                print(vsup)
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 역분사]\n매도 종료, 상위 "+str(Coins)+" 종목 분할 매수 대기중\n"+str(vsup)))

                while (end_time - datetime.timedelta(minutes=Time) < now < end_time):
                    now = datetime.datetime.now()
                    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                    time.sleep(10)
                    print(nowDatetime, "매수 대기 중")
                    time.sleep(10)

                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 역분사]\n상위 "+str(Coins)+" 종목 분할 매수 시작"))
                Residual = upbit.get_balance(ticker="KRW")

                for x in range(0,Coins) :
                    ticker   = vsup.index[x]
                    df2       = pyupbit.get_ohlcv(ticker,interval="minute240",count=3) 
                    coinOpen  = float(df2['open'][2]) # 시가
                    coinClose = float(df2['close'][2]) # 종가
                    coinPrevOpen = float(df2['open'][0]) # 전 시가 (가변 분할수 계산을 위한)
                    coinPrevLow  = float(min(df2['low'][0],df2['low'][1])) # 전 저가 (가변 분할수 계산을 위한)
                    d         = int((1-(coinPrevLow/coinPrevOpen))*100 ) if ischangediv else 0 # 가변 분할수
                    xdivision = min(division+d, maxDivision)  # 실제 분할수는 가변 분할수와 역산한 최대 분할수 중 작은값 채택

                    now = datetime.datetime.now()
                    nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                    print("\n[" + nowDatetime + "] " + str(Coins) + "개 코인 중 "+ str(x+1) +"번째 시행 시작")
                    
                    print(ticker, "[정보] 분할 수 : ", xdivision, " (추가 분할 수 :", str(d)+")") # 분할 수 출력
                    
                    if upbit.get_balance(ticker="KRW") > max(Residual * ratio / 100 , 5100 * xdivision) :
                        # 분할 매수 주문 제출 
                        for i in range(0, xdivision):
                            buyPrice = pyupbit.get_tick_size(coinOpen * (1 - (gap + i * pricegap) / 100)) # 매수가 = 시가에서부터 설정한 간격만큼 내려간 가격
                            qty      = max(Residual / xdivision / buyPrice  * 0.99 * (ratio/100),5100/buyPrice) # 수량 = 총자본을 분할수 및 매수가로 나눔
                            # 주의사항 **분할수 크고, 비중 및 자본금 적고, 코인수 많은 경우에 최소주문금액이 안되는 경우 5100원으로 주문을 체결합니다 **

                            upbit.buy_limit_order(ticker,buyPrice,qty) # 주문 제출(지정가 매수)
                            print(" [주문] " + str(i+1) + "회차, 가격 : " + str(format(buyPrice, '.3f')) + ", 수량 : " + str(format(qty, '.3f')) + " (" + str(format(buyPrice * qty, '.2f')) + " KRW)")
                            # time.sleep(0.125) #Exchange API 주문 1초당 8개 제한, 구글클라우드 SSH에선 없이 실행

                now = datetime.datetime.now()
                nowDatetime = now.strftime('%Y-%m-%d %H:%M:%S')
                bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 역분사]\n분할매수 주문 종료]"))
                
                if issellreorder :
                    for ticker3 in tickers:
                        pending3 = upbit.get_order(ticker3)
                        lp3=len(pending3)
                        print(ticker3,lp3)
                        if lp3 > 0 :
                            for o3 in range(0,lp3) :
                                if ( str(pending3[o3]['side']) == 'ask' ) and ( str(pending3[o3]['state']) == 'wait' ) :
                                    upbit.cancel_order(pending3[o3]['uuid'])
                                    ticP = pyupbit.get_tick_size(pyupbit.get_current_price(ticker3) * 0.99)
                                    sellorder(ticker3, ticP, float(pending3[o3]['remaining_volume']))
                    bot.sendMessage(chat_id=chat_id, text=(nowDatetime+" [업비트 역분사]\n재청산 종료, 다음 매매까지 대기중"))
            
            now = datetime.datetime.now()            
            tickers=pyupbit.get_tickers(fiat="KRW") 

    # 예외 처리
    except Exception as e:
        print(e)

    # 10초 기다림
    time.sleep(10)
       