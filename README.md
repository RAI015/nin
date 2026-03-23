# nin
[![CI](https://github.com/RAI015/nin/actions/workflows/ci.yml/badge.svg)](https://github.com/RAI015/nin/actions/workflows/ci.yml)

Raycast Script Command で Notion の INBOX データベースに1件追加する Python スクリプト。

## 30秒で分かる

Raycast から `title` または `title, body` を入力するだけで、Notion の指定 DB にページを追加する。外部ライブラリ不要。

- `title`（必須）と `body`（任意）を受け取り、Notion のページを作成
- 成功時は作成ページの URL を標準出力に表示
- 失敗時は HTTP ステータスとレスポンスを標準エラーに表示

## 実行例

入力（Raycast）:

```text
買い物, 牛乳を買う
```

出力（成功時）:

```text
https://www.notion.so/xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

- Command: `nin`
- Runtime: Python 3.10+
- Dependency: 標準ライブラリのみ

## Demo

### Input example

![Raycast input example](docs/images/raycast-input-example.jpg)

### Success output

![Raycast success output](docs/images/raycast-success-output.jpg)

## セットアップ

1. `nin.py` を Script Commands ディレクトリに配置
2. 実行権限を付与

```bash
chmod +x nin.py
```

3. Raycast で Script Directory を追加
   - `Raycast Settings > Extensions > Script Commands`

4. 機密設定ファイルを作成

```bash
cp secrets.env.example secrets.env
```

5. `secrets.env` に実値を設定

```env
NOTION_TOKEN=ntn_xxx
NOTION_DATABASE_ID=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
NOTION_TITLE_PROPERTY=タイトル
NOTION_VERSION=2022-06-28
NOTION_APPEND_BODY=1
```

6. Raycast から参照できるよう環境変数を設定（初回のみ）

```bash
launchctl setenv NOTION_ENV_FILE "/absolute/path/to/secrets.env"
```

7. Raycast を再起動

### 環境変数

| 変数名 | 必須 | デフォルト | 説明 |
|---|---|---|---|
| `NOTION_TOKEN` | ✅ | - | Notion Integration トークン |
| `NOTION_DATABASE_ID` | ✅ | - | 対象 DB の ID（32文字） |
| `NOTION_TITLE_PROPERTY` | | `タイトル` | タイトル型プロパティ名 |
| `NOTION_VERSION` | | `2022-06-28` | Notion-Version ヘッダー |
| `NOTION_APPEND_BODY` | | `1` | `1` のとき本文をページ本文に追加 |
| `NOTION_ENV_FILE` | | `~/.config/nin/secrets.env` | secrets ファイルのパス |

優先順位：環境変数 > secrets file > デフォルト値

## 使い方

`fullOutput` モードで動作する。

1. Raycast で `nin` を選択
2. 引数を入力して実行

`body` は省略可。

```text
title
title, body
```

ローカルでの動作確認：

```bash
NOTION_ENV_FILE="/absolute/path/to/secrets.env" ./nin.py "nin title, body"
```

## ライセンス

MIT
