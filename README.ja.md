<p align="center">
  <a href="README.md"><img src="docs/flags/gb.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.md">English</a> &nbsp;·&nbsp;
  <a href="README.es.md"><img src="docs/flags/py.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.es.md">Español</a> &nbsp;·&nbsp;
  <a href="README.de.md"><img src="docs/flags/de.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.de.md">Deutsch</a> &nbsp;·&nbsp;
  <a href="README.ja.md"><img src="docs/flags/jp.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ja.md"><b>日本語</b></a> &nbsp;·&nbsp;
  <a href="README.zh.md"><img src="docs/flags/cn.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.zh.md">中文</a> &nbsp;·&nbsp;
  <a href="README.ru.md"><img src="docs/flags/ru.svg" width="20" height="15" alt=""></a>&nbsp;<a href="README.ru.md">Русский</a>
</p>

# Pixtuoid para Orca

Windows 用の Orca プラグインです。フローティングのピクセルアートのウィンドウを開き、ローカルの Orca エージェント、そのワーカー、サブエージェントを、プロバイダー・役割・プロジェクトの名札付きのキャラクターとして表示します。ウィンドウに何を表示するかを選べます。

- **公式のオフィス**（`oficina`、既定）：Ivan Wang による [Pixtuoid](https://github.com/pixtuoid/pixtuoid) v0.23.0 をそのまま使います。
- **Dungeons & Agents**（`dungeon`）：Pixtuoid のファンタジー MOD である [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents)。オフィスはキャンプとダンジョンの階になり、各エージェントは役割をクラスで示す冒険者になります。冒険者をクリックすると、その Orca のセッションが開きます。

![デモ用ワークスペース：Codex・Antigravity・Claude Code のワーカーと Explore サブエージェントを持つ 2 つのオーケストレーター](docs/office-roles.png)

## 各モードの機能

| 機能 | 公式のオフィス | Dungeons & Agents |
|---|---|---|
| エージェント、ワーカー、サブエージェントをプロバイダー・役割・プロジェクト付きのキャラクターで表示 | 対応 | 対応 |
| エージェントが対応を求めたときの通知とステータスバーの件数 | 対応 | 対応 |
| Orca のパレットのコマンド、Orca からのインストールと更新 | 対応 | 対応 |
| 短い間隔のタイマーではなく、Orca がエージェントの変化を報告したときに Orca を読み取る | 対応 | 対応 |
| チームの色 | プロジェクトごと | パーティーごと：オーケストレーターとそのワーカー、サブエージェント |
| 役割（companion、orchestrator、worker、subagent）を示すクラス | なし | 対応 |
| ツールをスキル（`Spell (Bash)`、`Scry (Grep)` など）として表示し、Orca CLI の呼び出しを `Sending (Orca)` と表示 | なし（ツール名 `Orca` で表示） | 対応 |
| エージェントをクリック、または `Tab` のツリーで `Enter` して Orca のセッションを開く | なし | 対応 |

## 必要環境

- DirectX 12 対応の Windows x64
- `py` ランチャー付きの Python 3.11 以降（64 ビット）
- 対応エージェントを 1 つ以上インストールした Orca 1.4.265 以降。確認済みより新しい Orca では一度だけ通知が出ますが、そのまま動作するはずです。
- Claude Code、Codex、Antigravity のソースには `PATH` 上の `claude`、`codex`、`agy`

## Orca からインストール

1. Orca で **Settings → Plugins** を開き、**From a Git URL…** を選んで `https://github.com/icaceresc/pixtuoid-orca-windows` を入力します。または `orca plugin install icaceresc/pixtuoid-orca-windows` を実行します。インストール前に、プラグインが求めるアクセス（下記）が表示されます。
2. コマンドパレットで、公式のオフィスなら **Pixtuoid: Install or update the office app**、Dungeons & Agents なら **Pixtuoid: Use Dungeons & Agents** を実行します。ビルドをダウンロードし、固定された SHA-256 を確認し、Orca が報告するエージェントを接続します。
3. **Pixtuoid: Open office window** を実行するか、Orca のステータスバーの **Pixtuoid** をクリックします。

| コマンド | 内容 |
|---|---|
| Pixtuoid: Open office window | ウィンドウを開きます。同時に開けるのは 1 つだけです |
| Pixtuoid: Close office window | サイズと位置を保存して閉じます |
| Pixtuoid: Install or update the office app | 最後に選んだモードのビルドをインストールまたは更新します |
| Pixtuoid: Use the official Pixtuoid office | 公式のオフィスに切り替えます |
| Pixtuoid: Use Dungeons & Agents | Dungeons & Agents に切り替えます |
| Pixtuoid: Remove downloaded app and local data | アプリ、隔離したエージェントのプロファイル、ログを削除します |

| プラグインが求めるアクセス | 理由 |
|---|---|
| `agent:read` | エージェントの状態の変化を知るため。そのときにオフィスが Orca を読み取り、通知とステータスバーの件数もそれに従います |
| `workspace:read` | クリックしたエージェントのワークスペースをフォルダーから探すため |
| `workspace:write` | そのエージェントのセッションを前面に出すため |
| `notifications:show` | エージェントが対応を求めていることを知らせるため |

**更新。** プラグインは Orca が更新します（**Settings → Plugins**、または `orca plugin update icaceresc.pixtuoid-office`）。**Pixtuoid: Install or update the office app** は、オフィスのアプリをそのモードでプラグインが固定するビルドに更新し、開いていたウィンドウを再び開きます。このリポジトリの毎日のワークフローが Pixtuoid の新しい安定版を探し、SHA-256 を確認し、テストを実行して、新しい固定をレビュー用に提案します。自動でマージすることはありません。

## 表示内容

Orca がこのマシンで識別するエージェントごとに 1 人のキャラクターです。子はチームの色を身に着け、親と一緒に退出します。`Tab` でエージェントのツリーを表示します。

![エージェントのツリー：各オーケストレーターとそのワーカー、サブエージェント、ツールと状態](docs/office-dashboard.png)

| Orca での種類 | オフィスでの名前 |
|---|---|
| Orca ボット自身のセッション（Strategic Companion） | `cc·punky · companion` |
| 最上位のエージェント | `cc·my-repo · agent` |
| ワーカーを起動するエージェント（ワーカー自身も含む） | `cc·my-repo · orchestrator` |
| オーケストレーションのワーカー（どの深さでも） | `cx·worker · my-repo` |
| 親と異なるプロバイダーのワーカー | `cx·claude worker · my-repo` |
| Orca がセッション内で観測するサブエージェント | `cc·Explore subagent · my-repo` |
| Antigravity エージェントのワーカー | `cx·worker of antigravity · my-repo` |
| バックグラウンドのコマンド、モニター、ツール呼び出し | キャラクターなし |

接頭辞はプロバイダー（`cc` Claude Code、`cx` Codex、`oc` OpenCode、`ag` Antigravity）、プロジェクトは Orca のワークスペースのフォルダーです。机には名前の先頭の数文字だけが出ます。キャラクターにポインターを合わせるか `Tab` を押すと、名前全体、親、現在のツールが見えます。

| プロバイダー | エージェント | ワーカー | ネイティブのサブエージェント |
|---|---|---|---|
| Claude Code | 対応 | 対応 | 対応 |
| Codex | 対応 (1.4.263) | 対応 | 未確認 |
| OpenCode | 対応 (1.4.263) | 対応 (1.4.263) | 未確認 |
| Antigravity | 対応 (1.4.263) | 対応 | Orca の報告なし |

Orca 1.4.265 と 1.4.266 で（注記した項目は 1.4.263 で）ライブで確認済みです。4 つのプロバイダーはすべて、記録した Orca の応答を使い本物の Pixtuoid に対しても確認しています。

## 操作

| 操作 | 入力 |
|---|---|
| 移動 | 空いている所をドラッグ |
| サイズ変更 | 右下の角をドラッグ |
| ズーム | `Ctrl` `+` / `Ctrl` `-` / `Ctrl` `0` |
| エージェントのツリー | `Tab` |
| エージェントの名前、親、フォルダー、ツール | ポインターを合わせる |
| エージェントのセッションを Orca で開く（Dungeons & Agents） | クリック、または `Tab` のツリーで `Enter` |
| ヘルプ · 一時停止 · テーマ | `?` · `P` · `T` |
| 閉じてサイズと位置を保存 | `Q`、または **Pixtuoid: Close office window** |

## 表示される状態

| Orca の状態 | オフィスでの表示 |
|---|---|
| `working` | 机で作業中。Orca が報告するツール（`Bash`、`Edit`、`shell` など）をモニター、ツールチップ、フッターの集計に表示 |
| `waiting` / `blocked` | 許可を求めている（`!`）。「対応が必要」として数えられ、オフィスが開いている間はデスクトップ通知で知らせ、Orca のステータスバーにも件数が出ます |
| `done` / `idle` | 休憩中または歩き回っている |
| セッション終了、サブエージェントの完了やキャンセル | ドアから退出。子が先に退出 |

## 制限事項

- **エージェントのクリック**でセッションが開くのは Dungeons & Agents だけです。ターミナルのエージェントはそのペインにフォーカスします。Orca のチャットにはターミナルがないため、そのワークスペースを表示します。1 つのワークスペースに複数のチャットがある場合（ボットのホームなど）、Orca が表示するのはそこで最後に開いていたチャットで、クリックしたものとは限りません。サブエージェントは、それが動いているセッションを開きます。
- Pixtuoid は、同じプロバイダーの親にしか子を結び付けられません。別のプロバイダーのワーカーは親の接頭辞で親の下に置かれ、名前に自分のプロバイダーが入ります（`cx·claude worker`）。Claude Code のツリーでは接頭辞もワーカー自身のものになります。
- Pixtuoid は最上位の Antigravity エージェントの下に子を描けません。そのワーカーは `worker of antigravity` という名前の別の同僚として表示されます。
- Pixtuoid は同僚が最初に現れたときの名前を保持します。そのため、後からワーカーを起動し始めたエージェントは一度退出し、orchestrator として戻ってきます。役割が取り消されることはありません。
- Orca が報告するのはツール名だけで、モデル、エフォート、トークン使用量は報告しないため、オフィスにモデル、エフォート、トークンメーターは表示されません。
- プラグインから開いたオフィスは、Orca がエージェントの変化を報告するとすぐに Orca を読み取ります。それ以外は、作業中のエージェントがいれば 6 秒ごと、いなければ 30 秒ごとに読み取るため、サブエージェントの表示がその分遅れたり、ごく短いツールを見逃したりすることがあります。クローンから実行した場合は 1.5〜10 秒ごとに読み取ります。
- 通知とステータスバーの件数は、プラグインの起動後に Orca が報告した状態の変化に従います。
- 表示されるのは Orca 自身が観測するサブエージェントだけです。オフィスを開いた時点で終了していたエージェントは表示されません。
- ローカルの Orca ホストのみです。リモートの Orca 環境は無視されます。

## プライバシー

- オフィスが `orca worktree ps`（予備として `orca agent list`）から読み取るのは、ID、親とのリンク、プロバイダー、サブエージェントの種類、状態、ツール名、ワークスペースのフォルダー、そのワークスペースがボットのホームかどうかだけです。シェルのツールのコマンドは、Orca CLI を実行しているかを判断するためだけに見ます。プロンプト、応答、ツールの入力が転送・保存されることはありません。
- プラグインは動作中、各エージェントの状態と、そのペイン、ターミナル、ワークスペースの ID をメモリーに保持します。通知には Orca のセッションのタイトルを、このコンピューター上でだけ表示します。
- アダプターのネットワークアクセスは、固定されたビルドを GitHub からダウンロードすることだけです。
- アプリ、隔離したエージェントのプロファイル、ログは `%LOCALAPPDATA%\PixtuoidOrca` に置かれます（クローンから実行した場合はクローン内）。ワーカーのプロバイダーを名前に出すため、オフィスは 1 行のカード（名前とフォルダー）を隔離したプロファイルに書き、ワーカーが退出するかオフィスを閉じると削除します。クリックすると、クリックしたセッションの ID をそこに書き、プラグインが読み取ります。
- エージェントと Orca のグローバル設定は変更しません。

## クローンから実行

サポートしている方法はプラグインです。アダプターの開発や自分のビルドのインストールには、次のようにします。

```powershell
git clone https://github.com/icaceresc/pixtuoid-orca-windows.git
cd pixtuoid-orca-windows
py -3 instalar.py                     # 公式のオフィス。Dungeons & Agents は --modo dungeon
py -3 -m unittest -v test_oficina test_instalar
```

オフィスは **`Abrir oficina.lnk`** で開き、`Q` か `py -3 oficina.py --stop` で閉じます。エージェントのクリックにはプラグインが必要です。ソースを絞るには `py -3 instalar.py --sources claude-code codex`。

**自分のビルド。** オフィスを閉じた状態で `py -3 instalar.py --modo dungeon --local C:\path\to\dungeons-and-agents\target\release` を実行すると、ローカルビルドの `pixtuoid.exe` と `pixtuoid-hook.exe`、およびその横かリポジトリのルートにある `LICENSE` をインストールします。`--url https://... --sha256 <64 桁の16進数>` は、Pixtuoid の Windows 版 zip と同じ構成の zip をインストールします。`app/origen.json` にはインストールした内容とモードが記録されます。その後の通常の実行は自分のビルドを残してその旨を表示し、`--pinned` はそのモードの固定ビルドに戻し、`--modo` はモードを切り替えます。プラグインのコマンドは `%LOCALAPPDATA%\PixtuoidOrca` で同じことを行います。

## アンインストール

**Pixtuoid: Remove downloaded app and local data** を実行してから、**Settings → Plugins** でプラグインをアンインストールします。クローンはフォルダーを削除するだけです。

## クレジットとライセンス

- このプラグイン：[MIT ライセンス](LICENSE)。
- Ivan Wang による [Pixtuoid](https://github.com/pixtuoid/pixtuoid)、MIT ライセンス。インストール時にダウンロードし、再配布はしません。
- Pixtuoid の MOD である [Dungeons & Agents](https://github.com/icaceresc/dungeons-and-agents)、MIT ライセンス。インストール時にダウンロードし、再配布はしません。
- 国旗アイコン：[lipis/flag-icons](https://github.com/lipis/flag-icons) v7.2.3、[MIT ライセンス](docs/flags/LICENSE)。
- Orca は別の製品で、含まれていません。これは独立したプラグインで、Pixtuoid や Orca の公式プロジェクトではありません。
