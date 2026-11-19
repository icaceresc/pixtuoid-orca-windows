<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md"><b>日本語</b></a>
</p>

# Windows 版 Orca 用 Pixtuoid

ローカルの Orca エージェント、そのワーカー、サブエージェントを同僚として表示する、フローティングのピクセルアートのオフィスです。Orca プラグインとしてインストールすることも、クローンから実行することもできます。

## 表示内容

このマシンで Orca が識別するエージェントごとに 1 人のキャラクターが表示されます。子はチームの色の帽子をかぶり、親と一緒に退出します。

| Orca 側 | オフィス側 |
|---|---|
| エージェントセッション（Claude Code、Codex、OpenCode、Antigravity） | 専用のキャラクター |
| Orca のオーケストレーションで起動されたワーカー（深さは任意） | 起動したエージェントの子 |
| Orca がセッション内で観測するサブエージェント | そのセッションの子 |
| バックグラウンドコマンド、モニター、ツール呼び出し | キャラクターなし |

Orca 1.4.263 の実セッションで確認済み:

| プロバイダー | エージェント | ワーカー（子） | ネイティブのサブエージェント |
|---|---|---|---|
| Claude Code | 対応 | 対応 | 対応 |
| Codex | 対応 | 対応 | 未確認 |
| OpenCode | 対応 | 対応 | 未確認 |
| Antigravity | 対応 | 対応 | Orca の報告なし |

## 必要条件

- DirectX 12 対応の Windows x64
- Python 3.11 以降（64 ビット）と `py` ランチャー
- 起動中の Orca 1.4.263 以降と、対応エージェント 1 つ以上
- Claude Code、Codex、Antigravity のソースには `PATH` 上の `claude`、`codex`、`agy`

## クイックインストール

**Orca プラグインとして**

```powershell
orca plugin install icaceresc/pixtuoid-orca-windows
```

Orca がプラグインの権限を表示し、承認を求めます。プラグインは独自のコードを実行しますが、Orca の権限は要求しません。続いてコマンドパレットで **Pixtuoid: Install or update the office app** を実行します。Pixtuoid v0.23.0 を `%LOCALAPPDATA%\PixtuoidOrca` にダウンロードし、SHA-256 を検証して、Orca が報告するエージェントを接続します。

**クローンから**

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina
```

ソースを絞る場合: `py -3 instalar.py --sources claude-code codex`

## オフィスを開く

- プラグイン: コマンドパレットの **Pixtuoid: Open office window** と **Pixtuoid: Close office window**。
- クローン: **`Abrir oficina.lnk`** をダブルクリック。`Q` または `py -3 oficina.py --stop` で閉じます。

ウィンドウは Orca の外に浮かぶので、セカンドモニターに置いておけます。オフィスはインストールごとに 1 つだけ実行されます。`py -3 oficina.py --evidence` で状態を `actividad/` に記録します。

## 操作

| 操作 | 入力 |
|---|---|
| 移動 | 空いている場所をドラッグ |
| サイズ変更 | 右下の角をドラッグ |
| ズーム | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| ヘルプ · 一時停止 · テーマ | `?` · `P` · `T` |
| 閉じてサイズと位置を保存 | `Q` または閉じるコマンド |

## 表示される状態

| Orca の状態 | オフィスでの表示 |
|---|---|
| `working` | 机で作業中のキャラクター |
| `waiting` / `blocked` | 許可を求めるキャラクター |
| `done` / `idle` | 休憩中のキャラクター |
| セッション終了、サブエージェントの完了またはキャンセル | キャラクターが退出（子が先に退出） |

## 制限事項

- Pixtuoid v0.23.0 は、同じプロバイダーの親にしか子をつなげられません。別のプロバイダーのワーカーは、帽子付きで親の下に表示されますが、プロバイダーのラベルは親のものになります。
- Pixtuoid は Antigravity の下に子を描けません。Antigravity が起動したワーカーは、同じチーム色の別の同僚として表示されます。
- 表示されるのは Orca 自身が観測するサブエージェントだけです。階層は、それを公開する唯一の Orca インターフェースである `orca worktree ps` から取得します。
- オフィスを開いた時点で終了済みのエージェントは表示されません。
- 状態は Orca のターン状態を反映するもので、ツール、トークン、推論は反映しません。
- Orca へのポーリングは約 1.25 秒ごとのため、非常に短いターンは表示されないことがあります。Orca が混雑していると、新しい子が一瞬表示されてから親の下に移ることがあります。
- `waiting` / `blocked` は実セッションでまだ確認されていません。
- ローカルの Orca ホストのみ対応。リモートの Orca 環境は無視されます。

## プライバシー

- オフィスが `orca agent list` と `orca worktree ps` から読むのは、ID、親子のリンク、プロバイダー、エージェントの種類、状態、フォルダーだけです。プロンプト、応答、ツールへの入力は転送も保存もしません。
- アダプターのネットワークアクセスは、固定バージョンの Pixtuoid を GitHub からダウンロードすることだけです。
- アプリ、分離されたエージェントプロファイル、ログはクローン内または `%LOCALAPPDATA%\PixtuoidOrca`（`app/`、`perfil/`、`actividad/`）に保存されます。
- エージェントと Orca のグローバル設定は変更しません。

## アンインストール

- プラグイン: **Pixtuoid: Remove downloaded app and local data** を実行してから、Orca の Settings → Plugins でプラグインをアンインストールします。
- クローン: オフィスを閉じて、クローンのフォルダーを削除します。

ほかには何もインストールされません。

## クレジットとライセンス

- このアダプター: [MIT ライセンス](LICENSE)。
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid)（Ivan Wang 作、MIT ライセンス）。インストール時にダウンロードされ、再配布はしていません。
- 国旗アイコン: [lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3、[MIT ライセンス](docs/flags/LICENSE)。
- Orca は別製品で、同梱されていません。これは独立したアダプターであり、Pixtuoid や Orca の公式プロジェクトではありません。
