import streamlit as st
import cv2
import numpy as np
from PIL import Image

# 페이지 기본 설정
st.set_page_config(page_title="MirrorFit - 체형 분석 앱", page_icon="🪞", layout="centered")

# 세션 상태 초기화
if 'page' not in st.session_state:
    st.session_state.page = 'cover'
if 'survey_answers' not in st.session_state:
    st.session_state.survey_answers = {}
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = None

# 커스텀 스타일 적용
st.markdown("""
    <style>
    .stApp { background-color: #FDFDFD; color: #1A1A1A; font-family: sans-serif; }
    h1, h2, h3 { color: #111111; font-weight: 800; }
    .stButton>button {
        background-color: #111111; color: #FFFFFF; border: none;
        border-radius: 8px; padding: 0.8rem 1.6rem; font-weight: 700; width: 100%;
    }
    .stButton>button:hover { background-color: #333333; color: #FFFFFF; }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 표지 페이지 (Cover Page)
# ---------------------------------------------------------
if st.session_state.page == 'cover':
    st.markdown("<div style='height: 100px;'></div>", unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center;'>🪞 MIRRORFIT</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: gray; margin-bottom: 40px;'>나만의 맞춤형 체형 분석 서비스</p>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("분석 시작하기"):
            st.session_state.page = 'survey'
            st.rerun()

# ---------------------------------------------------------
# 2. 설문조사 페이지 (Survey Page)
# ---------------------------------------------------------
elif st.session_state.page == 'survey':
    st.markdown("### 📝 체형 자가 진단 설문")
    
    with st.form("survey_form"):
        q1 = st.radio("01. 목이 짧고 상체 볼륨감이 발달한 편인가요?", ["그렇다", "보통이다", "아니다"])
        q2 = st.radio("02. 어깨 라인이 직선적이거나 골격감이 느껴지나요?", ["그렇다", "보통이다", "아니다"])
        q3 = st.radio("03. 허리선이 높고 하체 곡선이 부드러운 편인가요?", ["그렇다", "보통이다", "아니다"])
        
        submitted = st.form_submit_button("다음 단계로 이동")
        if submitted:
            st.session_state.survey_answers = {"q1": q1, "q2": q2, "q3": q3}
            st.session_state.page = 'upload'
            st.rerun()
            
    if st.button("← 처음으로"):
        st.session_state.page = 'cover'
        st.rerun()

# ---------------------------------------------------------
# 3. 사진 업로드 및 분석 페이지 (Upload Page)
# ---------------------------------------------------------
elif st.session_state.page == 'upload':
    st.markdown("### 📷 전신 사진 업로드")
    image_file = st.file_uploader("사진 파일 선택 (JPG, PNG)", type=['jpg', 'jpeg', 'png'])
    
    if image_file is not None:
        image = Image.open(image_file)
        st.image(image, caption="업로드된 사진", use_container_width=True)
        st.session_state.uploaded_image = image
        
    if st.button("체형 분석하기"):
        if st.session_state.uploaded_image is not None:
            # 이미지 비율 기반 분석 로직 수행
            img_np = np.array(st.session_state.uploaded_image)
            h, w, _ = img_np.shape
            
            gray = cv2.cvtColor(img_np, cv2.COLOR_RGB2GRAY)
            upper_half = gray[:int(h*0.5), :]
            lower_half = gray[int(h*0.5):, :]
            
            upper_width = np.sum(upper_half > 100) / (upper_half.size + 1e-5)
            lower_width = np.sum(lower_half > 100) / (lower_half.size + 1e-5)
            ratio = upper_width / (lower_width + 1e-5)
            
            if ratio > 1.05:
                body_type = "스트레이트 (Straight)"
            elif ratio < 0.95:
                body_type = "웨이브 (Wave)"
            else:
                body_type = "내추럴 (Natural)"
                
            st.session_state.analysis_result = body_type
            st.session_state.page = 'result'
            st.rerun()
        else:
            st.warning("사진을 먼저 업로드해 주세요!")
            
    if st.button("← 설문으로"):
        st.session_state.page = 'survey'
        st.rerun()

# ---------------------------------------------------------
# 4. 결과 페이지 (Result Page)
# ---------------------------------------------------------
elif st.session_state.page == 'result':
    body_type = st.session_state.analysis_result
    st.markdown("### ✨ 체형 분석 결과")
    st.success(f"회원님의 분석된 체형은 **{body_type}**입니다!")
    
    tab1, tab2 = st.tabs(["👗 맞춤 코디 추천", "💪 체형 운동"])
    
    with tab1:
        st.markdown("##### 맞춤 코디 가이드")
        if "스트레이트" in body_type:
            st.write("- V넥, U넥 라인의 심플하고 깔끔한 상의 추천")
            st.write("- 일자 핏의 모던한 실루엣 연출")
        elif "웨이브" in body_type:
            st.write("- 허리선을 높여주는 하이웨이스트 및 플레어 스커트 추천")
            st.write("- 프릴이나 리본 디테일로 볼륨감 보완")
        else:
            st.write("- 오버사이즈 및 루즈핏 아이템 추천")
            st.write("- 자연스러운 드레이프 소재 활용")
            
    with tab2:
        st.markdown("##### 체형별 밸런스 운동")
        st.write("- 체형의 균형을 잡아주는 맞춤형 스트레칭 루틴을 진행해 보세요.")
        st.checkbox("오늘의 스트레칭 완료하기")
        
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)
    if st.button("처음부터 다시 시작하기"):
        st.session_state.page = 'cover'
        st.session_state.uploaded_image = None
        st.session_state.analysis_result = None
        st.rerun()