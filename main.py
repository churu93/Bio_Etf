import pandas as pd
import requests
import os
from datetime import datetime
import sys

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# 분석할 종목
ETF_LIST = {"466170": "KoAct 바이오헬스케어", "467260": "TIME K바이오액티브", "069500": "KODEX 200"}

def get_etf_data(ticker):
    # 네이버 금융의 '진짜' 데이터 통로 (모바일 API)
    url = f"https://m.stock.naver.com/api/json/etf/getEtfItemCompositionList.nhn?code={ticker}"
    
    # 브라우저인 척 하는 아주 상세한 정보 (헤더)
    headers = {
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.0 Mobile/15E148 Safari/604.1',
        'Referer': f'https://m.stock.naver.com/item/main/{ticker}/composition',
        'Accept': 'application/json, text/plain, */*'
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        print(f"   [진단] {ticker} 응답 상태: {res.status_code}")
        
        if res.status_code == 200:
            data = res.json()
            # 네이버 모바일 API의 실제 데이터 구조 (2026년 기준)
            items = data.get('result', {}).get('etfItemList', [])
            
            if not items:
                print(f"   ⚠️ {ticker}: 데이터 목록이 비어있습니다.")
                return pd.DataFrame()
                
            holdings = []
            for item in items:
                holdings.append({
                    '종목명': item.get('itemName'), 
                    '수량': float(item.get('quantity', 0))
                })
            
            return pd.DataFrame(holdings).set_index('종목명')
        else:
            print(f"   ❌ {ticker}: 서버 응답 에러 ({res.status_code})")
            return pd.DataFrame()
    except Exception as e:
        print(f"   ❌ {ticker}: 통신 오류 ({e})")
        return pd.DataFrame()

def main():
    print(f"🚀 분석 시작 시각: {datetime.now()}")
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
        
        # 파일 전송
        with open(file_name, 'rb') as f:
            res = requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", 
                                data={'chat_id': CHAT_ID, 'caption': '📊 ETF 리포트 전송 완료!'}, 
                                files={'document': f})
            print(f"📤 전송 결과: {res.status_code}")
    else:
        print("😭 모든 데이터를 가져오는 데 실패했습니다.")
        # 실패 메시지를 텔레그램으로 보냄
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': "⚠️ [실패] 깃허브에서 데이터를 가져오지 못했습니다. 경로를 재점검해야 합니다."})
        sys.exit(1)

if __name__ == "__main__":
    main()
