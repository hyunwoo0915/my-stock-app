mport streamlit as st
import yfinance as yf
import pandas as pd
from datetime import datetime

# ==========================================
# 1. 스마트폰 화면/웹 브라우저 기본 설정
# ==========================================
st.set_page_config(
    page_title="주도주 & 종가베팅 대시보드",
    page_icon="📈",
    layout="centered"
)

# 타이틀 및 안내문
st.title("📈 주도주 & 종가베팅 모니터")
st.caption(f"최신 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

# ==========================================
# 2. 추천 종목 데이터 (예시 및 데이터 로드)
# ==========================================
st.subheader("🔥 오늘의 종가베팅 / 주도주 후보")

# 관심 종목 리스트 (한국 주식: 코스피 .KS, 코스닥 .KQ)
stocks = {
    "삼성전자": "005930.KS",
    "SK하이닉스": "000660.KS",
    "현대차": "005380.KS",
    "알테오젠": "196170.KQ"
}

# 탭 메뉴로 종목 선택
selected_stock_name = st.selectbox("📌 조회할 종목을 선택하세요", list(stocks.keys()))
selected_ticker = stocks[selected_stock_name]

# ==========================================
# 3. 주가 데이터 가져오기 및 시각화
# ==========================================
with st.spinner("주가 데이터를 불러오는 중..."):
    stock_data = yf.Ticker(selected_ticker)
    df = stock_data.history(period="1mo") # 최근 1달 데이터

if not df.empty:
    current_price = df['Close'].iloc[-1]
    prev_price = df['Close'].iloc[-2]
    price_change = current_price - prev_price
    pct_change = (price_change / prev_price) * 100

    # 주요 지표 카드 형태로 표시
    col1, col2 = st.columns(2)
    col1.metric("현재가 / 종가", f"{int(current_price):,} 원", f"{pct_change:+.2f}%")
    col2.metric("당일 거래량", f"{int(df['Volume'].iloc[-1]):,} 주")

    # 주가 차트 그리기
    st.markdown("### 📊 최근 1개월 주가 추이")
    st.line_chart(df['Close'])

    # 매수 전 필수 체크리스트 (스마트폰에서 체크해볼 수 있는 기능)
    st.markdown("---")
    st.subheader("✅ 종가베팅 체크리스트")
    c1 = st.checkbox("당일 거래대금이 충분히 터졌는가?")
    c2 = st.checkbox("고가 대비 -3% 이내 부근에서 마감했는가?")
    c3 = st.checkbox("주요 수급(외국인/기관)이 들어왔는가?")
    
    if c1 and c2 and c3:
        st.success("🎉 종가베팅 조건 충족! 손절가(-2%) 준수하며 진입 검토 가능")
    else:
        st.warning("⚠️ 조건을 모두 충족하지 않았습니다. 신중하게 접근하세요.")

else:
    st.error("주가 데이터를 불러오지 못했습니다.")
