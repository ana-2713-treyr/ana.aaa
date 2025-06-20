import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Home")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

        # Kaggle 데이터셋 출처 및 소개
        st.markdown("""
                ---
                **인구 조사 데이터셋**   
                - 설명: 2008~2023까지 각 지역별 인구 분석  
                - 주요 변수:  
                  - `year`: 집계 기준 연도  
                  - `region_kr`: 시·도 단위 행정구역 (전국 포함)	 
                  - `population`: 해당 연·지역의 총 인구(명)
                  - `births`: 같은 연도 출생아 총계	  
                  - `deaths`: 같은 연도 사망자 총계	
                """)

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()


KOR2ENG = {
    "서울": "Seoul", "부산": "Busan", "대구": "Daegu", "인천": "Incheon",
    "광주": "Gwangju", "대전": "Daejeon", "울산": "Ulsan", "세종": "Sejong",
    "경기": "Gyeonggi", "강원": "Gangwon", "충북": "Chungbuk", "충남": "Chungnam",
    "전북": "Jeonbuk", "전남": "Jeonnam", "경북": "Gyeongbuk", "경남": "Gyeongnam",
    "제주": "Jeju", "전국": "National"
}

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        import streamlit as st
        import pandas as pd
        import numpy as np
        import matplotlib.pyplot as plt
        import seaborn as sns

        st.title("📊 인구 통계 EDA")
        uploaded = st.file_uploader("population_trends.csv 업로드", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        # ---------- 전처리 ----------
        df = pd.read_csv(uploaded)

        # 1) 세종 – 결측치 '-' → 0
        sejong_mask = df["지역"] == "세종"
        target_cols = ["인구", "출생아수(명)", "사망자수(명)"]
        for c in target_cols:
            df.loc[sejong_mask & (df[c] == "-"), c] = 0

        # 2) 수치형 변환
        for c in target_cols:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0).astype(int)

        # ----- 영어 지역명 매핑 -----
        kor2eng = {
            "서울":"Seoul","부산":"Busan","대구":"Daegu","인천":"Incheon","광주":"Gwangju",
            "대전":"Daejeon","울산":"Ulsan","세종":"Sejong","경기":"Gyeonggi","강원":"Gangwon",
            "충북":"Chungbuk","충남":"Chungnam","전북":"Jeonbuk","전남":"Jeonnam",
            "경북":"Gyeongbuk","경남":"Gyeongnam","제주":"Jeju","전국":"National"
        }

        # ------------------ 탭 구성 ------------------
        탭 = st.tabs(["기초 통계", "연도별 추이", "지역별 분석",
                     "변화량 분석", "시각화"])

        # === 1. 기초 통계 탭 ===
        with 탭[0]:
            st.subheader("데이터 구조 (`df.info()`)")
            st.code(df.info(buf=None, verbose=True, memory_usage=False))

            st.subheader("기초 통계량 (`df.describe()`)")
            st.dataframe(df.describe(include="all"))

        # === 2. 연도별 추이(전국) ===
        with 탭[1]:
            st.subheader("National Population Trend")

            nat = df[df["지역"] == "전국"].sort_values("연도")
            x = nat["연도"]
            y = nat["인구"]

            # 2035 예측: 최근 3년 평균 자연증가(출생-사망)
            recent3 = nat.tail(3)
            avg_net = (recent3["출생아수(명)"] - recent3["사망자수(명)"]).mean()
            y_pred = y.iloc[-1] + avg_net * (2035 - x.iloc[-1])

            fig, ax = plt.subplots()
            ax.plot(x, y, marker="o")
            ax.scatter(2035, y_pred, color="red")
            ax.text(2035, y_pred, f"{int(y_pred):,}", ha="left", va="bottom")
            ax.set_title("National Population (Forecast included)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            st.pyplot(fig)
            st.caption(
                f"최근 3년 평균 자연증가 ≈ {int(avg_net):,}명/년을 적용해 2035년 인구를 예측했습니다."
            )

        # === 3. 지역별 5년 변화 ===
        with 탭[2]:
            st.subheader("5-Year Population Change by Region")

            latest = df["연도"].max()
            prev = latest - 5
            cur = df[df["연도"] == latest][["지역", "인구"]]
            past = df[df["연도"] == prev][["지역", "인구"]].rename(columns={"인구":"이전"})
            merged = cur.merge(past, on="지역")
            merged = merged[merged["지역"] != "전국"]

            merged["change"]      = merged["인구"] - merged["이전"]
            merged["pct_change"]  = merged["change"] / merged["이전"] * 100
            merged["eng_region"]  = merged["지역"].map(kor2eng)
            merged = merged.sort_values("change", ascending=False)

            # 단위: 천 명
            merged["change_k"] = (merged["change"] / 1000).round(1)

            # --- 절대치 막대 ---
            fig1, ax1 = plt.subplots(figsize=(8,6))
            sns.barplot(y="eng_region", x="change_k",
                        data=merged, palette="viridis", ax=ax1)
            ax1.set_title("Population Change (Last 5 Years)")
            ax1.set_xlabel("Change (thousand)")
            ax1.set_ylabel("")
            # 값 표시
            for p in ax1.patches:
                ax1.text(p.get_width(), p.get_y()+0.5,
                         f"{p.get_width():.1f}", va="center")

            # --- % 변화 막대 ---
            fig2, ax2 = plt.subplots(figsize=(8,6))
            sns.barplot(y="eng_region", x="pct_change",
                        data=merged, palette="coolwarm", ax=ax2)
            ax2.set_title("Population Change Rate (%)")
            ax2.set_xlabel("Change (%)")
            ax2.set_ylabel("")
            for p in ax2.patches:
                ax2.text(p.get_width(), p.get_y()+0.5,
                         f"{p.get_width():.2f}%", va="center")

            st.pyplot(fig1); st.pyplot(fig2)

            st.markdown(
                "- **경기** 등 수도권은 여전히 인구가 순증하고 있지만, 다수 지방권은 순감세가 두드러집니다.\n"
                "- 변화율(% 기준)로 보면 **세종**처럼 규모는 작지만 성장률이 높은 도시가 상위권에 위치합니다."
            )

        # === 4. 증감 Top 100 ===
        with 탭[3]:
            st.subheader("증감 상위 100")

            tmp = df.sort_values(["지역", "연도"])
            tmp["diff"] = tmp.groupby("지역")["인구"].diff()
            top100 = tmp[tmp["지역"] != "전국"].nlargest(100, "diff").copy()

            top100["연도"] = top100["연도"].astype(int)
            top100["diff_fmt"] = top100["diff"].apply(lambda x: f"{int(x):,}")

            def highlight(val):
                color = "background-color: lightblue" if val > 0 else \
                        "background-color: lightcoral"
                return color

            styled = (
                top100[["연도","지역","diff_fmt"]]
                .rename(columns={"연도":"Year","지역":"Region","diff_fmt":"Δ"})
                .style
                .applymap(lambda v: highlight(int(v.replace(",",""))), subset=["Δ"])
            )

            st.dataframe(styled, use_container_width=True,
                         hide_index=True, height=600)

        # === 5. 시각화 (누적 영역) ===
        with 탭[4]:
            st.subheader("Stacked Area – Region × Year")

            pivot = (
                df[df["지역"] != "전국"]
                .pivot_table(index="연도", columns="지역", values="인구", aggfunc="first")
            )
            # 컬럼 영문으로 변환
            pivot.columns = [kor2eng[c] for c in pivot.columns]

            fig, ax = plt.subplots(figsize=(10,6))
            ax.stackplot(pivot.index, pivot.T, labels=pivot.columns)
            ax.set_title("Population by Region (Stacked Area)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc="upper left", ncol=2, fontsize="small")
            st.pyplot(fig)
# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()