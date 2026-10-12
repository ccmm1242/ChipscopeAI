import streamlit as st
import os
import ast
from datetime import datetime
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import PromptTemplate

# n월n주차함수
def get_week_info():
    now = datetime.now()
    last_monday = now - timedelta(days=now.weekday() + 7)
    month = last_monday.month
    first_day = datetime(last_monday.year, last_monday.month, 1)
    week_number = (last_monday.day - 1 + first_day.weekday()) // 7 + 1
    return f"{month}월 {week_number}주차"

week_info = get_week_info()

# 페이지 기본 설정
st.set_page_config(page_title="반도체 위클리 브리프()", page_icon="📄", layout="wide")

# 헤더 디자인 (증권사 리포트 스타일)
st.markdown(f"""
<div style="border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
    <h1 style="color: #333; margin-bottom: 0;">위클리 브리프 ({week_info})</h1>
    <p style="color: #666; font-size: 14px; margin-top: 5px;">SK Hynix Tech & Trend Scout | 매주 월요일 아침 발행</p>
</div>
""", unsafe_allow_html=True)

# API 키 확인
if "GOOGLE_API_KEY" not in os.environ or "TAVILY_API_KEY" not in os.environ:
    st.error("API 키가 설정되지 않았습니다. 코드를 확인해 주세요.")
    st.stop()

# 에이전트 세팅
search = TavilySearchResults(max_results=5)
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

# 프롬프트 세팅 (실제 AI 이미지 생성을 위한 마법의 URL 지시사항 추가)
prompt = PromptTemplate.from_template(
    """
    당신은 sk하이닉스 미래전략실 수석 팀장입니다.
    아래 검색된 데이터는 '지난 1주일간'의 최신 글로벌 반도체 뉴스입니다.
    이 데이터를 분석하여 SK하이닉스 임직원들에게 배포되는 공식적인 [위클리 브리프]를 작성해 주세요.

    [작성 가이드라인]
    1. 이모지(아이콘) 사용을 금지하고, 객관적이고 전문적인 문어체(~이다, ~전망된다)를 사용하십시오.
    2. '지난주 글로벌 반도체 시장 흐름'과 'SK하이닉스에 주는 시사점'을 단락으로 명확히 구분하십시오.
    3. 반도체 기술 개념(예: HBM 3D 스택 구조), 공급망 흐름, 또는 복잡한 이슈 등 시각적 이해가 필요한 부분에는 **반드시 1개 이상의 실제 그래픽 이미지(그림)**를 생성하여 삽입하십시오.
    4. 이미지를 생성하고 삽입할 때는 아래의 이미지 생성 API URL 포맷을 정확히 사용해야 합니다. URL의 맨 마지막 부분에 당신이 그리고 싶은 그림을 상세한 영문(English) 프롬프트로 묘사해서 적어 넣으면 실제 이미지가 화면에 렌더링됩니다.

       형식: ![이미지 설명](https://image.pollinations.ai/prompt/여기에_그림을_자세히_묘사하는_영문_프롬프트_작성_띄어쓰기_포함_가능?width=800&height=400)
       예시: ![HBM과 GDDR 구조 비교 시각화](https://image.pollinations.ai/prompt/A_high_quality_3d_infographic_comparing_HBM_vertical_stacking_and_GDDR_memory_chips?width=800&height=400)

    지난 1주일간 검색된 뉴스 데이터:
    {news_data}

    작성된 주간 리포트:
    """
)

# 데이터 수집 및 분석 실행
if st.button("이번 주 데이터 수집 및 주간 리포트 생성"):
    with st.spinner("지난 1주일간의 뉴스를 수집하고 시각 자료(이미지)를 생성하는 중입니다... (약 15~30초 소요)"):
        try:
            # 1. 뉴스 검색
            kr_results = search.invoke("지난 1주일 글로벌 반도체 최신 동향 삼성전자 SK하이닉스 이슈")
            en_results = search.invoke("Past 7 days semiconductor news Nvidia Intel TSMC trends")
            combined_news = kr_results + en_results

            # 2. AI 분석 및 리포트 작성
            chain = prompt | llm
            result = chain.invoke({"news_data": combined_news})

            # 3. 리포트 본문 출력
            st.markdown("### 📋 Executive Summary")
            st.markdown(result.content)

            st.markdown("<hr style='border: 1px solid #eee;'>", unsafe_allow_html=True)

            # 4. 출처 링크 표시
            st.markdown("#### 🔗 Reference (지난주 분석 출처)")
            st.caption("클릭 시 AI가 분석에 활용한 원문 기사로 이동합니다.")

            for i, news in enumerate(combined_news):
                if isinstance(news, dict) and 'url' in news:
                    url = news['url']
                    title = news.get('title', f"Reference Article {i+1}")
                    st.markdown(f"- [{title}]({url})")
                elif hasattr(news, 'url'):
                    url = getattr(news, 'url')
                    title = getattr(news, 'title', f"Reference Article {i+1}")
                    st.markdown(f"- [{title}]({url})")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
