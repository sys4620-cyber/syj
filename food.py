import streamlit as st
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# 앱 제목
st.title("🍴 맛집 검색")
st.write("구글 시트와 연동!" \
"https://docs.google.com/spreadsheets/d/15cE-_kb8MqX2khwr0zo8tbuU3hB8KO7UoY88rZCpHP4/edit?usp=sharing")

# --- 구글 시트 데이터 로드 ---
sheet_url = "https://docs.google.com/spreadsheets/d/15cE-_kb8MqX2khwr0zo8tbuU3hB8KO7UoY88rZCpHP4/edit?usp=sharing"

try:
    # GSheetsConnection을 이용해 연결 생성
    conn = st.connection("gsheets", type=GSheetsConnection)
    df = conn.read(spreadsheet=sheet_url, ttl=600)
    
    # 데이터 전처리 (카테고리 오타 방지 및 공백 제거)
    df['카테고리'] = df['카테고리'].astype(str).str.strip()
    df['만족도'] = pd.to_numeric(df['만족도'], errors='coerce')
    
    # [배달/외식 데이터 전처리] 대소문자 구분 없이 대문자 O, X로 통일 및 결측치 예외 처리
    df['배달'] = df['배달'].astype(str).str.strip().str.upper().fillna('X')
    df['외식'] = df['외식'].astype(str).str.strip().str.upper().fillna('X')
except Exception as e:
    st.error(f"구글 시트를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

# 세션 상태 초기화 (식사 방식 선택 변수 추가)
if 'selected_type' not in st.session_state:
    st.session_state.selected_type = None
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'selected_food' not in st.session_state:
    st.session_state.selected_food = None

# --- 1단계: 식사 방식 선택 ---
st.subheader("1단계: 식사 방식 선택")
types = ["배달", "외식", "미정"]
cols1 = st.columns(len(types))

for i, t in enumerate(types):
    if cols1[i].button(t):
        st.session_state.selected_type = t
        st.session_state.selected_category = None  # 상위 조건 변경 시 하위 단계 초기화
        st.session_state.selected_food = None

# [1차 필터링 논리 적용]
# 선택 조건에 맞는 데이터만 걸러내어 다음 단계의 카테고리/음식 버튼에 반영합니다.
if st.session_state.selected_type == "배달":
    filtered_df = df[df['배달'] == 'O']
elif st.session_state.selected_type == "외식":
    filtered_df = df[df['외식'] == 'O']
else:
    # '미정'이거나 아무것도 선택되지 않았을 때는 구글 시트 전체 데이터를 기준 삼음
    filtered_df = df.copy()


# --- 2단계: 카테고리 선택 ---
if st.session_state.selected_type:
    st.divider()
    st.subheader(f"2단계: [{st.session_state.selected_type}] 카테고리 선택")
    
    custom_order = ["한식", "일식", "중식", "양식", "분식" "아시안", "카페"]
    # 1차 필터링된 데이터 내에 존재하는 카테고리만 지정된 순서로 나열
    categories = [cat for cat in custom_order if cat in filtered_df['카테고리'].unique()]
    
    if categories:
        cols2 = st.columns(len(categories))
        for i, category in enumerate(categories):
            if cols2[i].button(category):
                st.session_state.selected_category = category
                st.session_state.selected_food = None  # 카테고리 변경 시 음식 초기화
    else:
        st.info("해당 조건에 맞는 카테고리가 없습니다.")


# --- 3단계: 상세 음식 선택 ---
if st.session_state.selected_category:
    st.divider()
    st.subheader(f"3단계: [{st.session_state.selected_category}] 상세 음식 선택")
    
    # 1차 필터링 및 카테고리가 일치하는 음식만 추출
    food_condition = filtered_df['카테고리'] == st.session_state.selected_category
    filtered_foods = sorted(filtered_df[food_condition]['음식'].unique())
    
    if filtered_foods:
        cols3 = st.columns(min(len(filtered_foods), 5))  # 한 줄에 최대 5개 버튼 배치
        for i, food in enumerate(filtered_foods):
            if cols3[i % 5].button(food):
                st.session_state.selected_food = food
    else:
        st.info("해당 조건에 맞는 상세 음식이 없습니다.")


# --- 4단계: 결과 나열 (평점 내림차순) ---
if st.session_state.selected_food:
    st.divider()
    st.subheader(f"4단계: [{st.session_state.selected_food}] 맛집 리스트 (평점순)")
    
    # 1, 2, 3단계 조건을 모두 만족하는 최종 데이터 필터링
    final_df = filtered_df[
        (filtered_df['카테고리'] == st.session_state.selected_category) & 
        (filtered_df['음식'] == st.session_state.selected_food)
    ]
    final_df = final_df.sort_values(by='만족도', ascending=False)
    
    # 결과 출력
    if not final_df.empty:
        for index, row in final_df.iterrows():
            with st.expander(f"⭐ {row['만족도']} - {row['장소']}"):
                st.write(f"**카테고리:** {row['카테고리']}")
                st.write(f"**대표 음식:** {row['음식']}")
                # 구글 시트에 주소 열이 없을 경우를 대비한 예외 처리 포함 출력
                address = row['주소'] if '주소' in final_df.columns and pd.notna(row['주소']) else "등록된 주소 없음"
                st.write(f"**주소:** {address}")
    else:
        st.info("조건에 일치하는 맛집이 없습니다.")

# 선택 초기화 버튼 (사이드바)
if st.sidebar.button("선택 초기화"):
    st.session_state.selected_type = None
    st.session_state.selected_category = None
    st.session_state.selected_food = None
    st.rerun()