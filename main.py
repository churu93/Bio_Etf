import pandas as pd
import requests
import os
from datetime import datetime
import time

# 깃허브 설정값 (나중에 설정할 거야)
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

ETF_LIST = {
    "466170": "KoAct 바이오헬스케어",
    "467260": "TIME K바이오액티브",
    "069500": "KODEX 200"
}

def get_etf_naver_mobile(ticker):
    """보안이 가장 취약한 네이버 모바일 API 경로를 공략합니다."""
    # 2026년 기준 가장 안정적인 모바일 API 주소야
    url = f"https://m.stock.naver.com/api/json/etf/getEtfItemCompositionList.nhn?code={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'}
    
    try:
        response = requests.get(url, headers=headers)
        # JSON 데이터가 아니면 에러 발생
        data = response.json()
        
        holdings = []
        # 네이버 모바일 API의 데이터 구조에 맞춰 추출
        for item in data.get('result', {}).get('etfItemList', []):
            holdings.append({
                '종목명': item['itemName'],
                '수량': float(item['quantity']) if item['quantity'] else 0.0
            })
        
        df = pd.DataFrame(holdings)
        return df.set_index('종목명') if not df.empty else pd.DataFrame()
    except:
        return pd.DataFrame()

def main():
    print(f"🚀 분석 시작: {datetime.now()}")
    all_results = {}

    for ticker, name in ETF_LIST.items():
        print(f"🔍 {name} 가져오는 중...")
        df = get_etf_naver_mobile(ticker)
        
        if not df.empty:
            all_results[name] = df
            print("   ✅ 성공!")
        else:
            print("   ❌ 실패")
        time.sleep(2) # 봇으로 오해받지 않게 천천히!

    if all_results:
        file_name = "ETF_Report.xlsx"
        with pd.ExcelWriter(file_name) as writer:
            for name, df in all_results.items():
                df.to_excel(writer, sheet_name=name[:30])
        
        # 텔레그램 전송
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument"
        with open(file_name, 'rb') as f:
            requests.post(url, data={'chat_id': CHAT_ID, 'caption': '📊 실시간 ETF 구성 종목'}, files={'document': f})
        print("✨ 전송 완료!")

if __name__ == "__main__":
    main()
