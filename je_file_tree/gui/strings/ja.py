"""Every text the window shows in Japanese; see ``je_file_tree.gui.i18n``."""

from __future__ import annotations

from je_file_tree.gui.strings.help_ja import HELP

_JA_FOLDER = "フォルダー"


JA: dict[str, str] = {
    "busy_scanning": ("スキャン中のため「{action}」は実行できません。"
        "スキャンの完了を待つか、先にスキャンを停止してください（Esc）。"),
    "busy_operation": ("別のファイル操作が実行中のため「{action}」は実行できません。"
        "操作の完了後にもう一度お試しください。"),
    "budget_filter": "予算を表示",
    "budget_filter_all": "すべての予算",
    "budget_filter_over": "上限超過",
    "budget_filter_unknown": "不明または未スキャン",
    "budget_filter_empty": "この条件に一致する予算はありません。「すべての予算」で全ルールを表示します。",
    "budget_editing_hidden": "編集中の「{name}」はこの条件では非表示です。状態：{status}。入力内容は保持されています。",
    "budget_count_over": "上限超過 {count} 件",
    "budget_count_unknown": "不明 {count} 件",
    "folder_context_target": "対象フォルダー",
    "folder_context_ready": "ファイルを選択した場合、その親フォルダーが対象です。",
    "folder_context_history": "増加の推移を見る",
    "folder_context_budget": "フォルダー予算を設定",
    "folder_context_empty": "スキャンを完了するとフォルダー操作を使用できます。",
    "folder_context_busy": "スキャンまたは現在の操作が終わるまでお待ちください。",
    "folder_context_closing": "このスキャンタブを閉じています。",
    "folder_context_virtual": "個別のソースをスキャンしてフォルダー操作を使用してください。",
    "folder_context_stale": "現在のスキャン内のフォルダーを選択してください。",
    "folder_context_link": "リンクにはフォルダー操作を使用できません。",
    "trend_choose_folder": "読み込み済みフォルダー…",
    "trend_loaded_folders": "読み込み済みの子フォルダー",
    "trend_full_path": "フォルダーのフルパス",
    "trend_root": "ルートに戻る",
    "trend_up": "上へ",
    "trend_enter": "フォルダーを開く",
    "trend_previous": "前のページ",
    "trend_next": "次のページ",
    "trend_choose_current": "このフォルダーを選択",
    "trend_folder_page": "{total} 件中 {first}–{last} 件。読み込み済みのフォルダーのみ。",
    "trend_period": "期間",
    "trend_period_all": "保存された全履歴",
    "trend_period_30": "過去 30 日",
    "trend_period_90": "過去 90 日",
    "trend_period_custom": "日付を指定",
    "trend_date_order": "終了日は開始日以降にしてください。",
    "trend_point_details": "選択した観測の詳細",
    "trend_select_point": "グラフまたは表で観測を選択。矢印キーで各観測に移動できます。",
    "trend_size_reason": "サイズ不明: {reason}",
    "trend_change_reason": "変化不明: {reason}",
    "trend_first_point": "この期間に前の観測がありません",
    "trend_point_value": "{date} · サイズ {size} ({exact_size}) · 変化 {change} ({exact_change})",
    "templates_select": "保存済みテンプレートを選択",
    "templates_remove": "テンプレートを削除",
    "templates_save_section": "開いた時点のワークスペースを保存",
    "templates_save_source": (
        "追加と更新は、この画面を開いた時点のタブと設定を保存します。"
        "下のプレビューの変更は保存しません。"),
    "templates_add_current": "開始時のタブを追加",
    "templates_update_current": "開始時のタブで更新",
    "templates_preview_hint": (
        '読み込みプレビュー · パスの変更は今回の読み込みだけに適用します。確認後に'
        '置換し、開始を押すとスキャンします。'),
    "templates_preview_modified": "今回の読み込みだけ変更済み · 置換する前にパスを再確認してください。",
    "templates_active": "選択中",
    "templates_scanning": "スキャン中",
    "templates_impact": (
        '置換でタブ {tabs} 個を閉じ、スキャン {scans} 件を停止し、結'
        '果 {results} 件を閉じます。利用できないプレビューパス：{unav'
        'ailable}。'),
    "templates_saved": '保存済みテンプレート',
    'workspace_templates': 'ワークスペースのテンプレート…',
    'templates_tab': 'タブ',
    'templates_kind': '範囲',
    'templates_status': '利用状況',
    'templates_single': '単一フォルダー',
    'templates_check': 'パスを確認',
    'templates_replace': 'タブを置換',
    'templates_hint': (
        '現在のタブを保存するか、テンプレートを選んで確認します。パスを編集し、確認し'
        'てからタブを置換してください。置換すると既存のスキャンと結果が閉じられます。'
        '読み込み後は開始を押すまでスキャンしません。利用できないパスも保持されます。'
        'ここで修正して再確認できます。追加と更新は現在のワークスペースを保存します。'),
    'templates_invalid': (
        'テンプレートが無効です。一意の名前と絶対パスを使用してください。既存の設定は'
        '変更していません。'),
    'templates_unchecked': '未確認',
    'templates_checking': 'すべてのパスを確認中…',
    'templates_ready': '利用可能',
    'templates_checked': (
        '確認が完了しました。利用できないパスも含めて読み込みます。エラーがあるタブで'
        'は開始できません。'),
    'templates_not_folder': 'フォルダーではありません',
    "completion_title": '前回の整理結果',
    "completion_undo": '可能な移動を元に戻す',
    "completion_rescan": '元のフォルダーを再スキャン',
    "completion_dismiss": '概要を閉じる',
    "completion_source": '対象: {path}',
    "completion_counts": (
        '移動: {moved}（{size}）、除外: {skipp'
        'ed}、失敗: {failed}'
    ),
    "completion_space": (
        'スキャン間の空き容量変化: {change}（他の操作を含む'
        '）'
    ),
    "completion_measurements": 'スキャン観測時刻: {before} → {after}',
    "completion_space_pending": (
        '比較できる後続の観測はまだありません。不明はゼロではありませ'
        'ん。'
    ),
    "completion_reason": '{reason}: {count}',
    "completion_more": 'すべての理由は操作履歴で確認できます。',
    "completion_errors": (
        '履歴エラー: {journal}、コピー終了処理エラー: {'
        'copies}。'
    ),
    "completion_hint": (
        '移動量は論理データ量で、解放された容量ではありません。ごみ箱'
        'を空にする操作は別途必要です。詳細は操作履歴と失敗レポートを'
        'ご覧ください。'
    ),
    "action_scan_presets_tip": "名前付きのパスと設定を保存・読み込みます。スキャンは開始しません",
    "action_scan_presets": 'スキャン設定…',
    "presets_empty": '保存済み設定はありません',
    "presets_hint": (
        '追加・更新は現在のスキャン設定と入力パスを保存します。読み込み後、「パスをスキャ'
        'ン」で開始します。並列数と除外はワークスペース共通です。'
    ),
    "presets_saved": '保存済み設定',
    "presets_name": '名前',
    "presets_add": '現在の設定を追加',
    "presets_update": '選択を更新',
    "presets_rename": '名前を変更',
    "presets_remove": '設定を削除',
    "presets_load": '読み込む',
    "presets_options": 'ワーカー: {workers}、除外: {exclusions}、有効: {flags}',
    "presets_no_flags": 'なし',
    "presets_invalid": (
        '重複しない名前（1～80 文字）、絶対パス、有効なスキャン設定を指定してください'
        '。最大 32 件です。'
    ),
    "presets_read_failed": '保存済み設定を読み取れません。既存データは保持しました。',
    "presets_loaded": '{name} を読み込みました。「パスをスキャン」で開始してください。',
    "highlights_title": 'スキャンの要点',
    "highlights_waiting": 'スキャン分析を待機中…',
    "highlights_folders": '直下の大きいフォルダーを選んで表示します。',
    "highlights_partial": '不完全な結果：サイズは読み取れた項目のみです。',
    "highlights_folder": '{name} — {size}',
    "highlights_cleanup_waiting": '整理：分析を待機中…',
    "highlights_cleanup": '候補 {count} 件を確認（{size}）',
    "highlights_cleanup_hint": '候補の容量は確認が必要で、すぐに空く容量ではありません。',
    "highlights_coverage_unknown": 'スキャン範囲はまだ不明です',
    "highlights_coverage": 'スキャン制限：除外 {skipped}、読取不可 {denied}、未読 {pending}',
    "column_advice": '削除の目安',
    "advice_low": '整理できる',
    "advice_review": '要確認',
    "advice_personal": '自分で判断',
    "advice_protected": '削除しない',
    "advice_managed": 'システム管理',
    "advice_pending": '分析中…',
    "advice_low_tip": (
        'リスクが低い整理候補です。プログラムがこのデータを再作成できます。移動する前に確認し'
        'てください。'
    ),
    "advice_review_tip": '確認が必要な整理候補です。まだ必要なものが含まれていないか確かめてください。',
    "advice_personal_tip": (
        'この項目に当てはまるルールはありません。必要かどうかはご自身で判断してください。確認'
        'なしに移動することはありません。'
    ),
    "advice_protected_tip": (
        '残してください：{reason}。削除するとシステムやインストール済みのプログラムが動かなく'
        'なることがあります。'
    ),
    "advice_managed_tip": (
        'この領域はオペレーティングシステムが管理しており、FileTree は移動しません。使用する'
        'システムツールは「詳細」に表示されます。'
    ),
    "advice_pending_tip": '整理の分析を実行中です。',
    "advice_summary": '{label} — {reason}',
    "advice_legend_tip": (
        'このスキャンの整理ルールと、このコンピューターの保護された場所に基づく目安です。参考'
        '情報であり、移動の前には必ず確認します。'
    ),
    "highlights_folders_label": '大きいフォルダー',
    "highlights_files_label": '大きいファイル',
    "highlights_files": '大きいファイルを選んで表示します。丸印は削除の目安です。',
    "reclaim_action": "空き容量を増やす…",
    "reclaim_action_tip": "このスキャンで見つかった項目から、指定した容量を空ける計画を立てます",
    "reclaim_title": "空き容量を増やす",
    "reclaim_hint": (
        "必要な容量を選んでください。FileTree はこのスキャンで見つかった項目を、安全なものから順に表示します。自動で"
        "選択されるものはなく、確認して「はい」と答えるまで何も移動しません。"
    ),
    "reclaim_target": "空ける容量:",
    "reclaim_custom": "任意の容量",
    "reclaim_share": "ドライブの空きがこの割合になるまで",
    "reclaim_drive": "スキャン時、ドライブは {total} 中 {free} が空いていました。",
    "reclaim_column_entry": "ステップまたは項目",
    "reclaim_column_total": "累計",
    "reclaim_step": "{risk}: {title} ({count})",
    "reclaim_duplicates": "重複ファイルの余分なコピー",
    "reclaim_duplicates_tip": (
        "「重複」タブで残すと選んだコピーと同じ内容のファイルです。残すコピーが提案されることはありません。"
    ),
    "reclaim_options": "どの規則にも当てはまらない大きなファイル — 確かな場合のみ",
    "reclaim_running": "{total} / {target}",
    "reclaim_beyond": "{total} / {target}(目標超過)",
    "reclaim_more": "ほかに {count} 件(表示していません)",
    "reclaim_overlap": "単独では {size}。一部は前のステップで計上済みです。",
    "reclaim_reached": "これらのステップで約 {found} を空けられ、指定した {target} に届きます。",
    "reclaim_short": (
        "これらのステップで空けられるのは約 {found} で、{target} まで {short} "
        "足りません。不要だと確かな場合は、最後に並ぶ大きなファイルで補える場合があります。"
    ),
    "reclaim_empty": "このスキャンでは提案できる項目が見つかりませんでした。",
    "reclaim_waiting": "整理の候補をまだ探しています。見つかり次第、計画に反映されます。",
    "reclaim_undecided": "{count} 組の重複は含まれていません。先に「重複」タブで残すコピーを選んでください。",
    "reclaim_selected": "選択: {selected} / {target}",
    "reclaim_note": (
        "これはスキャン結果からの推定です。実際に空く容量は異なる場合があります。ハードリンク、圧縮されたファイル、ク"
        "ラウドのファイルはサイズより使用量が少なく、ごみ箱に移動した項目はごみ箱を空にするまで容量を使い続けます。"
    ),
    "reclaim_show": "ツリーで表示",
    "reclaim_review": "確認してごみ箱に移動…",
    "shell_reading": "エクスプローラーの登録を読み取り中…",
    "shell_saving": "エクスプローラーの登録を保存中…",
    "shell_waiting": "現在のエクスプローラー設定の処理が終わるまで待機中…開始済みの保存は続行します。",
    "trash_failed_title": "移動できなかった項目",
    "trash_failed_summary": "失敗した項目: {count}。完全なパスと診断情報を確認してください。",
    "trash_holders_error": "ファイル使用プロセスの照会エラー: {reason}",
    "trash_skipped_title": "スキップした項目",
    "trash_skipped_summary": "{count} 件をスキップしました。再試行する前にフォルダーを再スキャンしてください。",
    "trash_skipped_hint": "行を選ぶと完全なパスと理由を表示します。{shortcut} で選択行をコピーします。",
    "closing_workers": (
        "FileTree を終了しています：バックグラウンド処理を停止し、"
        "現在のファイルシステム呼び出しの完了を待っています…"),
    "elevate_python_tip": (
        "Python から実行中：Windows UAC は昇格する実行ファイルの Python を表示します。"
        "FileTree の表示には FileTree 実行ファイルを使用してください。"),
    'overview_empty': 'フォルダーを選んで開始',
    'overview_live': 'スキャン中 · 集計は更新中です',
    'overview_complete': 'スキャン完了',
    'overview_partial': '不完全な結果 · 読み取れなかった項目があります',
    'overview_size': '論理サイズ',
    'overview_allocated': '記録された割り当て',
    'overview_files': 'ファイル',
    'overview_folders': _JA_FOLDER,
    'overview_problems': '読み取り不可の項目を確認（{count}）',
    'overview_navigation': '分析ビュー',
    'overview_coverage_hint': '今回のスキャン範囲を示します。除外設定とマウント境界は引き続き適用されます。',
    'overview_allocation_hint': '記録された割り当てには推定値や共有領域が含まれます。回収可能な容量ではありません。',
    'overview_live_hint': '更新中のツリーとグラフを確認できます。分析リストはスキャン終了後に表示されます。',
    'overview_result_hint': '分析ビューを選択し、項目を選んでツリー内の位置を確認します。',
    'overview_path': 'フォルダーまたはドライブのパス',
    'overview_scan_path': 'パスをスキャン',
    'overview_scan_path_tip': ('入力したフォルダーまたはドライブをスキャン（Enter）。'
                               '実行中のスキャンは安全に切り替えます。'),
    'overview_workflow': '1  フォルダーやドライブを選ぶ   →   2  容量を調べる   →   3  クリーンアップ前に確認',
    'overview_scan_running': 'バックグラウンドで読み取り中です。更新中の結果を確認できます。',
    'overview_scan_paused': ('一時停止を要求しました。現在のファイルシステム呼び出し完了を待つ場合があります。'
                             '再開または停止できます。'),
    'overview_scan_analysing': 'バックグラウンドで分析を準備中です。停止を要求できます。',
    'overview_scan_stopping': '現在のファイルシステム処理の終了を待っています。取得済みの部分的な結果は保持されます。',
    'overview_scan_elapsed': '経過 {time}',
    'recurring_review': '再スキャンして現在の候補を確認…',
    'recurring_validating': '日付の付いた提案を新しいスキャン全体と現在のソース メタデータと照合して検証しています…',
    'recurring_refused': (
        'プロポーザルを続行できません: {status}。新しいスケジュールされたスキャンを実行して、現在の観測を準備'
        'します。'
    ),
    'recurring_tabs_full': (
        '16 個のスキャン タブはすべて使用中です。スケジュールされたプロポーザルを確認する前にタブを閉じてくだ'
        'さい。'
    ),
    'trash_skip_proposal_changed': (
        '元のパス、候補レポートの設定または記録が変更されたか、確認できませんでした。元の項目を保持しました。'
    ),
    'trash_skip_proposal_expired': (
        '移動前に定期スキャンの候補レポートが期限切れになりました。元の項目を保持しました。'
    ),
    'action_recurring': 'スケジュールされたスキャンの提案…',
    'action_recurring_tip': '日付のスケジュールされた観測とその範囲を表示します。自動クリーンアップはありません。',
    'recurring_rule': 'ルール',
    'recurring_unknown': '不明',
    'recurring_new': '前回のスキャン以降の新しいジャンク',
    'recurring_current': '現在の候補',
    'recurring_growth': '最大の新規成長',
    'recurring_empty': (
        'このセッションにはスケジュールされたレポートはありません。バックグラウンド監視を有効にし、スキャンフ'
        'ォルダーを選択します。'
    ),
    'recurring_hint': (
        '観察のみ。何も自動的に移動されません。リストごとに最大 100 行。増加は論理バイトであり、回復可能なス'
        'ペースではありません。不明な比較は、新しいジャンクがないことを証明するものではありません。レポートは'
        '、このセッションのスケジュールされたスキャンの後に表示されます。ベースラインはローカル履歴に保存され'
        'ます。新しいタブで再スキャンを確認し、通常のキューと確認を使用します。'
    ),
    'recurring_summary': (
        '準備済み: {prepared}\n前のベースライン: {previous}\n有効期限: {expires}\n表示された候補: {retained} '
        '/ {total};カバレッジ: {coverage};比較: {comparison}\nステータス: {status}'
    ),
    'recurring_status_current': '観察されました。レビュー前に最新のソースの検証が必要',
    'recurring_status_expired': '期限切れ (スケジュールの欠如またはクロックのロールバックを含む)',
    'recurring_status_schedule_changed': 'スケジュールが変更または無効になった',
    'recurring_status_stale_scan': 'スキャン操作記録が変更されているか、使用不可になっています',
    'recurring_status_rule_changed': 'クリーンアップルールが変更されました',
    'recurring_status_incomplete': '不完全な報道または不明な身元',
    'recurring_status_paths_changed': 'ソースパスが変更されました',
    'recurring_status_unavailable': '設定または受信を確認できませんでした',
    'recurring_prepare_failed': '履歴が保存されました。スケジュールされたプロポーザルは利用できません: {detail}',
    'workspace_new': '新しいスキャンタブ',
    'workspace_new_tip': '独立したスキャン タブを開きます (Ctrl+T)。 Ctrl+W で現在のタブを閉じます。',
    'workspace_close': 'スキャンタブを閉じる',
    'workspace_empty': 'フォルダーを選択',
    'trash_skip_recycle_unverified': (
        'Windows リサイクル設定、完全なソース サイズ、またはネイティブ ビン メタデータを検証できませんでした'
        '。元の項目を保持しました。'
    ),
    'trash_skip_recycle_disabled': 'Windows このスコープではリサイクルが無効になっています。元の項目を保持しました。',
    'trash_skip_recycle_capacity': (
        '選択した内容と現在のビンの内容が、観察されたヘッドルームのあるリサイクル制限を超えています。元の項目'
        'を保持しました。'
    ),
    'action_check_updates': '毎日更新を確認',
    'action_background_monitor': 'バックグラウンドモニター…',
    'action_background_monitor_tip': (
        'トレイ通知と穏やかなスケジュールされたフォルダー履歴スキャンをオプトインします。'
    ),
    'background_enable': 'バックグラウンド監視を有効にする',
    'background_startup': 'サインイン時にこのモニターを開始します',
    'background_startup_hint': (
        'このユーザーのみに個別のオプトインを設定します。 FileTree が所有するログイン エントリを削除するには'
        '、チェックを外します。今後のログインに適用されます。別のコピーを開始したり、このモニターを閉じたりす'
        'ることはありません。'
    ),
    'background_startup_requires_monitor': 'ログインエントリを追加する前に、バックグラウンド監視を有効にします。',
    'background_startup_error': 'ログインの起動を変更できませんでした: {detail}',
    'background_hint': (
        'デフォルトではオフです。閉じると、FileTree が使用可能なシステム トレイに保持されます。終了すると終了'
        'します。 OSの利用可能な容量を1分ごとに確認し、選択したフォルダーのみを優しくスキャンします。スケジュ'
        'ールされたスキャンには、ローカル履歴が有効になっている必要があります。自動クリーンアップやスタートア'
        'ップ登録はありません。'
    ),
    'background_threshold': '利用可能なスペースを下回ると警告する',
    'background_interval': 'スキャン間隔 (時間)',
    'background_roots': 'スケジュールスキャンフォルダー',
    'background_add': 'スキャンフォルダーを追加…',
    'background_remove': '選択したフォルダーを削除します',
    'background_limit': '最大 32 個のスケジュールされたフォルダーを選択します。',
    'background_show': 'FileTree を表示',
    'background_off': 'バックグラウンド監視がオフになっています',
    'background_ready': 'バックグラウンド監視がオンになっています',
    'background_no_tray': (
        'システムトレイは使用できません。 FileTree は表示されたままになり、バックグラウンド監視は一時停止され'
        'ます。'
    ),
    'background_error': 'バックグラウンド監視: {detail}',
    'background_history_disabled': 'スケジュールされたスキャンを実行する前に、ローカル スキャン履歴を有効にします。',
    'background_scanning': 'スケジュールされたスキャン: {detail}',
    'background_saved': '保存されたスケジュールされた履歴: {detail}',
    'background_saved_partial': '未読スコープで保存されたスケジュールされた履歴: {detail}',
    'background_canceled': (
        'スケジュールされたスキャンがキャンセルされました。部分的なソース カバレッジは保存されませんでした: {'
        'detail}'
    ),
    'background_warning': '{detail}',
    'background_low_space': '{root} の空き容量が少ない: {free} ({percent}%)',
    'action_follow_changes': '変更を追跡',
    'action_follow_changes_tip': (
        'デフォルトではオフです。 Windows、Linux、macOS で変更されたフォルダーだけを読み直し、'
        '変更のないサブフォルダーはそのまま残します。'
    ),
    'follow_refreshed': '変更された {count} 個のフォルダーを更新しました',
    'follow_refresh_failed': '変更されたフォルダーを更新できませんでした: {reason}',
    'follow_waiting': '変更の追跡: スキャンを待機しています',
    'follow_starting': '変更を追跡: 開始中…',
    'follow_active': '次の変更点 ({detail})',
    'follow_failed': '変更の追跡が停止されました: {detail}',
    'follow_incomplete': '変更を追跡するには完全な物理スキャンが必要です',
    'follow_unsupported': '変更の追跡は Windows、Linux、macOS に対応しています',
    'follow_backend_usn': 'NTFS USN',
    'follow_backend_directory_changes': 'ディレクトリ通知',
    'follow_backend_inotify': 'inotify',
    'follow_backend_fsevents': 'FSEvents',
    'action_check_updates_tip': (
        '多くても 1 日に 1 回、HTTPS 経由で PyPI に問い合わせます。通知のみで、インストールはありません。'
    ),
    'update_available': 'FileTree {version} は利用可能です',
    'multi_roots': '複数のルート',
    'action_multi_scan': '複数のフォルダーをスキャン…',
    'action_multi_scan_tip': '1 回の結合スキャンで明示的なフォルダーを確認します。',
    'multi_choose': '複数のフォルダーをスキャンする',
    'multi_add': 'フォルダを追加…',
    'multi_remove': '選択したルートを削除します',
    'scan_all_drives': 'すべてのドライブをスキャンする',
    'multi_hint': (
        '選択したルートを最大 256 個結合します。結果は読み取り専用です。ファイル操作のためにソースを個別にス'
        'キャンします。 OS の容量はボリュームごとに維持されます。'
    ),
    'capacity_multiple_roots': '複数のルート: OS の容量はボリュームごとです。',
    'vc_title': 'コンパクトな選択された VHD…',
    'vc_apply': 'レビューしてコンパクトに…',
    'vc_hint': (
        '固定ローカル NTFS 上の切り離されたダイナミック VHD/VHDX のみが対象となります。読み取り専用の準備では'
        '、ID、ヘッダー、保守的な WSL/Docker ランタイム状態がチェックされます。ゲストの使用状況と保証された回'
        '復は不明のままです。 FileTree の既存の管理者が権限エラーのために再起動する前に、このレビューを閉じて'
        'ください。新たなスキャンと承認が必要です。'
    ),
    'vc_preparing': 'キャプチャされたディスクと停止したランタイムを確認しています…',
    'vc_ready': '正確なソースを確認し、そのマシンが停止したままであることを確認します。',
    'vc_details': (
        'ソース: {path}\n名前: {source}\nディスク UUID: {identifier}\n仮想容量: {capacity}\nプロバイダー バイ'
        'ト: {physical}\n\nバックエンド: Windows CompactVirtualDisk、切り離されたゼロブロック圧縮。ゲストの接'
        '続、起動またはシャットダウンはありません。ゲストが使用するバイトは不明です。'
    ),
    'vc_confirm': (
        '次の正確な仮想ディスクファイルをコンパクト化しますか？\n\n{path}\n\n「はい」を選ぶと、このファイルを'
        '使用するマシンが停止しており、処理中も停止したままであることを確認したものとみなします。実行状態と識'
        '別情報を改めて確認します。OS のゼロブロック処理では容量が回復しない場合があり、後からエラーが発生し'
        'てもメタデータがすでに変更されている可能性があります。自動的に元に戻す機能はありません。ゲストの使用'
        '量と空き容量の回復量は不明です。停止または閉じる操作は、実行中の OS 呼び出しを待ち、実際の結果を報告'
        'します。書き込み可能な状態で開く前に承認を記録します。'
    ),
    'vc_running': 'レビューしたディスクを再チェックして圧縮しています…',
    'vc_waiting': '現在のネイティブ呼び出しを待機しています。実際の結果はまた報告します…',
    'vc_done': (
        '{status}\n仮想ディスクファイルの占有量の観測値: {before} → {after}。OS の空き容量の回復を保証するも'
        'のではありません。ゲスト内の使用量は不明です。書き込みを試みた後は再スキャンが必要です。'
    ),
    'vc_failed': '圧縮: {reason}',
    'vc_not_compacted': '圧縮されていない',
    'vc_stale': (
        '書き込み可能な操作が試行されました。記録された観察は古いものです。別のレビューを行う前に、このウィン'
        'ドウを閉じて新たにスキャンしてください。'
    ),
    'vc_audit_refused': '承認を記録できませんでした。ネイティブ操作は開始されていません',
    'vc_audit_detail': '以前のバッキング割り当て: {before};後: {after}。エラー: {error}',
    'journal_status_compacted': 'ネイティブ圧縮が完了しました',
    'journal_reason_compaction': '明示的な仮想ディスクの圧縮',
    'vd_hint': (
        '読み取り専用インベントリ。プロバイダー ラベルは場所のヒントです。バッキング割り当て、プロバイダーの'
        'バイト、および仮想容量は別個です。ゲストの使用状況は不明のままです。ヘッダー クエリと圧縮レビューは'
        '明示的です。サポートされていない形式は表示されたままになります。ゲストが自動的に起動、停止、マウント'
        'することはありません。'
    ),
    'vd_name': 'ディスク名',
    'vd_source': 'ソース',
    'vd_issue_unverified': '未確認の身元',
    'vd_issue_unavailable': 'リンクされているか、クラウドか、または利用できない',
    'vd_issue_changed': 'ファイルが変更されました',
    'vd_issue_duplicate_hard_links': '複数のハードリンク名',
    'action_virtual_disks_tip': (
        '記録された仮想ディスクを確認し、読み取り専用のネイティブ VHD 情報を明示的にクエリします'
    ),
    'action_virtual_disks': '仮想ディスク…',
    'vd_kind': 'フォーマット',
    'vd_length': 'バッキングファイルの長さ',
    'vd_allocation': '記録された割り当て',
    'vd_capacity': '仮想容量',
    'vd_physical': 'プロバイダーの物理バイト',
    'vd_guest': 'ゲストが利用した',
    'vd_source_scan': '記録されたスキャン',
    'vd_source_wsl': 'WSL登録',
    'vd_source_docker': 'Docker のデフォルト (推定)',
    'vd_unsupported': 'ネイティブ VHD ツールはサポートされていません',
    'vd_not_queried': 'ネイティブヘッダーはクエリされません',
    'vd_fixed': '修正済み',
    'vd_dynamic': 'ダイナミック',
    'vd_differencing': '差異化',
    'vd_loaded': '装着中・使用中',
    'vd_detached': '積まれていない（観察）',
    'vd_inspect': '選択した VHD ヘッダーをクエリします',
    'vd_select': '記録されたエントリを表示する',
    'vd_reading': '仮想バッキング ファイルを検出しています…',
    'vd_querying': 'ネイティブヘッダーを読み取り中: {path}',
    'vd_summary': '{count}中{shown}を表示しています。 {issues} の問題/欠落。対象範囲: {coverage}。',
    'vd_failed': '仮想ディスク情報: {reason}',
    'vd_information_hint': (
        'ネイティブの観察では、圧縮を許可したり、マシンが停止していることを証明したりすることはありません。プ'
        'ロバイダーの物理バイトはゲストが使用するバイトではありません。ディスク UUID は行のツールチップにあり'
        'ます。'
    ),
    'link_summary': '{total} 枚の追加コピー: {ready} 準備完了、{skipped} は拒否されました。',
    'link_title': '追加のコピーをリンクします…',
    'link_hint': (
        '明示的に保存されたコピー (最大 1,000 個の追加ファイル) を使用して、完全に重複したファイルを確認しま'
        'す。保護されたファイル、変更されたファイル、クラウド ファイル、リンクされたファイル、およびサポート'
        'されていないファイルは拒否されます。保証される空き領域量はありません。'
    ),
    'link_copy': '置き換える追加のコピー',
    'link_keeper': '保持されたファイル',
    'link_apply': 'リンクは追加コピーをレビューしました…',
    'link_confirm': (
        '{count} 個の重複コピーをハードリンクに置き換えますか？ 処理できない {skipped} 行はスキップします。\n'
        '\n元のデータはごみ箱に保存されません。リンクされたすべての名前は、以後の内容、メタデータおよびアクセ'
        'ス権の変更を共有します。自動的に元に戻す機能はありません。失敗やキャンセル時には、作成済みリンクと元'
        'のコピーのバックアップが表示されたパスに残る場合があります。停止または閉じる操作は、実行中の OS 呼び'
        '出しの終了を待ちます。すべてのデータと名前付きストリームを再確認します。同時変更に対する確認は観察に'
        '基づくものであり、トランザクションではありません。詳細で各ペアと拒否理由を確認してください。'
    ),
    'link_progress': '再チェック/リンク: {path}',
    'link_done': (
        'ハードリンク: {linked} が公開されていますが、{other} はリンクされていません。再スキャンして観察を更'
        '新します。回復容量は不明。'
    ),
    'link_not_linked': 'リンクされていません',
    'link_retained': '保持されるパス:\n{paths}',
    'journal_status_linked': 'ハードリンクが公開されました',
    'journal_reason_duplicate_links': '明示的な重複ハードリンクの置換',
    'undo_button': '元に戻す ({count})',
    'undo_running': 'キャプチャされたゴミ箱アイテムを復元しています…',
    'undo_done': '元に戻す: {restored} は復元されましたが、{failed} は失敗しました',
    'undo_title': 'ゴミ箱の修復',
    'undo_result': '{status}\nオリジナル: {source}\nゴミ箱: {trashed}\n{reason}',
    'undo_unavailable': '一部の項目では元に戻すことができません: {reason}',
    'journal_status_restored': 'ゴミ箱から復元',
    'journal_reason_undo': '明示的なゴミ箱の取り消し',
    'menu_move_drive': '別のドライブに移動…',
    'copy_hint': (
        '別のドライブにある既存のフォルダーを選択します。オリジナルは、別のゴミ箱確認が行われるまで保持されま'
        'す。ファイル数、長さ、SHA-256 が 64 MiB 未満であることを確認します。より大きなペイロードは長さのみで'
        'す。失敗/キャンセルでは部分的な宛先が保持されます。最大 1,000 個のフォルダーを選択できます。'
    ),
    'copy_apply': 'レビュー済みフォルダーをコピーして確認します…',
    'copy_redirect': 'ゴミ箱に成功した後、元の各パスにジャンクション/シンボリック リンクを残します。',
    'copy_finish': '確認済みのオリジナルをごみ箱に移動します…',
    'copy_confirm': (
        '確認済みの {count} 組のフォルダーをコピーして検証しますか？ ほかの {skipped} 組はスキップします。既'
        '存の名前は上書きしません。元の項目は、ごみ箱への移動を別途承認するまで保持します。失敗やキャンセル時'
        'には、途中までコピーされた項目がコピー先に残ります。'
    ),
    'copy_progress': 'このフォルダー内の {path}: {done} / {total} ファイルをコピー/検証しています',
    'copy_done': (
        '検証済みのコピー: {copied};スキップされました: {skipped};失敗しました: {failed}。原本は保管されてい'
        'ます。'
    ),
    'copy_partial': '保持された部分的な宛先: {path}',
    'copy_trash_confirm': (
        '各項目をごみ箱へ移動する直前に、コピー先のフォルダーを再検証します。項目数と長さを比較します。64 MiB'
        ' 未満の内容は SHA-256 で照合し、それ以上の内容は長さだけを比較します。確認に失敗すると残りの処理を停'
        '止します。同時変更に対する確認はトランザクションではありません。'
    ),
    'copy_errors': (
        'コピーの検証または元のパスのリダイレクトに失敗しました。 「詳細」で実際のパスを確認してください。'
    ),
    'copy_verify_failed': '保持されたオリジナル: {source}\nコピー: {destination}\n検証が拒否されました: {reason}',
    'copy_redirect_failed': (
        'オリジナルはゴミ箱に移動されました: {source}\n確認されたコピーは保持されました: {destination}\nリダ'
        'イレクトに失敗しました (空のオリジナル パス ディレクトリが残る可能性があります): {reason}'
    ),
    'namespace_reason_same_volume': '同じボリューム。フォルダーに移動を使用する',
    'namespace_source_name': 'ソース名',
    'namespace_destination_name': '宛先名',
    'namespace_closed_errors': (
        '停止/クローズされた操作でエラーが報告されました。 「詳細」で送信元/宛先パスを検査します。'
    ),
    'namespace_refreshed': '{path}: {files} ファイルを更新しました。 {errors} スキャン エラー。',
    'namespace_refresh_failed': '{path} で更新に失敗しました: {reason}',
    'namespace_refreshing': '影響を受ける宛先を更新しています: {path}',
    'menu_move_folder': 'フォルダーに移動…',
    'menu_rename': '名前を変更…',
    'namespace_source': 'ソース',
    'namespace_destination': '目的地',
    'namespace_status': 'ステータス',
    'namespace_pattern': 'ファイル名のパターン',
    'namespace_rename_hint': (
        'すべてのソースと宛先を確認します。リテラルトークン: {name}、{stem}、{ext}、{n}。同じボリュームのみ。'
        '上書きはありません。選択されたエントリは最大 1,000 件です。'
    ),
    'namespace_move_hint': (
        '既存の宛先フォルダーを選択し、すべてのペアを確認します。同じボリュームのみ。上書きはありません。保護'
        'されている/リンク/利用できない/不完全なエントリは拒否されます。選択されたエントリは最大 1,000 件です'
        '。'
    ),
    'namespace_collision_skip': '既存の名前: スキップ',
    'namespace_collision_rename': '既存の名前: 番号付きサフィックスをプレビューする',
    'namespace_preview': 'パスのプレビュー',
    'namespace_apply': 'レビューしたパスを適用します…',
    'namespace_reading': 'ソースと宛先のメタデータを確認しています…',
    'namespace_preview_needed': 'オプションが変更されました。適用する前にパスを再度プレビューしてください。',
    'namespace_summary': (
        '{total} 最も外側のペア。 {ready} 準備完了。 {skipped} は拒否されました/変更されませんでした。'
    ),
    'namespace_confirm': (
        'プレビューの処理可能な {count} 組の元のパス／移動先のペアを適用しますか？ ほかの {skipped} 組はスキ'
        'ップします。詳細には処理可能な全ペアを表示します。既存の名前は上書きしません。停止または閉じる操作は'
        '、実行中の名前変更の終了を待ち、完了した変更を保持します。'
    ),
    'namespace_progress': '{done} / {total} ペアを処理しました',
    'namespace_done': (
        '移動/名前変更: {moved};スキップされました: {skipped};失敗しました: {failed}。閉じてスキャンを更新し'
        'ます。'
    ),
    'namespace_failed': '操作が失敗しました: {reason}',
    'namespace_reason_ready': '準備完了',
    'namespace_reason_unverified': '不明な身元',
    'namespace_reason_link': 'リンクが拒否されました',
    'namespace_reason_special': '特別入場は拒否されました',
    'namespace_reason_unavailable': '利用不可/クラウドエントリー',
    'namespace_reason_cancelled': '停止しました',
    'namespace_reason_outside': '現在のスキャン/ルート以外',
    'namespace_reason_missing': 'ソースがありません',
    'namespace_reason_kind': 'エントリタイプが変更されました',
    'namespace_reason_identity': 'ソースを交換しました',
    'namespace_reason_changed': 'ソースが変更されました',
    'namespace_reason_incomplete': '不完全な情報源の網羅',
    'namespace_reason_unreadable': '読めないソース',
    'namespace_reason_system_managed': 'システム管理のソース',
    'namespace_reason_protected': '保護されたソース',
    'namespace_reason_unchanged': '名前は変更されていません',
    'namespace_reason_descendant': '選択したソース内の宛先',
    'namespace_reason_protected_destination': '保護された宛先',
    'namespace_reason_volume': 'ボリュームが異なります。確認済みのコピーが必要です',
    'namespace_reason_collision': '名前はすでに存在します',
    'photos_exact': '完全な重複',
    'photos_find': '似た写真を探す',
    'photos_similar': '類似の写真',
    'photos_distance': 'ハッシュ距離 (0 ～ 16):',
    'photos_hint': (
        '視覚的な候補のみ: サムネイルとオリジナルを比較します。ハッシュの衝突が発生する可能性があります。自動'
        '残すファイル、追加コピーの選択、または回復の見積もりはありません。最初のアニメーション フレーム。'
    ),
    'photos_group': '{count} 画像;最初の画像の {distance} ビット以内',
    'photos_running': '画像の読み取り: {read};スキップ/失敗: {skipped}',
    'photos_summary': (
        '{groups} 類似画像グループ。 {read} 画像が読み取られました。 {skipped} はスキップ/失敗しました。'
    ),
    'photos_limited': '在庫または展示が限られている。最大 {count} 件の画像行/サムネイルが表示されます。',
    'archive_loading': 'アーカイブ メタデータを読み取り中…',
    'archive_virtual_name': '{name} [仮想]',
    'tree_more_rows': 'さらに {count} 個の項目 — クリックすると次の {page} 個を表示',
    'tree_more_rows_hint': ('大きなフォルダーは、ウィンドウの応答性を保つため一度に {page} 個ずつ表示します。'
        'この行をクリックするか Enter キーを押すと次のページを表示します。'
        'グラフや一覧で選んだ項目は、その項目のページが自動的に表示されます。'),
    'archive_virtual_hint': (
        'アーカイブ メンバー: 宣言された非圧縮サイズ、ディスク合計外。ファイル操作や抽出はありません。'
    ),
    'archive_failed': 'プレビューは利用できません: {reason}',
    'archive_rejected': '{count} の安全でない、リンクされた、または競合するメンバーが省略されました',
    'archive_empty': 'プレビュー可能なメンバーがいません',
    'archive_stopped': 'アーカイブのプレビューが停止しました。在庫が不完全',
    'archive_busy': '2 つのアーカイブ読み取りがすでに実行されています。再スキャンして再試行する',
    'archive_stop': 'このアーカイブを読むのをやめる',
    'action_count_hard_links': '見つかったハードリンクを 1 回だけ数える',
    'action_count_hard_links_tip': (
        'デフォルトではオフです。今後のスキャンでは名前付きサイズが保持され、カウントされた合計が追加されます'
        '。ブランチ/ゴミ箱の再スキャンにより、完全なルートが再構築されます。'
    ),
    'column_accounted_size': '集計サイズ',
    'column_accounted_allocated': '集計ディスク使用量',
    'hard_links_hint': (
        'ハードリンク アカウンティングを有効にすると、最初に検出された語彙名がバイト数に寄与します。ここでは'
        'エイリアスはゼロとカウントされます。名前付きサイズは実際のファイル長のままです。不明または矛盾した記'
        '録は推定のままです。共有エクステントは不明です。'
    ),
    'hard_links_summary': (
        'カウント: {size} (ディスク推定値 {allocated}); {aliases} 観察されたエイリアス。 {unknown} 不明なレコ'
        'ードです。グラフではカウントされた合計が使用されます。ファイル/タイプ/経過時間リストは名前付きサイズ'
        'を保持します。'
    ),
    'compression_mode_ntfs': 'NTFS 圧縮',
    'compression_mode_xpress8k': 'XPRESS8K 圧縮 (ほとんど変更されないファイル)',
    'compression_mode_uncompress': '解凍 (NTFS および実行可能モード)',
    'compression_apply': 'リストされたファイルを処理します…',
    'compression_restore_summary': (
        '{count}/{total} 件の記録ファイルはレビューの対象となります。 {shown} を表示しています。圧縮状態が不'
        '明な可能性があります。'
    ),
    'compression_confirm': (
        '範囲: {path}\nモード: {mode}\n候補 {total} 件のうち、一覧の {count} ファイル（論理サイズ {size}）だ'
        'けを処理します。\n\n現在の NTFS 範囲と、ファイルが変更されていないことを再確認します。リンク、クラウ'
        'ド／オフライン、スパース、隠し／システム、ハードリンクおよび保護されたファイルは処理しません。フォル'
        'ダーの既定設定と一覧にないファイルは変更しません。圧縮すると書き込みが遅くなる場合があります。XPRESS'
        ' は変更の少ないデータ向けです。圧縮解除には空き容量が必要です。停止や失敗時には一部の変更が残る場合'
        'があります。\n\nこの画面を閉じると実行中のコマンドをキャンセルし、その終了を待ってから、ファイルごと'
        'の割り当てを確認してこのフォルダーを再スキャンします。続行しますか？'
    ),
    'compression_progress': '{done}/{total} リストされたファイルを処理しています…',
    'compression_done': (
        '{done}/{attempted} コマンドが完了しました。 {failures} 回失敗しました。既知の一致するファイル割り当'
        'て: {before} → {after}; {unknown} 測定値は不明です。再スキャン間近です。合計は空き領域を保証するもの'
        'ではありません。最初の 20 個のエラーが表示されます。'
    ),
    'compression_canceled': (
        '止まった。以前のファイルまたは現在のファイルが変更されている可能性があります。再スキャン間近です。'
    ),
    'compression_failed': '操作が失敗しました: {reason}。部分的な変更は可能です。再スキャン間近です。',
    'action_exact_allocation': 'Windows のファイルごとの割り当てを測定',
    'action_exact_allocation_tip': (
        'デフォルトではオフです。追加のメタデータは、XPRESS/WOF ファイルなど、今後のスキャンを必要とします。'
        '有効にして再スキャンします。既知のクラウド/オフライン ファイルは照会されません。失敗したクエリは推定'
        '値のままです。'
    ),
    'menu_compression': 'NTFS 圧縮…',
    'compression_reading': '記録された圧縮候補を確認しています…',
    'compression_summary': (
        '{count}/{total} ファイルはタイプの候補です。 {shown} を表示しています。論理 {logical}、名前付き割り'
        '当て {allocated}。節約の可能性: 0–{allocated};固定の圧縮率は予測されません。 {unknown} ファイルには'
        '不明なメタデータがあります。'
    ),
    'compression_volume': 'ファイルシステム: {filesystem};割り当て単位: {unit}',
    'compression_unknown': '不明',
    'compression_ntfs_only': 'NTFS は確認されませんでした。このスコープではネイティブ圧縮は使用できません。',
    'compression_partial': '不完全なスキャン: 省略された/読み取り不可能なデータはこの推定値の範囲外です。',
    'compression_hint': (
        '読み取り専用タイプの推定: ログ、テキスト、コード、および場合によっては非圧縮画像形式。拡張子は圧縮可'
        '能であることを証明しません。非表示/システム、圧縮/スパース、再解析/クラウド/オフライン、および不明な'
        'レコードは省略されます。名前付き割り当てはハード リンクによって推定または共有される可能性があるため'
        '、回復可能な領域が保証されているわけではありません。ペイロードは読み取られません。ダブルクリックする'
        'と、記録されたファイルが選択されます。 Ctrl+C で行をコピーします。'
    ),
    'action_capture_owners': 'Windows のファイル所有者を記録',
    'action_capture_owners_tip': (
        'デフォルトではオフです。今後のスキャンに所有者のメタデータ クエリを追加します。有効にして再スキャン'
        'する'
    ),
    'tab_users': 'ユーザー',
    'column_owner': '所有者',
    'column_owner_id': '所有者の識別子',
    'owner_unknown': '不明な所有者',
    'owners_refresh': '記録された合計を更新する',
    'owners_reading': '記録された所有者の合計を追加し、アカウント名を解決しています...',
    'owners_unqueried': 'スキャン後に「ユーザー」を開き、記録された所有者の合計を照会します。',
    'owners_partial': '不完全なスキャン: 省略された/読み取り不可能なバイトとその所有者は不明のままです。',
    'owners_summary': (
        '{count} 所有者グループ。 {shown} を表示しています。 {files} ファイル、{size}。不明な所有者: {unknown'
        '_files} ファイル、{unknown_size}。'
    ),
    'owners_hint': (
        '全体スキャン、ファイル所有者のみ。ディレクトリの所有権は子孫を割り当てません。 POSIX uid はスキャン'
        'の統計から取得されます。 Windows で、[オプション] → [Windows ファイル所有者のキャプチャ] を有効にし'
        'て再スキャンします。無効、失敗、変更されたクエリ、またはクラウド/オフライン クエリは不明のままです。'
        '名前は uid/SID にフォールバックできます。名前付きの割り当ては推定されたままであり、名前ごとのハード '
        'リンクの数は変わりません。所有権は、実際の使用または削除の許可を証明するものではありません。クリーン'
        'アップアクションは用意されていません。'
    ),
    'bin_labels_refresh': 'ビンの合計を更新する',
    'bin_labels_hint': (
        '最大 256 個の準備完了ドライブの読み取り専用スナップショット。スキャンされたドライブが優先されます。 '
        'POSIX の合計は論理ペイロード バイトです。利用できない合計や一部の合計がゼロになることはありません。'
        'スコープは重複する可能性があります。合計しないでください。クエリを更新します。これはクリーンアップア'
        'クションを準備するものではありません。'
    ),
    'bin_label_scope_unknown': 'このスキャンのドライブのごみ箱: スコープは照会されません',
    'bin_label_unqueried': '{root} ごみ箱: クエリされませんでした',
    'bin_label_total': '{root} ごみ箱: {size}、{count} アイテム',
    'bin_label_partial': '{root} ごみ箱: 合計は不明です。既知の {size}、{count} アイテム',
    'action_file_times': 'ファイルの日時…',
    'action_file_times_tip': 'このスキャンで記録されたアクセス日と作成日をフィルターします。',
    'action_capture_file_times': 'ファイルのアクセス日時と作成日時を記録',
    'action_capture_file_times_tip': (
        'デフォルトではオフです。今後のスキャンでは、通常のファイルごとに 16 バイトが追加されます。有効にした'
        '後に再スキャンする'
    ),
    'column_accessed': '記録されたアクセス日時',
    'column_created': '作成日時',
    'file_times_hint': (
        '[オプション] → [ファイルのアクセス/作成時間をキャプチャ] を有効にしてから、再スキャンします。通常の'
        'ファイルのみ。ディレクトリ/リンク、および利用できない作成日は不明のままです。アクセス日は、バックグ'
        'ラウンド ツールによって無効化、遅延、または更新される可能性があります。実際の使用を証明することは決'
        'してありません。 POSIX ctime は作成時間ではありません。このビューでは、クリーンアップ アクションは準'
        '備されません。'
    ),
    'file_times_accessed': '…以降開かれていません (アクセス日の記録)',
    'file_times_created': '少なくとも…前に作成されました',
    'file_times_mode': '記録年齢モード',
    'file_times_days': '日数',
    'file_times_reading': '記録されたファイルの日付をフィルタリングしています…',
    'file_times_summary': (
        '{count} は一致、{size}; {shown} を表示しています。 {unknown}/{total} ファイルの日付は使用できないか'
        '、将来の日付です。'
    ),
    'file_times_policy_disabled': (
        'NTFS は、アクセス更新が無効になっていると報告します。アクセス年齢の一致は利用できません。作成フィル'
        'タリングは引き続き利用可能です。レジストリ設定には再起動が必要な場合がありますが、すべてのファイルシ'
        'ステムが記述されているわけではありません。'
    ),
    'file_times_policy_unknown': (
        'NTFS アクセス更新構成が不明です。アクセス年齢の一致は利用できません。作成フィルタリングは引き続き利'
        '用可能です。'
    ),
    'file_times_policy_enabled': (
        'NTFS レジストリ レポートは更新へのアクセスが有効になっています。保留中の再起動、ファイルシステム/プ'
        'ロバイダーの設定、および延期された更新が日付に影響を与える可能性があります。'
    ),
    'file_times_policy_platform': (
        'ファイルシステム/プロバイダーの設定により、アクセスの更新が延期または抑制される場合があります。これ'
        'らの日付を記録されたメタデータとして扱います。'
    ),
    'action_programs': 'インストール済みプログラム…',
    'action_programs_tip': 'このスキャンでインストーラー/ゲームのメタデータとインストール フォルダーを比較します',
    'program_name': 'プログラム・ゲーム',
    'program_source': 'メタデータソース',
    'program_version': 'バージョン/ビルド',
    'program_publisher': '出版社',
    'program_reported': '報告された推定値',
    'program_scanned': 'スキャンされた論理バイト',
    'program_allocated': 'スキャンされた名前付き割り当て',
    'program_coverage': '録音フォルダーの範囲',
    'program_location': 'インストールフォルダ',
    'program_registry': 'Windows レジストリ',
    'program_steam': 'Steam マニフェスト',
    'program_epic': 'エピックマニフェスト',
    'program_outside': '正確にスキャンされたフォルダーがありません',
    'program_hint': (
        'Windows 登録と認識された Steam/Epic マニフェストをアンインストールします。このスキャンで正確なフォル'
        'ダーにのみ一致しました。 Epic の修正された ProgramData マニフェスト フォルダーも読み込まれます。報告'
        'されるサイズは推定値です。欠落しているメタデータは不明のままです。共有/ネストされたフォルダーは重複'
        'する可能性があります。行を合計したり、回復可能な領域として扱ったりしないでください。ポータブル/パッ'
        'ケージ化されたアプリが存在しない場合があります。ダブルクリックすると、録音されたフォルダーが選択され'
        'ます。 Ctrl+C で行をコピーします。アンインストールは、Windows またはランチャーを通じてのみ行ってくだ'
        'さい。'
    ),
    'program_reading': 'インストールメタデータを読み取り中…',
    'program_summary': (
        '{count} 件中 {shown} 件のインストールを表示しています。 {issues} メタデータ項目が使用不可/不正な形式'
        '/省略されています'
    ),
    'program_failed': 'インストールを読み取れません: {reason}',
    'program_uninstall_page': 'Windows インストール済みアプリの設定を開きます',
    'program_open_failed': 'Windows はインストール済みアプリの設定ページを開けませんでした',
    'action_history': 'スキャン履歴…',
    'action_history_tip': 'このルートのサイズを経時的に確認し、以前のスキャンと比較します',
    'action_history_settings': 'スキャン履歴の設定…',
    'action_history_settings_tip': 'ローカル スキャン メタデータを有効にし、そのグローバルな保存制限を設定します',
    'history_enable': '完了したフルスキャンをローカルに保存する',
    'history_settings_hint': (
        '履歴にはフォルダー名、パス、合計、カバレッジが保存されますが、ファイルの内容は保存されません。デフォ'
        'ルト: 有効、すべてのルートで合計 1 GiB。認識された履歴メタデータのみが古いものから順に削除されます。'
        '無効にすると、既存の履歴が読み取れる状態が維持されます。変更は今後のフル スキャンに適用されます。下'
        '限は次回の保存時に有効になります。'
    ),
    'history_limit': '合計履歴制限',
    'history_time': 'スキャン時間',
    'history_logical': '論理サイズ',
    'history_allocated': '割り当てられた名前付きバイト',
    'history_coverage': '適用範囲',
    'history_incomplete': '不完全;既知のデータのみ',
    'history_complete': '完全な記録されたカバレッジ',
    'history_chart': '論理フォルダーのサイズの経時変化',
    'history_chart_range': '{first}: {before}; {last}: {after}',
    'history_empty': 'このルートのスキャンは保持されていません',
    'trend_folder': 'ルートからの相対フォルダー',
    'trend_folder_hint': '空欄はルート',
    'trend_start': '開始日（含む）',
    'trend_end': '終了日（含む）',
    'trend_apply': '傾向を表示',
    'trend_change': '変化',
    'trend_child': '直下のフォルダー',
    'trend_before': '開始時のサイズ',
    'trend_after': '終了時のサイズ',
    'trend_direct_files': '直下のファイル',
    'trend_unknown': '不明',
    'trend_net': '期間の正味変化: {change}',
    'trend_net_unknown': '期間の正味変化は不明',
    'trend_summary': '日時が有効なスキャン {shown}/{count} 件、無効なヘッダー {invalid} 件。'
                     '直下の項目 {children}/{child_count} 件。{cap}',
    'trend_capped': '期間が上限で切られたため全期間の変化は不明',
    'trend_invalid': '傾向の条件が無効です: {reason}',
    'trend_reason_legacy': '旧記録の条件が不明',
    'trend_reason_incomplete': 'スキャンが不完全',
    'trend_reason_incompatible': '条件またはルートが非互換',
    'trend_reason_missing': 'フォルダーが存在しない',
    'trend_reason_corrupt': '記録本文が破損',
    'trend_chart_known': '既知のサイズ {known}/{total} 件。不明箇所は線を切断',
    'trend_chart_unknown': '比較できるフォルダーサイズがありません',
    'trend_net_reason': '期間の正味変化は不明: {reason}',
    'trend_reason_truncated': '期間が上限で切られた',
    'trend_reason_insufficient': '観測が 2 件未満',
    'trend_tab_sizes': 'フォルダーサイズ',
    'trend_tab_sources': '直下の内訳',
    'trend_tab_compare': 'ルート全体との比較',
    'history_compare': '選択したスキャンと現在の結果を比較する',
    'history_reading': 'ローカルスキャン履歴を読み取っています…',
    'history_hint': (
        'このルートに対して保持されている最新の 1,000 件のフル スキャン。停止したスキャンとブランチの再スキャ'
        'ンは保存されません。不完全なスキャンでは、既知のデータのみが記述されます。フォルダーが見つからないか'
        'らといって、削除されたことは証明されません。合計ではハードリンク名を個別にカウントします。違いはメタ'
        'データであり、コンテンツの検証ではありません。'
    ),
    'history_summary': (
        '{count} 件中 {shown} 件のスキャンを表示しています。 {invalid} メタデータ ファイルが無効または使用で'
        'きません'
    ),
    'history_failed': '履歴を読み取れません: {reason}',
    'history_save_failed': 'スキャンは完了しましたが、履歴を保存できませんでした: {reason}',
    'action_scan_workers': 'スキャン スレッド数…',
    'action_scan_workers_tip': '新しいスキャンの同時実行性を選択します。高いほど速いとは限りません',
    'workers_prompt': (
        '新しいスキャンのワーカー (1 ～ 32)。デフォルトは {default} です。ネットワーク共有が遅い場合は、ワー'
        'カーを増やすことでメリットが得られる可能性があります。過剰な同時実行により、ディスク/サーバーに過負'
        '荷がかかる可能性があります。スキャンを実行すると、既存のワーカーが保持されます。実際の UNC のパフォ'
        'ーマンスはあなたのシェアに依存します。'
    ),
    'action_auto_cpu': 'CPU 使用率に合わせてスキャンスレッドを調整',
    'action_auto_cpu_tip': (
        '他のプログラムが CPU を使用している間は、新しいスキャンの読み取りスレッドを減らし、'
        '空いたら設定したスレッド数に戻します'
    ),
    'action_mft_scan': 'NTFS ドライブをファイルテーブルから読み取る',
    'action_mft_scan_tip': (
        '管理者として実行し NTFS ドライブ上のフォルダーをスキャンするとき、フォルダーを一つずつ一覧する代わりに'
        'ドライブのマスターファイルテーブルを直接読み取ります。その他のスキャンは従来どおりです'
    ),
    'action_bins': 'ごみ箱…',
    'action_bins_tip': 'ビンの合計と明示的なスコープ指定された OS の空の確認',
    'bin_finder_empty': 'マウントされているすべてのボリュームの Finder ゴミ箱を空にします…',
    'bin_finder_all': 'マウントされているすべてのボリューム (Finder 規模のゴミ箱)',
    'bin_finder_scopes': '現在のユーザーのゴミ箱スコープ:\n{scopes}\n\nマウントされたボリューム:\n{roots}',
    'bin_finder_first': (
        '現在のユーザーの Finder マウントされているすべてのボリュームのゴミ箱を空にしますか?\n\n{root}\n\n論'
        '理ペイロード: {size}\nアイテム: {count}'
    ),
    'bin_finder_irreversible': (
        'マウントされているすべてのボリュームについて、現在のユーザーの Finder のごみ箱を完全に空にしますか？'
        '\n\n{root}\n\n内容の論理サイズ: {size}\n項目数: {count}\n\nこの操作は元に戻せません。Finder の処理中'
        'に新しく入った項目も削除される場合があります。選択した行にかかわらず、マウントされているすべてのごみ'
        '箱に作用します。OS の処理はキャンセルできません。自動操作の許可やアクセス権の問題で一部だけ処理され'
        'る場合があり、Finder の処理が続いている可能性もあります。'
    ),
    'bin_preparing': '{root} の正確なゴミ箱スコープを確認しています…',
    'bin_no_approval': '完全に空ではないゴミ箱の承認はありません。リフレッシュしてもう一度見直してください。',
    'bin_scope_first': (
        'これらの現在のユーザーのゴミ箱ペイロード/受信スコープを空にしますか?\n\n{root}\n\n論理ペイロード: {s'
        'ize}\nアイテム: {count}'
    ),
    'bin_scope_irreversible': (
        '確認した次の範囲の内容を完全に削除しますか？\n\n{root}\n\n内容の論理サイズ: {size}\n項目数: {count}'
        '\n\nこの操作は元に戻せません。リンク先をたどらず、リンク自体を削除します。変更された項目は処理しませ'
        'ん。失敗時には一部だけ処理される場合があります。開始後はごみ箱を空にする操作をキャンセルできません。'
    ),
    'bin_partial': '{count} 件のレビュー済みアイテムを削除しました。残りの失敗: {reason}',
    'bin_empty': '選択したドライブのごみ箱を空にする…',
    'bin_first': '{root}?\n\n報告されたサイズ: {size}\nアイテム: {count} のごみ箱を空にします',
    'bin_irreversible': (
        '{root} のごみ箱に現在あるすべての項目を完全に削除しますか？\n\n報告されたサイズ: {size}\n項目数: {co'
        'unt}\n\nこの操作は元に戻せません。OS の処理中に新しく入った項目も削除される場合があります。開始後は '
        'OS の処理をキャンセルできません。'
    ),
    'bin_running': '{root} のごみ箱を空にしています。 OSの操作を待っています…',
    'bin_failed': '空化が完了しませんでした: {reason}',
    'bin_hint': (
        'マウントされたボリュームを 1 つ選択します。 Windows は、現在のユーザーの OS ビンを空にします。 Linux'
        ' インベントリはファイル/情報スコープを認識しました。 2 つの質問は、永久削除前の正確な範囲と合計を示'
        'します。 「停止」はアンケートをキャンセルします。アクティブな空化が完了する必要があります。 macOS は'
        '、グローバル レビュー後にマウントされた Finder ゴミ箱をすべて空にします (ネイティブ検証保留中)。容量'
        '/ビンの値は後で更新されます。再スキャンしてメイン ツリーを更新します。'
    ),
    "forecast_column": "空き容量の予測",
    "forecast_record": "予測のために使用量を記録する",
    "forecast_record_tip": (
        "この概要を開くたびに、FileTree は各ドライブの時刻・使用量・総容量のバイト数をローカルのデータフォルダーに"
        "保存します。1 ドライブにつき最大 {hours} 時間に 1 件、最大 {count} 件です。ファイルの情報は保存しません。"
    ),
    "forecast_growing": "1 日あたり約 {rate} — {date} ごろにいっぱい",
    "forecast_not_soon": "1 日あたり約 {rate} — {years} 年以内にはいっぱいになりません",
    "forecast_stable": "増えていません",
    "forecast_not_enough": "履歴がまだ足りません (数日必要です)",
    "forecast_off": "記録はオフです",
    "forecast_unknown": "不明 (使用量が報告されていません)",
    "forecast_off_tip": "下の記録をオンにすると、このドライブの使用量の履歴がたまります。",
    "forecast_unknown_tip": "システムがこのドライブの使用量を報告しなかったため、記録していません。",
    "forecast_not_enough_tip": (
        "現在 {count} 件、{days} 日分です。予測には {needed_days} 日以上にわたる {needed} "
        "件以上が必要です。この概要を開くと記録されます (最大数時間に 1 件)。"
    ),
    "forecast_estimate_tip": (
        "{days} 日分・{count} 件の使用量からの推定です (最大で直近 {window} "
        "日、総容量が最後に変わって以降)。最近の速度が続くと仮定しており、保証ではありません。"
    ),
    "forecast_newer": "空き容量の履歴は新しいバージョンの FileTree で保存されたため、変更せずに残しています。",
    "forecast_save_failed": "空き容量の履歴を保存できませんでした: {reason}",
    "forecast_unavailable": "空き容量の履歴を使用できません: システムがアプリのデータフォルダーを提供していません。",
    'action_volumes': 'ドライブの概要…',
    'action_volumes_tip': 'マウントされたボリューム、容量、割り当て単位、およびごみ箱の合計を検査する',
    'volume_root': 'マウントされたルート',
    'volume_name': 'ボリューム名',
    'volume_fs': 'ファイルシステム',
    'volume_total': '合計',
    'volume_used': '中古品',
    'volume_free': 'ご利用いただけます',
    'volume_cluster': '割り当て単位',
    'volume_trash': 'ごみ箱のバイト数',
    'volume_trash_count': 'アイテムをビンに入れる',
    'volume_reading': 'マウントされたボリュームとごみ箱の合計を読み取り中…',
    'volume_summary': (
        '{count} のうち、マウントされた {shown} 個のボリュームを表示しています。ダブルクリックしてスキャンし'
        'ます。'
    ),
    'volume_trash_partial': '合計は不明 ({known} は判明)',
    'volume_hint': (
        'OS 容量のスナップショット。利用可能なスペースには予約または割り当てが含まれない場合があります。マウ'
        'ントを繰り返すと容量を共有できるため、行を合計しないでください。 Windows アロケーション ユニットはク'
        'ラスターです。 POSIX ユニットはファイルシステムのフラグメントであり、最適な転送サイズではありません'
        '。ゴミ箱には、再利用可能な領域ではなく、OS によって報告された Windows 合計または既知の POSIX 論理ペ'
        'イロード バイトが表示されます。ディレクトリ/受信メタデータと共有割り当ては除外されます。エラーは不明'
        'のままです。 Stop は現在の OS 呼び出しを待ちます。キャンセルされたアンケートは破棄されます。 Ctrl+C '
        'で行をコピーします。ここでは空にするアクションは提供されません。'
    ),
    'action_disks': '物理ディスク…',
    'action_disks_tip': '物理ドライブ、その正常性とパーティション構成を確認します (読み取り専用)',
    'disks_title': '物理ディスク',
    'disks_hint': '読み取り専用: FileTree はシステムが報告する各物理ドライブの情報を表示するだけで、ディスク上の'
                  '内容は何も変更しません。シリアル番号は表示しません。',
    'disks_reading': '物理ディスクを読み取り中…',
    'disks_summary': '見つかった物理ディスク: {count} 台。',
    'disks_none': 'システムは物理ディスクを報告しませんでした。',
    'disks_problem_unsupported': 'このシステムでは物理ディスクを一覧表示できません。',
    'disks_problem_tool_missing': 'ディスクを一覧表示するシステム ツールが見つかりません。',
    'disks_problem_timeout': 'ディスクの一覧表示に時間がかかりすぎました。[最新の情報に更新] を試してください。',
    'disks_problem_failed': 'システムはディスクを一覧表示できませんでした。',
    'disks_problem_malformed': 'システムが報告したディスク一覧を読み取れませんでした。',
    'disks_refresh': '最新の情報に更新',
    'disks_select': 'ディスクを選ぶと、正常性とパーティションが表示されます。',
    'disks_col_disk': 'ディスク',
    'disks_col_model': 'モデル',
    'disks_col_media': '種類',
    'disks_col_bus': '接続',
    'disks_col_style': 'パーティション テーブル',
    'disks_col_size': 'サイズ',
    'disks_col_health': '正常性',
    'disks_col_number': '#',
    'disks_col_kind': 'パーティションの種類',
    'disks_col_label': 'ラベル',
    'disks_col_mounts': 'ドライブ文字 / マウント ポイント',
    'disks_col_fs': 'ファイル システム',
    'disks_col_offset': '開始位置',
    'disks_media_ssd': 'SSD',
    'disks_media_hdd': 'ハード ディスク (HDD)',
    'disks_media_unknown': '不明',
    'disks_unknown': '不明',
    'disks_state_healthy': '正常',
    'disks_state_warning': '警告',
    'disks_state_unhealthy': '故障の兆候',
    'disks_state_unknown': '不明',
    'disks_health_line': '正常性: {state}。{meaning}',
    'disks_meaning_healthy': 'ドライブは問題を報告していません。ドライブは予告なく故障することがあるため、'
                             'バックアップは続けてください。',
    'disks_meaning_warning': 'ドライブが問題を報告しています。早めに重要なファイルをバックアップし、'
                             'メーカーのツールで確認してください。',
    'disks_meaning_unhealthy': 'ドライブが故障しかけていると報告しています。今すぐ重要なファイルをバックアップし、'
                               '交換を検討してください。',
    'disks_meaning_unknown': 'システムがこのドライブの正常性を報告しないため、FileTree には判断できません。',
    'disks_counters': '温度: {temperature} · 摩耗: {wear} · 電源投入時間: {hours}',
    'disks_temperature_value': '{degrees} °C',
    'disks_wear_value': '定格寿命の {percent}% を使用',
    'disks_hours_value': '{hours} 時間',
    'disks_not_reported': '取得できません',
    'disks_counters_denied': 'このシステムでは、温度、摩耗、電源投入時間の取得に管理者権限が必要です。'
                             '表示するには FileTree を管理者として再起動してください。ここでは権限を求めません。',
    'disks_counters_missing': 'このドライブまたはドライバーは、温度、摩耗、電源投入時間を報告しません。',
    'disks_counters_unsupported': 'このシステムでは、摩耗と電源投入時間の取得に管理ツール (smartctl など) が'
                                  '必要ですが、FileTree はそれらを実行しません。',
    'disks_no_partitions': 'パーティションは報告されませんでした。',
    'disks_free_space': '未割り当て',
    'disks_bar_name': 'パーティション構成',
    'disks_tool_management': 'ディスクの管理…',
    'disks_tool_optimize': 'ドライブの最適化…',
    'disks_tool_volumes': 'ディスクとボリュームの設定…',
    'disks_tool_storage': 'ストレージの設定…',
    'action_export_report_html': 'スキャンレポート(HTML)…',
    'action_export_report_html_tip': '3 つのチャート画像が埋め込まれた自己完結型レポートを保存する',
    'action_export_report_xlsx': 'スキャンレポート（Excel）…',
    'action_export_report_xlsx_tip': 'レポート リストを別の Excel ワークシートに保存する',
    'html_filter': 'HTML レポート (*.html)',
    'xlsx_filter': 'Excel ワークブック (*.xlsx)',
    'report_title': 'FileTree スキャン レポート',
    'report_note': (
        '既知の記録された範囲のみ。配分は目安です。見出しのカウントは、表示/合計を示します。最上位のフォルダ'
        'ーが重なっています。行を追加しないでください。最大のファイルとフォルダーは 1,000 に制限されます。フ'
        'ァイルタイプは10,000まで。サイズはバイトです。年齢は、最終アクセスではなく、記録された変更時刻を使用'
        'します。利用できない日付は、既存の最も古い年齢グループに属します。 HTML チャートには、スキャン ルー'
        'ト全体が境界付きジオメトリで表示されます。 Excel テキストはエスケープされ、制御文字は 16 進数で表示'
        'され、セルは 32,767 文字に制限され、16 桁以上の整数は正確なテキストとして保存されます。'
    ),
    'report_bytes': '論理バイト',
    'report_allocated': '割り当てられたバイト数 (推定)',
    'report_created': 'レポートが作成されました',
    'report_reference': '年齢の目安',
    'report_skipped': 'スキップされたフォルダー',
    'report_denied': '読み取り不可能なフォルダー',
    'report_pending': '保留中のフォルダー',
    'report_summary': '概要',
    'report_notes': '注意事項',
    'report_field': 'フィールド',
    'report_value': '値',
    'report_top_folders': '最大のフォルダー (重複)',
    'report_categories': 'カテゴリー',
    'action_projects': 'プロジェクトと再構築可能なデータ…',
    'action_projects_tip': '記録されたプロジェクト、Git、生成されたデータのサイズを検査する',
    'project_path': '企画・運営店舗',
    'project_kind': '検出された種類',
    'project_other': 'ソース・その他',
    'project_git': '.git',
    'project_generated': '再構築可能なデータ',
    'project_coverage': '適用範囲',
    'project_partial': '不完全',
    'project_recorded': '記録範囲',
    'project_hint': (
        '既知の論理バイトのみ。ネストされたプロジェクトは重複します。 Git ポインター ファイルでは、外部メタデ'
        'ータが省略されます。生成されたデータにはカスタム ファイルが含まれる場合があります。移動する前に確認'
        'してください。 Maven、グローバル Gradle、Docker ストアは個別に表示されます。内容物は使い捨てではない'
        'と考えられます。'
    ),
    'project_reading': '記録されたプロジェクト データを検査しています…',
    'project_summary': '検出された {count} のうち最大のプロジェクト/ストア {shown} を表示しています。',
    'project_review': '適格な再構築可能なエントリを確認してください…',
    'project_review_count': (
        '現在の年齢、適用範囲、クリーンアップ ポリシーに基づいて対象となる {count} 件のうち、最大 {shown} 件'
        'のエントリを確認します。停止したスキャンではエントリを提案できません。'
    ),
    'project_git_kind': 'Git',
    'project_python': 'パイソン',
    'project_node': 'Node.js',
    'project_rust': 'さび',
    'project_jvm': 'JVM',
    'project_conda': 'コンダプロジェクト',
    'project_python_environment': 'Python環境',
    'project_conda_environment': 'Conda環境',
    'project_maven_store': 'メイブンストア',
    'project_gradle_store': 'グローバル Gradle ストア',
    'project_docker_store': 'Dockerデータ',
    'action_git_history': 'Git の履歴…',
    'action_git_history_tip': 'すべての Git 参照から到達可能な最大のオブジェクトを検査する',
    'git_oid': 'オブジェクトID',
    'git_kind': 'オブジェクトの種類',
    'git_length': '非圧縮長さ',
    'git_type_blob': 'ファイルの内容 (BLOB)',
    'git_type_tree': 'ディレクトリリスト (ツリー)',
    'git_type_commit': 'コミット',
    'git_type_tag': '注釈付きタグ',
    'git_hint': (
        '読み取り専用の Git 配管はすべての参照を検査し、最大 1,000 個のオブジェクトを保持します。サイズは非圧'
        '縮の長さであり、ディスク割り当てや回復可能な領域ではありません。 Git のオブジェクト名のヒントがあい'
        'まいになる可能性があるため、名前は省略されています。 Ctrl+C はオブジェクト ID/行をコピーします。オプ'
        'ションのロック、自動メンテナンス、遅延ネットワーク取得は無効になっています。 Git は --no-lazy-fetch '
        'をサポートする必要があります。リポジトリ所有権エラーはバイパスされません。停止はキャンセルします。こ'
        'こでは gc が実行されることはありません。'
    ),
    'git_reading': 'Git 履歴を検査しています…',
    'git_summary': '{count} 件中 {shown} 件の到達可能なオブジェクトを表示しています。非圧縮合計 {size}。',
    'git_gc_loose': (
        'Git gc は {count} 個の孤立したオブジェクトを統合することがありますが、これらの最大のオブジェクトは参'
        '照から到達可能なままであり、削除されません。実際の節約量やその他の到達不能/reflog データは不明です。'
    ),
    'git_gc_packed': (
        '固定するためのばらばらの物体はありません。 Git gc は、refs がこれらのオブジェクトを保持している間、'
        'これらのオブジェクトを削除しません。その他の到達不能/reflog データと実際の節約量は測定されませんでし'
        'た。'
    ),
    'git_failed': 'Git インスペクションが失敗しました: {reason}',
    'tree_filter_placeholder': '展開済みフォルダーを絞り込み…',
    'tree_filter_hint': (
        'すでに展開されているフォルダー内でのみ名前を照合します (大文字と小文字は区別されません)。祖先は目に'
        '見えるままになります。折りたたまれたコンテンツは検索されません。フィルタをクリアしてツリーを復元しま'
        'す。チャート/リストで非表示のエントリを選択すると、フィルターがクリアされます。スキャンの合計とエク'
        'スポートは変更されません。'
    ),
    'action_live_compare': '2 つのフォルダーを比較…',
    'action_live_compare_tip': '新しい相対パスを比較し、要求されたファイルのペアのみを検証します',
    'compare_choose_left': '左側のフォルダーを選択してください',
    'compare_choose_right': '適切なフォルダーを選択してください',
    'compare_relative': '相対パス',
    'compare_state': '比較',
    'compare_left_size': '左のサイズ',
    'compare_right_size': '適切なサイズ',
    'compare_left_time': '左が変更されました',
    'compare_right_time': '右修正',
    'compare_roots': '左: {left}\n右: {right}',
    'compare_hint': (
        '読み取り専用: 正確な Unicode/大文字と小文字の名前が一致します。リンクはたどられません。サイズや時間'
        'が等しいことは、内容が等しいことを証明するものではありません。ファイル ペアを選択し、Stop が利用可能'
        'な状態で完全なハッシュを確認します。変更され、読み取り不能になり、既知のクラウド ファイルは利用でき'
        'ないままになります。結果は、このスキャン/検証時間を指します。コピー、移動、同期は実行されません。 Ct'
        'rl+C で行をコピーします。 CSV は、表示されている行のみ (最大 10,000 行) をエクスポートします。'
    ),
    'compare_reading': '両方のフォルダーをスキャンしています…',
    'compare_error': '比較またはエクスポートに失敗しました: {reason}',
    'compare_hashing': '選択したファイル ペアを確認しています…',
    'compare_verify': '選択した内容を確認する',
    'compare_summary': '{count} 件中 {shown} 件の相対パスを表示しています (制限 10,000)。',
    'compare_incomplete': '補償内容は不完全です。読み取り不可能なスコープ内で欠落しているパスは不明のままです。',
    'compare_unavailable': '利用できないか変更されました',
    'compare_link': 'リンク;内容が読まれていない',
    'compare_only_left': '左側のみ',
    'compare_only_right': '右側のみ',
    'compare_different_kind': 'さまざまなエントリータイプ',
    'compare_folder': '両面にフォルダーあり',
    'compare_different_size': 'さまざまなサイズ',
    'compare_different_time': 'さまざまな時代。内容未チェック',
    'compare_unchecked': '内容は未確認',
    'compare_identical': '完全なハッシュの一致',
    'compare_different_bytes': '異なる内容',
    'problem_mount_boundary': 'マウント境界: コンテンツはスキャンされません',
    'action_special_files': 'クラウドと特殊ファイル…',
    'action_special_files_tip': '記録されたリコール、オフライン、圧縮およびスパース ファイルの状態を検査する',
    'special_states': '記録状態',
    'special_content_size': 'コンテンツ全体のサイズ',
    'special_recall': 'アクセス時にリコールされる可能性があります',
    'special_offline': 'オフライン',
    'special_compressed': '圧縮された',
    'special_sparse': 'まばらな',
    'special_allocation_low': '割り当てが低くなります。原因不明',
    'special_reading': '記録されたファイルのメタデータを読み取り中…',
    'special_hint': (
        'このリストはスキャン メタデータのみを使用します。ファイルを開いたりダウンロードしたりすることはあり'
        'ません。リコール/オフライン フラグは、OneDrive、Dropbox、またはその他のプロバイダーを記述することが'
        'できます。プロバイダーと、すでにローカルにどれだけあるのかを推測することはできません。コンテンツ全体'
        'のサイズは、オンライン コンテンツを含む論理長です。ダウンロード後の割り当ては不明です。まばらなホー'
        'ル、圧縮、および常駐データにより、割り当てが削減される可能性があります。リコール/オフライン エントリ'
        'のディスク上のゼロは推定値であり、クラウド割り当ての測定値ではありません。ダブルクリックすると、スキ'
        'ャンされたエントリが選択されます。 Ctrl+C は選択した行をコピーします。'
    ),
    'special_summary': (
        '{count} 件中 {shown} 件の一致するファイルを表示しています。全コンテンツ {size};割り当て {allocated} '
        'を記録しました。利用できないファイル メタデータ: {unknown}。最大の 1,000 が保持されます。'
    ),
    'special_partial': 'スキャン範囲は不完全です。表示されていないファイルは不明のままです。',
    'action_shell_integration': 'エクスプローラー統合…',
    'action_shell_integration_tip': (
        'エクスプローラーのフォルダー メニューで [FileTree でスキャン] を追加または削除します'
    ),
    'shell_enabled': 'エクスプローラーのフォルダー メニューに FileTree でスキャンを追加',
    'shell_scan': 'FileTree でスキャン',
    'shell_hint': (
        '変更を保存するのは、アカウントのフォルダー メニューのみです。管理者権限は必要ありません。 Windows 11'
        ' で、[その他のオプションを表示] を確認します。エントリを削除するには、ここでこれをオフにします。実行'
        '可能ファイルまたはソース チェックアウトを移動した後、再度登録します。開始済みの保存が完了してから閉じます。'
    ),
    'shell_failed': 'Explorer の統合を変更できませんでした。\n{reason}',
    'menu_properties': 'プロパティ',
    'properties_failed': 'Windows は次のプロパティを開けませんでした:\n{path}',
    'menu_theme': 'テーマ',
    'theme_system': 'システム',
    'theme_light': 'ライト',
    'theme_dark': 'ダーク',
    'menu_text_size': '文字サイズ',
    'text_size_larger': '大きく',
    'text_size_smaller': '小さく',
    'text_size_reset': 'システムのサイズに戻す',
    'text_size_percent': '{percent}%',
    'text_size_default': '{percent}%（システムのサイズ）',
    'chart_access_keys': (
        '矢印キーでレンダリングされたエントリを選択します。 Enter を押すとフォルダーが開きます。バックスペー'
        'スが上がります。グループ化されたエントリまたは非表示のエントリにはフォルダ ツリーを使用します。'
    ),
    'chart_access_tree_keys': (
        'Up/Down でカードを選択します。右/左でフォルダーを展開/折りたたみます。 Enter を押すとフォルダーが開'
        'きます。バックスペースが上がります。'
    ),
    'chart_access_folder': '表示中のフォルダー: {path}',
    'chart_access_selected': (
        '選択済み: {path}。サイズ {size};ディスク {allocated} 上。 {files} ファイル、{folders} フォルダー。'
    ),
    'system_file_hibernate': (
        '休止状態と高速スタートアップ状態。 Windows がこのファイルを管理します。管理者は、powercfg /hibernate'
        ' off を使用して休止状態を無効にすることができます。これにより、休止状態も削除され、高速スタートアッ'
        'プに影響を与える可能性があります。 FileTree は電源設定のみを開きます。'
    ),
    'system_file_pagefile': (
        '仮想メモリのバッキング ファイル。 Windows はサイズを自動的に管理できます。 [詳細設定] タブの [パフォ'
        'ーマンス設定] で [仮想メモリ] を確認します。これを減らすと、アプリケーションやクラッシュ ダンプに影'
        '響を与える可能性があります。'
    ),
    'system_file_swapfile': (
        'Windows スワップ バッキング ファイル (一時停止されたアプリ データを含む)。 Windows は仮想メモリと合'
        'わせて管理します。システム メモリの設定を削除するのではなく、見直してください。'
    ),
    'system_file_old': (
        '以前の Windows インストール。 「ディスク クリーンアップ」→「システム ファイルのクリーンアップ」で以'
        '前の Windows インストールを確認します。これを削除すると、そのインストールに戻ることができなくなりま'
        'す。'
    ),
    'system_file_recycle': (
        '削除されたエントリは、ごみ箱が空になるまでディスク領域を占有します。ごみ箱またはストレージ センスを'
        '確認します。空にすることは永続的です。'
    ),
    'system_file_restore': (
        'システム メタデータ、復元ポイント、シャドウ コピー。 「システム保護」→「構成」を確認して、復元ポイン'
        'トの制限を設定します。バックアップ所有のシャドウ コピーには、独自のバックアップ ツールが必要な場合が'
        'あります。未読のバイトは不明のままです。'
    ),
    'system_file_winsxs': (
        'Windows コンポーネント ストア。多くのエントリは Windows ファイルとハード リンクを共有しているため、'
        '名前ごとの合計が個別のストレージを過大評価する可能性があります。 Windows [ディスク クリーンアップ] →'
        ' [システム ファイルのクリーンアップ] で [アップデート クリーンアップ] を使用します。コンポーネントを'
        '手動で削除しないでください。'
    ),
    'system_file_updates': (
        'Windows ダウンロードデータを更新します。 Windows を確認してください。 [ディスク クリーンアップ] → ['
        'システム ファイルのクリーンアップ] を使用して一時ファイルを更新します。アクティブなダウンロードの管'
        '理は更新サービスに任せてください。'
    ),
    'system_file_delivery': (
        'Windows アップデートとアプリの配信の最適化ダウンロード キャッシュ。ディスク クリーンアップで配信最適'
        '化ファイルを確認します。 Windows はアクティブな転送を管理します。'
    ),
    'system_tool_power': '電源設定を開きます…',
    'system_tool_memory': '詳細なシステム設定を開きます…',
    'system_tool_cleanup': 'ディスククリーンアップを開きます…',
    'system_tool_storage': 'ストレージセンスを開く…',
    'system_tool_restore': 'オープンシステム保護…',
    'system_tool_failed': 'Windows ツールを開けませんでした。',
    'trash_skip_system_managed': (
        'Windows はこのエントリを管理します。代わりに詳細でシステム ツールを使用してください'
    ),
    'type_locations_title': 'フォルダーを含む (最大 1,000)',
    'type_location_size': '適合サイズ',
    'type_locations_tip': (
        '合計には、各フォルダー内の直接一致するファイルが含まれます。サブフォルダーは重複せずに別々に作成され'
        'ます。'
    ),
    'action_export_list': '現在のリスト (CSV)…',
    'action_export_list_tip': 'アクティブなリストのすべての行を、表示されているフィルターと並べ替え順に保存します。',
    'list_changed': 'キャプチャ中にリストが変更されました。もう一度エクスポートまたはコピーしてみてください。',
    'details_title': '詳細',
    'details_empty': 'エントリを選択して詳細を表示します',
    'details_live': 'スキャンが終了すると配信可能になります。',
    'details_loading': 'タイプと年齢分布を計算しています…',
    'details_recorded': (
        '記録されたファイルの合計のみ。未読のエントリはこれらのディストリビューションの外にあります。フォルダ'
        'ーの変更は最も新しい記録日です。'
    ),
    'details_bucket': '{label}: {size} · {count} ファイル',
    'breadcrumbs_back': '戻る (Alt+左)',
    'breadcrumbs_forward': '進む (Alt+右)',
    'breadcrumbs_more': '…',
    'breadcrumbs_more_tip': '以前の先祖を表示する',
    'action_print_view': '現在のビューを印刷…',
    'action_print_view_tip': 'システムの印刷ダイアログを使用して、表示された結果を 1 ページに印刷します',
    'action_export_view_pdf': '現在のビュー (PDF)…',
    'action_export_view_pdf_tip': '表示された結果を 1 つの適合 PDF ページに保存します',
    'pdf_filter': 'PDFドキュメント(*.pdf)',
    'view_pdf_exported': '保存された現在のビュー: {path}',
    'print_failed': 'ビューを印刷できませんでした: {reason}',
    'print_submitted': 'プリンターに送信されたビュー',
    'action_export_chart_png': '画面上のグラフ (PNG)…',
    'action_export_chart_png_tip': '現在のビューポートを含む表示されているグラフを保存します。',
    'action_export_chart_svg': '棒グラフまたはサンバースト (SVG)…',
    'action_export_chart_svg_tip': '完全に囲まれたバーまたはリングをベクトル図形およびテキストとして保存',
    'png_filter': 'PNG画像(*.png)',
    'svg_filter': 'SVG画像(*.svg)',
    'graphic_exported': '保存されたチャート: {path}',
    'treemap_colours_age': '修正された年齢による',
    'age_colour_unknown': '日付不明',
    'age_colour_tip': (
        '変更されてからの経過時間。フォルダーの色には、記録された最新の変更が使用されます。灰色は使用可能な日'
        '付がないことを意味します。グループ化されたタイルは灰色のままです。'
    ),
    'action_gentle': '低負荷スキャン',
    'action_gentle_tip': '新しいスキャンの CPU と I/O の優先順位が低くなります。もっと時間がかかるかもしれない',
    'scan_priority_warning': 'スキャンの注意事項: {reason}',
    'scan_pause': '一時停止',
    'scan_resume': '再開',
    'scan_pause_tip': (
        '新しいフォルダーの読み取りを一時停止します。現在の読み取りが終了します。一時停止中に動作を停止します'
        '。'
    ),
    'scan_paused': '一時停止 — {progress}',
    'scan_analysing': 'フォルダーの読み取りが完了しました。結果を分析中…',
    'column_drive_share': 'ドライブの%',
    'columns_reset': '列をリセット',
    'drive_share_tip': (
        '論理バイトをボリュームの合計容量で割った値。ハードリンク名は個別にカウントされます。これは割り当てら'
        'れたスペースでも回復可能なスペースでもありません。容量が利用できないか古い場合は不明です。'
    ),
    'action_recent_actions': '最近の操作…',
    'action_recent_actions_tip': '保持されている操作メタデータを検査し、編集された監査レポートをエクスポートします',
    'journal_time': '時間 (UTC)',
    'journal_source': '元のパス',
    'journal_identity': 'デバイス/ファイルのアイデンティティ',
    'journal_result': '結果',
    'journal_detail': '詳細',
    'journal_destination': 'ゴミ箱の送り先',
    'journal_reason_duplicates': '明示的な重複の決定',
    'journal_status_approved': '結果が不明 (承認済みのみ)',
    'journal_status_moved': 'ゴミ箱に移動しました',
    'journal_status_skipped': 'スキップされました',
    'journal_status_failed': 'プラットフォームの移動に失敗しました',
    'journal_reading': '保持されたアクションを読み取り中…',
    'journal_hint': (
        '最新の 500 件のアクション。メタデータのみ、90 日間 / 50 MB 保持されます。承認のみのイベントの最終結'
        '果は不明です。記録されたゴミ箱パスは復元を保証しません。'
    ),
    'journal_summary': (
        '{count} アクションが表示されました。 {invalid} レコードが破損しており、{unavailable} セグメントが使'
        '用できません。'
    ),
    'journal_read_failed': '操作ジャーナルを読み取れませんでした: {reason}',
    'journal_write_failed': (
        'ジャーナルの書き込みまたは保存に失敗しました。残りの動きは可能な限り停止されました。最近のアクション'
        'が不完全である可能性があります。\n\n{reason}'
    ),
    'trash_skip_journal': '承認されたアクションを記録できませんでした。何も動かなかった',
    'journal_export': '編集されたCSVをエクスポート…',
    'journal_exported': 'ホーム ディレクトリのプレフィックスを編集して保存された監査レポート。',
    'duplicate_folder_match': '{copy} = {original} ({size}、{files} ファイル; 一致する検索スナップショット)',
    'duplicate_folder_tip': (
        '一致する名前、サイズ、検証済みのハッシュ、および空のフォルダー構造。読み取り専用。クリーンアップの承'
        '認ではありません。'
    ),
    'duplicates_keep_selected': '選択したコピーを残す',
    'duplicates_kept_name': '残す: {name}',
    'duplicates_kept_path': '残すコピー: {path}。',
    'duplicates_choose_keeper': 'エクストラを選択する前に、このグループで保持されているコピーを選択してください。',
    'duplicates_group_blocked': 'グループはそのまま残されました。再スキャンが必要です: {reason}',
    'trash_skip_duplicate_choose': '保存されたコピーを選択し、グループを再度確認します',
    'trash_skip_duplicate_keep': '保存されたコピーが選択されました。グループはそのまま残されました。再スキャン',
    'trash_skip_duplicate_unverified': 'このグループには検証済みのハッシュがありません。再スキャンして再度検索する',
    'trash_skip_duplicate_hard_links': (
        'コピーにはハードリンク エイリアスが含まれます。グループはそのまま残されました。再スキャン'
    ),
    'trash_skip_duplicate_content': (
        'グループの内容が変更されたか、再ハッシュできませんでした。再スキャンして再度検索する'
    ),
    'menu_options': 'オプション',
    'action_cleanup_policy': 'クリーンアップポリシー…',
    'action_cleanup_policy_tip': 'ルールを有効にし、最低年齢を変更し、クリーンアップ提案からパスを除外します。',
    'policy_enabled': '有効',
    'policy_age': '最低経過日数（日数）',
    'policy_age_for': '{rule} の最低年齢',
    'policy_enabled_for': '{rule} を有効にする',
    'policy_hint': (
        'ポリシーの変更は提案のみに影響します。手動リスク ルールはチェックされないままになります。保存する前'
        'にプレビューします。'
    ),
    'policy_exclusions': (
        'これらのパスまたは名前は決して提案しないでください (1 行に 1 つ、パスは絶対パスである必要があります)'
        '。スキャンは変更されません。'
    ),
    'policy_preview': '変更のプレビュー',
    'policy_import': 'インポートポリシー JSON…',
    'policy_preview_needed': '保存する前に現在の設定をプレビューします。',
    'policy_preview_running': '候補数と論理サイズを比較しています…',
    'policy_preview_result': (
        '{added} 候補を追加します ({size})。 {removed} 候補 ({removed_size}) を削除します。何も動かなかった。'
    ),
    'policy_preview_partial': 'スキャンは不完全です。表示されていない候補とバイトは不明のままです。',
    'policy_no_scan': 'スキャンが完了していません: 効果を測定できません。これらの設定は、今後の提案に適用されます。',
    'policy_invalid': (
        '無効なポリシーです。サポートされているルール キー、はい/いいえフラグ、年齢 0 ～ 36500、および絶対パ'
        'スまたは名前パターンを使用します。'
    ),
    'policy_saved': 'クリーンアップ ポリシーが保存されました。提案が更新されています。',
    'policy_saved_invalid': (
        '保存されたクリーンアップ ポリシーが無効です。オプションでポリシーが確認されるまで、提案は無効になり'
        'ます。'
    ),
    'cleanup_review_manual': '手動で確認する',
    'cleanup_evidence': (
        'カテゴリ: {category};最低有効期間: {days} 日。リスク: {risk}。証拠: {evidence} 再構築/結果: {rebuild'
        '}'
    ),
    'cleanup_category_temporary': '一時ファイル',
    'cleanup_category_cache': 'ダウンロード/生成されたキャッシュ',
    'cleanup_category_application_state': 'アプリケーションの状態',
    'cleanup_category_build': 'プロジェクトのビルド出力',
    'cleanup_category_downloads': 'ユーザーのダウンロード',
    'cleanup_risk_low': 'リスクが低い。移動前に確認する',
    'cleanup_risk_manual': '手動レビュー。チェックなしで開始します',
    'cleanup_rebuild_temp': (
        '所有しているアプリケーションを閉じます。一時データは必ずしも再作成できるわけではありません。'
    ),
    'cleanup_rebuild_browser_cache': (
        'ブラウザを閉じます。キャッシュされたページを再度ダウンロードします。プロフィールとブックマークは除外'
        'されます。'
    ),
    'cleanup_rebuild_thumbnails': 'ファイルマネージャーを閉じます。必要に応じてプレビューが再度生成されます。',
    'cleanup_rebuild_crash_dumps': (
        '必要な衝突証拠を保管してください。過去のクラッシュ ダンプを再作成することはできません。'
    ),
    'cleanup_rebuild_package_caches': (
        'パッケージ マネージャーを使用して再度ダウンロードします。ネットワークアクセスを確認します。パッケー'
        'ジストアは対象外となります。'
    ),
    'cleanup_rebuild_build_output': (
        'プロジェクトの内容と依存関係のロックを確認し、プロジェクトの文書化されたコマンドを使用して再構築しま'
        'す。作成したファイルを保存します。'
    ),
    'cleanup_rebuild_old_installers': (
        'オフラインまたは利用できないインストーラーを維持します。まだ利用可能な場合は、発行者からダウンロード'
        'します。'
    ),
    'cleanup_rebuild_empty_folders': (
        'アプリケーションは空のフォルダーを予期する場合があります。まずその目的を確認してください。'
    ),
    'trash_holder': '{name} (PID {pid})',
    'trash_holders': (
        '{path}: {programs} で開いていることが観察されました。関連するプログラムを自分で閉じて、再試行してく'
        'ださい。'
    ),
    'trash_holders_limited': (
        '{path}: プロセスの可視性は制限されています。他の所有者や原因は不明である可能性があります。'
    ),
    'duplicates_savings': (
        '一意に割り当てられた推定値 {allocated};ゴミ箱 {recoverable} を空にした後に回復可能なファイル データ'
        '。'
    ),
    'duplicates_estimating': '固有の割り当てと回復可能なファイル データを見積もっています…',
    'duplicates_estimate_unavailable': (
        '割り当ての見積もりは利用できません。エクストラを選択する前に、もう一度検索を実行してください。'
    ),
    'duplicates_estimate_assumption': (
        '推定では、明示的に保持されたコピーの選択が使用されます。未決定のグループは不明です。各グループは、移'
        '動前にチェックされ、完全に再ハッシュされます。ハードリンクのエイリアスは決定を妨げます。共有エクステ'
        'ントとディレクトリのメタデータは不明のままです。ゴミ箱に移動してもスペースは空きません。'
    ),
    'capacity_details': '容量の詳細',
    'capacity_summary': 'OS 使用量 {used}、空き容量 {free}、重複を除いた占有量の推定 {unique}。{status}',
    'capacity_estimated': 'ボリューム全体の推定です。内訳が不明な領域は詳細に表示します。',
    'capacity_folder_only': 'フォルダーのみのスキャンです。ボリューム全体の容量と照合できません。',
    'capacity_incomplete': 'スキャンが不完全です。ボリューム全体の容量と照合できません。',
    'capacity_identity_unknown': 'ファイル ID が不明です。ボリューム全体の容量と照合できません。',
    'capacity_capacity_unavailable': 'OS の容量を取得できません。ボリューム全体の容量と照合できません。',
    'capacity_root_changed': 'スキャン対象のルートが変更されています。容量の照合前に再スキャンしてください。',
    'capacity_allocation_exceeds_used': '占有量の推定が OS の使用量を超えているため、容量を照合できません。',
    'capacity_coverage': '{skipped} をスキップしました。 {inaccessible} を読み取れません。保留中 {pending}',
    'capacity_bin_partial': 'ごみ箱の識別または読み取りが不完全です。表示値には確認できたデータだけを含みます。',
    'capacity_explanation': (
        '既知のファイル割り当てには、表示されるごみ箱データが含まれます。ハードリンク名は 1 回カウントされま'
        'す。他のマウントされたボリュームは除外されます。省略されたデータとファイルシステムのメタデータは不明'
        'であり、ゼロではありません。説明されていないデータには、アクセスできないデータ、メタデータ、スナップ'
        'ショット、共有エクステント、および割り当て推定が含まれる場合があります。 OS の容量とファイルはさまざ'
        'まな時点で測定されます。ファイルシステムはスキャン中に変更される可能性があります。利用できない空き容'
        '量は、測定されたメタデータの合計ではなく、報告された合計、使用済みおよび利用可能な空き容量の差です。'
        'これらは、NTFS、ext4、APFS のボリューム検証が保留中の推定値です。'
    ),
    'capacity_row_total': 'OS合計',
    'capacity_row_used': 'OS 使用量',
    'capacity_row_free': 'OS 利用可能な空き容量',
    'capacity_row_unavailable_free': '利用できない空き領域',
    'capacity_row_named_allocated': '名前ごとの占有量の推定',
    'capacity_row_unique_allocated': '重複を除いた占有量の推定',
    'capacity_row_hard_link_overcount': '除外したハードリンクの重複集計',
    'capacity_row_recycle_bin_seen': 'ごみ箱の割り当てが確認されました (含まれています)',
    'capacity_row_foreign_allocated_seen': '他のボリュームのファイル割り当てが確認されました (除外)',
    'capacity_row_unaccounted': '内訳不明の使用量',
    'capacity_row_metadata_bytes': 'ファイルシステムメタデータ / 予約済み',
    'capacity_row_omitted_bytes': '省略されたデータ',
    'capacity_row_other_volumes_bytes': 'その他のマウントされたボリューム',
    'capacity_row_mounts': '別デバイスへのマウント境界',
    'capacity_row_coverage': '検査範囲',
    'review_title': 'クリーンアップ提案を検討する',
    'review_logical_size': '論理サイズ',
    'review_risk': 'リスク',
    'review_risk_low': '低リスク',
    'review_risk_manual': '手動確認が必要',
    'review_details_label': '項目の詳細',
    'review_scope': 'スキャン範囲',
    'review_details': (
        '{path}\n'
        'ルール: {rule}\n'
        '更新日時: {modified}\n'
        '論理サイズ: {logical}; 割り当て推定: {allocated}\n'
        'リスク: {risk}\n'
        '保護: {protection}\n'
        '\n'
        '{consequence}'
    ),
    'review_hint': (
        'あらゆる道筋と結果を見直してください。エントリを保持するにはチェックを外します。 [続行] をクリックす'
        'ると確認が開きます。'
    ),
    'review_select': '移動',
    'review_rule': 'ルール',
    'review_reason': '理由',
    'review_protection': '保護',
    'review_consequence': '結果',
    'review_manual': '手動選択',
    'review_manual_reason': (
        'ユーザーが選択したエントリ。これを削除すると、それに依存するファイルやプログラムに影響が出る可能性が'
        'あります。'
    ),
    'review_not_protected': '保護されたパスが一致しない',
    'review_open_folder': '含まれているフォルダーを開く',
    'review_continue': '確認に進む',
    'review_estimating': '{count} エントリが選択されました。割り当てを見積もっています…',
    'review_summary': (
        '{count} 項目。論理サイズ {logical}、占有量の推定 {allocated}。ごみ箱を空にした後に回収できるファイル'
        'データ: {recoverable}。今すぐ増える空き容量: {free}。共有領域とディレクトリのメタデータは不明です。'
        'ごみ箱へ移動するだけでは空き容量は増えません。'
    ),
    'size_unknown': '不明',
    'trash_running': (
        '承認されたエントリの再検証と移動… [停止] をクリックすると、残りのエントリがキャンセルされます。'
    ),
    'trash_batch_done': (
        '{moved} を移動、{skipped} をスキップ、{failed} に失敗しました。 {size} はごみ箱に移動されました。'
    ),
    'trash_skipped': (
        'これらのエントリはスキップされました。再試行する前にフォルダーを再スキャンしてください:\n{names}'
    ),
    'trash_skip_outside': '現在のスキャンの外側',
    'trash_skip_unverified': '検証されたスキャン ID がありません',
    'trash_skip_incomplete': '不完全なスキャン範囲',
    'trash_skip_missing': 'エントリまたは親がありません',
    'trash_skip_unreadable': 'エントリを読み取ることができません',
    'trash_skip_link': 'エントリまたは親がリンクになりました',
    'trash_skip_kind': 'エントリの種類が変更されました',
    'trash_skip_identity': 'エントリが置き換えられました',
    'trash_skip_changed': 'サイズ、タイムスタンプ、またはフォルダーの内容が変更されました',
    'trash_skip_protected': '解決されたパスには異なる保護があります',
    'trash_skip_cancelled': '操作がキャンセルされました',
    'coverage_complete': (
        'カバレッジ: {size} は {known} フォルダー内で認識されます。 {skipped} はスキップされました、{denied} '
        'はアクセス不能、保留中 {pending} です。'
    ),
    'coverage_partial': (
        '不完全なカバレッジ: {known} フォルダー内で {size} が認識されています。 {skipped} はスキップされまし'
        'た、{denied} はアクセス不能、保留中 {pending} です。省略されたバイトは不明です。クリーンアップの前に'
        '不完全なブランチを再スキャンします。 「すべて選択」は無効になっています。'
    ),
    'problem_hidden_omitted': '非表示のエントリは省略されました。それらの大きさは不明です。',
    'problem_partial_folder': '一部のエントリを読み取れませんでした。このフォルダは不完全です。',
    'app_title': 'FileTree',
    'about_text': (
        '<h3>FileTree {version}</h3><p>ディスク容量がどこにあるかを確認してください。</p><p>MIT ライセンス · '
        '© 2026 JE-Chen</p>'
    ),
    'menu_file': 'ファイル(&F)',
    'menu_export': 'エクスポート(&E)',
    'menu_view': '表示(&V)',
    'menu_unit': 'サイズの単位(&U)',
    'menu_language': '言語(&L)',
    'menu_help': 'ヘルプ(&H)',
    'action_open': 'フォルダーを選択…',
    'action_open_tip': 'スキャンするフォルダーまたはドライブを選択します',
    'action_rescan': '再スキャン',
    'action_rescan_tip': '同じフォルダを再度スキャンして変更を取得します',
    'action_stop': '停止',
    'action_stop_tip': '実行中のスキャンを停止します',
    'action_export_folders': 'フォルダーリスト (CSV)…',
    'action_export_folders_tip': (
        'Excel またはその他のスプレッドシート用に、すべてのフォルダーをそのサイズで保存します'
    ),
    'action_export_largest': '最大のファイル (CSV)…',
    'action_export_largest_tip': '最大のファイルのリストを保存する',
    'action_export_json': 'フォルダー ツリー (JSON)…',
    'action_export_json_tip': 'スクリプトやその他のプログラムのフォルダー ツリーを保存します。',
    'action_trash': 'ごみ箱に移動',
    'action_trash_tip': '選択したファイルとフォルダーをごみ箱に移動します (最初に尋ねられます)。',
    'action_find': '検索…',
    'action_find_tip': 'スキャン内の任意の場所でファイルとフォルダーを名前で検索します',
    'action_quit': '終了',
    'action_quit_tip': '閉じる FileTree',
    'action_hidden': '隠しファイルを含める',
    'action_exclusions': 'スキャン中にスキップ…',
    'action_exclusions_tip': 'スキャンで除外されるフォルダーとフォルダー名 (node_modules など)',
    'exclusions_title': 'スキャン中にスキップする',
    'exclusions_hint': (
        'スキャンではこれらのフォルダーは除外されます。これらのフォルダーはリストされ、グレー表示され、サイズ'
        'は 0 になります。node_modules や *.cache などの名前は、その名前のすべてのフォルダーをスキップします'
        '。フォルダー パスはその 1 つのフォルダーをスキップします。リストは次回のスキャンから適用されます。'
    ),
    'exclusions_add_name': '名前を追加…',
    'exclusions_add_folder': 'フォルダーを追加…',
    'exclusions_remove': '削除',
    'exclusions_name_prompt': 'フォルダー名、*、?許可される:',
    'exclusions_saved': '{count} 件の除外が保存されました。次のスキャンから適用されます。',
    'tooltip_excluded': '{path}\nスキップ: 表示中です → スキャン中はスキップします',
    'action_hidden_tip': '隠しファイルと隠しフォルダーを数える (次回のスキャンに適用)',
    'action_help': '使い方',
    'action_help_tip': 'FileTree への短いガイド',
    'action_about': 'FileTree について',
    'action_about_tip': 'バージョンとライセンス',
    'app_title_admin': 'FileTree (管理者)',
    'action_elevate': '管理者として再起動',
    'action_elevate_tip': 'すべてのフォルダーを読み取ることができるように、管理者権限で FileTree を再度起動します。',
    'action_ask_admin': '起動時に管理者権限を要求',
    'action_ask_admin_tip': (
        'Windows は FileTree の起動時に許可を求めるため、保護されたフォルダーも読み取ることができます'
    ),
    'problems_hint': (
        '一部のフォルダーには管理者権限が必要です。これらも読み取るには、管理者として FileTree を再起動します'
        '。'
    ),
    'elevate_declined': 'FileTree は管理者権限なしでまだ実行されています。',
    "startup_invalid": "要求されたワークスペースを復元できませんでした: {reason}",
    "elevate_waiting": ("Windows の権限確認を承認または拒否してください。"
                        "このウィンドウを閉じても、要求の完了を待ちます。"),
    "elevate_failed": "管理者として FileTree を再起動できませんでした: {reason}",
    'unit_auto': '自動',
    'path_placeholder': 'フォルダーのパスを入力または貼り付けて Enter キーを押します',
    'choose_folder_title': 'スキャンするフォルダーを選択してください',
    'welcome_title': 'ディスク容量がどこに行くのかを確認する',
    'welcome_subtitle': (
        'フォルダーまたはドライブ全体を選択します。 FileTree は、その中のすべてのファイルを合計し、最大のフォ'
        'ルダーとファイルを最初に表示します。'
    ),
    'welcome_choose': 'フォルダーを選択してください…',
    'welcome_drives': 'ドライブ',
    'welcome_drive_tip': '{path} をスキャンします',
    'welcome_drive_free': '合計 {total}、空き容量 {free}',
    'welcome_drive_used': '使用率 {percent}',
    'welcome_recent': '最近スキャンした',
    'welcome_tip': (
        'ヒント: ファイル マネージャーからフォルダーをこのウィンドウにドラッグすることもできます。絶対 UNC 共'
        '有パスを Windows (\\\\server\\share) に貼り付けます。アクセスには現在のアカウントが使用されます。ス'
        'キャン ワーカーはオプションで調整できます。拒否/切断されたブランチは空ではなく、不完全なままになりま'
        'す。'
    ),
    'scan_starting': '開始中…',
    'scan_progress': 'スキャン中… {folders} フォルダー内の {files} ファイル · {size} · {time}',
    'scan_stop': '停止',
    'scan_stopping': '停止中…',
    'scan_cancelled': 'スキャンが停止されました。',
    'scan_stopped_partial': 'スキャンが停止しました: 結果には、これまでに読み取られた内容が表示されます。',
    'scan_failed_title': 'スキャンできません',
    'scan_mount_changed': (
        'マウント境界が変更されたか、検証できませんでした。これらの結果を使用する前に、再度スキャンしてくださ'
        'い。'
    ),
    'scan_failed': 'FileTree は {path} を読み取れませんでした。\n\n理由: {reason}',
    'not_a_folder': '{path} は存在するフォルダーではありません。',
    'duration_seconds': '{value} 秒',
    'duration_minutes': '{minutes} 分 {seconds} 秒',
    'summary': (
        '<b>{path}</b> — {files} ファイルおよび {folders} フォルダー ({time} でスキャン) 内の {size} (ディス'
        'ク上の {allocated})'
    ),
    'summary_live': (
        '<b>{path}</b> — これまでの {files} ファイルと {folders} フォルダー内の {size} (ディスク上の {allocat'
        'ed})'
    ),
    'summary_partial': (
        '<b>{path}</b> — {files} ファイルおよび {folders} フォルダー内の {size} (ディスク上の {allocated}) · '
        '<b>incomplete</b>: スキャンは次の時間に停止されました。 {time}'
    ),
    'tab_chart': 'チャート',
    'chart_treemap': 'ツリーマップ',
    'treemap_levels': 'レベル',
    'treemap_levels_all': 'すべて',
    'treemap_colours': '色',
    'treemap_colours_type': 'ファイルの種類別',
    'treemap_colours_folder': 'フォルダごと',
    'chart_treemap_tip': 'すべてのファイルは、必要なスペースに応じたサイズの長方形として表示されます',
    'chart_bars': '棒グラフ',
    'chart_sunburst': 'サンバースト',
    'chart_tree': 'ツリー',
    'chart_tree_tip': 'フォルダー階層: ブランチを展開、Ctrl+ホイールでズーム、ダブルクリックでフォーカス',
    'tree_orientation': '方向',
    'tree_orientation_horizontal': '左から右へ',
    'tree_orientation_vertical': '上から下へ',
    'tree_more': '{count} 個のフォルダー · {size}',
    'tree_unavailable': 'スキャンされていません',
    'chart_sunburst_tip': (
        '中央にフォルダーがあり、それぞれの深いレベルがリングになります。中央をクリックすると上に移動します'
    ),
    'chart_bars_tip': 'フォルダーのエントリごとに 1 つのバー (最大のものから順)、そのサイズとシェア',
    'bars_empty_folder': 'このフォルダーは空です。',
    'bars_more': '{count} 詳細: {size}',
    'tab_largest': '最大のファイル',
    'scope_folder': '選択したフォルダーのみ',
    'scope_folder_named': '{name} のみ',
    'scope_folder_tip': (
        'スキャン全体ではなく、ツリーで選択したフォルダーの最大のファイル、タイプ、経過時間を表示します'
    ),
    'tab_search': '検索',
    'tab_changes': '変更点',
    'action_compare': '保存したスキャンと比較…',
    'action_compare_tip': (
        '[エクスポート] → [フォルダー ツリー (JSON)] で保存したスキャンを開き、その後の成長を確認します。'
    ),
    'compare_title': '保存したスキャンと比較する',
    'compare_failed': 'このファイルは、FileTree:\n{reason} によって保存されたスキャンではありません。',
    'column_before': '以前',
    'column_now': '現在',
    'column_change': '増減',
    'changes_new': '新しい',
    'changes_gone': '消えた',
    'changes_whole_scan': '(スキャンしたフォルダー)',
    'changes_stop': '比較を終了',
    'changes_running': '比較中…',
    'changes_waiting': 'スキャンが完了すると、比較が行われます。',
    'changes_unknown_time': '未知の時間に',
    'changes_summary': (
        '{path} と比較すると、{when} が保存されました。その後、{before}、現在は {now} ({change})。 {count} フ'
        'ォルダーが変更されました。'
    ),
    'tab_duplicates': '重複ファイル',
    'tab_cleanup': 'クリーンアップ',
    'cleanup_suggestions': '提案',
    'cleanup_select_all': 'すべて選択',
    'cleanup_select_group': 'このグループを選択',
    'cleanup_running': '掃除するものを探しています…',
    'cleanup_hint': '通常、コンテンツが移動できる場所は、スキャン後にここに表示されます。',
    'cleanup_none': 'このスキャンでは何も示唆されません。',
    'cleanup_summary': (
        '{groups} グループ内の {size} 論理サイズ。エントリを選択して、ごみ箱に移動する前にパスと割り当てを確'
        '認します。移動してもすぐにスペースが解放されるわけではありません。'
    ),
    'cleanup_group': '{title} — {size} ({count})',
    'cleanup_temp': '一時ファイル',
    'cleanup_temp_tip': 'しばらく残されたファイルプログラム。まだ実行中のプログラムには必要な場合があります。',
    'cleanup_browser_cache': 'ブラウザのキャッシュ',
    'cleanup_browser_cache_tip': 'ウェブページと写真のコピー。ブラウザは必要に応じてそれらを再度ダウンロードします。',
    'cleanup_thumbnails': 'サムネイルキャッシュ',
    'cleanup_thumbnails_tip': '写真の小さなプレビュー。フォルダを開いたときに再度作成されます。',
    'cleanup_crash_dumps': 'クラッシュダンプ',
    'cleanup_crash_dumps_tip': (
        'プログラムがクラッシュしたときに保存されたメモリ。クラッシュを報告する場合にのみ役立ちます。'
    ),
    'cleanup_package_caches': 'パッケージのダウンロード キャッシュ (pip、npm…)',
    'cleanup_package_caches_tip': (
        'ダウンロードしたパッケージは次回のインストールのために保存されます。必要に応じて再度ダウンロードされ'
        'ます。'
    ),
    'cleanup_build_output': 'ビルド出力 (再ビルド可能)',
    'cleanup_build_output_tip': (
        'インストールされた依存関係とプロジェクトのコンパイルされたファイル。プロジェクトを再度ビルドすると、'
        'それらが再作成されます。'
    ),
    'cleanup_old_installers': 'ダウンロードのインストーラー',
    'cleanup_old_installers_tip': (
        'かなり前に実行された可能性が高いセットアップ ファイル。再度インストールしたものは保管しておいてくだ'
        'さい。'
    ),
    'cleanup_empty_folders': '空のフォルダー',
    'cleanup_empty_folders_tip': '何も入っていないフォルダー、または他の空のフォルダーのみ。',
    'duplicates_min_size': '比較する最小サイズ',
    'duplicates_any_size': 'すべてのサイズ',
    'duplicates_find': '重複を検索',
    'duplicates_stop': '停止',
    'duplicates_select_extra': '余分なコピーを選択',
    'duplicates_select_extra_tip': (
        '選択した残すファイルと成功したチェックでグループ内のエキストラを選択します。次に「削除」を押します'
    ),
    'duplicates_hint': (
        'スキャン内の任意の場所で同じ内容のファイルを検索します。同じサイズのファイルのみが読み取られますが、'
        '読み取りに時間がかかるため、より小さいサイズを選択しない限り、小さなファイルは無視されます。'
    ),
    'duplicates_starting': '同じサイズのファイルを探しています…',
    'duplicates_running': '{total} ファイルの {files} ({bytes} の {read}) を読み取ります…',
    'duplicates_stopped': '検索を中止しました。',
    'duplicates_none': '重複するファイルは見つかりませんでした。',
    'duplicates_summary': '{groups} の重複グループ: 追加コピーの {extra} 論理サイズ。',
    'duplicates_limited': '最も多くの追加スペースを持つ {shown} グループがリストされます。',
    'duplicates_skipped': '{count} 個のファイルを読み取れませんでした。',
    'duplicates_group': '{count} コピー × {size}: {extra} の論理追加コピー サイズ。',
    'search_placeholder': '名前の一部またはパターン:backup、*.mp4、*.iso;*.zip',
    'search_hint': (
        '* と ? を使用して名前の一部またはパターンを入力し、条件またはその両方を選択して、スキャン内の任意の'
        '場所にあるファイルとフォルダーを検索します。'
    ),
    'search_running': '検索中…',
    'search_larger': '最小サイズ（含む）',
    'search_smaller': '最大サイズ（含む）',
    'search_custom_ranges': '範囲を指定…',
    'search_changed_custom': '日付指定',
    'search_exact_bytes': '{value} B（正確）',
    'search_date_format': 'YYYY-MM-DD',
    'search_date_start': '開始日（含む）',
    'search_date_through': '終了日（含む）',
    'search_range_hint': ('空欄は制限なし。サイズは正確なバイト数、日付'
        'はローカル時間（YYYY-MM-DD）です。'),
    'search_range_size_error': ('0 以上、9223372036854775807 B 以下の整'
        '数バイト数を入力してください。1 バイト未満の端数は使えません。'),
    'search_range_order_error': '最小サイズは最大サイズ以下にしてください。',
    'search_range_date_error': ('有効なローカル日付を YYYY-MM-DD 形'
        '式で入力し、開始日を終了日以前にしてください。'),
    'search_range_invalid': ('検索範囲が無効です。サイズまたは日付の範'
        '囲を修正してから検索・保存してください。'),
    'search_no_limit': '制限なし',
    'search_changed': '変更されました',
    'search_changed_any': 'いつでも',
    'search_changed_week': '先週に',
    'search_changed_month': '先月に',
    'search_changed_year': '昨年に',
    'search_changed_stale_year': '1年ではない',
    'search_changed_stale_2y': '2年間ではない',
    'search_changed_stale_5y': '5年間ではない',
    'search_type': '種類',
    'search_type_any': '任意のタイプ',
    'search_show': '表示する',
    'search_kind_any': 'ファイルとフォルダー',
    'search_kind_files': 'ファイルのみ',
    'search_kind_folders': 'フォルダのみ',
    'search_saved': '保存された検索条件',
    'search_saved_none': '(なし)',
    'search_save': '保存…',
    'search_delete': '削除',
    'search_save_title': 'この検索を保存します',
    'search_save_prompt': '名前:',
    'search_none': '何も一致しません。',
    'problems_none': 'このスキャンではすべての項目を読み取れました。確認が必要な問題はありません。',
    'largest_none': '表示するファイルはありません。',
    'search_summary': '{count} 件一致、合計 {size} 件。',
    'search_limited': '最大の {shown} がリストされます。',
    'tab_types': 'ファイルの種類',
    'tab_age': '更新時期',
    'column_age': '最終変更',
    'age_month': '1ヶ月以内',
    'age_half_year': '1～6 か月前',
    'age_year': '6 ～ 12 か月前',
    'age_two_years': '1 ～ 2 年前',
    'age_older': '2年以上前',
    'largest_focus': '表示のみ: {what}',
    'largest_show_all': 'すべて表示',
    'list_files_tip': '行をダブルクリックすると、その最大のファイルが一覧表示されます',
    'tab_problems': '問題点',
    'tab_problems_count': '問題点 ({count})',
    'column_name': '名前',
    'column_size': 'サイズ',
    'column_allocated': 'ディスク使用量',
    'column_share': '親の%',
    'column_share_total': '全体の %',
    'column_files': 'ファイル',
    'column_folders': _JA_FOLDER,
    'column_modified': '更新日時',
    'column_folder': _JA_FOLDER,
    'column_extension': '拡張子',
    'column_type': '種類',
    'column_path': 'パス',
    'column_problem': '問題',
    'problem_access_denied': 'アクセスが拒否されました',
    'problem_not_found': 'もうそこにはいない',
    'problem_path_too_long': 'パスが長すぎます',
    'problem_not_scanned': '未スキャン: スキャンが最初に停止されました',
    'no_extension': '(延長なし)',
    'tooltip_unreadable': '{path}\n読み取れませんでした: {reason}',
    'tooltip_link': '{path}\nリンク: 表示されていますが、フォローされていません',
    'tooltip_not_scanned': '{path}\nスキャンされませんでした: スキャンが最初に停止されました',
    'treemap_empty': '何も見せられない',
    'treemap_up': '↑上へ',
    'treemap_up_tip': '上のフォルダーを表示',
    'treemap_tooltip': '<b>{name}</b><br>{size} (このビューの{share})<br>{path}',
    'treemap_more': '{count} 詳細',
    'treemap_more_tooltip': (
        '<b>{count} より小さいエントリ</b>/{name}、それぞれ小さすぎて描画できません<br>{size} (このビューの {'
        'share})'
    ),
    'treemap_more_open': 'ダブルクリックすると、このフォルダーが単独で表示されます',
    'largest_filter': '名前またはフォルダーでフィルター…',
    'types_all': '全種類',
    'category_images': '写真',
    'category_video': '動画',
    'category_audio': '音楽とオーディオ',
    'category_documents': '書類',
    'category_archives': 'アーカイブとディスクイメージ',
    'category_code': 'コードとデータ',
    'category_programs': 'プログラム',
    'category_other': 'その他',
    'status_selected': '{name}: {size} (そのフォルダーの {share})',
    'status_selected_root': '{name}: {size}',
    'menu_open_item': '開く',
    'menu_reveal': 'ファイルマネージャーで表示',
    'menu_copy_path': 'パスをコピー',
    'menu_show_chart': 'チャートで表示',
    'menu_scan_here': 'このフォルダーだけをスキャン',
    'menu_rescan_here': 'このフォルダーを再スキャン',
    'rescan_done': '再スキャン {name}: {before} → {after}',
    'refresh_notice': 'このスキャンの後、スキャン済みのフォルダー {count} 個の内容が変更されたため、'
                      'そこに表示されているサイズは古い可能性があります。'
                      'FileTree は指示がない限り再スキャンしません。',
    'refresh_now': '変更されたフォルダーを再スキャン',
    'refresh_now_tip': '変更されたフォルダーだけを読み直して結果を更新します',
    'trash_confirm_title': 'ごみ箱に移動',
    'protected_title': 'システムまたはプログラムフォルダー',
    'protected_question': (
        'エントリのうち {count} はシステム フォルダーまたはプログラム フォルダーです。これらを移動すると、シ'
        'ステムまたはプログラムが動作しなくなる可能性があります:\n\n{names}\n\nそれでも移動しますか?'
    ),
    'protected_system': 'オペレーティングシステムの一部',
    'protected_programs': 'インストールされているプログラム',
    'protected_settings': 'プログラムの設定とデータ',
    'protected_profile': 'ユーザーのプロファイルフォルダー',
    'trash_confirm': '「{name}」({size}) をごみ箱に移動しますか?\n\nそこから復元できます。',
    'trash_failed': '「{name}」をごみ箱に移動できませんでした。使用中または読み取り専用である可能性があります。',
    'trash_done': '「{name}」をごみ箱に移動しました: {size} は解放されました。',
    'action_trash_many': '{count} 個の項目をごみ箱に移動',
    'trash_confirm_many': (
        'これらの {count} アイテム (合計 {size}) をごみ箱に移動しますか?\n\n{names}\n\nそこから復元できます。'
    ),
    'trash_more': '…その他 {count}',
    'trash_failed_many': (
        '{count} 個のアイテムをごみ箱に移動できませんでした。これらは使用中または読み取り専用である可能性があ'
        'ります:\n\n{names}'
    ),
    'trash_done_many': '{count} 個のアイテムをごみ箱に移動しました: {size} が解放されました。',
    'permanent_delete': '完全に削除',
    'permanent_delete_tip': (
        '選択したファイルとフォルダーをごみ箱を使わずに完全に削除します'
        '（最初に確認し、元に戻せません）'
    ),
    'permanent_menu_many': '{count} 個の項目を完全に削除',
    'permanent_not_suggestions': (
        '完全に削除は、フォルダーツリー、最大のファイル、検索結果で選んだ項目にだけ使えます。'
        'クリーンアップや重複の候補には使えません。'
    ),
    'permanent_title': '完全に削除',
    'permanent_confirm': (
        '「{name}」({size}) を完全に削除しますか?\n\n{path}\n\n'
        'ごみ箱には移動されず、元に戻せません。'
    ),
    'permanent_confirm_many': (
        'これらの {count} 個の項目 (合計 {size}) を完全に削除しますか?\n\n{names}\n\n'
        'ごみ箱には移動されず、元に戻せません。'
    ),
    'permanent_confirm_folders': (
        'フォルダーは、スキャン時に記録された中身と一緒に削除されます。'
        'スキャン後に追加または変更された項目はそのまま残ります。'
    ),
    'permanent_protected_question': (
        '項目のうち {count} 個はシステムまたはプログラムのフォルダーです。完全に削除すると、'
        'システムやプログラムが動作しなくなる可能性があります:\n\n{names}\n\nそれでも削除しますか?'
    ),
    'permanent_managed': (
        'これらの項目は Windows が管理しているため、FileTree は削除しません。'
        '代わりに詳細に表示されるシステムツールを使ってください:\n\n{names}'
    ),
    'permanent_running': '完全に削除しています… {count} 個の項目を削除しました。Esc で停止します。',
    'permanent_done': (
        '{removed} 個の項目 ({size}) を完全に削除しました。'
        '残した項目: {refused}、失敗: {failed}。'
    ),
    'permanent_report_title': '完全に削除: 残した項目',
    'permanent_failed': 'システムが削除しませんでした: {reason}',
    'permanent_pending': '削除は保留中です: 別のプログラムがまだ開いています',
    'permanent_journal_reason': '明示的な完全削除',
    'permanent_journal_deleted': '完全に削除しました',
    'permanent_journal_partial': '一部を削除 (フォルダーは残しました)',
    'permanent_skip_outside': '現在のスキャン範囲外のため削除しません',
    'permanent_skip_unverified': '確認済みのスキャン識別情報がないため削除しません',
    'permanent_skip_incomplete': 'スキャンでこのフォルダーをすべて読み取れなかったため、中に入りません',
    'permanent_skip_missing': '項目またはそのフォルダーが見つかりません',
    'permanent_skip_unreadable': '項目を読み取れないため削除しません',
    'permanent_skip_link': '項目または上位フォルダーがリンクに変わったため削除しません',
    'permanent_skip_kind': '項目の種類が変わったため削除しません',
    'permanent_skip_identity': 'スキャン後に項目が置き換えられたため削除しません',
    'permanent_skip_changed': 'スキャン後にサイズまたは日時が変わったため削除しません',
    'permanent_skip_protected': '承認の対象外のシステムまたはプログラムのフォルダーのため削除しません',
    'permanent_skip_system_managed': 'Windows が管理する項目のため削除しません',
    'permanent_skip_cancelled': 'この項目の前に停止したため削除しません',
    'permanent_skip_journal': '承認した操作を記録できなかったため、何も削除しませんでした',
    'permanent_skip_read_only': '読み取り専用です。FileTree は属性を解除しないため削除しません',
    'permanent_skip_mount_point': 'マウントされたボリュームまたはマウントポイントのため削除しません',
    'permanent_skip_other_volume': '別のボリューム上にあるため削除しません',
    'permanent_skip_arrived': 'スキャン後に追加されたため残しました',
    'permanent_skip_not_empty': '中に残った項目があるため、フォルダーを残しました',
    'permanent_skip_failed': '中の項目の削除をシステムが拒否しました',
    'status_selected_many': '{count} 個のアイテムが選択されました: {size}',
    'export_title': 'エクスポート',
    'export_running': '{path} に保存中…',
    'csv_filter': 'CSV ファイル (*.csv)',
    'json_filter': 'JSON ファイル (*.json)',
    'export_done': '{count} 行を {path} に保存しました',
    'export_failed': 'ファイルを保存できませんでした。\n\n理由: {reason}',
    'help_title': 'FileTreeの使用方法',
    'help_html': HELP,
    "budget_close": "閉じる",
    "action_folder_budgets": "フォルダー容量予算…", "action_folder_budgets_tip": "上限と前回のスキャン使用量を管理",
    "budget_title": "フォルダー容量予算", "budget_name": "名前", "budget_path": "フォルダーのパス",
    "budget_limit": "上限", "budget_usage": "前回の使用量", "budget_excess": "超過量",
    "budget_status": "状態", "budget_add": "追加", "budget_update": "更新", "budget_delete": "削除",
    "budget_new": "新規", "budget_waiting": "完全スキャン待ち", "budget_unknown": "不明",
    "budget_over": "上限超過", "budget_within": "上限以内", "budget_alerted": "{status}、通知済み",
    "budget_dated_usage": "{when}：{usage}", "budget_invalid_limit": "正確なバイト上限を入力してください",
    "budget_summary": "予算：超過 {over} 件、不明 {unknown} 件",
    "budget_save_error": "フォルダー予算を保存できませんでした：{reason}",
    "budget_unknown_reason": "不明：{reason}", "budget_reason_missing": "スキャンにフォルダーがない",
    "budget_reason_linked": "リンクされたフォルダー", "budget_reason_not_folder": "フォルダーではない",
    "budget_reason_incomplete": "スキャンが不完全",
    "budget_invalid_input": "有効な名前、絶対パス、正確な上限を入力してください",
    "budget_invalid_data": "保存済みの予算データが無効です", "budget_duplicate_path": "このパスには予算があります",
    "budget_missing_rule": "この予算はもうありません", "budget_too_many": "予算が多すぎます",
    "budget_settings_locked": "予算設定は使用中です", "budget_storage_unavailable": "予算の保存先を利用できません",
    "budget_read_failed": "予算設定を読み取れません", "budget_write_failed": "予算設定を保存できません",
    "budget_observed": "観測日時",
    "budget_not_scanned": "未スキャン",
    "budget_changed_limit": "上限を変更済み。完全スキャン待ち",
    "budget_input_unit": "上限の単位（二進）",
    "budget_choose": "フォルダーを選択…",
    "budget_empty": "容量予算はまだありません。フォルダーを選び、名前と上限を入力して追加してください。",
    "budget_edit_hint": (
        '上限は正確な二進単位です。追加や編集ではスキャンしません。使用量は前回の観測値で、現在の値ではありません。上限'
        '変更後は新しい完全スキャンが必要です。'
    ),
    "budget_keep_draft": "未保存の入力を保持しました。保存するか新規を選んでから、別の対象を選択してください。",
    "budget_editing": "選択した予算を編集中",
    "budget_creating": "新しい予算",
    "budget_exact": "正確なサイズ：{value}",
    "budget_invalid_name": "予算名を入力してください",
    'search_edit_conditions': '条件を編集',
    'date_accept': '決定', 'date_cancel': 'キャンセル', 'date_choose': '日付を選択…',
    'date_clear': '日付をクリア',
    'search_fix_field': '示された入力を修正してから範囲を適用してください。',
    'search_size_unit': 'サイズ単位（2進数）',
    'search_condition_name': '名前：{value}',
    'search_condition_value': '{label}：{value}',
    'search_condition_dates': '日付（両端を含む）：{start} から {through}',
    'search_scope_none': '検索範囲：完了したスキャンがありません',
    'search_scope_root': 'スキャン全体：{path}',
    'search_scope_multi': 'スキャン全体：すべての結合元',
    'search_scope': '検索範囲',
    'search_clear_all': 'すべての条件を解除',
    'search_no_conditions': '名前または条件を指定して、スキャン全体を検索します。',
    'search_clear_condition': '解除',
    'search_remove_condition': '条件を解除：{condition}',
    "action_settings": "設定…",
    "action_settings_tip": "すべての設定を検索できる 1 つの画面で変更し、書き出しと読み込みもできます",
    "settings_title": "設定",
    "settings_search": "設定を検索",
    "settings_none": "一致する設定はありません。",
    "settings_appearance": "外観",
    "settings_scanning": "スキャン",
    "settings_recording": "スキャンで記録する情報",
    "settings_following": "追跡と監視",
    "settings_cleaning": "クリーンアップと履歴",
    "settings_system": "Windows",
    "settings_export": "設定を書き出す…",
    "settings_import": "設定を読み込む…",
    "settings_file_tip": (
        "外観、スキャンの選択、スキップするフォルダーを含みます。最近のフォルダー、スキャ"
        "ン設定、容量予算、バックグラウンド スキャン、クリーンアップ ポリシーは含みません"
        "。"
    ),
    "settings_invalid": "FileTree の設定ファイルとして使えません。設定は変更していません。",
    "settings_same": "すでにこの設定になっています。",
    "settings_confirm": "{count} 件の設定をこのファイルの値に変更しますか？",
    "treemap_colours_change": "変化別",
    "change_colour_new": "新規",
    "change_colour_grew_lot": "25% を超える増加",
    "change_colour_grew": "増加",
    "change_colour_same": "変化なし",
    "change_colour_shrank": "減少",
    "change_colour_shrank_lot": "25% を超える減少",
    "change_colour_none": "保存したスキャンと比較すると、変化が色で表示されます",
    "change_colour_tip": (
        "フォルダーは保存したスキャンからの変化で色分けします。保存したスキャンが記録する"
        "のはフォルダーだけなので、ファイルは入っているフォルダーの色になります"
    ),
    "cleanup_custom": "自分のルール: {name}",
    "cleanup_custom_tip": (
        "自分で書いたルールに一致します。内容がまだ必要かどうかは FileTree には判断でき"
        "ません。"
    ),
    "cleanup_category_custom": "自分のルール",
    "cleanup_rebuild_custom": "不明です。移動する前に 1 件ずつ確認してください。",
    "custom_rules_button": "自分のルール ({count})…",
    "custom_rules_title": "自分のクリーンアップ ルール",
    "custom_rules_hint": (
        "これらのルールで見つかった項目は必ず確認用に表示し、自動で選択したりバックグラウ"
        "ンド スキャンで提案したりしません。システム、プログラム、プロファイルのフォルダ"
        "ーは除外します。"
    ),
    "custom_rules_add": "追加",
    "custom_rules_update": "更新",
    "custom_rules_remove": "削除",
    "custom_rules_name": "名前",
    "custom_rules_name_tip": "グループの見出しに表示します",
    "custom_rules_folders": "フォルダー",
    "custom_rules_folders_tip": "Cache や MyApp/logs のようなパスの末尾。複数は ; で区切ります",
    "custom_rules_files": "ファイル",
    "custom_rules_files_tip": "*.bak のような名前。複数は ; で区切ります",
    "custom_rules_in_folder": "対象フォルダー",
    "custom_rules_in_folder_tip": (
        "この名前のフォルダーの直下にあるファイルだけを対象にします。空欄ならど"
        "のフォルダーでも対象です"
    ),
    "custom_rules_days": "変更のない日数",
    "custom_rules_days_tip": "これより新しい項目は含めません",
    "custom_rules_invalid": (
        "このルールは使えません。重複しない名前と、十分に具体的なパターンを 1 つ以上指"
        "定してください（英数字などを 3 文字以上、ドライブ名や円記号は不可、フォルダー"
        "は通常の名前で終わること）。"
    ),
    "action_problem_files": "問題のあるファイルを確認…",
    "action_problem_files_tip": (
        "空のファイル、切れたリンクやショートカット、長すぎるパス、Windows で使え"
        "ない名前を探します"
    ),
    "problem_files_found": "見つかった問題",
    "problem_files_target": "リンク先",
    "problem_files_all": "すべての問題",
    "problem_files_empty": "空のファイル",
    "problem_files_dead_link": "切れたリンク",
    "problem_files_long_path": "長すぎるパス",
    "problem_files_bad_name": "使えない名前",
    "problem_files_hint": (
        "表示中のスキャンを確認します。ディスクを読むのはリンクとローカルの小さなショー"
        "トカットだけで、たどることはありません。リンク先がネットワークや接続されていな"
        "いドライブにあるときは不明のままです。ここでは何も変更しません。ダブルクリック"
        "するとツリーで項目を選択します。"
    ),
    "problem_files_reading": "確認中…",
    "problem_files_summary": (
        "{shown} 件を表示、問題は {count} 件です。判断できなかったリンク: {unknown}。"
        "種類ごとに最初の 1,000 件を表示します。"
    ),
    "search_regex": "名前を正規表現として扱う",
    "search_regex_tip": (
        "名前のどこかに一致すれば見つかります。大文字と小文字は区別しません。時間がかかり"
        "すぎるおそれのあるパターンは受け付けません。"
    ),
    "search_regex_invalid": (
        "この正規表現は使えません。かっこを確認し、繰り返しの中の繰り返し、先読み・後"
        "読み、後方参照は避けてください。"
    ),
    "search_exclude": "除外する名前",
    "search_exclude_tip": (
        "検索欄と同じ書き方です: node_modules; *.tmp。一致したフォルダーは中身ごと除外し"
        "ます。"
    ),
    "search_owner": "所有者",
    "search_owner_tip": "名前または識別子の一部。所有者を記録したスキャンのファイルだけが対象です。",
    "search_min_depth": "この深さ以上",
    "search_max_depth": "この深さ以下",
    "search_depth_tip": "スキャンしたフォルダーの直下が深さ 1 です",
    "search_depth_error": "最小の深さが最大より大きくなっています。",
    "search_more_error": "名前または所有者の条件が長すぎるか、文字ではありません。",
    "search_condition_regex": "名前が一致: {value}",
    "search_condition_depth": "深さ: {least}～{most}",
    "theme_contrast": "ハイコントラスト",
    "theme_accent": "アクセント カラー…",
    "theme_accent_platform": "システムのアクセント カラーを使う",
    "theme_colour_blind": "色覚の違いに配慮したチャートの色",
    "preview_show": "内容をプレビュー",
    "preview_show_tip": (
        "選択したファイルの先頭を読み取ります。オンラインにしかないファイルをダウンロード"
        "することはありません。"
    ),
    "preview_none": "ファイルを選択するとプレビューできます。",
    "preview_reading": "読み取り中…",
    "preview_failed": (
        "プレビューできません。読み取れない、スキャン後に変更された、オンラインにしかない、"
        "または対応していないファイルです。"
    ),
    "preview_binary": "プレビューできるテキスト、画像、圧縮ファイルではありません。",
    "preview_more": "先頭だけを表示しています。続きがあります。",
    "preview_whole": "すべて表示しています。",
    "action_palette": "コマンドを検索…",
    "action_palette_tip": "文字を入力してメニューのコマンドを探し、実行します",
    "action_shortcuts": "キーボード ショートカット…",
    "action_shortcuts_tip": "メニューのコマンドのキーを選びます",
    "palette_title": "コマンドを検索",
    "palette_hint": "コマンドの一部を入力",
    "shortcuts_hint": (
        "欄をクリックして、Ctrl や Alt と別のキー、またはファンクション キーを押します。削除"
        "、停止、終了のキーは変わりません。"
    ),
    "shortcuts_command": "コマンド",
    "shortcuts_keys": "ショートカット",
    "shortcuts_reset": "既定に戻す",
    "shortcuts_conflict": "使えない、または重複しているショートカットがあります: {names}",
    "action_dev_tools": "開発ツール…",
    "action_dev_tools_tip": "Docker、pip、npm、Cargo などが使う容量と、それぞれのクリーンアップ コマンド",
    "dev_tools_tool": "ツール",
    "dev_tools_stores": "フォルダー",
    "dev_tools_inspect": "内容を見る",
    "dev_tools_clean": "クリーンアップ",
    "dev_tools_automatic": "自動で期限切れ",
    "dev_tools_hint": (
        "サイズは表示中のスキャンのものです。FileTree がこれらのコマンドを実行することはあり"
        "ません。コピーして自分で端末で実行してください。ツール自身のコマンドは使用中のデー"
        "タを避け、記録を正しく保ちますが、フォルダーを直接削除するとそうはなりません。"
    ),
    "dev_tools_reading": "探しています…",
    "dev_tools_none": "このスキャンに既知の開発ツールのデータはありません。",
    "dev_tools_summary": (
        "{count} 個のツールがディスクで {size} を使っています。ダブルクリックすると最大の"
        "フォルダーを選択します。"
    ),
    "dev_tools_copy_inspect": "内容を見るコマンドをコピー",
    "dev_tools_copy_clean": "クリーンアップのコマンドをコピー",
    "dev_tools_copied": "コピーしました: {command}",
    "action_scan_overview": "複数のコンピューターを比較…",
    "action_scan_overview_tip": "複数のコンピューターの保存したスキャンを並べて比較します",
    "overview_scans_hint": (
        "ほかのコンピューターで書き出したフォルダー ツリー (JSON) を追加します。フォル"
        "ダーはスキャンしたフォルダーからのパスで対応付けます。表示するのは記録されたサ"
        "イズだけで、ここから開く、移動する、削除することはできません。"
    ),
    "overview_scans_list": "スキャン",
    "overview_scans_add": "保存したスキャンを追加…",
    "overview_scans_rename": "名前を変更…",
    "overview_scans_remove": "一覧から外す",
    "overview_scans_label": "コンピューター",
    "overview_scans_depth": "階層:",
    "overview_scans_spread": "差",
    "overview_scans_total": "（スキャン全体）",
    "overview_scans_empty": "保存したスキャンを追加すると比較できます。",
    "overview_scans_reading": "読み取り中…",
    "overview_scans_summary": (
        "{count} 個のフォルダーのうち {shown} 個を大きい順に表示しています。「—」は"
        "そのスキャンにフォルダーがないことを示します。"
    ),
    "overview_scans_limit": "比較できるスキャンは {limit} 件までです。",
    "overview_scans_failed": "次のファイルを読み取れませんでした:",
    "overview_scans_item": "{label} — {size}（{saved}）",
    "overview_scans_csv": "CSV で保存…",
    "overview_scans_html": "HTML で保存…",
}
