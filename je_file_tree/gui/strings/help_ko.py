"""The how-to-use text in Korean; ``{key}`` stands for the label ``key`` shows in the window."""

from __future__ import annotations

HELP = """
<h2>세 단계로 사용하기</h2>
<ol>
<li><b>스캔할 위치를 고릅니다.</b> <i>{action_open}</i> 또는 드라이브를 클릭하거나, 폴더를 창으로 끌어다 놓거나,
위쪽 입력란에 경로를 입력하고 Enter를 누르세요.</li>
<li><b>합산하면서 보여 줍니다.</b> 폴더 트리가 바로 나타나고, 합산이 진행되는 동안 큰 폴더가 위로 올라옵니다.
<i>{action_stop}</i>(Esc)는 언제든지 누를 수 있으며, 그때까지 읽은 내용은 불완전 표시와 함께 남습니다.</li>
<li><b>공간을 차지하는 것을 찾습니다.</b> 가장 큰 폴더가 맨 위에 있습니다. 폴더 옆의 화살표를 클릭하면 안을 볼
수 있습니다.</li>
</ol>
<h2>결과 보는 법</h2>
<ul>
<li><b>폴더 트리</b>: 폴더나 파일의 크기, 디스크에서 실제로 차지하는 공간(<i>{column_allocated}</i>), 상위
폴더에서
차지하는 비율(<i>{column_share}</i>), 안에 있는 파일과 폴더 수, 마지막으로 바뀐 시간입니다. 열 제목을 클릭하면
정렬됩니다.
트리 아래의 <i>{details_title}</i>에서 선택한 항목을 자세히 볼 수 있습니다.</li>
<li><b>{highlights_title}</b>: 가장 큰 폴더와 파일, 정리할 만한 항목입니다.</li>
<li><b>{tab_chart}</b>: 같은 폴더를 네 가지로 보여 줍니다. <i>{chart_treemap}</i>은 파일을 사각형으로 그리며
큰 파일일수록
사각형이 큽니다. <i>{chart_bars}</i>는 항목마다 막대 하나로, 정확하게 비교하기 쉽습니다.
<i>{chart_sunburst}</i>는 폴더를 가운데에
두고 바깥 고리일수록 더 깊은 단계입니다. <i>{chart_tree}</i>는 펼칠 수 있는 폴더 카드이며 Ctrl+휠로
확대·축소합니다.
클릭하면 트리에서 항목을 찾고, 두 번 클릭하면 폴더로 들어가며, <i>{trend_up}</i>으로 돌아갑니다.</li>
<li><b>{tab_largest}</b>: 가장 큰 파일 1,000개입니다. <i>{column_advice}</i>는 정리해도 되는지, 먼저 확인해야
하는지, 직접 판단할지,
남겨 두어야 하는지를 알려 줍니다.</li>
<li><b>{tab_search}</b>(Ctrl+F): 이름, 크기, 날짜, 형식, 종류로 파일과 폴더를 찾습니다. <code>*.mp4</code>
같은 패턴은 전체 이름과
일치해야 하며, 여러 패턴은 <code>;</code>로 구분합니다. <i>{search_save}</i>로 검색에 이름을 붙여 보관할 수
있습니다.</li>
<li><b>{tab_cleanup}</b>: <i>{cleanup_suggestions}</i>은 보통 지워도 되는 위치를 이유와 위험도와 함께 보여
줍니다.
<i>{tab_duplicates}</i>은 내용이 같은 파일을 찾습니다. 남길 사본을 고른 다음
<i>{duplicates_select_extra}</i>을 누르세요.</li>
<li><b>{tab_types}</b> 및 <b>{tab_age}</b>: 파일 종류별, 마지막으로 바뀐 시기별 공간입니다. 행을 두 번
클릭하면 그중 가장 큰
파일을 보여 줍니다.</li>
<li><b>{tab_problems}</b>: 읽을 권한이 없던 폴더입니다. 안에 있는 내용은 합산되지 않습니다.</li>
</ul>
<h2>공간 확보</h2>
<ul>
<li><b>{action_trash}</b>(Delete)은 먼저 확인하며, 옮긴 것은 되돌릴 수 있습니다. 시스템과 프로그램 폴더는 두
번 확인합니다.
휴지통을 비운 뒤에야 공간이 확보됩니다.</li>
<li><b>{permanent_delete}</b>(Shift+Delete)는 휴지통을 거치지 않으며 되돌릴 수 없습니다. 매번 확인하고 승인한
항목만 삭제하며,
스캔 이후 바뀐 항목은 남겨 둡니다. FileTree가 스스로 삭제할 것을 고르지 않습니다.</li>
<li><b>{menu_file} → {reclaim_action}</b>: 필요한 공간을 입력하면 안전한 순서대로 단계를 보여 줍니다. 미리
선택되는 항목은 없습니다.</li>
<li>Ctrl+클릭이나 Shift+클릭으로 여러 항목을 고릅니다. 항목을 오른쪽 클릭하면 열기, 파일 관리자에서 보기, 경로
복사, 이동,
이름 바꾸기, <i>{menu_rescan_here}</i> 등을 할 수 있습니다.</li>
<li>이동하거나 삭제한 뒤에는 다시 스캔하지 않고 숫자가 갱신됩니다. FileTree는 요청할 때만 스캔합니다.</li>
</ul>
<h2>변화 살펴보기</h2>
<ul>
<li><b>{menu_file} → {action_compare}</b>: <i>{menu_export} → {action_export_json}</i>으로 스캔을 저장해 두고
나중 스캔과 비교합니다.
<b>{tab_changes}</b> 탭에 커지거나 작아진 폴더가 모두 표시됩니다.</li>
<li><b>{action_history}</b>: 시간에 따른 폴더 크기 변화입니다.</li>
<li><b>{action_folder_budgets}</b>: 폴더의 크기 한도를 정하고 얼마나 넘었는지 봅니다.</li>
<li><b>{menu_options} → {action_follow_changes}</b>: 바뀐 폴더를 자동으로 다시 읽습니다.</li>
</ul>
<h2>드라이브</h2>
<ul>
<li><b>{menu_view} → {action_volumes}</b>: 드라이브별 공간과 가득 찰 것으로 예상되는 시기입니다.</li>
<li><b>{action_disks}</b>: 물리 디스크의 종류, 상태, 온도, 파티션입니다. 보기만 합니다.</li>
<li><b>{action_bins}</b>: 휴지통에 든 용량입니다. 비우기 전에 두 번 확인합니다.</li>
</ul>
<h2>키보드 단축키</h2>
<table cellpadding="3">
<tr><td><b>Ctrl+O</b></td><td>폴더 선택</td></tr>
<tr><td><b>F5</b></td><td>다시 스캔</td></tr>
<tr><td><b>Esc</b></td><td>스캔 중지</td></tr>
<tr><td><b>Ctrl+F</b></td><td>검색</td></tr>
<tr><td><b>Ctrl+T / Ctrl+W</b></td><td>스캔 탭 열기 / 닫기</td></tr>
<tr><td><b>Alt+← / Alt+→</b></td><td>차트에서 뒤로 / 앞으로</td></tr>
<tr><td><b>Ctrl+P</b></td><td>현재 보기 인쇄</td></tr>
<tr><td><b>Delete</b></td><td>선택한 항목을 휴지통으로 이동</td></tr>
<tr><td><b>Shift+Delete</b></td><td>선택한 항목을 영구 삭제</td></tr>
<tr><td><b>Ctrl++ / Ctrl+−</b></td><td>글자 크게 / 작게</td></tr>
<tr><td><b>Ctrl+0</b></td><td>글자를 시스템 크기로 되돌리기</td></tr>
<tr><td><b>F1</b></td><td>이 도움말</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>종료</td></tr>
</table>
<p>macOS에서는 Ctrl 대신 ⌘를 사용합니다(다시 스캔은 ⌘R).</p>
<h2>알아 두면 좋은 점</h2>
<ul>
<li>크기는 Windows 탐색기와 같은 이진 단위(1 KB = 1,024바이트)입니다. <i>{menu_view} → {menu_unit}</i>에서
단위를 고정할 수
있습니다.</li>
<li>글자가 너무 작거나 크면 <i>{menu_view} → {menu_text_size}</i>, 밝은 테마와 어두운 테마는 <i>{menu_view} →
{menu_theme}</i>에서 바꿉니다.</li>
<li>바로 가기와 링크는 표시하지만 따라가지 않으므로 두 번 합산되지 않습니다.</li>
<li>Windows에서는 보호된 폴더도 읽을 수 있도록 시작할 때 관리자 권한을 요청합니다. 거절해도 정상적으로
실행되며, 읽지 못한
폴더는 <i>{tab_problems}</i>에 표시됩니다. 묻지 않게 하려면 <i>{menu_view} → {action_ask_admin}</i>을
끄세요.</li>
<li><i>{scope_folder}</i>을 누르면 <i>{tab_largest}</i>, <i>{tab_types}</i>, <i>{tab_age}</i>이 트리에서
선택한 폴더만 다룹니다.</li>
<li>숨김 파일도 합산합니다. 제외하려면 <i>{menu_view} → {action_hidden}</i>을 끄세요. 항상 스캔하지 않을 폴더는
<i>{menu_view} → {action_exclusions}</i>에 등록합니다.</li>
<li><i>{menu_file} → {menu_export}</i>로 결과를 CSV, JSON, Excel, HTML, PDF, 그림으로 저장합니다.</li>
</ul>
"""
