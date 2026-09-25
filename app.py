import datetime
import FinanceDataReader as fdr
import pandas as pd
import plotly.graph_objects as st_plotly
import plotly.graph_objects as go
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="국내 주식 시장 종합 분석 차트",
    page_icon="📈",
    layout="wide",
)


# 한국 거래소(KRX) 전체 종목 리스트 불러오기 (캐싱 처리로 속도 향상)
@st.cache_data(ttl=86400)
def load_stock_list():
    df_krx = fdr.StockListing("KRX")
    # 'Code', 'Name', 'Market' 등 필요 정보 정제
    df_krx["Display_Name"] = (
        "[" + df_krx["Market"] + "] " + df_krx["Name"] + " (" + df_krx["Code"] + ")"
    )
    return df_krx


# 주가 데이터 가져오기
def load_stock_data(symbol, start_date, end_date):
    df = fdr.DataReader(symbol, start_date, end_date)
    return df


# --- 메인 실행 로직 ---
st.title("📈 국내 전체 주식 시장 분석 앱")

# 데이터 로딩
try:
    stock_df = load_stock_list()
except Exception as e:
    st.error(f"종목 리스트를 불러오는데 실패했습니다: {e}")
    st.stop()

# [사이드바] 검색 및 설정 영역
st.sidebar.header("🔍 검색 및 분석 설정")

# 1. 시장 선택 필터
markets = ["ALL"] + list(stock_df["Market"].unique())
selected_market = st.sidebar.selectbox("시장(Market) 선택", markets)

if selected_market != "ALL":
    filtered_df = stock_df[stock_df["Market"] == selected_market]
else:
    filtered_df = stock_df

# 2. 종목 선택 (전체 종목 검색 가능)
stock_options = filtered_df["Display_Name"].tolist()
selected_stock_display = st.sidebar.selectbox(
    "종목 선택 (종목명/코드 검색)", stock_options, index=0
)

# 선택된 종목의 코드 및 이름 추출
selected_row = filtered_df[
    filtered_df["Display_Name"] == selected_stock_display
].iloc[0]
target_code = selected_row["Code"]
target_name = selected_row["Name"]
target_market = selected_row["Market"]

# 3. 날짜 범위 선택
today = datetime.date.today()
default_start = today - datetime.timedelta(days=365)  # 기본 1년

col_d1, col_d2 = st.sidebar.columns(2)
start_date = col_d1.date_input("시작일", default_start)
end_date = col_d2.date_input("종료일", today)

# 4. 이동평균선 설정
st.sidebar.subheader("📊 이동평균선(MA)")
show_ma = st.sidebar.checkbox("이동평균선 표시", value=True)
ma_days = st.sidebar.multiselect(
    "이평선 기간 선택", [5, 20, 60, 120, 200], default=[5, 20, 60]
)

# --- 메인 화면 지표 및 차트 ---
df_price = load_stock_data(target_code, start_date, end_date)

if df_price.empty:
    st.warning("해당 기간의 주가 데이터가 없습니다.")
else:
    # 기본 종목 정보 상단 표시
    st.subheader(f"{target_name} ({target_code}) - {target_market}")

    # 주요 시세 요약 (최신 데이터 기준)
    latest = df_price.iloc[-1]
    prev = df_price.iloc[-2] if len(df_price) > 1 else latest

    price_diff = latest["Close"] - prev["Close"]
    rate_of_change = (price_diff / prev["Close"]) * 100

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("현재가 (종가)", f"{int(latest['Close']):,}원", f"{price_diff:+,}원 ({rate_of_change:+.2f}%)")
    col2.metric("시가", f"{int(latest['Open']):,}원")
    col3.metric("고가", f"{int(latest['High']):,}원")
    col4.metric("거래량", f"{int(latest['Volume']):,}주")

    st.markdown("---")

    # 이동평균선 계산
    if show_ma:
        for day in ma_days:
            df_price[f"MA_{day}"] = df_price["Close"].rolling(window=day).mean()

    # Plotly 캔들차트 + 거래량 차트 그리법 (2단 레이아웃)
    fig = go.Figure()

    # 1. 캔들차트 추가
    fig.add_trace(
        go.Candlestick(
            x=df_price.index,
            open=df_price["Open"],
            high=df_price["High"],
            low=df_price["Low"],
            close=df_price["Close"],
            name="주가",
            increasing_line_color="#e12343",  # 상승 빨간색
            decreasing_line_color="#1d61d1",  # 하락 파란색
        )
    )

    # 2. 이동평균선 추가
    if show_ma:
        colors = ["#ff9900", "#109618", "#990099", "#0099c6", "#dd44dd"]
        for idx, day in enumerate(ma_days):
            if f"MA_{day}" in df_price.columns:
                fig.add_trace(
                    go.Scatter(
                        x=df_price.index,
                        y=df_price[f"MA_{day}"],
                        mode="lines",
                        name=f"{day}일선",
                        line=dict(width=1.5, color=colors[idx % len(colors)]),
                    )
                )

    # 차트 레이아웃 스타일 설정
    fig.update_layout(
        title=f"{target_name} 일봉 차트",
        yaxis_title="주가 (원)",
        xaxis_rangeslider_visible=False,  # 하단 줌 슬라이더 끄기
        height=550,
        margin=dict(l=20, r=20, t=40, b=20),
    )

    st.plotly_chart(fig, use_container_width=True)

    # 데이터 상세 보기 탭
    st.subheader("📋 상세 데이터 확인")
    tab1, tab2 = st.tabs(["일별 주가 시세 데이터", "기업 정보 및 지표"])

    with tab1:
        st.dataframe(
            df_price.sort_index(ascending=False), use_container_width=True
        )

    with tab2:
        # 선택된 종목의 KRX 정보 출력
        info_df = pd.DataFrame(selected_row).T
        st.dataframe(info_df, use_container_width=True)

