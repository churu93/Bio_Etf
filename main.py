import pandas as pd
import requests
import os
from datetime import datetime
import sys

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

ETF_LIST = {"466170": "KoAct 바이오헬스케어", "467260": "TIME K바이오액티브", "069500": "KODEX 200"}

def get_etf_data(ticker):
    # 가장 범용적인 네이버 금융 PC 버전 경로를 시도해볼게
    url = f"https://finance.naver.com/api/getHoldings.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    try:
        res = requests.get(url, headers=headers)
        data = res.json()
        holdings = []
        for item in data.get('holdings', []):
            holdings.append({'종목명': item['stock_name'], '수량': float(item['share_cnt'])})
        return pd.DataFrame(holdings).set_index('종목명')
    except:
        return pd.DataFrame()

def main():
    print(f"🚀 실행 시작: {datetime.now()}")
    all_results = {}
    
    for ticker, name in ETF_LIST.items():
        df = get_etf_data(ticker)
        if not df.empty:
            all_results[name] = df
            print(f"✅ {name} 성공")
        else:
            print(f"❌ {name} 데이터 없음")

    if all_results:
        file_name = "ETF_Report.xlsx"
        with pd.ExcelWriter(file_name) as writer:
            for name, df in all_results.items():
                df.to_excel(writer, sheet_name=name[:30])
        
        # 파일 전송
        with open(file_name, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", 
                          data={'chat_id': CHAT_ID, 'caption': '📊 ETF 리포트 전송 완료'}, files={'document': f})
    else:
        # 데이터가 없을 때 메시지 전송
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': "⚠️ 오늘 ETF 데이터를 가져오는데 실패했습니다. 서버 상태를 확인하세요."})
        print("😭 전송할 데이터가 없습니다.")
        sys.exit(1) # 강제로 에러를 발생시켜 깃허브에서 빨간색 X가 뜨게 함

if __name__ == "__main__":
    main()

if __name__ == "__main__":
    main()
