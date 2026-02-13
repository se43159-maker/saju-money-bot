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
    """네이버 API에 키워드를 5개씩 끊어서 요청 (에러 방지용)"""
    uri = "/keywordstool"
    method = "GET"
    all_results = []
    
    # 5개씩 나누어 요청
    for i in range(0, len(keywords), 5):
        chunk = keywords[i:i+5]
        timestamp = str(int(time.time() * 1000))
        headers = {
            "X-Timestamp": timestamp,
            "X-API-KEY": NAVER_ACCESS_LICENSE,
            "X-Customer": CUSTOMER_ID,
            "X-Signature": generate_signature(timestamp, method, uri)
        }
        params = {"hintKeywords": ",".join(chunk), "showDetail": 1}
        
        try:
            response = requests.get(BASE_URL + uri, params=params, headers=headers)
            if response.status_code == 200:
                all_results.extend(response.json().get('keywordList', []))
            time.sleep(0.5) # 과부하 방지
        except:
            continue
            
    return all_results

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def process_category(category_name, keyword_seeds):
    """카테고리별 검색량 1000 이상 상위 10개 추출"""
    stats = get_keyword_stats(keyword_seeds)
    if not stats:
        return f"❌ {category_name}: 데이터 요청 실패\n"

    # 검색량 기준 정렬 (내림차순)
    valid_list = []
    for s in stats:
        pc = s['monthlyPcQcCnt'] if isinstance(s['monthlyPcQcCnt'], int) else 0
        mo = s['monthlyMobileQcCnt'] if isinstance(s['monthlyMobileQcCnt'], int) else 0
        total = pc + mo
        if total >= 1000:
            valid_list.append({'kw': s['relKeyword'], 'total': total})

    sorted_list = sorted(valid_list, key=lambda x: x['total'], reverse=True)

    report = f"🔮 **{category_name} TOP 10**\n"
    for i, item in enumerate(sorted_list[:10]):
        # 100~200명 블로그를 위한 체급 분류
        rank_icon = "💎" if item['total'] <= 15000 else "⚠️"
        report += f"{i+1}. {rank_icon} `{item['kw']}`: {item['total']:,}회\n"
        
    if not sorted_list:
        report += "검색량 1,000회 이상 키워드 없음\n"
    
    return report + "\n"

def main():
    # 님 블로그 주제에 맞춘 정밀 시드 키워드
    saju_seeds = ["사주팔자", "만세력", "오늘의운세", "무료사주", "삼재", "일주론", "신살", "개운법", "사주풀이", "십이신살"]
    pungsu_seeds = ["풍수지리", "풍수인테리어", "침대방향", "거실풍수", "현관풍수", "재물운", "이사방향", "풍수액자", "주방풍수", "풍수그림"]

    final_report = f"📅 **{datetime.date.today()} 블로그 전략 리포트**\n"
    final_report += "✅ 목표: 검색량 1,000건 이상 추출\n\n"
    
    final_report += process_category("사주/운세", saju_seeds)
    final_report += process_category("풍수지리/인테리어", pungsu_seeds)
    
    final_report += "💡 **전략:** 💎는 1등 노출 가능, ⚠️는 참고용!"
    
    send_telegram(final_report)

if __name__ == "__main__":
    main()

