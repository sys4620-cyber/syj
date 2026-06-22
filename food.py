import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 앱 제목
st.title("🍴 맛집 탐색기")
st.write("구글 시트와 연동하여 평점 높은 맛집을 확인하세요!")

# --- 구글 시트 데이터 로드 ---
# 구글 시트 주소를 입력하세요 (1단계에서 복사한 주소)
sheet_url = "https://docs.google.com/spreadsheets/d/15cE-_kb8MqX2khwr0zo8tbuU3hB8KO7UoY88rZCpHP4/edit?usp=sharing"

try:
    # GSheetsConnection을 이용해 연결 생성
    conn = st.connection("gsheets", type=GSheetsConnection)
    # 구글 시트 읽어오기 (ttl=600은 10분 동안 캐싱하여 속도를 높임)
    df = conn.read(spreadsheet=sheet_url, ttl=600)
    
    # 데이터 전처리 (카테고리 오타 방지 및 공백 제거)
    df['카테고리'] = df['카테고리'].astype(str).str.strip()
    df['만족도'] = pd.to_numeric(df['만족도'], errors='coerce')
except Exception as e:
    st.error(f"구글 시트를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 세션 상태 초기화 (선택 값 유지용)
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'selected_food' not in st.session_state:
    st.session_state.selected_food = None

# --- 1단계: 카테고리 선택 (사용자 지정 순서 정렬) ---
st.subheader("1단계: 카테고리 선택")

custom_order = ["한식", "일식", "중식", "양식", "분식", "카페"]
categories = [cat for cat in custom_order if cat in df['카테고리'].unique()]

cols1 = st.columns(len(categories))

for i, category in enumerate(categories):
    if cols1[i].button(category):
        st.session_state.selected_category = category
        st.session_state.selected_food = None

# --- 2단계: 상세 음식 선택 ---
if st.session_state.selected_category:
    st.divider()
    st.subheader(f"2단계: [{st.session_state.selected_category}] 상세 음식 선택")
    
    filtered_foods = sorted(df[df['카테고리'] == st.session_state.selected_category]['음식'].unique())
    cols2 = st.columns(min(len(filtered_foods), 5))
    
    for i, food in enumerate(filtered_foods):
        if cols2[i % 5].button(food):
            st.session_state.selected_food = food

# --- 3단계: 결과 나열 (평점 내림차순) ---
if st.session_state.selected_food:
    st.divider()
    st.subheader(f"3단계: [{st.session_state.selected_food}] 맛집 리스트 (평점순)")
    
    result_df = df[(df['카테고리'] == st.session_state.selected_category) & 
                   (df['음식'] == st.session_state.selected_food)]
    result_df = result_df.sort_values(by='만족도', ascending=False)
    
    for index, row in result_df.iterrows():
        with st.expander(f"⭐ {row['만족도']} - {row['장소']}"):
            st.write(f"**카테고리:** {row['카테고리']}")
            st.write(f"**대표 음식:** {row['음식']}")
            st.write(f"**주소:** {row['주소']}")

# 초기화 버튼
if st.sidebar.button("선택 초기화"):
    st.session_state.selected_category = None
    st.session_state.selected_food = None
    st.rerun()