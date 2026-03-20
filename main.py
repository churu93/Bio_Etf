import pandas as pd
import requests
import os
from datetime import datetime
import sys
from bs4 import BeautifulSoup

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# 분석할 종목
ETF_LIST = {"466170": "KoAct 바이오헬스케어", "467260": "TIME K바이오액티브", "069500": "KODEX 200"}

def get_etf_data(ticker):
    # 네이버 PC 버전의 구성종목 페이지 (가장 안정적인 경로)
    url = f"https://finance.naver.com/item/main.naver?code={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"   ❌ {ticker}: 서버 응답 실패 ({response.status_code})")
            return pd.DataFrame()

        # HTML에서 표(Table) 추출
        soup = BeautifulSoup(response.text, 'lxml')
        # '구성종목' 표는 보통 'type_1' 혹은 특정 클래스를 가진 테이블에 있어
        # pandas의 read_html을 사용하여 모든 표를 긁어옴
        tables = pd.read_html(response.text)
        
        # ETF 구성종목 표 찾기 (보통 비중이나 종목명이 포함된 표)
        for table in tables:
            if '종목명' in table.columns or '구성종목' in table.columns:
                df = table.copy()
                # 컬럼명 정리
                df.columns = [str(c) for c in df.columns]
                name_col = '종목명' if '종목명' in df.columns else df.columns[0]
                qty_col = '비중' if '비중' in df.columns else (df.columns[1] if len(df.columns) > 1 else df.columns[0])
                
                df = df[[name_col, qty_col]].dropna()
                df.columns = ['종목명', '수량/비중']
                return df.set_index('종목명')
                
        return pd.DataFrame()
    except Exception as e:
        print(f"   ❌ {ticker}: 데이터 처리 중 오류 ({e})")
        return pd.DataFrame()

def main():
    print(f"🚀 [PC 크롤링 모드] 분석 시작: {datetime.now()}")
    all_results = {}
    
    for ticker, name in ETF_LIST.items():
        print(f"🔍 {name}({ticker}) 탐색 중...")
        df = get_etf_data(ticker)
        if not df.empty:
            all_results[name] = df
            print(f"   ✅ {len(df)}개 종목 확보")
        else:
            print(f"   ⚠️ 데이터를 찾을 수 없습니다.")

    if all_results:
        file_name = f"ETF_Report_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
        with pd.ExcelWriter(file_name) as writer:
            for name, df in all_results.items():
                df.to_excel(writer, sheet_name=name[:30])
        
        # 텔레그램 전송
        with open(file_name, 'rb') as f:
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", 
                          data={'chat_id': CHAT_ID, 'caption': f'📊 ETF 리포트 (PC버전 획득)\n날짜: {datetime.now().strftime("%Y-%m-%d")}'}, 
                          files={'document': f})
        print("✨ 전송 완료!")
    else:
        msg = "⚠️ [실패] 모든 데이터 획득에 실패했습니다. 사이트 구조가 변경되었을 수 있습니다."
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg})
        sys.exit(1)

if __name__ == "__main__":
    main()
