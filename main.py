import pandas as pd
import requests
import os
from datetime import datetime
import sys

# 깃허브 설정값
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

# 분석할 종목
ETF_LIST = {
    "466170": "KoAct 바이오헬스케어",
    "467260": "TIME K바이오액티브",
    "069500": "KODEX 200"
}

def get_etf_holdings(ticker):
    """네이버 금융의 ETF 구성종목 전용 페이지(Iframe)를 긁어옵니다."""
    # 여기가 진짜 데이터가 있는 주소야!
    url = f"https://finance.naver.com/item/holdings.naver?code={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36'
    }
    
    try:
        # 1. 페이지 요청
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            return pd.DataFrame()

        # 2. pandas의 read_html로 표(Table) 읽기
        # 이 페이지에는 표가 하나뿐이라 바로 읽어올 수 있어.
        tables = pd.read_html(response.text)
        
        for df in tables:
            # '종목명'이라는 글자가 포함된 표를 찾자
            if '종목명' in df.columns:
                # 필요한 컬럼만 추출 (종목명, 비중)
                # 네이버 표 구조에 따라 컬럼 인덱스로 접근하는게 가장 안전해
                res = df[['종목명', '편입비중']].copy()
                res.columns = ['종목명', '비중']
                res = res.dropna() # 빈 줄 제거
                return res.set_index('종목명')
                
        return pd.DataFrame()
    except Exception as e:
        print(f"      ⚠️ {ticker} 에러 발생: {e}")
        return pd.DataFrame()

def main():
    print(f"🚀 [Iframe 직접 공략] 분석 시작: {datetime.now()}")
    all_results = {}
    
    for ticker, name in ETF_LIST.items():
        print(f"🔍 {name}({ticker}) 탐색 중...", end=" ")
        df = get_etf_holdings(ticker)
        
        if not df.empty:
            all_results[name] = df
            print(f"✅ {len(df)}개 종목 확보")
        else:
            print("❌ 실패")

    if all_results:
        file_name = f"ETF_Report_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            for name, df in all_results.items():
                df.to_excel(writer, sheet_name=name[:30])
        
        # 텔레그램 전송
        print("📤 텔레그램 전송 중...")
        with open(file_name, 'rb') as f:
            caption = f"📊 ETF 실시간 구성 종목 리스트\n기준일: {datetime.now().strftime('%Y-%m-%d')}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", 
                          data={'chat_id': CHAT_ID, 'caption': caption}, files={'document': f})
        print("✨ 모든 작업 완료!")
    else:
        print("😭 데이터를 하나도 가져오지 못했습니다.")
        # 실패 시 텔레그램 알림
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': "⚠️ 오늘 ETF 데이터를 가져오지 못했습니다. 사이트 구조를 확인하세요."})
        sys.exit(1)

if __name__ == "__main__":
    main()
