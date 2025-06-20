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
        st.title("📊 인구수 EDA")
        uploaded = st .file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        # 세종 '-' 결측을 0으로 치환
        df.loc[df["지역"] == "세종", :] = df.loc[df["지역"] == "세종", :].replace("-", 0)
        num_cols = ["인구", "출생아수(명)", "사망자수(명)"]
        df[num_cols] = df[num_cols].apply(pd.to_numeric, errors="coerce")
        df["region_en"] = df["지역"].map(KOR2ENG).fillna(df["지역"])

        # ---- Tabs -------------------------------------------------------------
        tab_stats, tab_trend, tab_region, tab_change, tab_viz = st.tabs(
            ["Basic Stats", "National Trend", "Region Ranking", "Top Δ", "Pivot Area"]
        )

        # 1) Basic Stats --------------------------------------------------------
        with tab_stats:
            st.header("Basic Statistics & Data Structure")
            buf = io.StringIO()
            df.info(buf=buf)
            st.subheader("DataFrame info()")
            st.text(buf.getvalue())
            st.subheader("describe()")
            st.dataframe(df.describe(include="all"))

        # 2) National Trend & 2035 forecast ------------------------------------
        with tab_trend:
            st.header("National Population Trend")
            nat = df[df["지역"] == "전국"].sort_values("연도")
            fig, ax = plt.subplots()
            sns.lineplot(x="연도", y="인구", data=nat, marker="o", ax=ax)
            ax.set_title("National Population Trend")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")

            recent3 = nat.tail(3)
            net_change = (recent3["출생아수(명)"] - recent3["사망자수(명)"]).mean()
            last_year = nat["연도"].max()
            last_pop = nat["인구"].iloc[-1]
            years_ahead = 2035 - last_year
            pred_2035 = int(last_pop + net_change * years_ahead)

            ax.scatter(2035, pred_2035, color="red", zorder=5)
            ax.annotate(f"2035\n{pred_2035:,}", (2035, pred_2035), textcoords="offset points", xytext=(0, -15), ha="center", color="red")
            st.pyplot(fig)

            st.markdown(
                f"""
                **Forecast logic**  
                • Average net change (births − deaths) over last 3 yrs ≈ **{net_change:,.0f}**  
                • Extrapolated {years_ahead} yrs → 2035 population ≈ **{pred_2035:,}** persons
                """
            )

        # 3) Region 5‑year change ranking --------------------------------------
        with tab_region:
            st.header("Region 5‑Year Change Ranking")
            current_year = df["연도"].max()
            prev_year = current_year - 5
            cur = df[(df["연도"] == current_year) & (df["지역"] != "전국")]
            prev = df[(df["연도"] == prev_year) & (df["지역"] != "전국")]
            merged = cur.merge(prev, on="지역", suffixes=("_cur", "_prev"))
            merged["Δ"] = merged["인구_cur"] - merged["인구_prev"]
            merged["Δ_rate"] = merged["Δ"] / merged["인구_prev"]
            merged["Δ_thou"] = merged["Δ"] / 1_000
            merged["Δ_rate_pct"] = merged["Δ_rate"] * 100
            merged["region_en"] = merged["지역"].map(KOR2ENG).fillna(merged["지역"])
            merged.sort_values("Δ_thou", ascending=False, inplace=True)

            # Δ (천명) bar
            fig1, ax1 = plt.subplots(figsize=(8, 6))
            sns.barplot(y="region_en", x="Δ_thou", data=merged, palette="crest", ax=ax1)
            ax1.set_xlabel("Δ Population (×1,000)")
            ax1.set_ylabel("Region")
            for i, v in enumerate(merged["Δ_thou"]):
                ax1.text(v, i, f"{v:,.1f}", va="center")
            ax1.set_title("5‑Year Change")
            st.pyplot(fig1)

            # Δ rate (%) bar
            fig2, ax2 = plt.subplots(figsize=(8, 6))
            sns.barplot(y="region_en", x="Δ_rate_pct", data=merged, palette="flare_r", ax=ax2)
            ax2.set_xlabel("Δ Rate (%)")
            ax2.set_ylabel("Region")
            for i, v in enumerate(merged["Δ_rate_pct"]):
                ax2.text(v, i, f"{v:+.2f}%", va="center")
            ax2.set_title("5‑Year Rate Change")
            st.pyplot(fig2)

            st.markdown(f"Comparison between **{prev_year}** and **{current_year}**.")

        # 4) Top‑100 annual Δ table -------------------------------------------
        with tab_change:
            st.header("Top‑100 Annual Δ Cases")
            dfn = df[df["지역"] != "전국"].sort_values(["지역", "연도"])
            dfn["Δ"] = dfn.groupby("지역")["인구"].diff()
            top100 = dfn.nlargest(100, "Δ", keep="all").copy()
            top100["Δ_fmt"] = top100["Δ"].apply(lambda x: f"{x:,+}")
            top100["region_en"] = top100["지역"].map(KOR2ENG).fillna(top100["지역"])

            def color_delta(val):
                if pd.isna(val):
                    return ""
                return "background-color: rgba(0,0,255,0.2)" if val > 0 else "background-color: rgba(255,0,0,0.2)"

            styled = (
                top100[["연도", "region_en", "Δ_fmt"]]
                .rename(columns={"연도": "Year", "region_en": "Region", "Δ_fmt": "Δ"})
                .style
                .applymap(color_delta, subset=["Δ"])
                .hide(axis="index")
            )
            st.dataframe(styled, use_container_width=True)

        # 5) Pivot + stacked area ---------------------------------------------
        with tab_viz:
            st.header("Stacked Area by Region")
            pv = (
                df[df["지역"] != "전국"].pivot_table(index="연도", columns="region_en", values="인구", aggfunc="sum").fillna(0)
            )
            fig, ax = plt.subplots(figsize=(10, 6))
            pv.plot.area(ax=ax, stacked=True, linewidth=0)
            ax.set_title("Population by Region (Stacked Area)")
            ax.set_xlabel("Year")
            ax.set_ylabel("Population")
            ax.legend(loc="upper left", bbox_to_anchor=(1.02, 1))
            st.pyplot(fig)
            st.markdown("Stacked area chart shows each region’s share over time.")

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