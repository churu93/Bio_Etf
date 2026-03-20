import pandas as pd
from pykrx import stock
import requests
import os
from datetime import datetime, timedelta
import sys

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

ETF_LIST = {
    "466170": "KoAct 바이오헬스케어",
    "467260": "TIME K바이오액티브",
    "069500": "KODEX 200"
}

def get_etf_holdings_with_retry(ticker):
    """데이터가 나올 때까지 최근 7일간의 데이터를 역순으로 탐색합니다."""
    for i in range(7):
        target_date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
        try:
            # KRX 공식 PDF 데이터 획득 함수
            df = stock.get_etf_portfolio_deposit_file(ticker, target_date)
            
            if df is not None and not df.empty:
                print(f"      ✅ {target_date} 데이터 발견!")
                # 데이터가 Series 형태일 경우 처리
                if isinstance(df, pd.Series):
                    df = df.to_frame(name='수량')
                else:
                    # 첫 번째 컬럼을 수량으로 간주
                    df = df.iloc[:, [0]]
                    df.columns = ['수량']
                
                # 종목명 추가
                df['종목명'] = [stock.get_market_ticker_name(idx) for idx in df.index]
                return df[['종목명', '수량']], target_date
        except:
            continue
    return pd.DataFrame(), None

def main():
    print(f"🚀 [날짜 추적 모드] 분석 시작: {datetime.now()}")
    all_results = {}
    final_date = ""

    for ticker, name in ETF_LIST.items():
        print(f"🔍 {name}({ticker}) 탐색 중...", end="")
        df, found_date = get_etf_holdings_with_retry(ticker)
        
        if not df.empty:
            all_results[name] = df
            final_date = found_date # 마지막으로 찾은 날짜 저장
            print(f" ✅ {len(df)}개 종목 확보")
        else:
            print(" ❌ 7일치 데이터 없음")

    if all_results:
        file_name = f"ETF_Report_{final_date}.xlsx"
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            for name, df in all_results.items():
                df.to_excel(writer, sheet_name=name[:30])
        
        # 텔레그램 전송
        print("📤 텔레그램 전송 중...")
        with open(file_name, 'rb') as f:
            caption = f"📊 ETF 구성 종목 리스트\n최종 데이터 기준일: {final_date}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", 
                          data={'chat_id': CHAT_ID, 'caption': caption}, files={'document': f})
        print("✨ 전송 완료!")
    else:
        msg = "⚠️ 최근 7일간의 ETF 데이터를 찾을 수 없습니다. 거래소 서버를 확인해 주세요."
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg})
        print(msg)
        sys.exit(1)

if __name__ == "__main__":
    main()
