import os
import time
import hmac
import hashlib
import base64
import requests
import datetime

# --- [환경변수 로드] ---
NAVER_ACCESS_LICENSE = os.environ.get('NAVER_ACCESS_LICENSE')
NAVER_SECRET_KEY = os.environ.get('NAVER_SECRET_KEY')
CUSTOMER_ID = os.environ.get('CUSTOMER_ID')
TELEGRAM_TOKEN = os.environ.get('TELEGRAM_TOKEN')
CHAT_ID = os.environ.get('CHAT_ID')

BASE_URL = "https://api.naver.com"

def generate_signature(timestamp, method, uri):
    message = f"{timestamp}.{method}.{uri}"
    hash = hmac.new(NAVER_SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256)
    return base64.b64encode(hash.digest()).decode('utf-8')

def get_keyword_stats(keywords):
    """네이버 API를 통해 키워드 리스트의 상세 통계를 가져옴"""
    uri = "/keywordstool"
    method = "GET"
    timestamp = str(int(time.time() * 1000))
    
    headers = {
        "X-Timestamp": timestamp,
        "X-API-KEY": NAVER_ACCESS_LICENSE,
        "X-Customer": CUSTOMER_ID,
        "X-Signature": generate_signature(timestamp, method, uri)
    }
    
    # 키워드를 콤마로 연결 (최대 5개씩 끊어서 호출하는 것이 안전하지만 여기선 간략화)
    params = {"hintKeywords": ",".join(keywords), "showDetail": 1}
    
    try:
        response = requests.get(BASE_URL + uri, params=params, headers=headers)
        if response.status_code == 200:
            return response.json()['keywordList']
        return []
    except:
        return []

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def process_category(category_name, keyword_seeds):
    """카테고리별로 키워드를 분석하여 상위 10개를 뽑음"""
    stats = get_keyword_stats(keyword_seeds)
    if not stats:
        return f"❌ {category_name} 데이터 수집 실패\n"

    # 검색량 기준 내림차순 정렬
    sorted_stats = sorted(stats, key=lambda x: (int(x['monthlyPcQcCnt'] if isinstance(x['monthlyPcQcCnt'], int) else 0) + 
                                               int(x['monthlyMobileQcCnt'] if isinstance(x['monthlyMobileQcCnt'], int) else 0)), reverse=True)

    report = f"--- 🔮 **{category_name} TOP 10** ---\n"
    count = 0
    
    for item in sorted_stats:
        if count >= 10: break # 각 카테고리당 10개만
        
        kw = item['relKeyword']
        pc = item['monthlyPcQcCnt'] if isinstance(item['monthlyPcQcCnt'], int) else 0
        mo = item['monthlyMobileQcCnt'] if isinstance(item['monthlyMobileQcCnt'], int) else 0
        total = pc + mo
        
        # 1. 검색량 1,000회 이상 필터
        if total >= 1000:
            count += 1
            # 2. 님의 블로그 체급(100~200명) 맞춤 전략 분류
            if total <= 15000:
                report += f"💎 **[적중]** `{kw}`: {total:,}회\n"
            else:
                report += f"⚠️ **[대형]** `{kw}`: {total:,}회\n"
                
    if count == 0:
        report += "조건(1,000회 이상)에 맞는 키워드가 없습니다.\n"
    
    return report + "\n"

def main():
    # 1. 사주 카테고리 시드 키워드 (네이버가 연관 키워드를 확장해서 가져옴)
    saju_seeds = ["사주팔자", "만세력", "오늘의운세", "무료사주", "삼재", "꿈해몽", "궁합", "일주론", "신살", "개운법"]
    
    # 2. 풍수 카테고리 시드 키워드
    pungsu_seeds = ["풍수지리", "풍수인테리어", "침대방향", "거실풍수", "현관풍수", "재물운", "이사방향", "풍수액자", "주방풍수", "사무실풍수"]

    final_report = f"📅 **{datetime.date.today()} 블로그 전략 리포트**\n"
    final_report += "목표: 검색량 1,000건 이상 키워드 추출\n\n"
    
    final_report += process_category("사주/운세", saju_seeds)
    final_report += process_category("풍수지리/인테리어", pungsu_seeds)
    
    final_report += "💡 **전략:** [적중]은 메인 포스팅으로, [대형]은 참고용으로 활용하세요!"
    
    send_telegram(final_report)

if __name__ == "__main__":
    main()

