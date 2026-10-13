import streamlit as st
import os
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

# 1. 페이지 기본 설정
st.set_page_config(page_title="SK Hynix Weekly Tech Brief", page_icon="🔴", layout="wide")

# 2. 커스텀 CSS (버튼 색상 고정 및 가독성 개선)
st.markdown("""
<style>
    /* 전체 배경 화이트, 텍스트 블랙 강제 지정 */
    .stApp { background-color: #FFFFFF; color: #111111; }
    
    /* 리포트 본문 컨테이너 스타일 (PDF 느낌) */
    .report-container {
        background-color: #FFFFFF;
        border: 1px solid #DDDDDD;
        border-top: 5px solid #E0002A;
        padding: 30px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.08);
        margin-bottom: 20px;
    }
    
    /* 리포트 내 제목 스타일 */
    .report-container h1 { color: #E0002A; font-size: 26px; border-bottom: 2px solid #EAEAEA; padding-bottom: 10px; margin-bottom: 20px; }
    .report-container h2 { color: #222222; font-size: 20px; margin-top: 25px; margin-bottom: 15px; }
    .report-container h3 { color: #444444; font-size: 16px; margin-top: 15px; }
    .report-container p, .report-container li { color: #333333; line-height: 1.7; font-size: 15px; }
    
    /* 과거 히스토리 박스 스타일 */
    .history-box { background-color: #F8F9FA; padding: 15px; border-radius: 5px; border-left: 3px solid #888888; }
    
    /* 🛠️ 버튼 스타일 강제 고정 (레드 배경, 화이트 텍스트) */
    div.stButton > button:first-child {
        background-color: #E0002A !important;
        color: #FFFFFF !important;
        font-weight: bold !important;
        border: none !important;
        transition: all 0.3s;
    }
    div.stButton > button:first-child:hover {
        background-color: #b30022 !important; /* 마우스 올렸을 때 조금 더 진한 빨간색 */
        color: #FFFFFF !important;
        border: none !important;
    }
    div.stButton > button:first-child p {
        color: #FFFFFF !important;
    }
</style>
""", unsafe_allow_html=True)

# 3. 데이터베이스 초기 세팅 및 함수
def init_db():
    conn = sqlite3.connect('brief_history.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS reports
        (id INTEGER PRIMARY KEY AUTOINCREMENT, 
         week_title TEXT, 
         content TEXT, 
         created_at TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

def save_report_to_db(week_title, content, simulated_date):
    conn = sqlite3.connect('brief_history.db')
    c = conn.cursor()
    c.execute("SELECT id FROM reports WHERE week_title=?", (week_title,))
    result = c.fetchone()
    if result:
        c.execute("UPDATE reports SET content=?, created_at=? WHERE week_title=?", 
                  (content, simulated_date, week_title))
    else:
        c.execute("INSERT INTO reports (week_title, content, created_at) VALUES (?, ?, ?)", 
                  (week_title, content, simulated_date))
    conn.commit()
    conn.close()

def load_history():
    conn = sqlite3.connect('brief_history.db')
    df = pd.read_sql_query("SELECT week_title, content, created_at FROM reports ORDER BY created_at DESC", conn)
    conn.close()
    return df

init_db()

# 4. 헤더 UI
st.markdown("""
<div style="display: flex; align-items: center; margin-bottom: 20px;">
    <h1 style='color:#E0002A; font-size: 38px; margin:0; margin-right: 15px;'>SK</h1>
    <div>
        <h2 style="color: #111; margin:0;">Weekly Memory Brief</h2>
        <p style="color: #666; font-size: 14px; margin-top: 4px;">SK하이닉스 임직원을 위한 주간칼럼</p>
    </div>
</div>
<hr style='margin-top:0px; margin-bottom:30px;'>
""", unsafe_allow_html=True)

# API 키 세팅
if "GOOGLE_API_KEY" in st.secrets:
    os.environ["GOOGLE_API_KEY"] = st.secrets["GOOGLE_API_KEY"]
if "TAVILY_API_KEY" in st.secrets:
    os.environ["TAVILY_API_KEY"] = st.secrets["TAVILY_API_KEY"]

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    from langchain_community.tools.tavily_search import TavilySearchResults
    from langchain_core.prompts import PromptTemplate
except Exception as e:
    st.error("시스템 오류가 발생했습니다.")
    st.stop()

# 5. 메인 레이아웃 분할
left_col, right_col = st.columns([2, 1])

with left_col:
    # 🎯 생성할 주차 선택 옵션
    st.markdown("### 🛠️ 칼럼 생성 🛠️")
    
    week_options = {
        "9월 1주차": datetime(2026, 9, 7, 7, 0, 0),
        "9월 2주차": datetime(2026, 9, 14, 7, 0, 0),
        "9월 3주차": datetime(2026, 9, 21, 7, 0, 0),
        "9월 4주차": datetime(2026, 9, 28, 7, 0, 0),
        "10월 1주차": datetime(2026, 10, 5, 7, 0, 0),
        "10월 2주차": datetime(2026, 10, 12, 7, 0, 0),
        "10월 3주차": datetime(2026, 10, 19, 7, 0, 0)
    }
    
    selected_week = st.selectbox("DB에 주입할 브리프 주차를 선택하세요:", list(week_options.keys()), index=5)
    simulated_date = week_options[selected_week]
    
    if st.button(f"🚀 [{selected_week}] 브리프 생성 및 DB 저장", use_container_width=True):
        if not os.environ.get("GOOGLE_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
            st.error("🚨 API 키가 누락되었습니다.")
        else:
            with st.spinner(f"AI가 {selected_week} 기준 뉴스를 수집하고 리포트를 작성 중입니다... (약 20초)"):
                try:
                    search = TavilySearchResults(max_results=5)
                    llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash") # 최신 안정 버전으로 권장
                    
                    prompt = PromptTemplate.from_template(
                        """
                        당신은 SK하이닉스 최고 애널리스트입니다. 
                        현재 시점은 '{target_week}'입니다. 아래 뉴스를 바탕으로 {target_week}의 반도체 시장 흐름 보고서를 작성하세요.
                        출력 형식은 마크다운(Markdown)을 엄격히 지켜주세요.
                        
                        [보고서 양식 강제 사항]
                        # AI 인프라 확장에 따른 반도체 생태계 재편 및 메모리 전략 리포트
                        
                        ## 1. 글로벌 시장 흐름
                        (내용 작성 시 ### 소제목을 사용하여 문단을 나눌 것)
                        
                        ## 2. SK하이닉스 시사점
                        (내용 작성 시 ### 소제목을 사용하여 문단을 나눌 것)
                        
                        (주의: 절대로 마지막에 참조/출처 링크를 텍스트 안에 적지 마세요. 본문만 작성하세요.)
                        
                        뉴스 데이터: {news_data}
                        """
                    )

                    kr_results = search.invoke(f"SK하이닉스 반도체 HBM 최신 동향 {selected_week}")
                    en_results = search.invoke(f"Semiconductor news Nvidia Intel TSMC trends {selected_week}")
                    combined_news = kr_results + en_results
                    
                    chain = prompt | llm
                    result = chain.invoke({
                        "news_data": combined_news,
                        "target_week": selected_week
                    })
                    
                    # 🛡️ 에러 해결 핵심: 리스트 형태로 넘어올 경우 텍스트만 깔끔하게 추출
                    if isinstance(result.content, list):
                        final_content = result.content[0]['text']
                    else:
                        final_content = result.content
                    
                    # DB에 저장
                    save_report_to_db(selected_week, final_content, simulated_date)
                    
                    st.success(f"✅ [{selected_week}] 리포트가 성공적으로 DB에 주입되었습니다!")
                    
                    # 생성된 리포트 출력
                    st.markdown(f'<div class="report-container">', unsafe_allow_html=True)
                    st.markdown(final_content)
                    st.markdown('</div>', unsafe_allow_html=True)
                    
                    # 출처 링크 표시
                    st.markdown("### 🔗 Reference (분석 참조 기사)")
                    for i, news in enumerate(combined_news):
                        url = news.get('url', '#') if isinstance(news, dict) else getattr(news, 'url', '#')
                        title = news.get('title', f"Reference Article {i+1}") if isinstance(news, dict) else getattr(news, 'title', f"Reference {i+1}")
                        st.caption(f"- [{title}]({url})")

                except Exception as e:
                    import traceback
                    st.error("오류 발생")
                    st.code(traceback.format_exc(), language="python")

# --- [우측 칼럼: 데이터베이스(DB) 히스토리 뷰어] ---
with right_col:
    st.markdown("### 🗄️ Past Reports Archive")
    st.caption("SQLite DB에 저장된 과거 브리프 기록입니다.")
    
    history_df = load_history()
    
    if history_df.empty:
        st.info("아직 저장된 과거 리포트가 없습니다. 좌측에서 9월 1주차부터 차례대로 생성해 보세요!")
    else:
        for idx, row in history_df.iterrows():
            with st.expander(f"📄 {row['week_title']} 브리프"):
                st.caption(f"생성일시: {str(row['created_at'])[:16]}")
                st.markdown(f'<div class="history-box">', unsafe_allow_html=True)
                st.markdown(row['content'])
                st.markdown('</div>', unsafe_allow_html=True)
