#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# @raycast.schemaVersion 1
# @raycast.title nin
# @raycast.mode fullOutput
# @raycast.packageName Notion
# @raycast.description title, body -> Notion inbox
# @raycast.argument1 { "type": "text", "placeholder": "title, body" }
# @raycast.icon 📥
# @raycast.author

import json
import os
import re
import sys
import traceback
import urllib.error
import urllib.request

DEFAULT_SECRET_FILE = "~/.config/nin/secrets.env"


def usage() -> str:
    return (
        "使い方:\n"
        '  nin "タイトル, 本文"\n'
        '  nin "タイトル"\n'
        '  nin "タイトル," ""\n'
        "\n"
        "補足:\n"
        '- 先頭の "nin" は省略可（例: "タイトル"）\n'
        "- タイトルは必須、本文は省略・空文字可\n"
    )


def eprint(message: str) -> None:
    print(message, file=sys.stderr)


def normalize_database_id(raw_id: str) -> str:
    normalized = raw_id.replace("-", "").strip()
    if len(normalized) != 32 or not re.fullmatch(r"[0-9a-fA-F]{32}", normalized):
        raise ValueError(
            "NOTION_DATABASE_ID が不正です。32文字のID（ハイフン有無どちらでも可）を指定してください。"
        )

    return (
        f"{normalized[0:8]}-{normalized[8:12]}-{normalized[12:16]}-"
        f"{normalized[16:20]}-{normalized[20:32]}"
    )


def parse_input(raw_input: str) -> tuple[str, str]:
    if not raw_input or not raw_input.strip():
        raise ValueError("入力が空です。")

    text = raw_input.strip()

    if text.lower().startswith("nin "):
        text = text[4:].strip()
    elif text.lower() == "nin":
        raise ValueError("タイトルがありません。")

    if "," in text:
        title, body = text.split(",", 1)
        title = title.strip()
        body = body.strip()
    else:
        title = text.strip()
        body = ""

    if title == "":
        raise ValueError("タイトルが空です。")

    return title, body


def build_payload(
    database_id: str,
    title_property: str,
    title: str,
    body: str,
    append_body: bool,
) -> dict:
    payload: dict = {
        "parent": {"database_id": database_id},
        "properties": {
            title_property: {
                "title": [
                    {
                        "text": {"content": title},
                    }
                ]
            }
        },
    }

    if append_body:
        rich_text = []
        if body != "":
            rich_text = [{"type": "text", "text": {"content": body}}]

        payload["children"] = [
            {
                "object": "block",
                "type": "paragraph",
                "paragraph": {"rich_text": rich_text},
            }
        ]

    return payload


def build_http_error_hint(status_code: int) -> str:
    if status_code in (401, 403):
        return "ヒント: トークン誤り、または対象DBにIntegrationが共有されていない可能性があります。"
    if status_code == 404:
        return "ヒント: database id の取り違え（ページIDとの混同含む）を確認してください。"
    if status_code == 429:
        return "ヒント: レート制限の可能性があります。少し待って再実行してください。"
    if 500 <= status_code <= 599:
        return "ヒント: Notion側障害の可能性があります。時間をおいて再試行してください。"
    return ""


def notion_request(token: str, notion_version: str, payload: dict) -> str:
    url = "https://api.notion.com/v1/pages"
    body = json.dumps(payload).encode("utf-8")
    headers = {
        "Authorization": f"Bearer {token}",
        "Notion-Version": notion_version,
        "Content-Type": "application/json",
    }
    request = urllib.request.Request(url=url, data=body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            raw = response.read().decode("utf-8", errors="replace")
            data = json.loads(raw) if raw else {}
            page_url = data.get("url")

            if not page_url:
                page_id = data.get("id", "")
                if page_id:
                    page_url = f"https://www.notion.so/{page_id.replace('-', '')}"

            if not page_url:
                raise RuntimeError("成功レスポンスにページURLが含まれていません。")

            return page_url

    except urllib.error.HTTPError as exc:
        response_text = exc.read().decode("utf-8", errors="replace")
        eprint(f"HTTP Error: {exc.code}")
        eprint(f"Response Body: {response_text}")
        hint = build_http_error_hint(exc.code)
        if hint:
            eprint(hint)
        raise
    except urllib.error.URLError as exc:
        eprint("Network Error: Notion APIへの接続に失敗しました。")
        eprint(f"Reason: {exc.reason}")
        raise


def load_env_file(path: str) -> dict[str, str]:
    expanded = os.path.expanduser(path)
    if not os.path.exists(expanded):
        return {}
    if not os.path.isfile(expanded):
        raise ValueError(f"シークレットファイルがファイルではありません: {expanded}")

    values: dict[str, str] = {}
    try:
        with open(expanded, "r", encoding="utf-8") as fp:
            for line_no, line in enumerate(fp, start=1):
                raw = line.strip()
                if not raw or raw.startswith("#"):
                    continue
                if "=" not in raw:
                    raise ValueError(
                        f"シークレットファイルの形式が不正です ({expanded}:{line_no})"
                    )
                key, value = raw.split("=", 1)
                key = key.strip()
                value = value.strip()

                if not key:
                    raise ValueError(
                        f"シークレットファイルのキーが空です ({expanded}:{line_no})"
                    )

                if (
                    len(value) >= 2
                    and value[0] == value[-1]
                    and value[0] in ("'", '"')
                ):
                    value = value[1:-1]

                values[key] = value
    except OSError as exc:
        raise ValueError(f"シークレットファイルを読めませんでした: {expanded} ({exc})") from exc

    return values


def load_config() -> tuple[str, str, str, str, bool]:
    secret_file = os.environ.get("NOTION_ENV_FILE", DEFAULT_SECRET_FILE).strip()
    file_values = load_env_file(secret_file)

    def get_setting(name: str, default: str = "") -> str:
        env_value = os.environ.get(name)
        if env_value is not None and env_value.strip() != "":
            return env_value.strip()
        return file_values.get(name, default).strip()

    token = get_setting("NOTION_TOKEN")
    raw_database_id = get_setting("NOTION_DATABASE_ID")
    title_property = get_setting("NOTION_TITLE_PROPERTY", "タイトル")
    notion_version = get_setting("NOTION_VERSION", "2022-06-28")
    append_body = get_setting("NOTION_APPEND_BODY", "1") == "1"

    if not token:
        raise ValueError(
            "NOTION_TOKEN が未設定です。環境変数またはシークレットファイルを確認してください。"
        )
    if not raw_database_id:
        raise ValueError(
            "NOTION_DATABASE_ID が未設定です。環境変数またはシークレットファイルを確認してください。"
        )

    database_id = normalize_database_id(raw_database_id)
    return token, database_id, title_property, notion_version, append_body


def main() -> int:
    try:
        raw_input = sys.argv[1] if len(sys.argv) > 1 else ""
        if not raw_input.strip():
            print('入力例: "タイトル, 本文"')
            return 0

        title, body = parse_input(raw_input)
        token, database_id, title_property, notion_version, append_body = load_config()
        payload = build_payload(
            database_id=database_id,
            title_property=title_property,
            title=title,
            body=body,
            append_body=append_body,
        )
        page_url = notion_request(
            token=token,
            notion_version=notion_version,
            payload=payload,
        )
        print(page_url)
        return 0
    except ValueError as exc:
        eprint(f"Input/Config Error: {exc}")
        eprint("")
        eprint(usage())
        return 1
    except Exception as exc:
        eprint(f"Unexpected Error: {exc}")
        eprint(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
