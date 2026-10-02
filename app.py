import streamlit as st

from translator import (
    LANGUAGES,
    MAX_CHARS,
    APIError,
    AuthenticationError,
    MissingAPIKeyError,
    NetworkError,
    get_config,
    translate,
)

# 결과 탭 라벨. 여기에 없는 언어는 LANGUAGES의 표시 이름을 쓴다.
TAB_LABELS: dict[str, str] = {
    "english": "🇺🇸 English",
    "japanese": "🇯🇵 日本語",
    "vietnamese": "🇻🇳 Tiếng Việt",
}

# Windows는 국기 이모지를 글자(US, JP…)로 표시하므로 탭에만 컬러 이모지 폰트를 적용한다.
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Color+Emoji&display=swap');
[role="tab"] p {
    font-family: "Source Sans", "Source Sans Pro", "Noto Color Emoji", sans-serif;
    font-size: 1rem;
}
/* 번역 결과는 코드가 아닌 일반 글이므로 본문 글꼴로 표시한다. */
[data-testid="stCode"] code {
    font-family: "Source Sans", "Source Sans Pro", sans-serif;
    font-size: 1rem;
    line-height: 1.6;
}
/* 기본 카운터는 입력창에 포커스가 있을 때만 보이므로 숨기고 직접 표시한다. */
[data-testid="stTextArea"] [data-testid="InputInstructions"] {
    display: none;
}
h1 {
    word-break: keep-all;
}
@media (max-width: 640px) {
    h1 {
        font-size: 2rem !important;
    }
}
.char-counter {
    text-align: right;
    font-size: 0.85rem;
    opacity: 0.6;
    margin-top: -0.75rem;
}
.char-counter.over {
    color: #DC2626;
    opacity: 1;
}
</style>
"""


@st.cache_data(show_spinner=False)
def cached_translate(text: str, targets: tuple[str, ...]) -> dict[str, str]:
    # 예외는 캐시되지 않으므로 실패한 요청은 다음에 다시 시도된다.
    return translate(text, list(targets))


st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

with st.sidebar:
    st.subheader("ℹ️ 정보")
    st.caption(f"사용 모델: `{get_config()[1]}`")
    st.markdown(
        "1. 번역할 글을 입력하세요.\n"
        "2. 번역할 언어를 고르세요.\n"
        "3. **번역하기**를 누르고 결과를 복사하세요."
    )

st.title("🌐 다국어 번역기")
st.caption("입력한 글을 영어·일본어·베트남어로 번역합니다.")

text = st.text_area(
    "번역할 글",
    placeholder="번역할 글을 입력하세요...",
    max_chars=MAX_CHARS,
    height=200,
    label_visibility="collapsed",
)
counter_class = "char-counter over" if len(text) >= MAX_CHARS else "char-counter"
st.markdown(
    f'<div class="{counter_class}">{len(text):,} / {MAX_CHARS:,}자</div>',
    unsafe_allow_html=True,
)

# st.columns는 모바일에서 세로로 쌓이므로 가로 컨테이너로 한 줄을 유지한다.
with st.container(horizontal=True, horizontal_alignment="distribute"):
    selected = [
        key
        for key, (label, _) in LANGUAGES.items()
        if st.checkbox(label, value=True, key=f"lang_{key}")
    ]

if st.button("번역하기", type="primary", width="stretch"):
    if not text.strip():
        st.warning("번역할 글을 입력해 주세요.")
    elif len(text) > MAX_CHARS:
        st.warning(f"글은 최대 {MAX_CHARS}자까지 번역할 수 있습니다.")
    elif not selected:
        st.warning("번역할 언어를 하나 이상 선택해 주세요.")
    else:
        try:
            with st.spinner("번역 중입니다..."):
                st.session_state["results"] = cached_translate(text, tuple(selected))
        except MissingAPIKeyError:
            st.error("API 키가 설정되지 않았습니다. `.env` 파일(배포 시 Secrets)에 OPENAI_API_KEY를 입력해 주세요.")
        except AuthenticationError:
            st.error("API 키가 올바르지 않습니다. OPENAI_API_KEY 값을 확인해 주세요.")
        except NetworkError:
            st.error("번역 서버에 연결할 수 없습니다. 인터넷 연결을 확인한 뒤 다시 시도해 주세요.")
        except APIError as e:
            st.error(f"번역 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요.\n\n상세: {e}")

results: dict[str, str] = st.session_state.get("results", {})
if results:
    st.divider()
    tabs = st.tabs([TAB_LABELS.get(key, LANGUAGES[key][0]) for key in results])
    for tab, translated in zip(tabs, results.values()):
        with tab:
            st.code(translated, language=None, wrap_lines=True)
