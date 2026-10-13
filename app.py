import streamlit as st
import os
from datetime import datetime, timedelta

# 1. 묻지도 따지지도 않고 화면부터 강제로 띄우기
st.set_page_config(page_title="글로벌 반도체 주간 동향 분석", page_icon="📄", layout="wide")

# '지난주 월요일'을 기준으로 n월 n주차를 계산하는 함수
def get_week_info():
    now = datetime.now()
    last_monday = now - timedelta(days=now.weekday() + 7)
    month = last_monday.month
    first_day = datetime(last_monday.year, last_monday.month, 1)
    week_number = (last_monday.day - 1 + first_day.weekday()) // 7 + 1
    return f"{month}월 {week_number}주차"

week_info = get_week_info()

# 헤더 디자인 
st.markdown(f"""
<div style="border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
    <h1 style="color: #333; margin-bottom: 0;">반도체 위클리 브리프 ({week_info})</h1>
    <p style="color: #666; font-size: 14px; margin-top: 5px;">SK Hynix Tech & Trend Scout | 매주 월요일 아침 발행</p>
</div>
""", unsafe_allow_html=True)

# 2. [가장 중요] API 키 상태를 화면에 적나라하게 보여주기
st.markdown("### 🚨 현재 시스템 상태 점검 (디버깅)")

has_google_key = "GOOGLE_API_KEY" in st.secrets
has_tavily_key = "TAVILY_API_KEY" in st.secrets

st.write(f"1. Streamlit Secrets(금고)에 구글 키가 등록되어 있나요? 👉 **{has_google_key}**")
st.write(f"2. Streamlit Secrets(금고)에 타빌리 키가 등록되어 있나요? 👉 **{has_tavily_key}**")

if not has_google_key or not has_tavily_key:
    st.error("""
    **⛔ 오류: API 키가 금고(Secrets)에 없습니다!**
    
    웹사이트는 정상적으로 켜졌지만, Streamlit Cloud의 [Settings] -> [Secrets] 창에 API 키가 설정되어 있지 않아 멈췄습니다. 
    아래 형식을 참고하여 Secrets 창에 키를 꼭 입력해 주세요.
    
    ```toml
    GOOGLE_API_KEY = "본인의_제미나이_키_입력"
    TAVILY_API_KEY = "본인의_타빌리_키_입력"
    ```
    """)
    st.stop() # 키가 없으면 더 이상 진행하지 않고 안전하게 멈춤

# 3. 키가 있다면 안전하게 꺼내오기
os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

st.success("✅ 모든 API 키가 정상적으로 확인되었습니다! 아래 버튼을 눌러보세요.")

# 4. 안전하게 지연 로딩하는 AI 모듈 (앱 켜질 때 충돌 방지)
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain_core.prompts import PromptTemplate
except Exception as e:
    st.error(f"모듈 로딩 중 에러 발생: {e}")
    st.stop()

# 5. 실행 버튼 구조
if st.button("이번 주 데이터 수집 및 주간 리포트 생성"):
    with st.spinner("지난 1주일간의 뉴스를 수집하고 시각 자료(이미지)를 생성하는 중입니다... (약 15~30초 소요)"):
        try:
            search = TavilySearchResults(max_results=5) 
            llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

            prompt = PromptTemplate.from_template(
                """
                당신은 증권사 수석 연구원이자 반도체 산업 전문 애널리스트입니다.
                아래 검색된 데이터는 '지난 1주일간'의 최신 글로벌 반도체 뉴스입니다. 
                이 데이터를 분석하여 SK하이닉스 임직원들에게 배포되는 공식적인 [반도체 위클리 브리프]를 작성해 주세요.
                
                [작성 가이드라인]
                1. 이모지(아이콘) 사용을 금지하고, 객관적이고 전문적인 문어체(~이다, ~전망된다)를 사용하십시오.
                2. '지난주 글로벌 반도체 시장 흐름'과 'SK하이닉스에 주는 시사점'을 단락으로 명확히 구분하십시오.
                3. 반도체 기술 개념(예: HBM 3D 스택 구조), 공급망 흐름, 또는 복잡한 이슈 등 시각적 이해가 필요한 부분에는 반드시 1개 이상의 실제 그래픽 이미지(그림)를 생성하여 삽입하십시오.
                4. 이미지를 생성하고 삽입할 때는 아래의 이미지 생성 API URL 포맷을 정확히 사용해야 합니다. URL의 맨 마지막 부분에 당신이 그리고 싶은 그림을 상세한 영문(English) 프롬프트로 묘사해서 적어 넣으면 실제 이미지가 화면에 렌더링됩니다.
                   
                   형식: ![이미지 설명](https://image.pollinations.ai/prompt/여기에_그림을_자세히_묘사하는_영문_프롬프트_작성_띄어쓰기_포함_가능?width=800&height=400)
                   예시: ![HBM과 GDDR 구조 비교 시각화](https://image.pollinations.ai/prompt/A_high_quality_3d_infographic_comparing_HBM_vertical_stacking_and_GDDR_memory_chips?width=800&height=400)
                
                지난 1주일간 검색된 뉴스 데이터:
                {news_data}
                
                작성된 주간 리포트:
                """
            )

            kr_results = search.invoke("지난 1주일 글로벌 반도체 최신 동향 삼성전자 SK하이닉스 이슈")
            en_results = search.invoke("Past 7 days semiconductor news Nvidia Intel TSMC trends")
            combined_news = kr_results + en_results
            
            chain = prompt | llm
            result = chain.invoke({"news_data": combined_news})
            
            st.markdown("### 📋 Executive Summary")
            st.markdown(result.content)
            
            st.markdown("<hr style='border: 1px solid #eee;'>", unsafe_allow_html=True)
            
            st.markdown("#### 🔗 Reference (지난주 분석 출처)")
            st.caption("클릭 시 AI가 분석에 활용한 원문 기사로 이동합니다.")
            
            for i, news in enumerate(combined_news):
                # 안전한 딕셔너리 및 객체 속성 처리
                if isinstance(news, dict):
                    url = news.get('url', '#')
                    title = news.get('title', f"Reference Article {i+1}")
                    st.markdown(f"- [{title}]({url})")
                else:
                    url = getattr(news, 'url', '#')
                    title = getattr(news, 'title', f"Reference Article {i+1}")
                    st.markdown(f"- [{title}]({url})")

        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
