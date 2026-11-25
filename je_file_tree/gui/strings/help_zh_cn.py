"""The how-to-use text in Simplified Chinese; ``{key}`` stands for the label ``key`` shows in the window."""

from __future__ import annotations

from je_file_tree.gui.strings.joining import cjk

HELP = cjk("""
<h2>三个步骤就会用</h2>
<ol>
<li><b>选择要扫描的地方。</b>点<i>{action_open}</i>或其中一个磁盘，把文件夹拖到窗口上，
或在上方的框里输入路径后按 Enter。</li>
<li><b>边扫边看。</b>文件夹树会立刻出现，FileTree 一边汇总，最大的文件夹一边往上排。
随时可以点<i>{action_stop}</i>（Esc）：已经读到的部分会留在界面上，并标记为不完整。</li>
<li><b>找出占空间的东西。</b>最大的文件夹排在最上面，点文件夹旁的箭头就能看里面的内容。</li>
</ol>
<h2>看懂结果</h2>
<ul>
<li><b>文件夹树</b>：每个文件夹或文件的大小、实际占用的磁盘空间（<i>{column_allocated}</i>）、
占上级文件夹的比例（<i>{column_share}</i>）、里面有几个文件和文件夹，以及最近一次变动的时间。
点列标题可以排序。树下方的<i>{details_title}</i>有所选项目的更多信息。</li>
<li><b>{highlights_title}</b>：最大的文件夹与文件，以及可以清理的项目。</li>
<li><b>{tab_chart}</b>：同一个文件夹的四种看法。<i>{chart_treemap}</i>把每个文件画成一个方块，文件越大、方块越
大。
<i>{chart_bars}</i>每个项目一条，最容易精确比较。<i>{chart_sunburst}</i>把文件夹放在中央，往外一圈是更深一级。
<i>{chart_tree}</i>是可以展开的文件夹卡片，Ctrl+滚轮缩放。单击可在文件夹树中找到项目，
双击进入文件夹，<i>{trend_up}</i>返回。</li>
<li><b>{tab_largest}</b>：最大的 1,000 个文件。<i>{column_advice}</i>说明文件可以清理、要先确认、由你决定，还
是应该保留。</li>
<li><b>{tab_search}</b>（Ctrl+F）：按名称、大小、日期、类型与种类查找文件和文件夹。<code>*.mp4</code> 这类模式
要匹配完整名称，
多个模式用 <code>;</code> 分开。<i>{search_save}</i>可以给搜索取名保存。</li>
<li><b>{tab_cleanup}</b>：<i>{cleanup_suggestions}</i>列出内容通常可以删掉的地方，并说明原因与风险。
<i>{tab_duplicates}</i>找出内容相同的文件；先选要保留的副本，再点<i>{duplicates_select_extra}</i>。</li>
<li><b>{tab_types}</b>与<b>{tab_age}</b>：按文件种类、按最后变动时间统计占用的空间，双击一行可列出其中最大的文
件。</li>
<li><b>{tab_problems}</b>：FileTree 没有权限读取的文件夹，里面的内容不会计算在内。</li>
</ul>
<h2>释放空间</h2>
<ul>
<li><b>{action_trash}</b>（Delete）会先询问，移走的东西可以还原；系统与程序文件夹会再问一次。
清空回收站之后空间才会释放。</li>
<li><b>{permanent_delete}</b>（Shift+Delete）不经过回收站，无法恢复。每次都会询问，只删除你同意的项目，
扫描后有变动的项目会保留。FileTree 不会自己决定要删什么。</li>
<li><b>{menu_file} → {reclaim_action}</b>：说明需要多少空间，就会按安全程度列出步骤，不会替你勾选任何项目。</li>
<li>用 Ctrl+单击或 Shift+单击选中多个项目。在项目上点右键，可以打开、在文件管理器中显示、复制路径、移动、
重命名，或<i>{menu_rescan_here}</i>。</li>
<li>移动或删除后数字会直接更新，不会重新扫描；FileTree 只在你要求时才扫描。</li>
</ul>
<h2>跟踪变化</h2>
<ul>
<li><b>{menu_file} → {action_compare}</b>：先用<i>{menu_export} → {action_export_json}</i>把扫描保存起来，之后
再和新的扫描比较。
<b>{tab_changes}</b>标签页会列出每个变大或变小的文件夹。</li>
<li><b>{action_history}</b>：文件夹随时间的增长。</li>
<li><b>{action_folder_budgets}</b>：给文件夹设置容量上限，并显示超出多少。</li>
<li><b>{menu_options} → {action_follow_changes}</b>：文件夹有变动时自动重新读取那些文件夹。</li>
</ul>
<h2>磁盘</h2>
<ul>
<li><b>{menu_view} → {action_volumes}</b>：每个磁盘的空间，以及预计何时用满。</li>
<li><b>{action_disks}</b>：每个物理磁盘的类型、健康状态、温度与分区，仅供查看。</li>
<li><b>{action_bins}</b>：各回收站的内容量；清空前会询问两次。</li>
</ul>
<h2>键盘快捷键</h2>
<table cellpadding="3">
<tr><td><b>Ctrl+O</b></td><td>选择文件夹</td></tr>
<tr><td><b>F5</b></td><td>重新扫描</td></tr>
<tr><td><b>Esc</b></td><td>停止扫描</td></tr>
<tr><td><b>Ctrl+F</b></td><td>搜索</td></tr>
<tr><td><b>Ctrl+T／Ctrl+W</b></td><td>打开／关闭扫描标签页</td></tr>
<tr><td><b>Alt+←／Alt+→</b></td><td>在图表中返回／前进</td></tr>
<tr><td><b>Ctrl+P</b></td><td>打印当前视图</td></tr>
<tr><td><b>Delete</b></td><td>把选中的项目移到回收站</td></tr>
<tr><td><b>Shift+Delete</b></td><td>永久删除选中的项目</td></tr>
<tr><td><b>Ctrl++／Ctrl+−</b></td><td>放大／缩小文字</td></tr>
<tr><td><b>Ctrl+0</b></td><td>文字恢复系统大小</td></tr>
<tr><td><b>F1</b></td><td>这份说明</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>退出</td></tr>
</table>
<p>在 macOS 上请用 ⌘ 代替 Ctrl（⌘R 是重新扫描）。</p>
<h2>小知识</h2>
<ul>
<li>大小按二进制单位计算（1 KB = 1,024 字节），和 Windows 资源管理器相同；
可以在<i>{menu_view} → {menu_unit}</i>改用固定的单位。</li>
<li>文字太小或太大？用<i>{menu_view} → {menu_text_size}</i>调整；浅色或深色
用<i>{menu_view} → {menu_theme}</i>切换。</li>
<li>快捷方式与链接会列出来，但不会进入计算，所以不会重复计算。</li>
<li>在 Windows 上，FileTree 启动时会请求管理员权限，受保护的文件夹也能读取。拒绝的话照常运行，
读不到的文件夹列在<i>{tab_problems}</i>。不想每次被问，可以关掉<i>{menu_view} → {action_ask_admin}</i>。</li>
<li><i>{scope_folder}</i>会让<i>{tab_largest}</i>、<i>{tab_types}</i>与<i>{tab_age}</i>改为跟着文件夹树中选中
的文件夹。</li>
<li>默认会计算隐藏文件，可以关掉<i>{menu_view} → {action_hidden}</i>。要让某些文件夹每次都不扫描，
把它们加进<i>{menu_view} → {action_exclusions}</i>。</li>
<li>用<i>{menu_file} → {menu_export}</i>保存结果：CSV、JSON、Excel、HTML、PDF 或图片。</li>
</ul>
""")
