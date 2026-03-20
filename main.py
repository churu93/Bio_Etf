import pandas as pd
import requests
import os
from datetime import datetime
import sys

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

ETF_LIST = {"466170": "KoAct 바이오헬스케어", "467260": "TIME K바이오액티브", "069500": "KODEX 200"}

def get_etf_data(ticker):
    # 네이버 금융 모바일 상세 API
    url = f"https://m.stock.naver.com/api/json/etf/getEtfItemCompositionList.nhn?code={ticker}"
    
    # 실제 아이폰 브라우저처럼 보이게 하는 설정
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Referer': f'https://m.stock.naver.com/item/main/{ticker}/composition',
        'Accept': 'application/json, text/plain, */*',
        'Cookie': 'NNB=ABCDEFG12345;' # 가짜 쿠키 추가 (보안 우회용)
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        print(f"   [진단] {ticker} 응답 상태: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            items = data.get('result', {}).get('etfItemList', [])
            
            if not items:
                return pd.DataFrame()
                
            holdings = []
            for item in items:
                holdings.append({
                    '종목명': item.get('itemName'), 
                    '수량': float(item.get('quantity', 0))
                })
            return pd.DataFrame(holdings).set_index('종목명')
        return pd.DataFrame()
    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return pd.DataFrame()

def main():
    print(f"🚀 실행 시작: {datetime.now()}")
    all_results = {}
    
    for ticker, name in ETF_LIST.items():
        print(f"🔍 {name}({ticker}) 탐색 중...")
        df = get_etf_data(ticker)
        if not df.empty:
            all_results[name] = df
            print(f"   ✅ {len(df)}개 종목 확보")
        
    if all_results:
        file_name = f"ETF_Report_{datetime.now().strftime('%m%d')}.xlsx"
        with pd.ExcelWriter(file_name) as writer:
            for name, df in all_results.items():
                df.to_excel(writer, sheet_name=name[:30])
        
        with open(file_name, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", 
                          data={'chat_id': CHAT_ID, 'caption': '📊 ETF 리포트 전송 성공!'}, 
                          files={'document': f})
        print("✨ 전송 완료!")
    else:
        # 텔레그램으로 상세 실패 원인 전송
        error_msg = "⚠️ [데이터 획득 실패] 서버 보안에 막혔습니다. 다른 경로를 시도해야 합니다."
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': error_msg})
        print("😭 전송할 데이터가 없습니다.")
        sys.exit(1)

if __name__ == "__main__":
    main()
