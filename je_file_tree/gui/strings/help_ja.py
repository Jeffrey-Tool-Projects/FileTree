"""The how-to-use text in Japanese; ``{key}`` stands for the label ``key`` shows in the window."""

from __future__ import annotations

from je_file_tree.gui.strings.joining import cjk

HELP = cjk("""
<h2>3 つのステップで使えます</h2>
<ol>
<li><b>スキャンする場所を選びます。</b><i>{action_open}</i>かドライブをクリックするか、フォルダーをウィンドウ
にドラッグします。
上の欄にパスを入力して Enter を押しても始められます。</li>
<li><b>集計しながら表示します。</b>フォルダーツリーはすぐに表示され、集計が進むにつれて大きいフォルダーが上に
並びます。
<i>{action_stop}</i>（Esc）はいつでも押せます。そこまでに読み取った分は、不完全と表示されて残ります。</li>
<li><b>容量を使っているものを見つけます。</b>大きいフォルダーほど上にあります。横の矢印をクリックすると中身が
見られます。</li>
</ol>
<h2>結果の見方</h2>
<ul>
<li><b>フォルダーツリー</b>：フォルダーやファイルのサイズ、実際に使っているディスク容量
（<i>{column_allocated}</i>）、
上のフォルダーに占める割合（<i>{column_share}</i>）、含まれるファイル数とフォルダー数、最後に変更された日時で
す。
列の見出しをクリックすると並べ替えられます。ツリーの下の<i>{details_title}</i>で、選択した項目を詳しく確認でき
ます。</li>
<li><b>{highlights_title}</b>：大きいフォルダーとファイル、整理できそうな項目です。</li>
<li><b>{tab_chart}</b>：同じフォルダーを 4 通りに表示します。<i>{chart_treemap}</i>はファイルを四角形で表し、
大きいファイルほど大きく描きます。
<i>{chart_bars}</i>は項目ごとに 1 本の棒で、正確に比べやすい表示です。<i>{chart_sunburst}</i>はフォルダーを中
央に置き、
外側の輪ほど深い階層です。<i>{chart_tree}</i>は展開できるフォルダーのカードで、Ctrl+ホイールで拡大縮小できます。
クリックするとツリー内の位置を表示し、ダブルクリックでフォルダーに入り、<i>{trend_up}</i>で戻ります。</li>
<li><b>{tab_largest}</b>：大きい順に 1,000 個のファイルです。<i>{column_advice}</i>は、整理できる、先に確認が
必要、自分で判断、
削除しない、のどれに当たるかを示します。</li>
<li><b>{tab_search}</b>（Ctrl+F）：名前、サイズ、日時、種類でファイルとフォルダーを探しま
す。<code>*.mp4</code> のようなパターンは
名前全体と一致する必要があり、複数のパターンは <code>;</code> で区切ります。<i>{search_save}</i>で検索に名前を
付けて保存できます。</li>
<li><b>{tab_cleanup}</b>：<i>{cleanup_suggestions}</i>は、通常は削除してよい場所を理由とリスクとともに表示しま
す。
<i>{tab_duplicates}</i>は内容が同じファイルを探します。残すコピーを選んでか
ら<i>{duplicates_select_extra}</i>を押します。</li>
<li><b>{tab_types}</b>と<b>{tab_age}</b>：ファイルの種類別、最後に変更された時期別の容量です。行をダブルクリッ
クすると、
その中の大きいファイルを表示します。</li>
<li><b>{tab_problems}</b>：読み取る権限がなかったフォルダーです。中身は集計に含まれません。</li>
</ul>
<h2>空き容量を増やす</h2>
<ul>
<li><b>{action_trash}</b>（Delete）は必ず確認し、移動したものは元に戻せます。システムやプログラムのフォルダー
は 2 回確認します。
容量が空くのは、ごみ箱を空にした後です。</li>
<li><b>{permanent_delete}</b>（Shift+Delete）はごみ箱を使わず、元に戻せません。毎回確認し、承認した項目だけを
削除します。
スキャン後に変更された項目は残します。何を削除するかを FileTree が決めることはありません。</li>
<li><b>{menu_file} → {reclaim_action}</b>：必要な容量を指定すると、安全な順に手順を表示します。自動で選択され
るものはありません。</li>
<li>Ctrl+クリックや Shift+クリックで複数の項目を選べます。項目を右クリックすると、開く、ファイルマネージャーで
表示、パスのコピー、
移動、名前の変更、<i>{menu_rescan_here}</i>などができます。</li>
<li>移動や削除の後、数値は再スキャンせずに更新されます。FileTree がスキャンするのは、指示したときだけです。</li>
</ul>
<h2>変化を追う</h2>
<ul>
<li><b>{menu_file} → {action_compare}</b>：<i>{menu_export} → {action_export_json}</i>でスキャンを保存してお
き、後のスキャンと比較します。
<b>{tab_changes}</b>タブに、増えたフォルダーと減ったフォルダーが表示されます。</li>
<li><b>{action_history}</b>：フォルダーの容量の推移です。</li>
<li><b>{action_folder_budgets}</b>：フォルダーの上限を決め、超過した量を確認できます。</li>
<li><b>{menu_options} → {action_follow_changes}</b>：変更されたフォルダーを自動で読み直します。</li>
</ul>
<h2>ドライブ</h2>
<ul>
<li><b>{menu_view} → {action_volumes}</b>：各ドライブの容量と、いっぱいになる時期の予測です。</li>
<li><b>{action_disks}</b>：物理ディスクの種類、状態、温度、パーティションです。表示だけで変更はしません。</li>
<li><b>{action_bins}</b>：ごみ箱の内容量です。空にする前に 2 回確認します。</li>
</ul>
<h2>キーボード ショートカット</h2>
<table cellpadding="3">
<tr><td><b>Ctrl+O</b></td><td>フォルダーを選ぶ</td></tr>
<tr><td><b>F5</b></td><td>再スキャン</td></tr>
<tr><td><b>Esc</b></td><td>スキャンを停止</td></tr>
<tr><td><b>Ctrl+F</b></td><td>検索</td></tr>
<tr><td><b>Ctrl+T / Ctrl+W</b></td><td>スキャンタブを開く / 閉じる</td></tr>
<tr><td><b>Alt+← / Alt+→</b></td><td>チャートで戻る / 進む</td></tr>
<tr><td><b>Ctrl+P</b></td><td>現在の表示を印刷</td></tr>
<tr><td><b>Delete</b></td><td>選択した項目をごみ箱に移動</td></tr>
<tr><td><b>Shift+Delete</b></td><td>選択した項目を完全に削除</td></tr>
<tr><td><b>Ctrl++ / Ctrl+−</b></td><td>文字を大きく / 小さく</td></tr>
<tr><td><b>Ctrl+0</b></td><td>文字をシステムのサイズに戻す</td></tr>
<tr><td><b>Ctrl+,</b></td><td>設定</td></tr>
<tr><td><b>F1</b></td><td>このガイド</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>終了</td></tr>
</table>
<p>macOS では Ctrl の代わりに ⌘ を使います（再スキャンは ⌘R）。</p>
<h2>知っておくと便利なこと</h2>
<ul>
<li>サイズは 2 進単位（1 KB = 1,024 バイト）で、エクスプローラーと同じです。<i>{menu_view} → {menu_unit}</i>で
単位を固定できます。</li>
<li>文字が小さすぎる、または大きすぎるときは<i>{menu_view} → {menu_text_size}</i>、ライトとダークの切り替え
は<i>{menu_view} → {menu_theme}</i>を使います。</li>
<li>ショートカットとリンクは表示しますが、たどりません。二重に数えることはありません。</li>
<li>Windows では、保護されたフォルダーも読み取れるように、起動時に管理者権限を求めます。断っても通常どおり動作
し、
読み取れなかったフォルダーは<i>{tab_problems}</i>に表示されます。確認が不要な
ら<i>{menu_view} → {action_ask_admin}</i>をオフにします。</li>
<li><i>{scope_folder}</i>を押すと、<i>{tab_largest}</i>、<i>{tab_types}</i>、<i>{tab_age}</i>がツリーで選択し
たフォルダーだけを対象にします。</li>
<li>隠しファイルも数えます。除くには<i>{menu_view} → {action_hidden}</i>をオフにします。いつもスキャンしないフ
ォルダーは
<i>{menu_view} → {action_exclusions}</i>に登録します。</li>
<li>結果は<i>{menu_file} → {menu_export}</i>で CSV、JSON、Excel、HTML、PDF、画像として保存できます。</li>
</ul>
""")
