"""OpenAI를 이용한 번역 로직. Streamlit UI 코드는 app.py에 둔다."""

import json
import os

import openai
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DEFAULT_MODEL = "gpt-6-astra"
MAX_CHARS = 5000

# 대상 언어의 단일 출처. 언어를 추가할 때는 여기만 수정한다.
# 키: JSON 응답 키, 값: (화면 표시 이름, 프롬프트용 영어 이름)
LANGUAGES: dict[str, tuple[str, str]] = {
    "english": ("영어", "English"),
    "japanese": ("일본어", "Japanese"),
    "vietnamese": ("베트남어", "Vietnamese"),
}

_RULES = (
    "You are a professional translator. "
    "Automatically detect the source language. "
    "Preserve the original meaning, nuance, and tone. "
    "Keep line breaks and paragraph structure exactly as in the source. "
    "Render proper nouns (names of people, places, organizations) in the target language's "
    "standard script and spelling (e.g. 서울 -> Seoul / ソウル), without changing what they refer to. "
    "Do not add explanations, notes, or quotation marks; output only the translation."
)


class TranslationError(Exception):
    """번역 중 발생하는 오류의 기본 클래스."""


class MissingAPIKeyError(TranslationError):
    """OPENAI_API_KEY가 설정되지 않음."""


class AuthenticationError(TranslationError):
    """API 키가 잘못되었거나 권한이 없음."""


class NetworkError(TranslationError):
    """OpenAI 서버에 연결할 수 없음."""


class APIError(TranslationError):
    """그 밖의 API 오류 (모델 없음, 사용량 초과 등)."""


def _read_setting(name: str) -> str | None:
    """st.secrets → 환경 변수(.env) 순서로 설정값을 읽는다."""
    try:
        if name in st.secrets:
            return str(st.secrets[name])
    except Exception:
        # secrets.toml이 없는 로컬 환경
        pass
    return os.getenv(name)


def get_config() -> tuple[str | None, str]:
    """(API 키, 모델명)을 반환한다."""
    api_key = _read_setting("OPENAI_API_KEY")
    model = _read_setting("OPENAI_MODEL") or DEFAULT_MODEL
    return api_key, model


def _json_prompt(targets: list[str]) -> str:
    keys = ", ".join(f'"{key}" ({LANGUAGES[key][1]})' for key in targets)
    return (
        f"{_RULES}\n"
        f"Translate the user's text into each of these languages: {keys}.\n"
        "Respond with a single JSON object whose keys are exactly those keys "
        "and whose values are the translations."
    )


def _single_prompt(target: str) -> str:
    return f"{_RULES}\nTranslate the user's text into {LANGUAGES[target][1]}."


def _chat(client: OpenAI, model: str, system: str, text: str, json_mode: bool) -> str:
    kwargs = {"response_format": {"type": "json_object"}} if json_mode else {}
    try:
        response = client.chat.completions.create(
            # gpt-6-astra는 temperature 기본값(1)만 지원하므로 지정하지 않는다.
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": text},
            ],
            **kwargs,
        )
    except openai.AuthenticationError as e:
        raise AuthenticationError(str(e)) from e
    except (openai.APIConnectionError, openai.APITimeoutError) as e:
        raise NetworkError(str(e)) from e
    except openai.OpenAIError as e:
        raise APIError(str(e)) from e
    return response.choices[0].message.content or ""


def translate(text: str, targets: list[str]) -> dict[str, str]:
    """text를 targets 언어로 번역해 {언어 키: 번역문}을 반환한다.

    한 번의 호출로 JSON 응답을 받고, 파싱에 실패하거나 빠진 언어가 있으면
    해당 언어만 개별 호출로 다시 번역한다.
    """
    unknown = [t for t in targets if t not in LANGUAGES]
    if unknown:
        raise ValueError(f"지원하지 않는 언어: {unknown}")
    if not targets:
        return {}

    api_key, model = get_config()
    if not api_key:
        raise MissingAPIKeyError("OPENAI_API_KEY가 설정되지 않았습니다.")
    client = OpenAI(api_key=api_key)

    results: dict[str, str] = {}
    raw = _chat(client, model, _json_prompt(targets), text, json_mode=True)
    try:
        data = json.loads(raw)
        if isinstance(data, dict):
            results = {
                key: data[key].strip()
                for key in targets
                if isinstance(data.get(key), str) and data[key].strip()
            }
    except json.JSONDecodeError:
        pass

    for key in targets:
        if key not in results:
            results[key] = _chat(client, model, _single_prompt(key), text, json_mode=False).strip()

    return {key: results[key] for key in targets}
