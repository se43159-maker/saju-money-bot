import os
import time
import hmac
import hashlib
import base64
import requests
import datetime
from korean_lunar_calendar import KoreanLunarCalendar

# 1. 깃허브 금고(Secrets)에서 열쇠 꺼내기
NAVER_ACCESS_LICENSE = os.environ.get('NAVER_ACCESS_LICENSE')
NAVER_SECRET_KEY = os.environ.get('NAVER_SECRET_KEY')
CUSTOMER_ID = os.environ.get('CUSTOMER_ID')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

BASE_URL = "https://api.naver.com"

# 2. 네이버 API 서명 생성 (보안)
def generate_signature(timestamp, method, uri):
    message = f"{timestamp}.{method}.{uri}"
    hash = hmac.new(NAVER_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(hash.digest()).decode('utf-8')

# 3. 키워드 검색량 조회 함수
def get_search_volume(keyword):
    uri = "/keywordstool"
    method = "GET"
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": NAVER_ACCESS_LICENSE,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": generate_signature(timestamp, method, uri)
    }
    
    try:
        # 네이버에 데이터 요청
        response = requests.get(BASE_URL + uri, params={"hintKeywords": keyword, "showDetail": 1}, headers=headers)
        
        if response.status_code != 200:
            return 0
            
        data = response.json()
        if not data['keywordList']:
            return 0
            
        # 첫 번째 결과 가져오기
        item = data['keywordList'][0]
        pc = item['monthlyPcQcCnt']
        mo = item['monthlyMobileQcCnt']
        
        # '< 10' 같은 문자는 0으로 처리
        if isinstance(pc, str): pc = 0
        if isinstance(mo, str): mo = 0
            
        return pc + mo
    except Exception as e:
        print(f"Error checking {keyword}: {e}")
        return 0

# 4. 텔레그램 발송 함수
def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID, 
        'text': msg, 
        'parse_mode': 'Markdown'
    }
    requests.post(url, json=payload)

# 5. 메인 실행 로직
def main():
    print("--- 봇 가동 시작 ---")
    
    # 예시: 사주 관련 키워드 리스트
    target_keywords = ["2026년삼재", "토정비결", "오늘의운세", "꿈해몽"]
    
    report_msg = "🚨 **[사주 키워드 트래픽 리포트]**\n\n"
    found_gold = False
    
    for kw in target_keywords:
        vol = get_search_volume(kw)
        print(f"키워드: {kw} / 검색량: {vol}")
        
        # 검색량이 1,000건 넘는 것만 알림
        if vol >= 1000:
            report_msg += f"✅ `{kw}` : **{vol:,}회**\n"
            found_gold = True
            
    if found_gold:
        report_msg += "\n지금 바로 글을 작성하세요!"
        send_telegram(report_msg)
        print("알림 발송 완료")
    else:
        print("조건에 맞는 키워드가 없어 알림을 보내지 않았습니다.")

if __name__ == "__main__":
    main()
