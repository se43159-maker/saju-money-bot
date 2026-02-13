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
    """네이버 API에 키워드를 5개씩 끊어서 요청 (과부하 및 에러 방지)"""
    uri = "/keywordstool"
    method = "GET"
    all_results = []
    
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
            time.sleep(0.5)
        except:
            continue
            
    return all_results

def send_telegram(msg):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    requests.post(url, json={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})

def process_category(category_name, keyword_seeds):
    """카테고리별 검색량 1000 이상 상위 10개 추출 및 등급 분류"""
    stats = get_keyword_stats(keyword_seeds)
    if not stats:
        return f"❌ {category_name}: 데이터 수집 실패\n"

    valid_list = []
    for s in stats:
        # 월간 검색량 수치 예외 처리 (문자열 '10 미만' 등 처리)
        pc = s['monthlyPcQcCnt'] if isinstance(s['monthlyPcQcCnt'], int) else 0
        mo = s['monthlyMobileQcCnt'] if isinstance(s['monthlyMobileQcCnt'], int) else 0
        total = pc + mo
        
        # 중복 제거 및 검색량 1000 이상만 포함
        if total >= 1000:
            valid_list.append({'kw': s['relKeyword'], 'total': total})

    # 검색량 높은 순으로 정렬 후 중복 제거
    unique_list = {item['kw']: item for item in valid_list}.values()
    sorted_list = sorted(unique_list, key=lambda x: x['total'], reverse=True)

    report = f"🔮 **{category_name} TOP 10**\n"
    count = 0
    for item in sorted_list:
        if count >= 10: break
        
        # 💎 다이아: 1,000~15,000 (공략 가능)
        # ⚠️ 느낌표: 15,000 초과 (대형 키워드)
        rank_icon = "💎" if item['total'] <= 15000 else "⚠️"
        report += f"{count+1}. {rank_icon} `{item['kw']}`: {item['total']:,}회\n"
        count += 1
        
    if count == 0:
        report += "검색량 1,000회 이상 키워드가 없습니다.\n"
    
    return report + "\n"

def main():
    # 블로그 지수에 최적화된 세부 시드 키워드 (더 정밀하게 수정됨)
    saju_seeds = [
        "일주론풀이", "십이신살", "상관운", "편인격", "겁재운", 
        "들삼재날삼재", "사주도화살", "계수일간", "을목특징", "개운법"
    ]
    
    pungsu_seeds = [
        "거실풍수인테리어", "현관종위치", "침대머리방향", "안방가구배치", "주방풍수지리",
        "풍수그림위치", "재물운인테리어", "현관거울풍수", "베란다식물풍수", "금전운지갑"
    ]

    final_report = f"📅 **{datetime.date.today()} 블로그 전략 리포트**\n"
    final_report += "✅ 기준: 월 검색량 1,000회 이상\n\n"
    
    final_report += process_category("사주 교육/풀이", saju_seeds)
    final_report += process_category("풍수 생활/인테리어", pungsu_seeds)
    
    final_report += "💡 **블로그 지수 맞춤 전략**\n"
    final_report += "- 💎: 100~200명 블로그가 1등 하기 좋습니다.\n"
    final_report += "- ⚠️: 검색량은 많으나 경쟁이 매우 치열합니다."
    
    send_telegram(final_report)

if __name__ == "__main__":
    main()

