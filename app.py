import streamlit as st
import os
from datetime import datetime, timedelta

# 1. 페이지 기본 설정 및 탭 이름 변경
st.set_page_config(page_title="SK Hynix Weekly Tech Brief", page_icon="🔴", layout="wide")

# 🎨 2. 커스텀 CSS (디자인 스킨 입히기)
st.markdown("""
<style>
    /* 전체 배경은 깔끔한 하얀색 */
    .stApp {
        background-color: #FFFFFF;
    }
    
    /* 헤더 및 포인트 컬러 설정 (SK하이닉스 레드: #E0002A) */
    .highlight-red {
        color: #E0002A;
        font-weight: bold;
    }
    
    /* 리포트 카드 디자인 */
    .report-card {
        background-color: #F8F9FA;
        border-left: 5px solid #E0002A;
        padding: 20px;
        border-radius: 5px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    
    /* 버튼 디자인 세련되게 변경 */
    div.stButton > button:first-child {
        background-color: #E0002A;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-size: 16px;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    div.stButton > button:first-child:hover {
        background-color: #C00020;
        box-shadow: 0 4px 10px rgba(224, 0, 42, 0.3);
    }

    /* 경계선 스타일 */
    hr {
        border-top: 1px solid #EAEAEA;
    }
</style>
""", unsafe_allow_html=True)

# '지난주 월요일'을 기준으로 n월 n주차를 계산하는 함수
def get_week_info():
    now = datetime.now()
    last_monday = now - timedelta(days=now.weekday() + 7)
    month = last_monday.month
    first_day = datetime(last_monday.year, last_monday.month, 1)
    week_number = (last_monday.day - 1 + first_day.weekday()) // 7 + 1
    return f"{month}월 {week_number}주차"

week_info = get_week_info()

# 📝 3. 세련된 헤더(Header) 영역
col1, col2 = st.columns([1, 4])
with col1:
    # (선택) 여기에 실제 로고 이미지 URL을 넣으면 더 완벽해집니다!
    st.markdown("<h1 style='color:#E0002A; font-size: 40px; margin-bottom:0;'>SK</h1>", unsafe_allow_html=True)
with col2:
    st.markdown(f"""
    <div style="margin-top: 10px;">
        <h2 style="color: #333; margin-bottom: 0;">Weekly Tech Brief <span style="color:#888; font-size:20px;">| {week_info}</span></h2>
        <p style="color: #666; font-size: 14px; margin-top: 5px;">AI가 분석하는 글로벌 반도체 기술 동향 및 시사점</p>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)

# 🔑 4. API 키 가져오기 (오류 방지용 검증 포함)
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

# 앱 실행 전 라이브러리 검증
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain_core.prompts import PromptTemplate
except Exception as e:
    st.error("시스템 로딩 오류. 잠시 후 다시 시도해 주세요.")
    st.stop()

# 🚀 5. 데이터 분석 및 출력 섹션
# 레이아웃을 칼럼(단)으로 나누어 가독성을 높입니다.
left_col, right_col = st.columns([2, 1])

with left_col:
    st.markdown("### 📊 글로벌 마켓 & 인사이트 분석")
    st.caption("클릭 시 AI가 최근 7일간의 글로벌 반도체 기사를 수집하여 리포트를 작성합니다.")
    
    if st.button("이번 주 브리프 생성하기"):
        if not os.environ.get("GOOGLE_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
            st.error("🚨 환경 설정(API 키) 오류. 시스템 관리자에게 문의하세요.")
            st.stop()
            
        with st.spinner("AI가 전 세계 뉴스를 실시간으로 분석하고 있습니다... (약 20초 소요)"):
            try:
                search = TavilySearchResults(max_results=5) 
                llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash")

                # 프롬프트(지시문)도 깔끔한 출력을 위해 개선
                prompt = PromptTemplate.from_template(
                    """
                    당신은 SK하이닉스의 수석 연구원이자 반도체 산업 전문 애널리스트입니다.
                    아래 검색된 데이터는 '지난 1주일간'의 최신 글로벌 반도체 뉴스입니다. 
                    
                    [작성 가이드라인]
                    1. 이모지(아이콘) 사용 금지, 간결하고 전문적인 문어체(~이다, ~전망된다) 사용.
                    2. 출력 내용은 마크다운(Markdown) 형식을 사용하여 제목과 본문을 깔끔하게 구분할 것.
                    3. [1. 주간 글로벌 반도체 시장 흐름]과 [2. SK하이닉스 인사이트 및 시사점]으로 섹션을 나눌 것.
                    4. 반도체 기술 개념, 공급망 이슈 등 시각적 이해가 필요한 부분(최소 1곳 이상)에는 **반드시 아래 이미지 생성 포맷을 삽입**할 것.
                       - 포맷: ![이미지 설명](https://image.pollinations.ai/prompt/그림을_묘사하는_상세한_영문_프롬프트?width=800&height=400)
                    
                    지난 1주일간 검색된 뉴스 데이터:
                    {news_data}
                    
                    리포트 본문:
                    """
                )

                kr_results = search.invoke("지난 1주일 글로벌 반도체 최신 동향 삼성전자 SK하이닉스 HBM 이슈")
                en_results = search.invoke("Past 7 days semiconductor news Nvidia Intel TSMC AI trends")
                combined_news = kr_results + en_results
                
                chain = prompt | llm
                result = chain.invoke({"news_data": combined_news})
                
                # 리포트 본문을 커스텀 CSS 박스 안에 예쁘게 출력
                st.markdown('<div class="report-card">', unsafe_allow_html=True)
                st.markdown(result.content)
                st.markdown('</div>', unsafe_allow_html=True)
                
                # 참고 문헌 리스트 출력
                st.markdown("#### 🔗 References (출처 기사)")
                st.caption("AI가 분석에 활용한 원문 기사 리스트입니다.")
                for i, news in enumerate(combined_news):
                    if isinstance(news, dict):
                        url = news.get('url', '#')
                        title = news.get('title', f"Reference Article {i+1}")
                        st.markdown(f"- [{title}]({url})")
                    else:
                        url = getattr(news, 'url', '#')
                        title = getattr(news, 'title', f"Reference Article {i+1}")
                        st.markdown(f"- [{title}]({url})")

            except Exception as e:
                st.error("데이터 수집 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.")

with right_col:
    # 오른쪽 사이드 패널에 프로그램 안내와 부가 정보 배치
    st.markdown("### 📌 About")
    st.info(
        "**[Weekly Memory Brief]**\n\n"
        "이 웹 서비스는 AI 에이전트(Agent) 기술을 활용하여 흩어져 있는 방대한 반도체 뉴스를 수집하고, "
        "SK하이닉스 실무진에게 필요한 핵심 인사이트만을 자동으로 요약·추출하기 위해 기획되었습니다."
    )
    
    st.markdown("#### 주요 기능")
    st.markdown("""
    - 실시간 글로벌 뉴스 트래킹 (Tavily AI)
    - 맥락 기반 인사이트 도출 (LLM)
    - 텍스트 기반 시각화 자동 생성
    """)
    
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("Developed for SK Hynix Tech & Trend Scout Project")
