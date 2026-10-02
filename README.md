# 다국어 번역기

입력한 글을 영어 / 일본어 / 베트남어로 번역하는 Streamlit 앱입니다.

## 설치

```bash
pip install -r requirements.txt
```

## 환경 변수 설정

`.env.example`을 복사해 `.env` 파일을 만들고 값을 입력합니다.

```env
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-6-astra
```

> 파일 이름은 정확히 `.env`여야 합니다 (`.env.txt` 아님).
> Windows 메모장으로 저장하면 `.txt`가 붙을 수 있으니 확인하세요.

## 실행

```bash
streamlit run app.py
```

브라우저에서 http://localhost:8501 이 열립니다.

## 배포 (Streamlit Community Cloud)

1. GitHub에 push (`.env`는 `.gitignore`로 제외됨)
2. https://share.streamlit.io 에서 저장소 연결, Main file: `app.py`
3. Advanced settings → Secrets에 입력

```toml
OPENAI_API_KEY = "sk-..."
OPENAI_MODEL = "gpt-6-astra"
```
