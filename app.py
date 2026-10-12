import streamlit as st
import os
from datetime import datetime, timedelta

# 반드시 가장 먼저
st.set_page_config(page_title="반도체 위클리 브리프", page_icon="📄", layout="wide")

# 시크릿 -> 환경변수
for key in ("GOOGLE_API_KEY", "TAVILY_API_KEY"):
    if key in st.secrets:
        os.environ[key] = st.secrets[key]

def get_week_info():
    now = datetime.now()
    last_monday = now - timedelta(days=now.weekday() + 7)
    first_day = datetime(last_monday.year, last_monday.month, 1)
    week_number = (last_monday.day - 1 + first_day.weekday()) // 7 + 1
    return f"{last_monday.month}월 {week_number}주차"

week_info = get_week_info()

st.markdown(f"""
<div style="border-bottom: 2px solid #000; padding-bottom: 10px; margin-bottom: 20px;">
    <h1 style="color: #333; margin-bottom: 0;">위클리 브리프 ({week_info})</h1>
    <p style="color: #666; font-size: 14px; margin-top: 5px;">SK Hynix Tech & Trend Scout | 매주 월요일 아침 발행</p>
</div>
""", unsafe_allow_html=True)

if "GOOGLE_API_KEY" not in os.environ or "TAVILY_API_KEY" not in os.environ:
    st.error("API 키가 설정되지 않았습니다. Streamlit Cloud의 Secrets를 확인해 주세요.")
    st.stop()

# 헤더가 먼저 뜬 뒤에 무거운 import
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.prompts import PromptTemplate

@st.cache_resource
def get_clients():
    search = TavilySearchResults(max_results=5)
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")
    return search, llm

search, llm = get_clients()

prompt = PromptTemplate.from_template("""...기존 프롬프트 그대로...""")

if st.button("이번 주 데이터 수집 및 주간 리포트 생성"):
    with st.spinner("뉴스를 수집하고 리포트를 생성하는 중입니다..."):
        try:
            kr_results = search.invoke("지난 1주일 글로벌 반도체 최신 동향 삼성전자 SK하이닉스 이슈")
            en_results = search.invoke("Past 7 days semiconductor news Nvidia Intel TSMC trends")
            combined_news = kr_results + en_results

            result = (prompt | llm).invoke({"news_data": combined_news})

            st.markdown("### 📋 Executive Summary")
            st.markdown(result.content)
            st.markdown("<hr style='border: 1px solid #eee;'>", unsafe_allow_html=True)

            st.markdown("#### 🔗 Reference (지난주 분석 출처)")
            for i, news in enumerate(combined_news):
                if isinstance(news, dict) and "url" in news:
                    st.markdown(f"- [{news.get('title', f'Reference Article {i+1}')}]({news['url']})")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {e}")
