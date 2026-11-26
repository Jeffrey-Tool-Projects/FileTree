"""The how-to-use text in Traditional Chinese; ``{key}`` stands for the label ``key`` shows in the window."""

from __future__ import annotations

from je_file_tree.gui.strings.joining import cjk

HELP = cjk("""
<h2>三個步驟就會用</h2>
<ol>
<li><b>選擇要掃描的地方。</b>按<i>{action_open}</i>或其中一顆磁碟，把資料夾拖曳到視窗上，
或在上方的方框輸入路徑後按 Enter。</li>
<li><b>邊掃邊看。</b>資料夾樹會立刻出現，FileTree 一邊加總，最大的資料夾一邊往上排。
隨時可以按<i>{action_stop}</i>（Esc）：已經讀到的部分會留在畫面上，並標示為不完整。</li>
<li><b>找出佔空間的東西。</b>最大的資料夾排在最上面，按資料夾旁的箭頭就能看裡面的內容。</li>
</ol>
<h2>看懂結果</h2>
<ul>
<li><b>資料夾樹</b>：每個資料夾或檔案的大小、實際佔用的磁碟空間（<i>{column_allocated}</i>）、
佔上一層資料夾的比例（<i>{column_share}</i>）、裡面有幾個檔案和資料夾，以及最近一次變動的時間。
按欄位標題可以排序。樹下方的<i>{details_title}</i>有選取項目的更多資料。</li>
<li><b>{highlights_title}</b>：最大的資料夾與檔案，以及可以清理的項目。</li>
<li><b>{tab_chart}</b>：同一個資料夾的四種看法。<i>{chart_treemap}</i>把每個檔案畫成一個方塊，檔案越大、方塊越
大。
<i>{chart_bars}</i>每個項目一條，最容易精確比較。<i>{chart_sunburst}</i>把資料夾放在中央，往外一圈是更深一層。
<i>{chart_tree}</i>是可以展開的資料夾卡片，Ctrl+滾輪縮放。按一下可在資料夾樹中找到項目，
按兩下進入資料夾，<i>{trend_up}</i>返回。</li>
<li><b>{tab_largest}</b>：最大的 1,000 個檔案。<i>{column_advice}</i>說明檔案可以清理、要先確認、由你決定，還
是應該保留。</li>
<li><b>{tab_search}</b>（Ctrl+F）：依名稱、大小、日期、類型與種類找檔案和資料夾。<code>*.mp4</code> 這類樣式要
符合完整名稱，
好幾個樣式用 <code>;</code> 分開。<i>{search_save}</i>可以替搜尋取名保存。</li>
<li><b>{tab_cleanup}</b>：<i>{cleanup_suggestions}</i>列出內容通常可以刪掉的地方，並說明原因與風險。
<i>{tab_duplicates}</i>找出內容相同的檔案；先選要保留的副本，再按<i>{duplicates_select_extra}</i>。</li>
<li><b>{tab_types}</b>與<b>{tab_age}</b>：依檔案種類、依最後變動時間統計佔用的空間，按兩下一列可列出其中最大的
檔案。</li>
<li><b>{tab_problems}</b>：FileTree 沒有權限讀取的資料夾，裡面的內容不會計算在內。</li>
</ul>
<h2>釋放空間</h2>
<ul>
<li><b>{action_trash}</b>（Delete）會先詢問，移走的東西可以還原；系統與程式資料夾會再問一次。
清空資源回收筒之後空間才會釋放。</li>
<li><b>{permanent_delete}</b>（Shift+Delete）不經過資源回收筒，無法復原。每次都會詢問，只刪除你同意的項目，
掃描後有變動的項目會保留。FileTree 不會自己決定要刪什麼。</li>
<li><b>{menu_file} → {reclaim_action}</b>：說明需要多少空間，就會依安全程度列出步驟，不會替你勾選任何項目。</li>
<li>用 Ctrl+按一下或 Shift+按一下選取好幾個項目。在項目上按右鍵，可以開啟、在檔案總管中顯示、複製路徑、移動、
重新命名，或<i>{menu_rescan_here}</i>。</li>
<li>移動或刪除後數字會直接更新，不會重新掃描；FileTree 只在你要求時才掃描。</li>
</ul>
<h2>追蹤變化</h2>
<ul>
<li><b>{menu_file} → {action_compare}</b>：先用<i>{menu_export} → {action_export_json}</i>把掃描存起來，之後再
和新的掃描比較。
<b>{tab_changes}</b>分頁會列出每個變大或變小的資料夾。</li>
<li><b>{action_history}</b>：資料夾隨時間的成長。</li>
<li><b>{action_folder_budgets}</b>：替資料夾設定容量上限，並顯示超出多少。</li>
<li><b>{menu_options} → {action_follow_changes}</b>：資料夾有變動時自動重新讀取那些資料夾。</li>
</ul>
<h2>磁碟</h2>
<ul>
<li><b>{menu_view} → {action_volumes}</b>：每顆磁碟的空間，以及預估何時用滿。</li>
<li><b>{action_disks}</b>：每顆實體磁碟的類型、健康狀態、溫度與分割區，只供查看。</li>
<li><b>{action_bins}</b>：各資源回收筒的內容量；清空前會詢問兩次。</li>
</ul>
<h2>鍵盤快速鍵</h2>
<table cellpadding="3">
<tr><td><b>Ctrl+O</b></td><td>選擇資料夾</td></tr>
<tr><td><b>F5</b></td><td>重新掃描</td></tr>
<tr><td><b>Esc</b></td><td>停止掃描</td></tr>
<tr><td><b>Ctrl+F</b></td><td>搜尋</td></tr>
<tr><td><b>Ctrl+T／Ctrl+W</b></td><td>開啟／關閉掃描分頁</td></tr>
<tr><td><b>Alt+←／Alt+→</b></td><td>在圖表中返回／前進</td></tr>
<tr><td><b>Ctrl+P</b></td><td>列印目前畫面</td></tr>
<tr><td><b>Delete</b></td><td>把選取的項目移到資源回收筒</td></tr>
<tr><td><b>Shift+Delete</b></td><td>永久刪除選取的項目</td></tr>
<tr><td><b>Ctrl++／Ctrl+−</b></td><td>放大／縮小文字</td></tr>
<tr><td><b>Ctrl+0</b></td><td>文字恢復系統大小</td></tr>
<tr><td><b>Ctrl+,</b></td><td>設定</td></tr>
<tr><td><b>Ctrl+K</b></td><td>尋找指令</td></tr>
<tr><td><b>F1</b></td><td>這份說明</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>結束</td></tr>
</table>
<p>在 macOS 上請用 ⌘ 取代 Ctrl（⌘R 是重新掃描）。</p>
<h2>小知識</h2>
<ul>
<li>大小以二進位單位計算（1 KB = 1,024 位元組），和 Windows 檔案總管相同；
可以在<i>{menu_view} → {menu_unit}</i>改用固定的單位。</li>
<li>文字太小或太大？用<i>{menu_view} → {menu_text_size}</i>調整；淺色或深色
用<i>{menu_view} → {menu_theme}</i>切換。</li>
<li>捷徑與連結會列出來，但不會跟進去計算，所以不會重複計算。</li>
<li>在 Windows 上，FileTree 啟動時會要求系統管理員權限，受保護的資料夾也能讀取。拒絕的話照常執行，
讀不到的資料夾列在<i>{tab_problems}</i>。不想每次被問，可以關掉<i>{menu_view} → {action_ask_admin}</i>。</li>
<li><i>{scope_folder}</i>會讓<i>{tab_largest}</i>、<i>{tab_types}</i>與<i>{tab_age}</i>改為跟著資料夾樹中選取
的資料夾。</li>
<li>預設會計算隱藏檔案，可以關掉<i>{menu_view} → {action_hidden}</i>。要讓某些資料夾每次都不掃描，
把它們加進<i>{menu_view} → {action_exclusions}</i>。</li>
<li>用<i>{menu_file} → {menu_export}</i>儲存結果：CSV、JSON、Excel、HTML、PDF 或圖片。</li>
</ul>
""")
