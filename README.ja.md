<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md"><b>日本語</b></a> &nbsp;·&nbsp;
  <a href="README.zh.md"><img src="docs/flags/cn.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.zh.md">中文</a> &nbsp;·&nbsp;
  <a href="README.ru.md"><img src="docs/flags/ru.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ru.md">Русский</a>
</p>

# Windows 版 Orca 用 Pixtuoid

ローカルの Orca エージェント、そのワーカー、サブエージェントを、プロバイダー・役割・プロジェクトの名札付きで同僚として表示する、フローティングのピクセルアートのオフィスです。このリポジトリのクローンから実行します。

![デモ用ワークスペース：Codex・Antigravity・Claude Code のワーカーと Explore サブエージェントを持つ 2 つのオーケストレーター](docs/office-roles.png)

## 表示内容

Orca がこのマシンで識別するエージェントごとに 1 人のキャラクターです。子はチームの色の帽子をかぶり、親と一緒に退出します。`Tab` でエージェントのツリーを表示します。

![エージェントのツリー：各オーケストレーターとそのワーカー、サブエージェント、ツールと状態](docs/office-dashboard.png)

| Orca での種類 | オフィスでの名前 |
|---|---|
| 最上位のエージェント | `cc·my-repo` |
| ワーカーを起動したエージェント | `cc·my-repo · orchestrator` |
| オーケストレーションのワーカー（どの深さでも） | `cx·worker · my-repo` |
| 親と異なるプロバイダーのワーカー | `cx·claude worker · my-repo` |
| Orca がセッション内で観測するサブエージェント | `cc·Explore subagent · my-repo` |
| Antigravity エージェントのワーカー | `cx·worker of antigravity · my-repo` |
| バックグラウンドのコマンド、モニター、ツール呼び出し | キャラクターなし |

接頭辞はプロバイダー（`cc` Claude Code、`cx` Codex、`oc` OpenCode、`ag` Antigravity）、プロジェクトは Orca のワークスペースのフォルダーです。机には名前の先頭の数文字だけが出ます。キャラクターにポインターを合わせるか `Tab` を押すと、名前全体、親、現在のツールが見えます。

Pixtuoid v0.23.0 と Orca 1.4.266 で（注記した項目は 1.4.263 で）ライブで確認済みです。4 つのプロバイダーはすべて、記録した Orca の応答を使い本物の Pixtuoid に対しても確認しています。

| プロバイダー | エージェント | ワーカー | ネイティブのサブエージェント |
|---|---|---|---|
| Claude Code | 対応 | 対応 | 対応 |
| Codex | 対応 (1.4.263) | 対応 | 未確認 |
| OpenCode | 対応 (1.4.263) | 対応 (1.4.263) | 未確認 |
| Antigravity | 対応 (1.4.263) | 対応 | Orca の報告なし |

## 必要環境

- DirectX 12 対応の Windows x64
- `py` ランチャー付きの Python 3.11 以降（64 ビット）
- 起動中の Orca 1.4.263 以降と、対応エージェント 1 つ以上。1.4.266 まで確認済みです。より新しい Orca では一度だけ通知が出ますが、そのまま動くはずです。
- Claude Code、Codex、Antigravity のソースには、それぞれ `claude`、`codex`、`agy` が `PATH` に必要

## クイックインストール

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py
py -3 -m unittest -v test_oficina test_instalar
```

`instalar.py` は Pixtuoid v0.23.0 をクローン内にダウンロードし、SHA-256 を検証して、Orca が報告するエージェントを接続します。ソースを絞るには `py -3 instalar.py --sources claude-code codex`。

**自分のビルド。** オフィスを閉じた状態で `py -3 instalar.py --local C:\path\to\pixtuoid\target\release` を実行すると、ローカルビルドの `pixtuoid.exe` と `pixtuoid-hook.exe`、およびその隣かリポジトリのルートにある `LICENSE` をインストールします。`py -3 instalar.py --url https://... --sha256 <64 桁の16進数>` は、Pixtuoid の Windows 用 zip と同じ構成で自分が公開した zip をインストールします。SHA-256 は必須です。`app/origen.json` がインストール内容を記録します。後でオプションなしの `py -3 instalar.py` を実行しても自分のビルドは保持され、その旨が表示されます。`py -3 instalar.py --pinned` で v0.23.0 に戻ります。

**更新。** このリポジトリの毎日のワークフローが Pixtuoid の新しい安定版を探し、SHA-256 を検証し、テストを実行して、新しいバージョン固定をレビュー用に提案します。自動でマージすることはありません。更新を取り込んだら、オフィスを閉じて `py -3 instalar.py` をもう一度実行します。

Orca プラグイン（v2.0.0）は一時停止中です。インストールしてオフィスを開くことはできますが、上記の機能はありません。クローンを使ってください。

## オフィスを開く

**`Abrir oficina.lnk`** をダブルクリックします。閉じるには `Q` を押すか、`py -3 oficina.py --stop` を実行します。

ウィンドウは Orca の外に浮かぶので、2 台目のモニターに置いておけます。1 つのフォルダーで動くオフィスは 1 つだけです。起動するものはすべて通常より低い優先度で動き、Orca は 1 サイクルにつき CLI 呼び出し 1 回で読むので、PC の作業が優先されます。`py -3 oficina.py --evidence` は状態を `actividad/` に記録します。

## 操作

| 操作 | 入力 |
|---|---|
| 移動 | 空いている所をドラッグ |
| サイズ変更 | 右下の角をドラッグ |
| ズーム | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| エージェントのツリー | `Tab` |
| エージェントの名前、親、フォルダー、ツール | ポインターを合わせる |
| ヘルプ · 一時停止 · テーマ | `?` · `P` · `T` |
| 閉じてサイズと位置を保存 | `Q`、または `py -3 oficina.py --stop` |

## 表示される状態

| Orca の状態 | オフィスでの表示 |
|---|---|
| `working` | 机で作業中。Orca が報告するツール（`Bash`、`Edit`、`shell` など）をモニター、ツールチップ、フッターの集計に表示 |
| `waiting` / `blocked` | 許可を求めている（`!`）。「対応が必要」として数えられる |
| `done` / `idle` | 休憩中または歩き回っている |
| セッション終了、サブエージェントの完了やキャンセル | ドアから退出。子が先に退出 |

## 制限事項

- Pixtuoid は、同じプロバイダーの親にしか子を結び付けられません。別のプロバイダーのワーカーは親の接頭辞と色で親の下に置かれ、名前に自分のプロバイダーが入ります（`cx·claude worker`）。Claude Code のツリーでは接頭辞もワーカー自身のものになります。
- Pixtuoid は最上位の Antigravity エージェントの下に子を描けません。そのワーカーは `worker of antigravity` という名前の別の同僚として表示されます。
- 役割は、エージェントが最初に現れたときに Orca が示すものです。後からワーカーを起動し始めたエージェントは名前が変わりませんが、そのワーカーは下に表示されます。
- Orca が報告するのはツール名だけで、モデル、エフォート、トークン使用量は報告しないため、オフィスにモデル、エフォート、トークンメーターは表示されません。ツールの入力は一切読まないので、横にファイルやコマンドは表示されません。
- キャラクターをクリックしても、そのターミナルにはフォーカスしません。Orca はエージェントのプロセスを公開しておらず、Windows での Pixtuoid のフォーカスは自身の Antigravity 連携にしか対応していないためです。
- オフィスは Orca の読み取りの間に 1.5〜10 秒待ち、PC や Orca が忙しいときはさらに長く待つため、ごく短いターンやツールは見逃すことがあります。Orca が忙しいあいだ、新しい子が一瞬表示されてから親の下へ移ることがあります。
- 表示されるのは Orca 自身が観測するサブエージェントだけです。オフィスを開いた時点で終了していたエージェントは表示されません。
- ローカルの Orca ホストのみです。リモートの Orca 環境は無視されます。

## プライバシー

- オフィスが `orca worktree ps`（予備として `orca agent list`）から読むのは、ID、親のリンク、プロバイダー、サブエージェントの種類、状態、ツール名、ワークスペースのフォルダーだけです。プロンプト、応答、ツールの入力は転送も保存もしません。
- アダプターのネットワークアクセスは、固定した Pixtuoid リリースの GitHub からのダウンロードだけです。
- アプリ、分離したエージェントプロファイル、ログはクローン内（`app/`、`perfil/`、`actividad/`）に残ります。ワーカーのプロバイダーを表示するため、オフィスは分離プロファイルに 1 行のカード（名前とフォルダー）を書き、ワーカーが退出するかオフィスが閉じると削除します。
- エージェントと Orca のグローバル設定は変更しません。

## アンインストール

オフィスを閉じて、クローンのフォルダーを削除します。ほかには何もインストールされません。一時停止中のプラグインをインストールした場合は、**Pixtuoid: Remove downloaded app and local data** を実行してから、Orca の Settings → Plugins でアンインストールします。

## クレジットとライセンス

- このアダプター：[MIT ライセンス](LICENSE)。
- [Pixtuoid](https://github.com/pixtuoid/pixtuoid)（Ivan Wang 作、MIT ライセンス）。インストール時にダウンロードし、再配布はしません。
- 国旗アイコン：[lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3、[MIT ライセンス](docs/flags/LICENSE)。
- Orca は別製品で、含まれていません。これは独立したアダプターであり、Pixtuoid や Orca の公式プロジェクトではありません。
