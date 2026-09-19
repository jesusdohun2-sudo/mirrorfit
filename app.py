import streamlit as st
import cv2
import numpy as np
from PIL import Image
import io
import sqlite3
import hashlib

# MediaPipe 안전 로드
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    HAS_MP = True
except Exception:
    HAS_MP = False

# 페이지 기본 설정
st.set_page_config(page_title="MirrorFit - Pro & Admin Edition", page_icon="🪞", layout="centered")

# ---------------------------------------------------------
# 0. 유틸리티 및 데이터베이스 초기화
# ---------------------------------------------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    conn = sqlite3.connect('mirrorfit.db', check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS market (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            price TEXT,
            status TEXT,
            content TEXT,
            body_type TEXT,
            image BLOB
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS snaps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            body_type TEXT,
            image BLOB
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            body_type TEXT,
            image BLOB
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section TEXT,
            title TEXT,
            content TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    return sqlite3.connect('mirrorfit.db', check_same_thread=False)

def preprocess_image(image, max_size=800):
    image.thumbnail((max_size, max_size))
    return image

# 관리자 계정 이메일 정의
ADMIN_EMAIL = "admin@mirrorfit.com"

# 쿼리 파라미터 및 세션 상태 초기화
query_params = st.query_params
if "page" in query_params:
    st.session_state.page = query_params["page"]

if 'page' not in st.session_state:
    st.session_state.page = 'cover'
if 'survey_answers' not in st.session_state:
    st.session_state.survey_answers = {}
if 'uploaded_image' not in st.session_state:
    st.session_state.uploaded_image = None
if 'annotated_image' not in st.session_state:
    st.session_state.annotated_image = None
if 'analysis_result' not in st.session_state:
    st.session_state.analysis_result = "스트레이트 (Straight)"
if 'analysis_ratio' not in st.session_state:
    st.session_state.analysis_ratio = 1.0
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'current_user' not in st.session_state:
    st.session_state.current_user = ""
if 'is_admin' not in st.session_state:
    st.session_state.is_admin = False
if 'show_login_modal' not in st.session_state:
    st.session_state.show_login_modal = False
if 'liked_market_items' not in st.session_state:
    st.session_state.liked_market_items = []

# 🖤 오리지널 미니멀 하이엔드 스타일 CSS
st.markdown("""
    <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    
    .stApp {
        background-color: #FAFAFB;
        color: #1A1A1A;
        font-family: 'Pretendard', sans-serif;
    }
    
    h1, h2, h3, h4 {
        color: #111111;
        font-weight: 800;
        letter-spacing: -0.8px;
    }
    
    .stButton>button {
        background-color: #111111;
        color: #FFFFFF;
        border: none;
        border-radius: 8px;
        padding: 0.8rem 1.6rem;
        font-weight: 700;
        font-size: 15px;
        box-shadow: 0 4px 14px rgba(0,0,0,0.1);
        transition: all 0.2s ease-in-out;
    }
    .stButton>button:hover {
        background-color: #333333;
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        border-bottom: 1px solid #EAEAEA;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 8px;
        padding: 10px 20px;
        font-weight: 700;
        color: #888888;
        background-color: #F4F4F4;
        border: none;
    }
    .stTabs [aria-selected="true"] {
        color: #FFFFFF !important;
        background-color: #111111 !important;
    }
    
    .card-box {
        background-color: #FFFFFF;
        border: 1px solid #EAEAEA;
        border-radius: 12px;
        padding: 16px;
        margin-bottom: 15px;
        box-shadow: 0 4px 12px rgba(0,0,0,0.03);
    }
    .notice-box {
        background-color: #FFF8E1;
        border: 1px solid #FFE082;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# 1. 표지 페이지 (Cover Page - 우측 상단 로그인 버튼 추가)
# ---------------------------------------------------------
if st.session_state.page == 'cover':
    # 상단 우측 로그인 버튼을 위한 컬럼 배치
    _, top_right_col = st.columns([5, 1])
    with top_right_col:
        if st.button("로그인", key="cover_login_btn"):
            st.session_state.page = 'login'
            st.rerun()

    st.markdown("<div style='height: 80px;'></div>", unsafe_allow_html=True)
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="font-size: 46px; margin-bottom: 6px; letter-spacing: -1.5px;">MIRRORFIT</h1>
            <p style="font-size: 13px; color: #666666; margin-bottom: 50px; font-weight: 600; text-transform: uppercase; letter-spacing: 3px;">Skeleton Fit & Style Archive</p>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("분석하러 가기", use_container_width=True):
            st.session_state.page = 'survey'
            st.rerun()

# ---------------------------------------------------------
# 1-1. 직접 로그인 페이지 (Login Page for Returning Users)
# ---------------------------------------------------------
elif st.session_state.page == 'login':
    st.markdown("### 🔐 기존 회원 로그인")
    st.markdown("<p style='color: #666666; font-size: 14px; margin-bottom: 25px;'>이미 체형 분석을 완료하셨다면 로그인하여 맞춤 라운지로 바로 입장하세요.</p>", unsafe_allow_html=True)
    
    with st.form("direct_login_form"):
        uid = st.text_input("아이디 (이메일)")
        upw = st.text_input("비밀번호", type="password")
        
        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        if st.form_submit_button("로그인하기", use_container_width=True):
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("SELECT password FROM users WHERE username = ?", (uid,))
            row = cur.fetchone()
            conn.close()
            
            if row and row[0] == hash_password(upw):
                st.session_state.logged_in = True
                st.session_state.current_user = uid
                if uid == ADMIN_EMAIL:
                    st.session_state.is_admin = True
                    st.success("관리자(Admin) 계정으로 로그인되었습니다!")
                else:
                    st.session_state.is_admin = False
                    st.success("로그인 성공!")
                
                st.session_state.page = 'community'
                st.rerun()
            else:
                st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
                
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("← 처음 표지로 돌아가기"):
        st.session_state.page = 'cover'
        st.rerun()

# ---------------------------------------------------------
# 2. 설문조사 페이지 (Survey Page)
# ---------------------------------------------------------
elif st.session_state.page == 'survey':
    st.markdown("### 📝 체형 자가 진단 설문")
    st.markdown("<p style='color: #666666; font-size: 14px; margin-bottom: 25px;'>정확한 체형 분석을 위해 5가지 질문에 답해 주세요.</p>", unsafe_allow_html=True)
    
    with st.form("survey_form"):
        q1 = st.radio("01. 목의 길이와 상체 실루엣", ["목이 짧고 굵은 편이며 승모근과 상체 볼륨이 발달 (스트레이트)", "보통이다", "목이 가늘고 긴 편 (웨이브)"], key="q1")
        q2 = st.radio("02. 어깨와 상체 프레임", ["어깨 라인이 직선적이거나 탄탄한 골격감", "보통이다", "어깨가 좁고 곡선적임"], key="q2")
        q3 = st.radio("03. 허리선과 하체 볼륨", ["허리선이 비교적 낮고 하체 곡선이 곧음", "보통이다", "허리선이 높고 하체 곡선이 부드러움 (웨이브)"], key="q3")
        q4 = st.radio("04. 손목 및 관절의 뼈마디 느낌", ["손목 관절이나 무릎 뼈마디가 굵고 프레임감이 도드라짐 (내추럴)", "보통이다", "관절이 가늘고 매끄러움"], key="q4")
        q5 = st.radio("05. 체형 전체의 입체감", ["입체적 볼륨 중심", "골격 프레임 중심", "균형 잡힌 보통"], key="q5")
        
        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
        if st.form_submit_button("다음 단계 (사진 첨부)", use_container_width=True):
            st.session_state.survey_answers = {"q1": q1, "q2": q2, "q3": q3, "q4": q4, "q5": q5}
            st.session_state.page = 'upload'
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("← 처음으로", key="back_cover"):
        st.session_state.page = 'cover'
        st.rerun()

# ---------------------------------------------------------
# 3. 사진 첨부 페이지 (Upload Page)
# ---------------------------------------------------------
elif st.session_state.page == 'upload':
    st.markdown("### 📷 전신 사진 첨부")
    st.markdown("<div class='card-box'>정면 전신이 잘 나오는 사진을 업로드하거나 촬영해 주세요. MediaPipe가 어깨와 골격 포인트를 자동으로 감지합니다.</div>", unsafe_allow_html=True)
    
    upload_option = st.radio("입력 방식 선택", ["사진 파일 업로드", "카메라로 직접 촬영"], horizontal=True)
    image_file = st.file_uploader("이미지 파일 선택", type=['jpg', 'jpeg', 'png']) if upload_option == "사진 파일 업로드" else st.camera_input("카메라 촬영")
        
    if image_file is not None:
        raw_image = Image.open(image_file)
        processed_image = preprocess_image(raw_image)
        st.image(processed_image, caption="첨부된 전신 사진", use_container_width=True)
        st.session_state.uploaded_image = processed_image
        
    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)
    if st.button("체형 분석 시작하기", use_container_width=True):
        if st.session_state.uploaded_image is not None:
            with st.spinner("AI가 신체 관절 뼈대를 정밀 분석 중입니다..."):
                img_np = np.array(st.session_state.uploaded_image)
                annotated_img = img_np.copy()
                survey = st.session_state.survey_answers
                ratio = 1.0
                
                if HAS_MP:
                    try:
                        with mp_pose.Pose(static_image_mode=True, model_complexity=1, min_detection_confidence=0.25) as pose:
                            results = pose.process(img_np)
                            if results.pose_landmarks:
                                landmarks = results.pose_landmarks.landmark
                                h, w, _ = annotated_img.shape
                                ls, rs = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER.value], landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
                                lh, rh = landmarks[mp_pose.PoseLandmark.LEFT_HIP.value], landmarks[mp_pose.PoseLandmark.RIGHT_HIP.value]
                                
                                ratio = abs(ls.x - rs.x) / (abs(lh.x - rh.x) + 1e-5)
                                for conn in mp_pose.POSE_CONNECTIONS:
                                    p1, p2 = landmarks[conn[0]], landmarks[conn[1]]
                                    if p1.visibility > 0.25 and p2.visibility > 0.25:
                                        cv2.line(annotated_img, (int(p1.x*w), int(p1.y*h)), (int(p2.x*w), int(p2.y*h)), (255, 255, 0), 4)
                                for lm in landmarks:
                                    if lm.visibility > 0.25:
                                        cv2.circle(annotated_img, (int(lm.x*w), int(lm.y*h)), 6, (0, 255, 0), -1)
                    except Exception:
                        pass
                
                st.session_state.analysis_ratio = round(ratio, 2)
                st.session_state.annotated_image = Image.fromarray(annotated_img)
                
                score = 0
                if "스트레이트" in survey.get("q1", ""): score += 2
                if "웨이브" in survey.get("q3", ""): score -= 2
                if "내추럴" in survey.get("q4", ""): score += 1
                if ratio > 1.05: score += 1
                elif ratio < 0.95: score -= 1
                
                body_type = "스트레이트 (Straight)" if score >= 1 else ("웨이브 (Wave)" if score <= -1 else "내추럴 (Natural)")
                st.session_state.analysis_result = body_type
                st.session_state.page = 'result'
                st.rerun()
        else:
            st.warning("⚠️ 사진을 먼저 첨부해 주세요!")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("← 설문조사로"):
        st.session_state.page = 'survey'
        st.rerun()

# ---------------------------------------------------------
# 4. 분석 결과 페이지 (Result Page)
# ---------------------------------------------------------
elif st.session_state.page == 'result':
    body_type = st.session_state.analysis_result
    st.markdown("### ✨ AI 골격 체형 분석 리포트")
    st.markdown(f"""
        <div style="background-color: #111111; color: #FFFFFF; padding: 24px; border-radius: 12px; margin-bottom: 25px; text-align: center;">
            <p style="font-size: 12px; color: #AAAAAA; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1.5px;">YOUR SKELETON TYPE</p>
            <h2 style="color: #FFFFFF; margin: 0; font-size: 28px;">{body_type}</h2>
        </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1.2])
    with col1:
        st.markdown("##### 🦴 스켈레톤 관절 시각화")
        disp_img = st.session_state.get('annotated_image') or st.session_state.uploaded_image
        if disp_img: st.image(disp_img, use_container_width=True)
    with col2:
        st.markdown("##### 📊 분석 요약")
        st.markdown(f"- **어깨/골반 비율 지표:** `{st.session_state.analysis_ratio}`\n- **특징 요약:** {body_type.split(' ')[0]} 타입은 골격의 입체감과 비율이 조화로운 체형입니다.")
        st.info("💡 사진 위 노란색 뼈대 라인과 초록색 관절 포인트를 확인하세요.")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    
    if not st.session_state.logged_in:
        st.markdown(f"<p style='font-size: 13px; color: #666;'>💡 관리자 계정 테스트용 안내: 아이디를 <b>{ADMIN_EMAIL}</b>로 가입 후 로그인하시면 관리자 대시보드가 활성화됩니다.</p>", unsafe_allow_html=True)
        if st.button("맞춤 코디 및 커뮤니티 공간 입장하기 (로그인 필요)", use_container_width=True):
            st.session_state.show_login_modal = True
            st.rerun()
            
        if st.session_state.show_login_modal:
            st.markdown("---")
            st.markdown("### 🔐 MirrorFit 계정 인증")
            tab_l, tab_s = st.tabs(["로그인", "회원가입"])
            
            with tab_l:
                with st.form("login_f"):
                    uid = st.text_input("아이디 (이메일)")
                    upw = st.text_input("비밀번호", type="password")
                    if st.form_submit_button("로그인"):
                        conn = get_db_connection()
                        cur = conn.cursor()
                        cur.execute("SELECT password FROM users WHERE username = ?", (uid,))
                        row = cur.fetchone()
                        conn.close()
                        
                        if row and row[0] == hash_password(upw):
                            st.session_state.logged_in = True
                            st.session_state.current_user = uid
                            if uid == ADMIN_EMAIL:
                                st.session_state.is_admin = True
                                st.success("관리자(Admin) 계정으로 로그인되었습니다!")
                            else:
                                st.session_state.is_admin = False
                                st.success("로그인 성공!")
                            
                            st.session_state.show_login_modal = False
                            st.session_state.page = 'community'
                            st.rerun()
                        else:
                            st.error("아이디 또는 비밀번호가 올바르지 않습니다.")
                            
            with tab_s:
                with st.form("signup_f"):
                    suid = st.text_input("사용할 아이디 (이메일)", key="su")
                    supw = st.text_input("사용할 비밀번호", type="password", key="sp")
                    if st.form_submit_button("회원가입 완료"):
                        if suid and supw:
                            try:
                                conn = get_db_connection()
                                conn.execute("INSERT INTO users (username, password) VALUES (?, ?)", (suid, hash_password(supw)))
                                conn.commit()
                                conn.close()
                                st.success("회원가입 완료! 로그인해 주세요.")
                            except sqlite3.IntegrityError:
                                st.error("이미 존재하는 아이디입니다.")
    else:
        role_label = "관리자 (Admin)" if st.session_state.is_admin else "일반 회원"
        st.success(f"현재 **{st.session_state.current_user}** ({role_label})님으로 로그인되어 있습니다.")
        if st.button("공간 입장하기", use_container_width=True):
            st.session_state.page = 'community'
            st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    if st.button("처음부터 다시 진단하기"):
        st.session_state.page = 'cover'
        st.session_state.survey_answers = {}
        st.session_state.uploaded_image = None
        st.session_state.annotated_image = None
        st.session_state.show_login_modal = False
        st.rerun()

# ---------------------------------------------------------
# 5. 커뮤니티 및 관리자 대시보드 (Community & Admin Page)
# ---------------------------------------------------------
elif st.session_state.page == 'community':
    if not st.session_state.logged_in:
        st.warning("로그인이 필요한 서비스입니다.")
        st.session_state.page = 'result'
        st.rerun()
        
    body_type = st.session_state.analysis_result
    c1, c2 = st.columns([4, 1])
    with c1: 
        if st.session_state.is_admin:
            st.markdown("### 🛡️ MirrorFit 관리자 대시보드 (Admin Panel)")
        else:
            st.markdown(f"### 🖤 [{body_type}] 맞춤 라운지")
    with c2:
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.session_state.current_user = ""
            st.session_state.is_admin = False
            st.session_state.page = 'cover'
            st.rerun()
            
    # 관리자 계정일 경우 관리자 전용 대시보드 탭 제공
    if st.session_state.is_admin:
        adm_tab1, adm_tab2, adm_tab3, adm_tab4 = st.tabs(["👥 가입 회원 관리", "📢 공지사항 등록", "🗑️ 콘텐츠 관리", "📊 플랫폼 통계"])
        
        with adm_tab1:
            st.markdown("##### 📋 가입 회원 목록 및 계정 관리")
            conn = get_db_connection()
            users = conn.cursor().execute("SELECT username FROM users").fetchall()
            conn.close()
            
            if users:
                st.write(f"총 가입 회원 수: **{len(users)}명**")
                for u in users:
                    u_name = u[0]
                    is_admin_user = (u_name == ADMIN_EMAIL)
                    
                    col_u1, col_u2 = st.columns([3, 1])
                    with col_u1:
                        st.markdown(f"👤 **{u_name}** {'⭐ [관리자]' if is_admin_user else ''}")
                    with col_u2:
                        if not is_admin_user:
                            if st.button("계정 삭제", key=f"del_user_{u_name}"):
                                conn = get_db_connection()
                                conn.execute("DELETE FROM users WHERE username = ?", (u_name,))
                                conn.commit()
                                conn.close()
                                st.success(f"{u_name} 계정이 삭제되었습니다.")
                                st.rerun()
            else:
                st.info("등록된 회원이 없습니다.")
                
        with adm_tab2:
            st.markdown("##### 📢 섹션별 공지사항 작성")
            with st.form("admin_notice_form"):
                n_section = st.selectbox("공지 대상 섹션", ["코디", "운동", "중고"])
                n_title = st.text_input("공지사항 제목")
                n_content = st.text_area("공지 내용")
                
                if st.form_submit_button("공지사항 등록"):
                    if n_title and n_content:
                        conn = get_db_connection()
                        conn.execute("INSERT INTO announcements (section, title, content) VALUES (?, ?, ?)", (n_section, n_title, n_content))
                        conn.commit()
                        conn.close()
                        st.success("공지사항이 성공적으로 등록되었습니다!")
                        st.rerun()
                    else:
                        st.warning("제목과 내용을 모두 입력해 주세요.")
                        
            st.markdown("---")
            st.markdown("##### 🗑️ 등록된 공지사항 목록")
            conn = get_db_connection()
            notices = conn.cursor().execute("SELECT id, section, title, content FROM announcements ORDER BY id DESC").fetchall()
            conn.close()
            
            if notices:
                for n in notices:
                    with st.expander(f"[{n[1]}] {n[2]}"):
                        st.write(n[3])
                        if st.button("공지 삭제", key=f"del_notice_{n[0]}"):
                            conn = get_db_connection()
                            conn.execute("DELETE FROM announcements WHERE id = ?", (n[0],))
                            conn.commit()
                            conn.close()
                            st.success("공지사항이 삭제되었습니다.")
                            st.rerun()
            else:
                st.info("등록된 공지사항이 없습니다.")

        with adm_tab3:
            st.markdown("##### 🗑️ 전체 콘텐츠 통합 관리 (코디·운동·중고)")
            sub_t1, sub_t2, sub_t3 = st.tabs(["코디 스냅 관리", "운동 루틴 관리", "중고 마켓 관리"])
            
            with sub_t1:
                conn = get_db_connection()
                adm_snaps = conn.cursor().execute("SELECT id, title, content, body_type, image FROM snaps ORDER BY id DESC").fetchall()
                conn.close()
                if adm_snaps:
                    for s in adm_snaps:
                        with st.expander(f"[{s[3]}] {s[1]}"):
                            st.write(s[2])
                            if s[4]: st.image(Image.open(io.BytesIO(s[4])), width=200)
                            if st.button("스냅 삭제", key=f"adm_del_snap_{s[0]}"):
                                conn = get_db_connection()
                                conn.execute("DELETE FROM snaps WHERE id = ?", (s[0],))
                                conn.commit()
                                conn.close()
                                st.success("스냅이 삭제되었습니다.")
                                st.rerun()
                else:
                    st.info("등록된 코디 스냅이 없습니다.")
                    
            with sub_t2:
                conn = get_db_connection()
                adm_workouts = conn.cursor().execute("SELECT id, title, content, body_type, image FROM workouts ORDER BY id DESC").fetchall()
                conn.close()
                if adm_workouts:
                    for w in adm_workouts:
                        with st.expander(f"[{w[3]}] {w[1]}"):
                            st.write(w[2])
                            if w[4]: st.image(Image.open(io.BytesIO(w[4])), width=200)
                            if st.button("운동 삭제", key=f"adm_del_workout_{w[0]}"):
                                conn = get_db_connection()
                                conn.execute("DELETE FROM workouts WHERE id = ?", (w[0],))
                                conn.commit()
                                conn.close()
                                st.success("운동 루틴이 삭제되었습니다.")
                                st.rerun()
                else:
                    st.info("등록된 운동 루틴이 없습니다.")
                    
            with sub_t3:
                conn = get_db_connection()
                adm_markets = conn.cursor().execute("SELECT id, title, price, status, content, body_type, image FROM market ORDER BY id DESC").fetchall()
                conn.close()
                if adm_markets:
                    for m in adm_markets:
                        with st.expander(f"[{m[5]}] {m[1]} ({m[2]} - {m[3]})"):
                            st.write(m[4])
                            if m[6]: st.image(Image.open(io.BytesIO(m[6])), width=200)
                            if st.button("상품 삭제", key=f"adm_del_market_{m[0]}"):
                                conn = get_db_connection()
                                conn.execute("DELETE FROM market WHERE id = ?", (m[0],))
                                conn.commit()
                                conn.close()
                                st.success("마켓 상품이 삭제되었습니다.")
                                st.rerun()
                else:
                    st.info("등록된 중고 마켓 상품이 없습니다.")

        with adm_tab4:
            st.markdown("##### 📈 플랫폼 운영 통계")
            conn = get_db_connection()
            m_count = conn.cursor().execute("SELECT COUNT(*) FROM market").fetchone()[0]
            s_count = conn.cursor().execute("SELECT COUNT(*) FROM snaps").fetchone()[0]
            w_count = conn.cursor().execute("SELECT COUNT(*) FROM workouts").fetchone()[0]
            conn.close()
            
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                st.markdown(f"""
                    <div class="card-box" style="text-align: center;">
                        <h4 style="margin: 0; color: #111;">마켓 매물</h4>
                        <p style="font-size: 20px; font-weight: bold; margin: 5px 0 0 0;">{m_count}개</p>
                    </div>
                """, unsafe_allow_html=True)
            with col_b:
                st.markdown(f"""
                    <div class="card-box" style="text-align: center;">
                        <h4 style="margin: 0; color: #111;">코디 스냅</h4>
                        <p style="font-size: 20px; font-weight: bold; margin: 5px 0 0 0;">{s_count}개</p>
                    </div>
                """, unsafe_allow_html=True)
            with col_c:
                st.markdown(f"""
                    <div class="card-box" style="text-align: center;">
                        <h4 style="margin: 0; color: #111;">운동 루틴</h4>
                        <p style="font-size: 20px; font-weight: bold; margin: 5px 0 0 0;">{w_count}개</p>
                    </div>
                """, unsafe_allow_html=True)
    else:
        # 일반 회원용 탭 구성 (코디, 운동, 중고)
        tab1, tab2, tab3 = st.tabs(["👗 맞춤 코디 추천", "💪 체형 운동 공간", "🛒 중고 의류 마켓"])
        
        # --- 탭 1: 코디 섹션 ---
        with tab1:
            conn = get_db_connection()
            coord_notices = conn.cursor().execute("SELECT title, content FROM announcements WHERE section = '코디' ORDER BY id DESC").fetchall()
            conn.close()
            
            if coord_notices:
                for tn in coord_notices:
                    st.markdown(f"""
                        <div class="notice-box">
                            <h4 style="margin: 0 0 4px 0; font-size: 15px; color: #B71C1C;">📢 [공지] {tn[0]}</h4>
                            <p style="margin: 0; font-size: 13px; color: #333;">{tn[1]}</p>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("##### 📸 OOTD 스타일 스냅 공유")
            with st.form("snap_f"):
                st_title = st.text_input("스타일 제목 입력")
                st_content = st.text_area("코디 설명 및 브랜드 정보")
                st_img = st.file_uploader("스냅 사진 첨부", type=['jpg', 'jpeg', 'png'])
                if st.form_submit_button("스냅 업로드") and st_title:
                    img_b = st_img.read() if st_img else None
                    conn = get_db_connection()
                    conn.execute("INSERT INTO snaps (title, content, body_type, image) VALUES (?, ?, ?, ?)", (st_title, st_content, body_type, img_b))
                    conn.commit()
                    conn.close()
                    st.success("스냅이 등록되었습니다!")
                    st.rerun()
                    
            conn = get_db_connection()
            snaps = conn.cursor().execute("SELECT id, title, content, body_type, image FROM snaps ORDER BY id DESC").fetchall()
            conn.close()
            
            if snaps:
                cols = st.columns(2)
                for idx, s in enumerate(snaps):
                    with cols[idx % 2]:
                        st.markdown(f"""
                            <div class="card-box">
                                <span style="font-size: 11px; background-color: #111111; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600;">{s[3]}</span>
                                <h4 style="margin: 8px 0 4px 0; font-size: 16px;">{s[1]}</h4>
                                <p style="font-size: 13px; color: #666; margin-bottom: 8px;">{s[2]}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if s[4]: st.image(Image.open(io.BytesIO(s[4])), use_container_width=True)
                        
                        if st.session_state.is_admin:
                            if st.button("🗑️ [관리자] 스냅 삭제", key=f"del_snap_{s[0]}"):
                                conn = get_db_connection()
                                conn.execute("DELETE FROM snaps WHERE id = ?", (s[0],))
                                conn.commit()
                                conn.close()
                                st.success("스냅이 삭제되었습니다.")
                                st.rerun()
                        
        # --- 탭 2: 운동 섹션 ---
        with tab2:
            conn = get_db_connection()
            workout_notices = conn.cursor().execute("SELECT title, content FROM announcements WHERE section = '운동' ORDER BY id DESC").fetchall()
            conn.close()
            
            if workout_notices:
                for tn in workout_notices:
                    st.markdown(f"""
                        <div class="notice-box">
                            <h4 style="margin: 0 0 4px 0; font-size: 15px; color: #B71C1C;">📢 [공지] {tn[0]}</h4>
                            <p style="margin: 0; font-size: 13px; color: #333;">{tn[1]}</p>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("##### 💪 체형 교정 맞춤 운동 루틴 공유")
            with st.form("workout_form"):
                w_title = st.text_input("운동 루틴 제목")
                w_content = st.text_area("운동 방법 및 세트 설명")
                w_img = st.file_uploader("참고 사진 첨부", type=['jpg', 'jpeg', 'png'])
                if st.form_submit_button("운동 루틴 업로드") and w_title:
                    w_b = w_img.read() if w_img else None
                    conn = get_db_connection()
                    conn.execute("INSERT INTO workouts (title, content, body_type, image) VALUES (?, ?, ?, ?)", (w_title, w_content, body_type, w_b))
                    conn.commit()
                    conn.close()
                    st.success("운동 루틴이 등록되었습니다!")
                    st.rerun()

            st.markdown("---")
            st.markdown("##### 📋 유저 공유 운동 루틴")
            conn = get_db_connection()
            workouts = conn.cursor().execute("SELECT id, title, content, body_type, image FROM workouts ORDER BY id DESC").fetchall()
            conn.close()

            if workouts:
                cols = st.columns(2)
                for idx, w in enumerate(workouts):
                    with cols[idx % 2]:
                        st.markdown(f"""
                            <div class="card-box">
                                <span style="font-size: 11px; background-color: #111111; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600;">{w[3]}</span>
                                <h4 style="margin: 8px 0 4px 0; font-size: 16px;">{w[1]}</h4>
                                <p style="font-size: 13px; color: #666; margin-bottom: 8px;">{w[2]}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if w[4]: st.image(Image.open(io.BytesIO(w[4])), use_container_width=True)

                        if st.session_state.is_admin:
                            if st.button("🗑️ [관리자] 운동 삭제", key=f"del_workout_{w[0]}"):
                                conn = get_db_connection()
                                conn.execute("DELETE FROM workouts WHERE id = ?", (w[0],))
                                conn.commit()
                                conn.close()
                                st.success("운동 루틴이 삭제되었습니다.")
                                st.rerun()
            else:
                st.info("등록된 운동 루틴이 없습니다.")
            
        # --- 탭 3: 중고 마켓 섹션 ---
        with tab3:
            conn = get_db_connection()
            market_notices = conn.cursor().execute("SELECT title, content FROM announcements WHERE section = '중고' ORDER BY id DESC").fetchall()
            conn.close()
            
            if market_notices:
                for tn in market_notices:
                    st.markdown(f"""
                        <div class="notice-box">
                            <h4 style="margin: 0 0 4px 0; font-size: 15px; color: #B71C1C;">📢 [공지] {tn[0]}</h4>
                            <p style="margin: 0; font-size: 13px; color: #333;">{tn[1]}</p>
                        </div>
                    """, unsafe_allow_html=True)

            st.markdown("##### 🛒 옷 중고 거래 마켓")
            f_col1, f_col2 = st.columns([2, 1])
            with f_col1: search_kw = st.text_input("🔍 상품 검색", placeholder="키워드 입력")
            with f_col2: filter_tp = st.selectbox("체형 필터", ["전체 체형", "스트레이트 (Straight)", "웨이브 (Wave)", "내추럴 (Natural)"])
            
            with st.expander("➕ 내 옷장 상품 등록하기"):
                with st.form("market_f"):
                    m_title = st.text_input("상품명")
                    m_price = st.text_input("가격")
                    m_status = st.selectbox("거래 상태", ["판매 중", "예약중", "판매 완료"])
                    m_content = st.text_area("상품 설명")
                    m_img = st.file_uploader("상품 사진", type=['jpg', 'jpeg', 'png'])
                    if st.form_submit_button("마켓에 등록") and m_title:
                        m_b = m_img.read() if m_img else None
                        conn = get_db_connection()
                        conn.execute("INSERT INTO market (title, price, status, content, body_type, image) VALUES (?, ?, ?, ?, ?, ?)", (m_title, m_price, m_status, m_content, body_type, m_b))
                        conn.commit()
                        conn.close()
                        st.success("상품이 등록되었습니다!")
                        st.rerun()
                        
            conn = get_db_connection()
            markets = conn.cursor().execute("SELECT id, title, price, status, content, body_type, image FROM market ORDER BY id DESC").fetchall()
            conn.close()
            
            if filter_tp != "전체 체형":
                markets = [m for m in markets if filter_tp in m[5]]
            if search_kw:
                markets = [m for m in markets if search_kw.lower() in m[1].lower() or search_kw.lower() in m[4].lower()]
                
            if markets:
                cols = st.columns(2)
                for idx, m in enumerate(markets):
                    m_key = f"market_{m[0]}"
                    liked = m_key in st.session_state.liked_market_items
                    with cols[idx % 2]:
                        st.markdown(f"""
                            <div class="card-box">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <span style="font-size: 11px; background-color: #111111; color: white; padding: 3px 8px; border-radius: 4px; font-weight: 600;">{m[5]}</span>
                                    <span style="font-size: 12px; font-weight: 700; color: #FF5252;">[{m[3]}]</span>
                                </div>
                                <h4 style="margin: 8px 0 4px 0; font-size: 16px;">{m[1]}</h4>
                                <p style="font-size: 14px; font-weight: 700; color: #111; margin-bottom: 4px;">{m[2]}</p>
                                <p style="font-size: 13px; color: #666; margin-bottom: 8px;">{m[4]}</p>
                            </div>
                        """, unsafe_allow_html=True)
                        if m[6]: st.image(Image.open(io.BytesIO(m[6])), use_container_width=True)
                        
                        bc1, bc2 = st.columns(2)
                        with bc1:
                            if st.button("💬 채팅", key=f"chat_{m_key}"): st.info("판매자와 1:1 채팅 연결")
                        with bc2:
                            if liked:
                                if st.button("🤍 찜 취소", key=f"unlike_{m_key}"):
                                    st.session_state.liked_market_items.remove(m_key)
                                    st.rerun()
                            else:
                                if st.button("🖤 찜하기", key=f"like_{m_key}"):
                                    st.session_state.liked_market_items.append(m_key)
                                    st.rerun()
                                    
                        if st.session_state.is_admin:
                            if st.button("🗑️ [관리자] 상품 삭제", key=f"del_market_{m[0]}"):
                                conn = get_db_connection()
                                conn.execute("DELETE FROM market WHERE id = ?", (m[0],))
                                conn.commit()
                                conn.close()
                                st.success("마켓 상품이 삭제되었습니다.")
                                st.rerun()

    st.markdown("<div style='height: 30px;'></div>", unsafe_allow_html=True)
    if st.button("← 분석 결과로 돌아가기"):
        st.session_state.page = 'result'
        st.rerun()