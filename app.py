import streamlit as st
import os
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(page_title="SK Hynix Weekly Tech Brief", page_icon="🔴", layout="wide")

# 2. 커스텀 CSS (디자인 스킨 입히기)
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; }
    .highlight-red { color: #E0002A; font-weight: bold; }
    .report-card {
        background-color: #F8F9FA; border-left: 5px solid #E0002A;
        padding: 20px; border-radius: 5px; margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    div.stButton > button:first-child {
        background-color: #E0002A; color: white; border: none;
        border-radius: 8px; padding: 10px 24px; font-size: 16px; font-weight: 600;
    }
    hr { border-top: 1px solid #EAEAEA; }
</style>
""", unsafe_allow_html=True)

# n월 n주차 계산
def get_week_info():
    now = datetime.now()
    last_monday = now - timedelta(days=now.weekday() + 7)
    month = last_monday.month
    first_day = datetime(last_monday.year, last_monday.month, 1)
    week_number = (last_monday.day - 1 + first_day.weekday()) // 7 + 1
    return f"{month}월 {week_number}주차"

week_info = get_week_info()

# 3. 헤더
col1, col2 = st.columns([1, 4])
with col1:
    st.markdown("<h1 style='color:#E0002A; font-size: 40px; margin-bottom:0;'>SK</h1>", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div style="margin-top: 10px;">
        <h2 style="color: #333; margin-bottom: 0;">Weekly Tech Brief <span style="color:#888; font-size:20px;">| {week_info}</span></h2>
        <p style="color: #666; font-size: 14px; margin-top: 5px;">AI가 분석하는 글로벌 반도체 기술 동향 및 시사점</p>
    </div>
    """, unsafe_allow_html=True)
st.markdown("<hr>", unsafe_allow_html=True)

# 4. API 키 가져오기
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain_core.prompts import PromptTemplate
except Exception as e:
    st.error(f"라이브러리 로딩 에러: {e}")
    st.stop()

# 5. 데이터 분석 섹션
left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown("### 📊 글로벌 마켓 & 인사이트 분석")
    st.caption("클릭 시 AI가 최근 7일간의 글로벌 반도체 기사를 수집하여 리포트를 작성합니다.")
    
    if st.button("이번 주 브리프 생성하기"):
        if not os.environ.get("GOOGLE_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
            st.error("🚨 API 키가 누락되었습니다. Secrets 설정을 확인하세요.")
            st.stop()
            
        with st.spinner("AI가 뉴스를 수집하고 분석 중입니다..."):
            try:
                # [디버깅] 1단계: 검색 API 테스트
                st.write("진행 상황 1: Tavily 검색 엔진 준비 중...")
                search = TavilySearchResults(max_results=5)
                
                # [디버깅] 2단계: Gemini API 테스트 (구형 모델명 에러 방지를 위해 gemini-1.5-pro 사용)
                st.write("진행 상황 2: Gemini 모델 준비 중...")
                llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash")
                
                prompt = PromptTemplate.from_template(
                    """
                    당신은 SK하이닉스의 수석 연구원이자 반도체 산업 전문 애널리스트입니다.
                    아래 검색된 최신 뉴스를 바탕으로 리포트를 작성하세요.
                    1. 이모지 사용 금지, 간결한 문어체.
                    2. 마크다운으로 제목과 본문 구분.
                    3. [1. 글로벌 시장 흐름]과 [2. SK하이닉스 시사점]으로 섹션 분리.
                    
                    뉴스 데이터: {news_data}
                    """
                )

                st.write("진행 상황 3: 뉴스 검색 중...")
                kr_results = search.invoke("SK하이닉스 반도체 최신 동향")
                en_results = search.invoke("Semiconductor news Nvidia Intel TSMC trends")
                combined_news = kr_results + en_results
                
                st.write("진행 상황 4: AI 리포트 작성 중 (가장 오래 걸림)...")
                chain = prompt | llm
                result = chain.invoke({"news_data": combined_news})
                
                # 결과 출력 (성공하면 진행 상황 텍스트는 덮어씌워짐)
                st.empty() # 진행 상황 텍스트 지우기
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(result.content)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 출처
                st.markdown("#### 🔗 References")
                for i, news in enumerate(combined_news):
                    if isinstance(news, dict):
                        url = news.get('url', '#')
                        title = news.get('title', f"Article {i+1}")
                        st.markdown(f"- [{title}]({url})")
                    else:
                        url = getattr(news, 'url', '#')
                        title = getattr(news, 'title', f"Article {i+1}")
                        st.markdown(f"- [{title}]({url})")

            # 🚨 [디버깅의 핵심] 에러가 나면 정확히 무슨 에러인지 빨간 상자로 화면에 띄움
            except Exception as e:
                import traceback
                error_trace = traceback.format_exc()
                st.error("🚨 데이터 수집/분석 중 상세 오류가 발생했습니다:")
                st.code(error_trace, language="python")

with right_col:
    st.markdown("### 📌 About")
    st.info("**[SK Pre-SKALA 프로젝트]**\n\nAI 기반 맞춤형 뉴스 요약 에이전트")
    st.caption("Developed for SK Hynix Tech Scout")
