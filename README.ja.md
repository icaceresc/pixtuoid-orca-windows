<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""> English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""> Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""> Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""> <b>日本語</b></a>
</p>

# Pixtuoid for Orca（Windows 版）

ローカルの Orca エージェントセッションを、同僚として表示するフローティングのピクセルアートオフィスです。

## 表示内容

このマシンで Orca が識別したエージェントセッションごとに、キャラクターが 1 人表示されます。対応エージェントは **Claude Code、Codex、OpenCode、Antigravity** です。エージェントがターンを実行している間は働き、終わると休み、セッションが閉じられると退室します。

## 必要環境

- DirectX 12 対応の Windows x64
- Python 3.11 以降（64 ビット）
- 対応エージェントが 1 つ以上インストールされ、起動中の Orca
- Claude Code・Codex・Antigravity を使う場合は、`claude`・`codex`・`agy` が `PATH` にあること

## クイックインストール

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

インストーラーは Pixtuoid v0.23.0 をダウンロードし、SHA-256 を検証してから、Orca が報告するエージェントを接続します。対象を絞る場合: `py -3 instalar.py --sources claude-code codex`

## オフィスを開く

クローン内の **`Abrir oficina.lnk`** をダブルクリックします。同時に起動できるオフィスは 1 つだけです。`py -3 oficina.py --evidence` で起動すると、状態が `actividad/` に記録されます。

## 操作

| 操作 | 入力 |
|---|---|
| 移動 | 空いている場所をドラッグ |
| サイズ変更 | 右下の角をドラッグ |
| ズーム | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| ヘルプ・一時停止・テーマ | `?`・`P`・`T` |
| 閉じてサイズと位置を保存 | `Q` |

## 表示される状態

| Orca の状態 | オフィスでの表示 |
|---|---|
| `working` | 席で作業中 |
| `waiting` / `blocked` | 許可を求めている |
| `done` | 休憩中 |
| セッション終了 | 退室 |

## 制限事項

- 表示されるのはメインのエージェントセッションのみです。サブエージェントには専用のキャラクターがありません。
- オフィスを開いた時点で終了済みのセッションは表示されません。
- 状態は Orca が把握しているターンの状態であり、ツール・トークン・推論は反映しません。
- Orca への問い合わせは約 2 秒ごとのため、非常に短いターンは表示されないことがあります。
- `waiting` / `blocked` は、実際のセッションではまだ検証していません。
- 対象はローカルの Orca ホストのみで、リモート環境は無視されます。

## プライバシー

- オフィスが `orca agent list` から利用するのは、セッション ID・プロバイダー・状態・フォルダーのみです。プロンプトや応答を転送・保存することはありません。
- アダプターがネットワークにアクセスするのは、インストーラーが固定バージョンを GitHub からダウンロードするときだけです。
- アプリ、分離されたエージェントプロファイル、ログはクローン内（`app/`、`perfil/`、`actividad/`）に保存され、Git の管理対象外です。
- エージェントや Orca のグローバル設定は変更しません。

## アンインストール

`Q` でオフィスを閉じ、クローンのフォルダーを削除します。フォルダーの外には何もインストールされません。

## クレジットとライセンス

- 本アダプター: [MIT ライセンス](LICENSE)。
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid)（作者: Ivan Wang、MIT ライセンス）。インストール時にダウンロードし、再配布はしていません。
- 国旗アイコン: [lipis/flag-icons](https://github.com/lipis/flag-icons)（[MIT ライセンス](docs/flags/LICENSE)）。
- Orca は別製品であり、本リポジトリには含まれません。本プロジェクトは独立したアダプターであり、Pixtuoid や Orca の公式プロジェクトではありません。
