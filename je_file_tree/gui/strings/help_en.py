"""The how-to-use text in English; ``{key}`` stands for the label ``key`` shows in the window."""

from __future__ import annotations

HELP = """
<h2>FileTree in three steps</h2>
<ol>
<li><b>Choose what to scan.</b> Click <i>{action_open}</i> or one of the drives, drag a folder onto the window, or
type a path in the box at the top and press Enter.</li>
<li><b>Watch it fill in.</b> The tree appears right away and the biggest folders move to the top while FileTree adds
up every file. Press <i>{action_stop}</i> (Esc) at any time: what was read so far stays on screen, marked as
incomplete.</li>
<li><b>Find what takes the space.</b> The biggest folders are at the top of the tree. Click the arrow next to a folder
to look inside.</li>
</ol>
<h2>Reading the results</h2>
<ul>
<li><b>Folder tree</b>: the size of each folder or file, the space it takes on the disk
(<i>{column_allocated}</i>), its
share of the folder above (<i>{column_share}</i>), how many files and folders it holds and when something in it last
changed. Click a column title to sort. <i>{details_title}</i>, under the tree, says more about the selected
entry.</li>
<li><b>{highlights_title}</b>: the largest folders and files, and what could be cleaned up.</li>
<li><b>{tab_chart}</b>: four views of the same folder. <i>{chart_treemap}</i> draws every file as a rectangle,
the bigger
the file the bigger the rectangle. <i>{chart_bars}</i> gives each entry one bar, the easiest to read exactly.
<i>{chart_sunburst}</i> puts the folder in the centre with deeper levels in rings around it. <i>{chart_tree}</i> shows
folder cards to expand; Ctrl+wheel zooms. Click to find an entry in the tree, double-click a folder to go into it,
<i>{trend_up}</i> goes back.</li>
<li><b>{tab_largest}</b>: the 1,000 biggest files. <i>{column_advice}</i> says whether a file can be cleaned,
needs a check
first, is your call, or should be kept.</li>
<li><b>{tab_search}</b> (Ctrl+F): files and folders by name, size, date, type and kind. A pattern such as
<code>*.mp4</code> must match the whole name; separate several with <code>;</code>. <i>{search_save}</i> keeps a
search
under a name.</li>
<li><b>{tab_cleanup}</b>: <i>{cleanup_suggestions}</i> lists places whose contents can usually go, with the
reason and the
risk. <i>{tab_duplicates}</i> finds files with the same content; choose the copy to keep, then
<i>{duplicates_select_extra}</i>.</li>
<li><b>{tab_types}</b> and <b>{tab_age}</b>: the space per kind of file and by when it last changed.
Double-click a row
to list its largest files.</li>
<li><b>{tab_problems}</b>: folders FileTree was not allowed to read. What is inside them is not counted.</li>
</ul>
<h2>Freeing space</h2>
<ul>
<li><b>{action_trash}</b> (Delete) asks first, and what it moves can be restored. System and program folders are asked
about twice. The space is free only after the bin is emptied.</li>
<li><b>{permanent_delete}</b> (Shift+Delete) does not use the bin and cannot be undone. It asks every time,
deletes only
what you approved and leaves anything that changed since the scan. FileTree never chooses what to delete.</li>
<li><b>{menu_file} → {reclaim_action}</b>: say how much you need and get ranked steps, safest first. Nothing is ticked
for you.</li>
<li>Pick several entries with Ctrl+click or Shift+click. Right-click an entry to open it, show it in the file manager,
copy its path, move or rename it, or <i>{menu_rescan_here}</i>.</li>
<li>After a move or delete the numbers update without scanning again; FileTree scans only when you ask.</li>
</ul>
<h2>Following changes</h2>
<ul>
<li><b>{menu_file} → {action_compare}</b>: save a scan with <i>{menu_export} → {action_export_json}</i>, then
compare a later
one with it. The <b>{tab_changes}</b> tab lists every folder that grew or shrank.</li>
<li><b>{action_history}</b>: how a folder grew over time.</li>
<li><b>{action_folder_budgets}</b>: a size limit for a folder, and how far it is over.</li>
<li><b>{menu_options} → {action_follow_changes}</b>: read changed folders again as they change.</li>
</ul>
<h2>Drives</h2>
<ul>
<li><b>{menu_view} → {action_volumes}</b>: space on every drive, and when it is likely to be full.</li>
<li><b>{action_disks}</b>: type, health, temperature and partitions of each disk, read only.</li>
<li><b>{action_bins}</b>: what the bins hold, and emptying one after two questions.</li>
</ul>
<h2>Keyboard shortcuts</h2>
<table cellpadding="3">
<tr><td><b>Ctrl+O</b></td><td>Choose a folder</td></tr>
<tr><td><b>F5</b></td><td>Scan again</td></tr>
<tr><td><b>Esc</b></td><td>Stop the scan</td></tr>
<tr><td><b>Ctrl+F</b></td><td>Search</td></tr>
<tr><td><b>Ctrl+T / Ctrl+W</b></td><td>Open / close a scan tab</td></tr>
<tr><td><b>Alt+Left / Alt+Right</b></td><td>Back / forward in the chart</td></tr>
<tr><td><b>Ctrl+P</b></td><td>Print the current view</td></tr>
<tr><td><b>Delete</b></td><td>Move the selected entries to the Recycle Bin</td></tr>
<tr><td><b>Shift+Delete</b></td><td>Delete the selected entries permanently</td></tr>
<tr><td><b>Ctrl++ / Ctrl+−</b></td><td>Larger / smaller text</td></tr>
<tr><td><b>Ctrl+0</b></td><td>Text at the system size</td></tr>
<tr><td><b>F1</b></td><td>This guide</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Quit</td></tr>
</table>
<p>On macOS use ⌘ instead of Ctrl (⌘R to scan again).</p>
<h2>Good to know</h2>
<ul>
<li>Sizes use binary units (1 KB = 1,024 bytes), like Windows Explorer. Choose a fixed unit under
<i>{menu_view} → {menu_unit}</i>.</li>
<li>Text too small or too large? <i>{menu_view} → {menu_text_size}</i>. Light or dark: <i>{menu_view} →
{menu_theme}</i>.</li>
<li>Shortcuts and links are listed but never followed, so nothing is counted twice.</li>
<li>On Windows, FileTree asks for administrator rights when it starts, to read protected folders too. Say no and it
runs normally; folders it could not read are under <i>{tab_problems}</i>. Turn the question off under
<i>{menu_view} → {action_ask_admin}</i>.</li>
<li><i>{scope_folder}</i> makes <i>{tab_largest}</i>, <i>{tab_types}</i> and <i>{tab_age}</i> follow the folder
selected in
the tree.</li>
<li>Hidden files are counted unless you turn off <i>{menu_view} → {action_hidden}</i>. To leave folders out of every
scan, list them in <i>{menu_view} → {action_exclusions}</i>.</li>
<li>Save results with <i>{menu_file} → {menu_export}</i>: CSV, JSON, Excel, HTML, PDF or pictures.</li>
</ul>
"""
