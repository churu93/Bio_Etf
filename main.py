import pandas as pd
import requests
import os
from datetime import datetime
import sys

# 깃허브 설정값
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('CHAT_ID')

ETF_LIST = {
    "466170": "KoAct 바이오헬스케어",
    "467260": "TIME K바이오액티브",
    "069500": "KODEX 200"
}

def get_etf_holdings(ticker):
    """네이버 금융 Iframe 페이지를 인코딩 보정 후 읽어옵니다."""
    url = f"https://finance.naver.com/item/holdings.naver?code={ticker}"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        'Referer': f'https://finance.naver.com/item/main.naver?code={ticker}'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        # 중요: 네이버는 EUC-KR 인코딩을 사용하므로 강제 지정해줍니다.
        response.encoding = 'euc-kr' 
        
        if response.status_code != 200:
            print(f"      [에러] {ticker} 응답코드: {response.status_code}")
            return pd.DataFrame()

        # 표 읽기 (인코딩된 텍스트를 직접 전달)
        tables = pd.read_html(response.text)
        
        for df in tables:
            # MultiIndex(이중 제목)인 경우 단일 제목으로 합치기
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(-1)
            
            # 컬럼명에서 공백 제거
            df.columns = [str(c).replace(" ", "") for c in df.columns]
            
            # '종목명' 또는 '구성종목' 키워드가 들어있는 열 찾기
            target_col = None
            for c in df.columns:
                if '종목명' in c or '구성종목' in c or '품목명' in c:
                    target_col = c
                    break
            
            if target_col:
                # 비중/비율 컬럼 찾기
                weight_col = None
                for c in df.columns:
                    if '비중' in c or '비율' in c or '퍼센트' in c:
                        weight_col = c
                        break
                
                if weight_col:
                    res = df[[target_col, weight_col]].copy()
                    res.columns = ['종목명', '비중']
                    return res.dropna().set_index('종목명')
                    
        return pd.DataFrame()
    except Exception as e:
        print(f"      [진단] {ticker} 처리 중 예외 발생: {e}")
        return pd.DataFrame()

def main():
    print(f"🚀 [최종 보정 모드] 분석 시작: {datetime.now()}")
    all_results = {}
    
    for ticker, name in ETF_LIST.items():
        print(f"🔍 {name}({ticker}) 탐색 중...", end=" ", flush=True)
        df = get_etf_holdings(ticker)
        
        if not df.empty:
            all_results[name] = df
            print(f"✅ {len(df)}개 종목 확보")
        else:
            print("❌ 실패 (데이터 구조 매칭 안됨)")

    if all_results:
        file_name = f"ETF_Report_{datetime.now().strftime('%m%d_%H%M')}.xlsx"
        with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
            for name, df in all_results.items():
                df.to_excel(writer, sheet_name=name[:30])
        
        # 텔레그램 전송
        with open(file_name, 'rb') as f:
            caption = f"📊 ETF 실시간 구성 종목 리스트\n기준일: {datetime.now().strftime('%Y-%m-%d')}"
            requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendDocument", 
                          data={'chat_id': CHAT_ID, 'caption': caption}, files={'document': f})
        print("✨ 모든 작업 완료!")
    else:
        print("😭 모든 시도가 실패했습니다.")
        requests.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", 
                      data={'chat_id': CHAT_ID, 'text': "⚠️ 2026-03-20: 네이버 데이터 구조 분석 실패. 다른 소스를 탐색해야 합니다."})
        sys.exit(1)

if __name__ == "__main__":
    main()
