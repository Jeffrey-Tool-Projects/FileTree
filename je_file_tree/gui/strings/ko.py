"""Every text the window shows in Korean; see ``je_file_tree.gui.i18n``."""

from __future__ import annotations

from je_file_tree.gui.strings.help_ko import HELP

KO: dict[str, str] = {
    "busy_scanning": ("스캔이 진행 중이라 '{action}'을(를) 실행할 수 없습니다. "
        "스캔이 끝날 때까지 기다리거나 먼저 스캔을 중지하세요(Esc)."),
    "busy_operation": ("다른 파일 작업이 진행 중이라 '{action}'을(를) 실행할 수 없습니다. "
        "작업이 끝난 후 다시 시도하세요."),
    "budget_filter": "예산 표시",
    "budget_filter_all": "모든 예산",
    "budget_filter_over": "한도 초과",
    "budget_filter_unknown": "알 수 없음 또는 미스캔",
    "budget_filter_empty": "이 필터에 맞는 예산이 없습니다. 모든 예산을 선택하면 전체 규칙을 볼 수 있습니다.",
    "budget_editing_hidden": "편집 중인 {name} 규칙은 이 필터에서 숨겨져 있습니다. 상태: {status}. 초안은 유지됩니다.",
    "budget_count_over": "한도 초과 {count}개",
    "budget_count_unknown": "알 수 없음 {count}개",
    "folder_context_target": "대상 폴더",
    "folder_context_ready": "파일을 선택하면 해당 파일이 있는 폴더에 적용됩니다.",
    "folder_context_history": "용량 증가 추세 보기",
    "folder_context_budget": "폴더 용량 예산 설정",
    "folder_context_empty": "스캔을 완료한 후 폴더 작업을 사용하세요.",
    "folder_context_busy": "스캔 또는 현재 작업이 끝날 때까지 기다리세요.",
    "folder_context_closing": "이 스캔 탭을 닫는 중입니다.",
    "folder_context_virtual": "개별 원본을 스캔한 후 폴더 작업을 사용하세요.",
    "folder_context_stale": "현재 스캔에 있는 폴더를 선택하세요.",
    "folder_context_link": "링크에는 폴더 작업을 사용할 수 없습니다.",
    "trend_choose_folder": "불러온 폴더 선택…",
    "trend_loaded_folders": "불러온 하위 폴더",
    "trend_full_path": "전체 폴더 경로",
    "trend_root": "루트로 돌아가기",
    "trend_up": "상위",
    "trend_enter": "폴더 열기",
    "trend_previous": "이전 페이지",
    "trend_next": "다음 페이지",
    "trend_choose_current": "이 폴더 사용",
    "trend_folder_page": "총 {total}개 중 {first}–{last}개. 불러온 폴더만 표시합니다.",
    "trend_period": "기간",
    "trend_period_all": "보관된 전체 기록",
    "trend_period_30": "최근 30일",
    "trend_period_90": "최근 90일",
    "trend_period_custom": "사용자 지정 날짜",
    "trend_date_order": "종료일은 시작일 이후여야 합니다.",
    "trend_point_details": "선택한 관측값 상세",
    "trend_select_point": "차트나 표에서 관측값을 선택하세요. 방향키로 각 관측값을 이동합니다.",
    "trend_size_reason": "크기 알 수 없음: {reason}",
    "trend_change_reason": "변화 알 수 없음: {reason}",
    "trend_first_point": "이 기간에 이전 관측값이 없음",
    "trend_point_value": "{date} · 크기 {size} ({exact_size}) · 변화 {change} ({exact_change})",
    "templates_select": "저장한 템플릿 선택",
    "templates_remove": "템플릿 삭제",
    "templates_save_section": "창을 열 때의 작업 공간 저장",
    "templates_save_source": (
        '추가와 업데이트는 이 창을 열 때의 탭과 옵션을 저장합니다. 아래 미'
        '리 보기의 변경은 저장하지 않습니다.'),
    "templates_add_current": "열 때의 탭 추가",
    "templates_update_current": "열 때의 탭으로 업데이트",
    "templates_preview_hint": (
        '불러오기 미리 보기 · 경로 변경은 이번 불러오기에만 적용됩니다. 확'
        '인 후 교체하고 시작을 눌러 검사하세요.'),
    "templates_preview_modified": "이번 불러오기만 수정됨 · 탭 교체 전에 경로를 다시 확인하세요.",
    "templates_active": "활성",
    "templates_scanning": "검사 중",
    "templates_impact": (
        '교체하면 탭 {tabs}개를 닫고 검사 {scans}개를 중지하며 결'
        '과 {results}개를 닫습니다. 미리 보기의 사용할 수 없는 경로'
        ': {unavailable}.'),
    "templates_saved": '저장한 템플릿',
    'workspace_templates': '작업 공간 템플릿…',
    'templates_tab': '탭',
    'templates_kind': '범위',
    'templates_status': '사용 가능 여부',
    'templates_single': '단일 폴더',
    'templates_check': '경로 확인',
    'templates_replace': '탭 교체',
    'templates_hint': (
        '현재 탭을 저장하거나 템플릿을 선택하여 미리 봅니다. 경로를 편집하고'
        ' 확인한 다음 탭을 교체하세요. 교체하면 기존 검사와 결과가 닫힙니다'
        '. 불러온 탭은 시작을 누를 때까지 검사하지 않습니다. 사용할 수 없'
        '는 경로도 유지됩니다. 여기서 수정하고 다시 확인하세요. 추가와 업데'
        '이트는 현재 작업 공간을 저장합니다.'),
    'templates_invalid': (
        '잘못된 템플릿입니다. 고유한 이름과 절대 경로를 사용하세요. 기존 설'
        '정은 변경되지 않았습니다.'),
    'templates_unchecked': '확인 전',
    'templates_checking': '모든 경로 확인 중…',
    'templates_ready': '사용 가능',
    'templates_checked': (
        '경로 확인이 완료되었습니다. 사용할 수 없는 경로를 포함한 모든 입력'
        '을 불러옵니다. 오류가 있는 탭은 시작할 수 없습니다.'),
    'templates_not_folder': '폴더가 아닙니다',
    "completion_title": '최근 정리 결과',
    "completion_undo": '복원 가능한 이동 취소',
    "completion_rescan": '원래 폴더 다시 스캔',
    "completion_dismiss": '요약 닫기',
    "completion_source": '원본: {path}',
    "completion_counts": (
        '이동: {moved} ({size}); 제외: {ski'
        'pped}; 실패: {failed}'
    ),
    "completion_space": (
        '스캔 사이에 관측한 여유 공간 변화: {change} '
        '(다른 활동 포함)'
    ),
    "completion_measurements": '스캔 관측 시간: {before} → {after}',
    "completion_space_pending": (
        '비교 가능한 후속 스캔 관측이 아직 없습니다. 알 수 '
        '없음은 0이 아닙니다.'
    ),
    "completion_reason": '{reason}: {count}',
    "completion_more": '전체 이유는 작업 기록에서 확인할 수 있습니다.',
    "completion_errors": (
        '기록 오류: {journal}; 복사 마무리 오류: {'
        'copies}.'
    ),
    "completion_hint": (
        '이동 크기는 논리 데이터양이며 확보된 공간이 아닙니다.'
        ' 휴지통 비우기는 별도 작업입니다. 자세한 내용은 작업'
        ' 기록과 실패 보고서에서 확인하세요.'
    ),
    "action_scan_presets_tip": "이름을 지정한 경로와 옵션을 저장하고 불러옵니다. 스캔은 시작하지 않습니다",
    "action_scan_presets": '자주 쓰는 스캔 설정…',
    "presets_empty": '저장된 설정 없음',
    "presets_hint": (
        '추가와 업데이트는 현재 스캔 옵션과 입력한 경로를 저장합니다. 불러온 후'
        ' 경로 스캔을 눌러 시작하세요. 스레드 수와 제외 규칙은 작업 공간에 적'
        '용됩니다.'
    ),
    "presets_saved": '저장된 설정',
    "presets_name": '이름',
    "presets_add": '현재 옵션 추가',
    "presets_update": '선택 업데이트',
    "presets_rename": '이름 바꾸기',
    "presets_remove": '설정 삭제',
    "presets_load": '불러오기',
    "presets_options": '스레드: {workers}; 제외 규칙: {exclusions}; 사용: {flags}',
    "presets_no_flags": '없음',
    "presets_invalid": (
        '중복되지 않는 이름(1–80자), 절대 경로, 올바른 스캔 옵션을 사용하'
        '세요. 최대 32개를 저장할 수 있습니다.'
    ),
    "presets_read_failed": '저장된 설정을 읽을 수 없습니다. 기존 데이터는 유지했습니다.',
    "presets_loaded": '{name} 설정을 불러왔습니다. 경로 스캔을 눌러 시작하세요.',
    "highlights_title": '스캔 핵심 정보',
    "highlights_waiting": '스캔 분석 대기 중…',
    "highlights_folders": '바로 아래의 큰 폴더를 선택하여 위치를 확인하세요.',
    "highlights_partial": '불완전한 결과: 읽은 항목의 크기만 포함합니다.',
    "highlights_folder": '{name} — {size}',
    "highlights_cleanup_waiting": '정리: 분석 대기 중…',
    "highlights_cleanup": '후보 {count}개 검토 ({size})',
    "highlights_cleanup_hint": '후보 데이터 크기는 검토가 필요하며 즉시 확보할 수 있는 공간이 아닙니다.',
    "highlights_coverage_unknown": '스캔 범위 정보가 아직 없습니다',
    "highlights_coverage": '스캔 제한: 제외 {skipped}, 읽기 불가 {denied}, 대기 {pending}',
    "column_advice": '삭제 가능 여부',
    "advice_low": '정리 가능',
    "advice_review": '확인 필요',
    "advice_personal": '직접 판단',
    "advice_protected": '삭제 금지',
    "advice_managed": '시스템 관리',
    "advice_pending": '분석 중…',
    "advice_low_tip": (
        '위험이 낮은 정리 후보입니다. 프로그램이 이 데이터를 다시 만들 수 있습니다. 이동하기 '
        '전에 검토하세요.'
    ),
    "advice_review_tip": '검토가 필요한 정리 후보입니다. 아직 필요한 내용이 없는지 확인하세요.',
    "advice_personal_tip": (
        '이 항목에 해당하는 규칙이 없으므로 필요한지는 직접 판단해야 합니다. 확인 없이는 아무'
        '것도 이동하지 않습니다.'
    ),
    "advice_protected_tip": (
        '유지하세요: {reason}. 제거하면 시스템이나 설치된 프로그램이 동작하지 않을 수 있습니'
        '다.'
    ),
    "advice_managed_tip": (
        "이 공간은 운영 체제가 관리하며 FileTree는 이동하지 않습니다. 사용할 시스템 도구는 '"
        "세부 정보'에 표시됩니다."
    ),
    "advice_pending_tip": '정리 분석이 아직 진행 중입니다.',
    "advice_summary": '{label} — {reason}',
    "advice_legend_tip": (
        '이 스캔의 정리 규칙과 이 컴퓨터의 보호된 위치를 바탕으로 한 안내입니다. 참고용이며 '
        '이동하기 전에 항상 먼저 묻습니다.'
    ),
    "highlights_folders_label": '가장 큰 폴더',
    "highlights_files_label": '가장 큰 파일',
    "highlights_files": '가장 큰 파일을 선택하여 위치를 확인하세요. 점은 삭제 가능 여부 안내입니다.',
    "reclaim_action": "공간 확보…",
    "reclaim_action_tip": "이번 스캔에서 찾은 항목으로 원하는 만큼 공간을 확보하는 계획을 세웁니다",
    "reclaim_title": "공간 확보",
    "reclaim_hint": (
        "필요한 공간을 선택하세요. FileTree는 이번 스캔에서 이미 찾은 항목을 가장 안전한 것부터 보여 줍니다. "
        "자동으로 선택되는 항목은 없으며, 검토하고 '예'라고 답하기 전에는 아무것도 이동하지 않습니다."
    ),
    "reclaim_target": "확보할 공간:",
    "reclaim_custom": "직접 입력",
    "reclaim_share": "드라이브 여유 공간이 이 비율이 될 때까지",
    "reclaim_drive": "스캔 당시 여유 공간: {free} / {total}",
    "reclaim_column_entry": "단계 또는 항목",
    "reclaim_column_total": "누계",
    "reclaim_step": "{risk}: {title} ({count})",
    "reclaim_duplicates": "중복 파일의 추가 사본",
    "reclaim_duplicates_tip": (
        "'중복' 탭에서 유지하기로 선택한 사본과 내용이 같은 파일입니다. 유지할 사본은 절대 제안되지 않습니다."
    ),
    "reclaim_options": "어떤 규칙에도 해당하지 않는 큰 파일 — 확실할 때만",
    "reclaim_running": "{total} / {target}",
    "reclaim_beyond": "{total} / {target} (목표 초과)",
    "reclaim_more": "표시되지 않은 항목 {count}개",
    "reclaim_overlap": "단독 크기 {size}. 일부는 이전 단계에서 이미 계산되었습니다.",
    "reclaim_reached": "이 단계들로 약 {found} 확보 가능 — 요청한 {target}에 충분합니다.",
    "reclaim_short": (
        "이 단계들로는 약 {found}만 확보할 수 있어 {target}까지 {short} 부족합니다. 더 이상 필요 없다고 확실하면 "
        "마지막에 나열된 큰 파일로 나머지를 채울 수 있습니다."
    ),
    "reclaim_empty": "이번 스캔에서 제안할 수 있는 항목을 찾지 못했습니다.",
    "reclaim_waiting": "정리 제안을 아직 찾는 중입니다. 준비되면 계획에 반영됩니다.",
    "reclaim_undecided": "중복 그룹 {count}개는 제외되었습니다. 먼저 '중복' 탭에서 유지할 사본을 선택하세요.",
    "reclaim_selected": "선택됨: {selected} / {target}",
    "reclaim_note": (
        "스캔 결과에 따른 추정치입니다. 실제로 확보되는 공간은 다를 수 있습니다. 하드 링크, 압축된 파일, 클라우드 "
        "파일은 크기보다 사용량이 적고, 휴지통으로 이동한 항목은 휴지통을 비울 때까지 공간을 계속 차지합니다."
    ),
    "reclaim_show": "트리에서 표시",
    "reclaim_review": "검토 후 휴지통으로 이동…",
    "shell_reading": "탐색기 등록을 읽는 중…",
    "shell_saving": "탐색기 등록을 저장하는 중…",
    "shell_waiting": "현재 탐색기 설정 요청이 끝날 때까지 기다리는 중…이미 시작한 저장은 계속됩니다.",
    "trash_failed_title": "이동하지 못한 항목",
    "trash_failed_summary": "실패한 항목: {count}개. 전체 경로와 진단 정보를 확인하세요.",
    "trash_holders_error": "파일 사용 프로세스 조회 오류: {reason}",
    "trash_skipped_title": "건너뛴 항목",
    "trash_skipped_summary": "{count}개 항목을 건너뛰었습니다. 다시 시도하기 전에 해당 폴더를 다시 스캔하세요.",
    "trash_skipped_hint": "행을 선택하면 전체 경로와 이유를 표시합니다. {shortcut}로 선택한 행을 복사합니다.",
    "closing_workers": "FileTree 종료 중: 백그라운드 작업을 중지하고 현재 파일 시스템 호출이 끝나기를 기다리는 중…",
    "elevate_python_tip": (
        "Python으로 실행 중: Windows UAC에는 권한을 높이는 실행 파일인 Python이 표시됩니다. "
        "FileTree 표시를 원하면 FileTree 실행 파일을 사용하세요."),
    'overview_empty': '폴더를 선택하여 시작하세요',
    'overview_live': '스캔 중 · 통계가 계속 갱신됩니다',
    'overview_complete': '스캔 완료',
    'overview_partial': '불완전한 결과 · 읽지 못한 항목이 있습니다',
    'overview_size': '논리 크기',
    'overview_allocated': '기록된 할당량',
    'overview_files': '파일',
    'overview_folders': '폴더',
    'overview_problems': '읽지 못한 항목 확인 ({count})',
    'overview_navigation': '분석 보기',
    'overview_coverage_hint': '이번 스캔의 범위입니다. 제외 규칙과 마운트 경계는 계속 적용됩니다.',
    'overview_allocation_hint': '기록된 할당량은 추정치나 공유 공간일 수 있으며 회수 가능한 공간을 뜻하지 않습니다.',
    'overview_live_hint': '갱신되는 트리와 차트를 탐색할 수 있습니다. 분석 목록은 스캔이 끝나면 표시됩니다.',
    'overview_result_hint': '분석 보기를 선택하고 항목을 선택하여 트리에서 위치를 확인하세요.',
    'overview_path': '폴더 또는 드라이브 경로',
    'overview_scan_path': '경로 스캔',
    'overview_scan_path_tip': '입력한 폴더나 드라이브를 스캔합니다(Enter). 실행 중인 스캔은 안전하게 교체됩니다.',
    'overview_workflow': '1  폴더나 드라이브 선택   →   2  공간 사용량 탐색   →   3  정리 전 검토',
    'overview_scan_running': '백그라운드에서 폴더를 읽는 중입니다. 갱신되는 결과를 탐색할 수 있습니다.',
    'overview_scan_paused': ('일시 중지를 요청했습니다. 현재 파일 시스템 호출이 먼저 끝날 수 있습니다. '
                             '재개하거나 중지할 수 있습니다.'),
    'overview_scan_analysing': '백그라운드에서 분석을 준비하는 중입니다. 중지를 요청할 수 있습니다.',
    'overview_scan_stopping': '현재 파일 시스템 작업이 끝나기를 기다립니다. 얻은 부분 결과는 유지됩니다.',
    'overview_scan_elapsed': '경과 {time}',
    'recurring_review': '다시 스캔하고 현재 후보 항목 검토…',
    'recurring_validating': '전체 신규 스캔 및 현재 소스 메타데이터에 대해 날짜가 지정된 제안을 검증하는 중…',
    'recurring_refused': '제안을 계속할 수 없습니다: {status}. 현재 관찰을 준비하려면 새로운 예약 검사를 실행하세요.',
    'recurring_tabs_full': '16개의 스캔 탭이 모두 사용 중입니다. 예정된 제안을 검토하기 전에 탭을 닫으세요.',
    'trash_skip_proposal_changed': (
        '원본 경로 또는 후보 보고서 설정·기록이 변경되었거나 확인할 수 없습니다. 원본을 유지했습니다.'
    ),
    'trash_skip_proposal_expired': '이동 전에 예약 스캔의 후보 보고서가 만료되었습니다. 원본을 유지했습니다.',
    'action_recurring': '예약된 스캔 제안…',
    'action_recurring_tip': '날짜가 지정된 예정된 관찰 및 해당 범위를 봅니다. 자동 정리가 되지 않습니다.',
    'recurring_rule': '규칙',
    'recurring_unknown': '알 수 없음',
    'recurring_new': '마지막 스캔 이후 새로운 정크',
    'recurring_current': '현재 후보 항목',
    'recurring_growth': '최대 신규 성장',
    'recurring_empty': (
        '이 세션에는 예약된 보고서가 없습니다. 백그라운드 모니터링을 활성화하고 스캔 폴더를 선택합니다.'
    ),
    'recurring_hint': (
        '관찰만; 아무것도 자동으로 이동되지 않습니다. 목록당 최대 100개 행. 증가는 복구 가능한 공간이 아닌 논'
        '리적 바이트입니다. 알려지지 않은 비교는 새로운 쓰레기가 없음을 증명하지 않습니다. 보고서는 이 세션에'
        '서 예약된 검사 후에 나타납니다. 기준선은 로컬 기록에 보관됩니다. 새 탭에서 재검색을 검토하고 일반 대'
        '기열과 확인을 사용합니다.'
    ),
    'recurring_summary': (
        '준비됨: {prepared}\n이전 기준: {previous}\n만료: {expires}\n표시된 후보: {retained} / {total}; 적용 '
        '범위: {coverage}; 비교: {comparison}\n상태: {status}'
    ),
    'recurring_status_current': '관찰됨; 검토 전 새로운 소스 검증 필요',
    'recurring_status_expired': '만료됨(일정 누락 또는 시계 롤백 포함)',
    'recurring_status_schedule_changed': '일정이 변경되거나 비활성화되었습니다.',
    'recurring_status_stale_scan': '스캔 작업 기록이 변경되었거나 사용할 수 없음',
    'recurring_status_rule_changed': '청소 규칙이 변경되었습니다.',
    'recurring_status_incomplete': '불완전한 적용 범위 또는 알 수 없는 신원',
    'recurring_status_paths_changed': '소스 경로가 변경됨',
    'recurring_status_unavailable': '설정 또는 작업 기록을 확인할 수 없습니다.',
    'recurring_prepare_failed': '기록이 저장되었습니다. 예약된 제안을 사용할 수 없음: {detail}',
    'workspace_new': '새 스캔 탭',
    'workspace_new_tip': '독립적인 스캔 탭을 엽니다(Ctrl+T). Ctrl+W로 현재 탭을 닫습니다.',
    'workspace_close': '스캔 탭 닫기',
    'workspace_empty': '폴더 선택',
    'trash_skip_recycle_unverified': (
        'Windows 재활용 설정, 전체 소스 크기 또는 기본 저장소 메타데이터를 확인할 수 없습니다. 소스가 유지됩'
        '니다.'
    ),
    'trash_skip_recycle_disabled': 'Windows 이 범위에서는 재활용이 비활성화됩니다. 소스가 유지됩니다.',
    'trash_skip_recycle_capacity': (
        '선택 항목 및 현재 쓰레기통 내용물이 여유 공간이 있는 관찰된 재활용 한도를 초과합니다. 소스가 유지됩'
        '니다.'
    ),
    'action_check_updates': '매일 업데이트 확인',
    'action_background_monitor': '백그라운드 모니터…',
    'action_background_monitor_tip': '트레이 알림 및 일정에 따른 폴더 기록 검색을 선택하세요.',
    'background_enable': '백그라운드 모니터링 활성화',
    'background_startup': '로그인할 때 이 모니터 시작',
    'background_startup_hint': (
        '이 사용자에 대해서만 별도의 선택이 가능합니다. FileTree 소유의 로그인 항목을 제거하려면 선택을 취소'
        '하세요. 향후 로그인에 적용됩니다. 다른 복사를 시작하거나 이 모니터를 닫지 않습니다.'
    ),
    'background_startup_requires_monitor': '로그인 항목을 추가하기 전에 백그라운드 모니터링을 활성화하십시오.',
    'background_startup_error': '로그인 시작을 변경할 수 없습니다: {detail}',
    'background_hint': (
        '기본적으로 꺼져 있습니다. 닫으면 사용 가능한 시스템 트레이에 FileTree이 유지됩니다. 그만둬 끝내세요.'
        ' 매분마다 OS의 사용 가능한 용량을 확인하고 선택한 폴더만 부드럽게 검사합니다. 예약된 검색에는 활성화'
        '된 로컬 기록이 필요합니다. 자동 정리 또는 시작 등록이 없습니다.'
    ),
    'background_threshold': '사용 가능한 공간 아래에 경고',
    'background_interval': '검사 간격(시간)',
    'background_roots': '예약된 검사 폴더',
    'background_add': '스캔 폴더 추가…',
    'background_remove': '선택한 폴더 제거',
    'background_limit': '최대 32개의 예약 폴더를 선택하세요.',
    'background_show': 'FileTree 표시',
    'background_off': '백그라운드 모니터링이 꺼져 있습니다',
    'background_ready': '백그라운드 모니터링이 켜져 있습니다.',
    'background_no_tray': (
        '시스템 트레이를 사용할 수 없습니다. FileTree은 계속 표시되고 배경 모니터링은 일시 중지됩니다.'
    ),
    'background_error': '백그라운드 모니터링: {detail}',
    'background_history_disabled': '예약된 검사를 실행하기 전에 로컬 검사 기록을 활성화하십시오.',
    'background_scanning': '예약된 검사: {detail}',
    'background_saved': '저장된 예약 내역: {detail}',
    'background_saved_partial': '읽지 않은 범위와 함께 저장된 예약 내역: {detail}',
    'background_canceled': '예약된 검사가 취소되었습니다. 부분 소스 범위가 저장되지 않았습니다: {detail}',
    'background_warning': '{detail}',
    'background_low_space': '{root}의 사용 가능한 공간 부족: {free} ({percent}%)',
    'action_follow_changes': '변경 사항 따라가기',
    'action_follow_changes_tip': (
        '기본적으로 꺼져 있습니다. Windows, Linux, macOS에서 변경된 폴더만 다시 읽고, '
        '변경되지 않은 하위 폴더는 그대로 둡니다.'
    ),
    'follow_refreshed': '변경된 폴더 {count}개를 업데이트했습니다',
    'follow_refresh_failed': '변경된 폴더를 업데이트할 수 없습니다: {reason}',
    'follow_waiting': '변경 사항 따르기: 스캔 대기 중',
    'follow_starting': '변경사항 따르기: 시작 중…',
    'follow_active': '다음 변경 사항({detail})',
    'follow_failed': '변경사항 팔로우가 중지되었습니다: {detail}',
    'follow_incomplete': '변경 사항을 따르려면 완전한 물리적 스캔이 필요합니다.',
    'follow_unsupported': '변경 사항 따르기는 Windows, Linux, macOS를 지원합니다',
    'follow_backend_usn': 'NTFS USN',
    'follow_backend_directory_changes': '디렉터리 알림',
    'follow_backend_inotify': 'inotify',
    'follow_backend_fsevents': 'FSEvents',
    'action_check_updates_tip': '최대 하루에 한 번 HTTPS를 통해 PyPI에 문의하세요. 설치 없이 참고만 가능합니다.',
    'update_available': 'FileTree {version} 사용 가능',
    'multi_roots': '여러 뿌리',
    'action_multi_scan': '여러 폴더 스캔…',
    'action_multi_scan_tip': '한 번의 결합 스캔으로 명시적 폴더를 검토합니다.',
    'multi_choose': '여러 폴더 스캔',
    'multi_add': '폴더 추가…',
    'multi_remove': '선택한 루트 제거',
    'scan_all_drives': '모든 드라이브 검사',
    'multi_hint': (
        '최대 256개의 선택된 뿌리를 결합합니다. 결과는 읽기 전용입니다. 파일 작업을 위해 소스를 별도로 스캔합'
        '니다. OS 용량은 볼륨별로 유지됩니다.'
    ),
    'capacity_multiple_roots': '다중 루트: OS 용량은 볼륨당입니다.',
    'vc_title': '컴팩트한 VHD 선택…',
    'vc_apply': '검토하고 컴팩트하게…',
    'vc_hint': (
        '고정 로컬 NTFS의 분리된 동적 VHD/VHDX만 적합합니다. 읽기 전용 준비는 ID, 헤더 및 보수적인 WSL/Docker'
        ' 런타임 상태를 확인합니다. 게스트 사용량 및 보장된 복구는 알 수 없습니다. 권한 오류로 인해 FileTree'
        '의 기존 관리자 재시작을 사용하기 전에 이 검토를 닫으십시오. 새로운 스캔과 승인이 필요합니다.'
    ),
    'vc_preparing': '캡처된 디스크 및 중지된 런타임을 확인하는 중…',
    'vc_ready': '정확한 소스를 검토하고 해당 기계가 계속 중지되어 있는지 확인하세요.',
    'vc_details': (
        '소스: {path}\n이름: {source}\n디스크 UUID: {identifier}\n가상 용량: {capacity}\n공급자 바이트: {phys'
        'ical}\n\n백엔드: Windows CompactVirtualDisk, 분리형 제로 블록 압축. 게스트 연결, 실행 또는 종료가 없'
        '습니다. 게스트가 사용하는 바이트는 알 수 없습니다.'
    ),
    'vc_confirm': (
        '다음 정확한 가상 디스크 파일을 압축 정리하시겠습니까?\n\n{path}\n\n예를 선택하면 이 파일을 사용하는 '
        '머신이 중지되었으며 작업 내내 중지 상태를 유지한다는 것을 확인한 것으로 간주합니다. 실행 상태와 식별'
        ' 정보를 새로 확인합니다. 운영체제의 제로 블록 작업으로 공간이 회복되지 않을 수 있으며, 나중에 오류가'
        ' 발생하더라도 메타데이터가 이미 변경되었을 수 있습니다. 자동으로 되돌리는 기능은 없습니다. 게스트의 '
        '사용량 및 여유 공간 회복량은 알 수 없습니다. 중지 또는 닫기는 진행 중인 운영체제 호출이 끝날 때까지 '
        '기다리고 실제 결과를 보고합니다. 쓰기 가능한 상태로 열기 전에 승인을 기록합니다.'
    ),
    'vc_running': '검토된 디스크를 다시 확인하고 압축하는 중…',
    'vc_waiting': '현재 운영체제 호출을 기다리는 중입니다. 실제 결과가 보고될 예정입니다…',
    'vc_done': (
        '{status}\n가상 디스크 파일 할당량 관측값: {before} → {after}. OS 여유 공간 회복을 보장하지 않습니다.'
        ' 게스트 사용량은 알 수 없으며 쓰기를 시도한 후에는 새로 스캔해야 합니다.'
    ),
    'vc_failed': '압축: {reason}',
    'vc_not_compacted': '압축되지 않음',
    'vc_stale': (
        '쓰기 가능한 작업이 시도되었습니다. 기록된 관찰 내용은 오래되었습니다. 다른 검토 전에 새로 스캔하려면'
        ' 이 창을 닫으세요.'
    ),
    'vc_audit_refused': '승인을 기록할 수 없습니다. 운영체제 작업이 시작되지 않았습니다.',
    'vc_audit_detail': '이전 백업 할당: {before}; 이후: {after}. 오류: {error}',
    'journal_status_compacted': '네이티브 압축 완료',
    'journal_reason_compaction': '명시적 가상 디스크 압축',
    'vd_hint': (
        '읽기 전용 인벤토리 공급자 라벨은 위치 힌트입니다. 지원 할당, 공급자 바이트 및 가상 용량은 별개입니다'
        '. 게스트 사용량은 알 수 없습니다. 헤더 쿼리와 압축 검토는 명시적입니다. 지원되지 않는 형식은 계속 표'
        '시됩니다. 게스트가 자동으로 시작, 중지 또는 마운트되지 않습니다.'
    ),
    'vd_name': '디스크 이름',
    'vd_source': '소스',
    'vd_issue_unverified': '확인되지 않은 신원',
    'vd_issue_unavailable': '연결됨, 클라우드 또는 사용할 수 없음',
    'vd_issue_changed': '파일이 변경됨',
    'vd_issue_duplicate_hard_links': '여러 하드 링크 이름',
    'action_virtual_disks_tip': '기록된 가상 디스크를 검토하고 읽기 전용 기본 VHD 정보를 명시적으로 쿼리합니다.',
    'action_virtual_disks': '가상 디스크…',
    'vd_kind': '형식',
    'vd_length': '백업 파일 길이',
    'vd_allocation': '기록된 할당',
    'vd_capacity': '가상 용량',
    'vd_physical': '공급자 물리적 바이트',
    'vd_guest': '사용된 게스트',
    'vd_source_scan': '기록된 스캔',
    'vd_source_wsl': 'WSL 등록',
    'vd_source_docker': 'Docker 기본값(추론)',
    'vd_unsupported': '기본 VHD 도구는 지원되지 않습니다.',
    'vd_not_queried': '쿼리되지 않은 기본 헤더',
    'vd_fixed': '고정',
    'vd_dynamic': '동적',
    'vd_differencing': '차별화',
    'vd_loaded': '탑재/사용 중',
    'vd_detached': '로드되지 않음(관찰)',
    'vd_inspect': '선택한 VHD 헤더 쿼리',
    'vd_select': '기록된 항목 표시',
    'vd_reading': '가상 백업 파일 검색 중…',
    'vd_querying': '기본 헤더 읽기: {path}',
    'vd_summary': '{count} 중 {shown} 표시 중; {issues} 문제/누락. 적용 범위: {coverage}.',
    'vd_failed': '가상 디스크 정보: {reason}',
    'vd_information_hint': (
        '기본 관찰은 압축을 승인하거나 기계가 정지되었음을 증명하지 않습니다. 공급자 실제 바이트는 게스트 사'
        '용 바이트가 아닙니다. 디스크 UUID는 행 도구 설명에 있습니다.'
    ),
    'link_summary': '{total} 추가 사본: {ready} 준비됨, {skipped} 거부됨.',
    'link_title': '추가 사본을 연결하십시오…',
    'link_hint': (
        '명시적으로 보관된 복사본(최대 1,000개 추가)을 사용하여 정확한 중복 파일을 검토합니다. 보호된 파일, '
        '변경된 파일, 클라우드 파일, 링크된 파일, 지원되지 않는 파일은 거부됩니다. 여유 공간이 보장되지 않습'
        '니다.'
    ),
    'link_copy': '교체할 추가 사본',
    'link_keeper': '보관된 파일',
    'link_apply': '링크가 추가 사본을 검토했습니다…',
    'link_confirm': (
        '중복 복사본 {count}개를 하드 링크로 바꾸시겠습니까? 처리할 수 없는 {skipped}개 행은 건너뜁니다.\n\n'
        '기존 데이터는 휴지통에 보관하지 않습니다. 연결된 모든 이름은 이후의 내용, 메타데이터 및 접근 권한 변'
        '경을 공유합니다. 자동으로 되돌리는 기능은 없습니다. 실패하거나 취소하면 생성한 링크와 기존 복사본의 '
        '백업이 표시된 경로에 남을 수 있습니다. 중지 또는 닫기는 진행 중인 운영체제 호출이 끝날 때까지 기다립'
        '니다. 전체 데이터와 모든 명명된 스트림을 다시 확인합니다. 동시 변경에 대한 확인은 관찰에 기반하며 트'
        '랜잭션이 아닙니다. 상세 내용에서 모든 쌍과 거부 이유를 확인하세요.'
    ),
    'link_progress': '재확인/링크: {path}',
    'link_done': (
        '하드 링크: {linked} 게시됨, {other} 연결되지 않음. 관찰 내용을 새로 고치려면 다시 스캔하세요. 복구된'
        ' 용량은 알 수 없습니다.'
    ),
    'link_not_linked': '연결되지 않음',
    'link_retained': '유지된 경로:\n{paths}',
    'journal_status_linked': '하드 링크 게시됨',
    'journal_reason_duplicate_links': '명시적 중복 하드링크 교체',
    'undo_button': '실행 취소({count})',
    'undo_running': '캡처된 휴지통 항목을 복원하는 중…',
    'undo_done': '실행 취소: {restored} 복원, {failed} 실패',
    'undo_title': '쓰레기 복원',
    'undo_result': '{status}\n원본: {source}\n휴지통: {trashed}\n{reason}',
    'undo_unavailable': '일부 항목은 실행취소할 수 없습니다: {reason}',
    'journal_status_restored': '휴지통에서 복원됨',
    'journal_reason_undo': '명시적 휴지통 실행 취소',
    'menu_move_drive': '다른 드라이브로 이동…',
    'copy_hint': (
        '다른 드라이브에 있는 기존 폴더를 선택합니다. 원본은 별도의 휴지통 확인 전까지 보관됩니다. 64MiB 미만'
        '의 파일 수, 길이 및 SHA-256을 확인하세요. 더 큰 페이로드는 길이만 제한됩니다. 실패/취소 시 부분 대상'
        '이 유지됩니다. 최대 1,000개의 폴더를 선택할 수 있습니다.'
    ),
    'copy_apply': '검토된 폴더 복사 및 확인…',
    'copy_redirect': '휴지통을 성공적으로 삭제한 후 각 원래 경로에 교차점/기호 링크를 남겨두세요.',
    'copy_finish': '검증된 원본을 휴지통으로 이동…',
    'copy_confirm': (
        '검토한 폴더 {count}쌍을 복사하고 검증하시겠습니까? 나머지 {skipped}쌍은 건너뜁니다. 기존 이름을 덮어'
        '쓰지 않습니다. 원본은 휴지통 이동을 별도로 승인할 때까지 유지합니다. 실패하거나 취소하면 일부만 복사'
        '된 항목이 대상에 남습니다.'
    ),
    'copy_progress': '이 폴더에 {path}: {done} / {total} 파일 복사/확인 중',
    'copy_done': '확인된 사본: {copied}; 건너뛰었습니다: {skipped}; 실패: {failed}. 원본은 그대로 유지됩니다.',
    'copy_partial': '유지된 부분 대상: {path}',
    'copy_trash_confirm': (
        '각 원본을 휴지통으로 이동하기 직전에 복사된 폴더를 다시 검증합니다. 항목 수와 길이를 비교합니다. 64 '
        'MiB 미만의 내용은 SHA-256으로 대조하고, 그 이상의 내용은 길이만 비교합니다. 검증에 실패하면 나머지 '
        '작업을 중지합니다. 동시 변경에 대한 확인은 트랜잭션이 아닙니다.'
    ),
    'copy_errors': '복사 확인 또는 원본 경로 리디렉션에 실패했습니다. 세부정보에서 실제 경로를 검토하세요.',
    'copy_verify_failed': '보관된 원본: {source}\n복사본: {destination}\n확인 거부됨: {reason}',
    'copy_redirect_failed': (
        '원본이 휴지통으로 이동됨: {source}\n확인된 사본 보관됨: {destination}\n리디렉션 실패(빈 원본 경로 디'
        '렉터리가 남아 있을 수 있음): {reason}'
    ),
    'namespace_reason_same_volume': '동일한 볼륨; 폴더로 이동 사용',
    'namespace_source_name': '소스 이름',
    'namespace_destination_name': '목적지 이름',
    'namespace_closed_errors': (
        '중지/폐쇄된 작업에서 오류가 보고되었습니다. 세부정보에서 소스/대상 경로를 검사합니다.'
    ),
    'namespace_refreshed': '{path}: {files} 파일을 새로 고쳤습니다. {errors} 스캔 오류.',
    'namespace_refresh_failed': '{path}에서 새로 고침 실패: {reason}',
    'namespace_refreshing': '영향을 받은 대상 새로 고침: {path}',
    'menu_move_folder': '폴더로 이동…',
    'menu_rename': '이름 바꾸기…',
    'namespace_source': '소스',
    'namespace_destination': '목적지',
    'namespace_status': '상태',
    'namespace_pattern': '파일 이름 패턴',
    'namespace_rename_hint': (
        '모든 소스와 대상을 검토하세요. 리터럴 토큰: {name}, {stem}, {ext}, {n}. 동일한 볼륨만; 덮어쓰기 없음'
        '. 최대 1,000개의 항목을 선택할 수 있습니다.'
    ),
    'namespace_move_hint': (
        '기존 대상 폴더를 선택하고 모든 쌍을 검토하십시오. 동일한 볼륨만; 덮어쓰기 없음. 보호된/링크/사용할 '
        '수 없는/불완전한 항목은 거부됩니다. 최대 1,000개의 항목을 선택할 수 있습니다.'
    ),
    'namespace_collision_skip': '기존 이름: 건너뛰기',
    'namespace_collision_rename': '기존 이름: 번호가 매겨진 접미사 미리보기',
    'namespace_preview': '미리보기 경로',
    'namespace_apply': '검토된 경로 적용…',
    'namespace_reading': '소스 및 대상 메타데이터 확인 중…',
    'namespace_preview_needed': '옵션이 변경되었습니다. 적용하기 전에 경로를 다시 미리 봅니다.',
    'namespace_summary': '{total} 가장 바깥쪽 쌍; {ready} 준비; {skipped} 거부됨/변경되지 않음.',
    'namespace_confirm': (
        '미리보기의 처리 가능한 원본·대상 {count}쌍을 적용하시겠습니까? 나머지 {skipped}쌍은 건너뜁니다. 상세'
        ' 내용에는 처리 가능한 모든 쌍을 표시합니다. 기존 이름을 덮어쓰지 않습니다. 중지 또는 닫기는 진행 중'
        '인 이름 변경이 끝날 때까지 기다리며, 완료된 변경은 유지합니다.'
    ),
    'namespace_progress': '{done} / {total} 쌍 처리됨',
    'namespace_done': (
        '이동/이름 변경: {moved}; 건너뛰었습니다: {skipped}; 실패: {failed}. 스캔을 새로 고치려면 닫으세요.'
    ),
    'namespace_failed': '작업 실패: {reason}',
    'namespace_reason_ready': '준비',
    'namespace_reason_unverified': '알 수 없는 신원',
    'namespace_reason_link': '링크가 거부되었습니다.',
    'namespace_reason_special': '특별입국 거부',
    'namespace_reason_unavailable': '사용할 수 없음/클라우드 항목',
    'namespace_reason_cancelled': '중지됨',
    'namespace_reason_outside': '외부 현재 스캔/루트',
    'namespace_reason_missing': '소스 누락',
    'namespace_reason_kind': '항목 유형이 변경됨',
    'namespace_reason_identity': '소스가 교체됨',
    'namespace_reason_changed': '소스가 변경됨',
    'namespace_reason_incomplete': '불완전한 소스 범위',
    'namespace_reason_unreadable': '읽을 수 없는 소스',
    'namespace_reason_system_managed': '시스템 관리 소스',
    'namespace_reason_protected': '보호된 소스',
    'namespace_reason_unchanged': '이름은 변경되지 않음',
    'namespace_reason_descendant': '선택한 소스 내의 대상',
    'namespace_reason_protected_destination': '보호된 목적지',
    'namespace_reason_volume': '다른 볼륨; 검증된 사본이 필요합니다',
    'namespace_reason_collision': '이름이 이미 존재합니다.',
    'photos_exact': '정확한 중복',
    'photos_find': '비슷한 사진 찾기',
    'photos_similar': '비슷한 사진',
    'photos_distance': '해시 거리(0~16):',
    'photos_hint': (
        '시각적 후보만 해당: 썸네일과 원본을 비교하세요. 해시 충돌이 가능합니다. 자동 유지할 파일, 추가 사본 '
        '선택 또는 복구 추정이 없습니다. 첫 번째 애니메이션 프레임.'
    ),
    'photos_group': '{count} 이미지; 첫 번째 이미지의 {distance} 비트 내',
    'photos_running': '이미지 읽기: {read}; 건너뛰기/실패: {skipped}',
    'photos_summary': '{groups} 유사 이미지 그룹; {read} 이미지 읽기; {skipped} 건너뛰거나 실패했습니다.',
    'photos_limited': '제한된 재고 또는 디스플레이 최대 {count}개의 이미지 행/썸네일이 표시됩니다.',
    'archive_loading': '아카이브 메타데이터를 읽는 중…',
    'archive_virtual_name': '{name} [가상]',
    'tree_more_rows': '항목 {count}개 더 있음 — 클릭하면 다음 {page}개 표시',
    'tree_more_rows_hint': ('큰 폴더는 창이 원활하게 반응하도록 한 번에 {page}개 항목씩 표시합니다. '
        '이 행을 클릭하거나 Enter 키를 누르면 다음 페이지를 표시합니다. '
        '차트나 목록에서 선택한 항목은 해당 페이지가 자동으로 표시됩니다.'),
    'archive_virtual_hint': '아카이브 멤버: 선언된 비압축 크기, 디스크 총계 외부. 파일 작업이나 추출이 없습니다.',
    'archive_failed': '미리보기를 사용할 수 없음: {reason}',
    'archive_rejected': '{count} 안전하지 않거나 연결되었거나 충돌하는 구성원이 생략되었습니다.',
    'archive_empty': '미리보기 가능한 회원 없음',
    'archive_stopped': '아카이브 미리보기가 중지되었습니다. 재고가 불완전하다',
    'archive_busy': '두 개의 아카이브 읽기가 이미 실행 중입니다. 다시 스캔하여 다시 시도',
    'archive_stop': '이 아카이브 읽기를 중지하세요',
    'action_count_hard_links': '발견된 하드 링크를 한 번만 계산',
    'action_count_hard_links_tip': (
        '기본적으로 꺼져 있습니다. 향후 스캔에서는 이름이 지정된 크기를 유지하고 계산된 총계를 추가합니다. Br'
        'anch/Trash는 전체 루트를 재구축합니다.'
    ),
    'column_accounted_size': '계산된 크기',
    'column_accounted_allocated': '계산된 디스크 크기',
    'hard_links_hint': (
        '하드 링크 계정을 활성화하면 처음으로 관찰된 어휘 이름이 바이트에 기여합니다. 여기서 별칭은 0으로 계'
        '산됩니다. 명명된 크기는 실제 파일 길이로 유지됩니다. 알 수 없거나 일관성이 없는 기록은 추정 상태로 '
        '유지됩니다. 공유 범위를 알 수 없습니다.'
    ),
    'hard_links_summary': (
        '계산됨: {size}(디스크 추정치 {allocated}); {aliases} 관찰된 별칭; {unknown} 알 수 없는 레코드입니다.'
        ' 차트에서는 계산된 합계를 사용합니다. 파일/유형/연령 목록은 이름이 지정된 크기를 유지합니다.'
    ),
    'compression_mode_ntfs': 'NTFS 압축',
    'compression_mode_xpress8k': 'XPRESS8K 압축(거의 수정되지 않은 파일)',
    'compression_mode_uncompress': '압축 해제(NTFS 및 실행 모드)',
    'compression_apply': '나열된 파일 처리 중…',
    'compression_restore_summary': (
        '{count}/{total} 녹음된 파일이 검토 대상입니다. {shown}을 표시합니다. 압축 상태를 알 수 없습니다.'
    ),
    'compression_confirm': (
        '범위: {path}\n모드: {mode}\n후보 {total}개 중 목록에 있는 파일 {count}개(논리 크기 {size})만 처리합'
        '니다.\n\n현재 NTFS 범위와 파일이 변경되지 않았는지 다시 확인합니다. 링크, 클라우드·오프라인, 스파스,'
        ' 숨김·시스템, 하드 링크 및 보호된 파일은 처리하지 않습니다. 폴더의 기본 설정과 목록에 없는 파일은 변'
        '경하지 않습니다. 압축하면 쓰기 속도가 느려질 수 있습니다. XPRESS는 변경이 적은 데이터에 적합합니다. '
        '압축 해제에는 여유 공간이 필요합니다. 중지하거나 실패하면 일부 변경이 남을 수 있습니다.\n\n이 창을 '
        '닫으면 진행 중인 명령을 취소하고 종료를 기다린 뒤, 파일별 할당을 확인하여 이 폴더를 다시 스캔합니다.'
        ' 계속하시겠습니까?'
    ),
    'compression_progress': '{done}/{total} 나열된 파일을 처리 중입니다…',
    'compression_done': (
        '{done}/{attempted} 명령이 완료되었습니다. {failures} 실패. 알려진 일치 파일 할당: {before} → {after}'
        '; {unknown} 측정값을 알 수 없습니다. 다시 검색할 예정입니다. 총계는 여유 공간을 보장하지 않습니다. '
        '처음 20개의 오류가 표시됩니다.'
    ),
    'compression_canceled': '중지됨; 이전 또는 현재 파일이 변경되었을 수 있습니다. 재검색이 종료되었습니다.',
    'compression_failed': '작업 실패: {reason}. 부분적인 변경이 가능합니다. 재검사에 가깝습니다.',
    'action_exact_allocation': 'Windows 파일별 할당량 측정',
    'action_exact_allocation_tip': (
        '기본적으로 꺼져 있습니다. XPRESS/WOF 파일을 포함하여 향후 스캔을 위한 추가 메타데이터 호출. 활성화하'
        '고 다시 검색합니다. 알려진 클라우드/오프라인 파일은 쿼리되지 않은 상태로 유지됩니다. 실패한 쿼리는 '
        '추정치로 유지됩니다.'
    ),
    'menu_compression': 'NTFS 압축…',
    'compression_reading': '기록된 압축 후보 검토 중…',
    'compression_summary': (
        '{count}/{total} 파일은 유형 후보입니다. {shown} 표시; 논리적 {logical}, 명명된 할당 {allocated}. 잠'
        '재적 절약: 0–{allocated}; 고정된 압축률은 예측되지 않습니다. {unknown} 파일에 알 수 없는 메타데이터'
        '가 있습니다.'
    ),
    'compression_volume': '파일 시스템: {filesystem}; 할당 단위: {unit}',
    'compression_unknown': '알 수 없음',
    'compression_ntfs_only': 'NTFS이 확인되지 않았습니다. 이 범위에서는 기본 압축을 사용할 수 없습니다.',
    'compression_partial': '불완전한 스캔: 생략되었거나 읽을 수 없는 데이터가 이 추정치를 벗어났습니다.',
    'compression_hint': (
        '읽기 전용 유형 추정: 로그, 텍스트, 코드 및 압축되지 않은 이미지 형식일 수 있습니다. 확장자는 압축성'
        '을 증명하지 않습니다. 숨김/시스템, 압축/희소, 재분석/클라우드/오프라인 및 알 수 없는 레코드는 생략됩'
        '니다. 명명된 할당은 하드 링크에 의해 추정되거나 공유될 수 있으므로 복구 가능한 공간이 보장되지 않습'
        '니다. 페이로드를 읽지 않았습니다. 두 번 클릭하면 녹음된 파일이 선택됩니다. Ctrl+C는 행을 복사합니다.'
    ),
    'action_capture_owners': 'Windows 파일 소유자 기록',
    'action_capture_owners_tip': (
        '기본적으로 꺼져 있습니다. 향후 스캔에 소유자 메타데이터 쿼리를 추가합니다. 활성화 및 다시 검색'
    ),
    'tab_users': '사용자',
    'column_owner': '소유자',
    'column_owner_id': '소유자 식별자',
    'owner_unknown': '알 수 없는 소유자',
    'owners_refresh': '기록된 총계 새로 고침',
    'owners_reading': '기록된 소유자 합계 추가 및 계정 이름 확인 중...',
    'owners_unqueried': '기록된 소유자 합계를 쿼리하려면 스캔 후 사용자를 엽니다.',
    'owners_partial': (
        '불완전한 스캔: 생략되거나 읽을 수 없는 바이트와 해당 소유자를 알 수 없는 상태로 남아 있습니다.'
    ),
    'owners_summary': (
        '{count} 소유자 그룹; {shown} 표시; {files} 파일, {size}. 알 수 없는 소유자: {unknown_files} 파일, {u'
        'nknown_size}.'
    ),
    'owners_hint': (
        '전체 스캔, 파일 소유자만 해당; 디렉터리 소유권은 하위 항목을 할당하지 않습니다. POSIX uid는 스캔 통'
        '계에서 나옵니다. Windows에서 옵션을 활성화하고 → Windows 파일 소유자를 캡처하고 다시 검색합니다. 비'
        '활성화, 실패, 변경 또는 클라우드/오프라인 쿼리는 알 수 없는 상태로 유지됩니다. 이름은 uid/SID로 대체'
        '될 수 있습니다. 명명된 할당은 추정된 상태로 유지되며 하드 링크는 이름별로 계산됩니다. 소유권은 실제 '
        '사용 또는 제거 권한을 증명하지 않습니다. 정리 작업이 준비되지 않았습니다.'
    ),
    'bin_labels_refresh': '빈 합계 새로 고침',
    'bin_labels_hint': (
        '최대 256개의 준비된 드라이브에 대한 읽기 전용 스냅샷으로, 검사된 드라이브의 우선 순위를 지정합니다. '
        'POSIX 총계는 논리적 페이로드 바이트입니다. 사용할 수 없거나 부분 합계는 0을 의미하지 않습니다. 범위'
        '는 겹칠 수 있습니다. 합산하지 마십시오. 쿼리하려면 새로고침하세요. 이는 정리 작업을 준비하지 않습니'
        '다.'
    ),
    'bin_label_scope_unknown': '이 스캔 드라이브의 휴지통: 범위가 쿼리되지 않았습니다.',
    'bin_label_unqueried': '{root} 휴지통: 쿼리되지 않음',
    'bin_label_total': '{root} 휴지통: {size}, {count} 항목',
    'bin_label_partial': '{root} 휴지통: 총 알 수 없음; 알려진 {size}, {count} 항목',
    'action_file_times': '파일 날짜…',
    'action_file_times_tip': '이 스캔에서 기록된 액세스 및 생성 날짜를 필터링합니다.',
    'action_capture_file_times': '파일 액세스/만든 날짜 기록',
    'action_capture_file_times_tip': (
        '기본적으로 꺼져 있습니다. 향후 스캔에 일반 파일당 16바이트를 추가합니다. 활성화 후 다시 검색'
    ),
    'column_accessed': '기록된 액세스',
    'column_created': '만든 날짜',
    'file_times_hint': (
        '옵션 활성화 → 파일 액세스/생성 시간을 캡처한 다음 다시 검색합니다. 일반 파일만 해당; 디렉토리/링크 '
        '및 사용할 수 없는 생성 날짜는 아직 알 수 없습니다. 액세스 날짜는 백그라운드 도구를 통해 비활성화, 지'
        '연 또는 업데이트될 수 있습니다. 실제 사용을 증명하지 않습니다. POSIX ctime은 생성 시간이 아닙니다. '
        '이 보기는 정리 작업을 준비하지 않습니다.'
    ),
    'file_times_accessed': '다음 이후로 열리지 않았습니다... (접속 날짜 기록)',
    'file_times_created': '적어도… 전에 생성됨',
    'file_times_mode': '기록된 연령 모드',
    'file_times_days': '일',
    'file_times_reading': '녹화된 파일 날짜 필터링 중…',
    'file_times_summary': (
        '{count} 일치, {size}; {shown}을 표시합니다. {unknown}/{total} 파일에는 사용할 수 없거나 미래 날짜가 '
        '있습니다.'
    ),
    'file_times_policy_disabled': (
        'NTFS은 액세스 업데이트가 비활성화되었다고 보고합니다. 접속 연령 매칭이 불가능합니다. 생성 필터링은 '
        '계속 사용할 수 있습니다. 레지스트리 설정은 다시 시작해야 할 수 있으며 모든 파일 시스템을 설명하지는 '
        '않습니다.'
    ),
    'file_times_policy_unknown': (
        'NTFS 액세스 업데이트 구성을 알 수 없습니다. 접속 연령 매칭이 불가능합니다. 생성 필터링은 계속 사용할'
        ' 수 있습니다.'
    ),
    'file_times_policy_enabled': (
        'NTFS 레지스트리 보고서 액세스 업데이트가 활성화되었습니다. 재시작 보류, 파일 시스템/공급자 설정 및 '
        '지연된 업데이트가 여전히 날짜에 영향을 미칠 수 있습니다.'
    ),
    'file_times_policy_platform': (
        '파일 시스템/공급자 설정으로 인해 액세스 업데이트가 지연되거나 억제될 수 있습니다. 이러한 날짜를 기록'
        '된 메타데이터로 취급하십시오.'
    ),
    'action_programs': '설치된 프로그램…',
    'action_programs_tip': '이 스캔에서는 설치 프로그램/게임 메타데이터를 설치 폴더와 비교합니다.',
    'program_name': '프로그램/게임',
    'program_source': '메타데이터 소스',
    'program_version': '버전/빌드',
    'program_publisher': '출판사',
    'program_reported': '보고된 추정치',
    'program_scanned': '스캔된 논리 바이트',
    'program_allocated': '스캔된 명명된 할당',
    'program_coverage': '녹음된 폴더 범위',
    'program_location': '설치 폴더',
    'program_registry': 'Windows 레지스트리',
    'program_steam': '스팀 매니페스트',
    'program_epic': '에픽 매니페스트',
    'program_outside': '정확한 스캔 폴더가 없습니다.',
    'program_hint': (
        'Windows 등록 및 인식된 Steam/Epic 매니페스트를 제거하고 이 스캔에서 정확한 폴더에만 일치합니다. Epic'
        '의 고정 ProgramData 매니페스트 폴더도 읽습니다. 보고된 크기는 추정치입니다. 누락된 메타데이터는 알 '
        '수 없는 상태로 유지됩니다. 공유/중첩 폴더는 겹칠 수 있습니다. 행을 합산하거나 복구 가능한 공간으로 '
        '취급하지 마십시오. 휴대용/패키지 앱이 없을 수 있습니다. 두 번 클릭하면 녹음된 폴더가 선택됩니다. Ctr'
        'l+C는 행을 복사합니다. Windows 또는 실행 프로그램을 통해서만 제거하세요.'
    ),
    'program_reading': '설치 메타데이터를 읽는 중…',
    'program_summary': (
        '{count} 설치 중 {shown} 표시 중; {issues} 사용할 수 없거나 형식이 잘못되었거나 생략된 메타데이터 항'
        '목'
    ),
    'program_failed': '설치를 읽을 수 없습니다: {reason}',
    'program_uninstall_page': 'Windows 설치된 앱 설정 열기',
    'program_open_failed': 'Windows 설치된 앱 설정 페이지를 열 수 없습니다.',
    'action_history': '스캔 기록…',
    'action_history_tip': '시간이 지남에 따라 이 루트의 크기를 검토하고 이전 스캔과 비교합니다.',
    'action_history_settings': '스캔 기록 설정…',
    'action_history_settings_tip': '로컬 스캔 메타데이터를 활성화하고 전역 보존 제한을 설정합니다.',
    'history_enable': '완료된 전체 검사를 로컬에 보관',
    'history_settings_hint': (
        '기록에는 폴더 이름, 경로, 합계 및 적용 범위가 저장되며 파일 내용은 저장되지 않습니다. 기본값: 활성화'
        '됨, 모든 루트에서 총 1GiB. 인식된 기록 메타데이터만 제거됩니다. 가장 오래된 것부터 제거됩니다. 비활'
        '성화하면 기존 기록을 계속 읽을 수 있습니다. 변경 사항은 향후 전체 검색에 적용됩니다. 하한은 다음 저'
        '장 시 적용됩니다.'
    ),
    'history_limit': '총 내역 한도',
    'history_time': '스캔 시간',
    'history_logical': '논리 크기',
    'history_allocated': '할당된 명명된 바이트',
    'history_coverage': '적용 범위',
    'history_incomplete': '미완성; 알려진 데이터만',
    'history_complete': '녹음된 범위를 완료하세요.',
    'history_chart': '시간 경과에 따른 논리적 폴더 크기',
    'history_chart_range': '{first}: {before}; {last}: {after}',
    'history_empty': '이 루트에 대해 보관된 스캔이 없습니다.',
    'trend_folder': '루트 상대 폴더',
    'trend_folder_hint': '비워 두면 루트',
    'trend_start': '시작 날짜(포함)',
    'trend_end': '끝 날짜(포함)',
    'trend_apply': '추세 적용',
    'trend_change': '변화',
    'trend_child': '직계 하위 폴더',
    'trend_before': '시작 크기',
    'trend_after': '종료 크기',
    'trend_direct_files': '직계 파일',
    'trend_unknown': '알 수 없음',
    'trend_net': '기간 순변화: {change}',
    'trend_net_unknown': '기간 순변화를 알 수 없음',
    'trend_summary': '날짜가 유효한 스캔 {shown}/{count}개, 잘못된 헤더 {invalid}개. '
                     '직계 항목 {children}/{child_count}개. {cap}',
    'trend_capped': '기간이 제한되어 전체 순변화를 계산할 수 없음',
    'trend_invalid': '잘못된 추세 조건: {reason}',
    'trend_reason_legacy': '이전 기록의 스캔 규칙을 알 수 없음',
    'trend_reason_incomplete': '불완전한 스캔',
    'trend_reason_incompatible': '스캔 규칙 또는 루트가 호환되지 않음',
    'trend_reason_missing': '폴더 없음',
    'trend_reason_corrupt': '스캔 본문 손상',
    'trend_chart_known': '알려진 크기 {known}/{total}개. 알 수 없는 지점에서 선이 끊김',
    'trend_chart_unknown': '비교할 수 있는 폴더 크기가 없음',
    'trend_net_reason': '기간 순변화를 알 수 없음: {reason}',
    'trend_reason_truncated': '기간 기록이 제한됨',
    'trend_reason_insufficient': '관측값이 2개 미만',
    'trend_tab_sizes': '폴더 크기',
    'trend_tab_sources': '직계 기여 항목',
    'trend_tab_compare': '전체 루트 비교',
    'history_compare': '선택한 스캔을 현재 결과와 비교',
    'history_reading': '로컬 검사 기록을 읽는 중…',
    'history_hint': (
        '이 루트에 대한 최근 1,000개의 전체 검색이 보관되었습니다. 중지된 검사와 분기 재검사는 저장되지 않습'
        '니다. 불완전한 스캔은 알려진 데이터만 설명합니다. 누락된 폴더는 삭제된 것으로 입증되지 않습니다. 총'
        '계는 하드링크 이름을 별도로 계산합니다. 차이점은 콘텐츠 확인이 아니라 메타데이터입니다.'
    ),
    'history_summary': '{count} 스캔 중 {shown} 표시 중; {invalid} 유효하지 않거나 사용할 수 없는 메타데이터 파일',
    'history_failed': '기록을 읽을 수 없습니다: {reason}',
    'history_save_failed': '스캔이 완료되었지만 기록을 저장할 수 없습니다: {reason}',
    'action_scan_workers': '스캔 스레드 수…',
    'action_scan_workers_tip': '새로운 스캔에 대한 동시성을 선택하십시오. 높을수록 항상 빠른 것은 아닙니다',
    'workers_prompt': (
        '새 스캔을 위한 작업자(1–32). 기본값은 {default}입니다. 느린 네트워크 공유는 더 많은 작업자로부터 이'
        '익을 얻을 수 있습니다. 과도한 동시성은 디스크/서버에 과부하를 줄 수 있습니다. 스캔을 실행하면 기존 '
        '작업자가 유지됩니다. 실제 UNC 성능은 귀하의 공유에 따라 달라집니다.'
    ),
    'action_auto_cpu': 'CPU 사용량에 맞춰 스캔 스레드 조정',
    'action_auto_cpu_tip': (
        '다른 프로그램이 CPU를 사용하는 동안에는 새 스캔의 읽기 스레드를 줄이고, '
        'CPU가 한가해지면 설정한 스레드 수로 되돌립니다'
    ),
    'action_mft_scan': 'NTFS 드라이브를 파일 테이블에서 읽기',
    'action_mft_scan_tip': (
        '관리자 권한으로 실행하여 NTFS 드라이브의 폴더를 스캔할 때 폴더를 하나씩 나열하는 대신 '
        '드라이브의 마스터 파일 테이블을 직접 읽습니다. 다른 스캔은 이전과 같습니다'
    ),
    'action_bins': '휴지통…',
    'action_bins_tip': '빈 합계 및 명시적인 범위 OS 비우기 검토',
    'bin_finder_empty': '마운트된 모든 볼륨의 Finder 휴지통을 비우세요…',
    'bin_finder_all': '마운트된 모든 볼륨(Finder 전체 휴지통)',
    'bin_finder_scopes': '현재 사용자 휴지통 범위:\n{scopes}\n\n마운트된 볼륨:\n{roots}',
    'bin_finder_first': (
        '마운트된 모든 볼륨에서 현재 사용자의 Finder 휴지통을 비우시겠습니까?\n\n{root}\n\n논리 페이로드: {si'
        'ze}\n항목: {count}'
    ),
    'bin_finder_irreversible': (
        '마운트된 모든 볼륨에서 현재 사용자의 Finder 휴지통을 영구적으로 비우시겠습니까?\n\n{root}\n\n내용의 '
        '논리 크기: {size}\n항목 수: {count}\n\n이 작업은 되돌릴 수 없습니다. Finder 작업 중 새로 들어온 항목'
        '도 삭제될 수 있습니다. 선택한 행과 관계없이 마운트된 모든 휴지통에 적용됩니다. 운영체제 작업은 취소'
        '할 수 없습니다. 자동화 허용 또는 접근 권한 문제로 일부만 처리될 수 있으며, Finder 작업이 계속 진행 '
        '중일 수도 있습니다.'
    ),
    'bin_preparing': '{root}에서 정확한 휴지통 범위를 검토하는 중…',
    'bin_no_approval': '비어 있지 않은 완전한 휴지통 승인이 없습니다. 새로고침하고 다시 검토하세요.',
    'bin_scope_first': (
        '현재 사용자 휴지통 페이로드/작업 기록 범위를 비우시겠습니까?\n\n{root}\n\n논리 페이로드: {size}\n항'
        '목: {count}'
    ),
    'bin_scope_irreversible': (
        '다음 정확한 범위에서 검토한 내용을 영구 삭제하시겠습니까?\n\n{root}\n\n내용의 논리 크기: {size}\n항'
        '목 수: {count}\n\n이 작업은 되돌릴 수 없습니다. 링크의 대상을 따라가지 않고 링크 자체를 삭제합니다. '
        '변경된 항목은 처리하지 않습니다. 실패하면 일부만 처리된 결과가 남을 수 있습니다. 비우기를 시작한 뒤'
        '에는 취소할 수 없습니다.'
    ),
    'bin_partial': '{count} 검토 항목이 삭제되었습니다. 남은 실패: {reason}',
    'bin_empty': '선택한 드라이브의 휴지통 비우기…',
    'bin_first': '{root}의 휴지통을 비우세요?\n\n보고된 크기: {size}\n항목: {count}',
    'bin_irreversible': (
        '{root}의 휴지통에 현재 있는 모든 항목을 영구 삭제하시겠습니까?\n\n보고된 크기: {size}\n항목 수: {cou'
        'nt}\n\n이 작업은 되돌릴 수 없습니다. 운영체제 작업 중 새로 들어온 항목도 삭제될 수 있습니다. 시작한 '
        '뒤에는 운영체제 작업을 취소할 수 없습니다.'
    ),
    'bin_running': '{root}에서 휴지통 비우기; OS 작업을 기다리는 중…',
    'bin_failed': '비우기가 완료되지 않았습니다: {reason}',
    'bin_hint': (
        '마운트된 볼륨 하나를 선택합니다. Windows은 현재 사용자 OS 저장소를 비웁니다. Linux 인벤토리는 파일/'
        '정보 범위를 인식합니다. 두 가지 질문은 영구 제거 전의 정확한 범위와 합계를 보여줍니다. 중지는 설문조'
        '사를 취소합니다. 활성 비우기가 완료되어야 합니다. macOS는 전체 검토 후 마운트된 모든 Finder 휴지통을'
        ' 비웁니다(기본 유효성 검사 보류 중). 용량/bin 값은 나중에 새로 고쳐집니다. 메인 트리를 업데이트하려'
        '면 다시 스캔하세요.'
    ),
    "forecast_column": "여유 공간 예측",
    "forecast_record": "예측을 위해 사용 공간 기록",
    "forecast_record_tip": (
        "이 개요를 열 때마다 FileTree는 각 드라이브의 시각, 사용 바이트와 전체 바이트를 로컬 데이터 폴더에 "
        "저장합니다. 드라이브마다 최대 {hours}시간에 1개, 최대 {count}개입니다. 파일 정보는 저장하지 않습니다."
    ),
    "forecast_growing": "하루 약 {rate} — {date}쯤 가득 참",
    "forecast_not_soon": "하루 약 {rate} — {years}년 안에는 가득 차지 않음",
    "forecast_stable": "늘지 않음",
    "forecast_not_enough": "아직 기록이 부족합니다(며칠 필요)",
    "forecast_off": "기록이 꺼져 있음",
    "forecast_unknown": "알 수 없음(사용 공간이 보고되지 않음)",
    "forecast_off_tip": "아래에서 기록을 켜면 이 드라이브의 사용 공간 기록이 쌓입니다.",
    "forecast_unknown_tip": "시스템이 이 드라이브의 사용 공간을 보고하지 않아 기록하지 않았습니다.",
    "forecast_not_enough_tip": (
        "지금까지 {days}일 동안 {count}개입니다. 예측하려면 {needed_days}일 이상에 걸친 {needed}개 이상이 "
        "필요합니다. 이 개요를 열 때 기록됩니다(최대 몇 시간에 1개)."
    ),
    "forecast_estimate_tip": (
        "{days}일 동안의 사용 공간 {count}개로 추정한 값입니다(최대 최근 {window}일, 전체 크기가 마지막으로 바뀐 "
        "이후). 최근 속도가 계속된다고 가정하며 보장되지 않습니다."
    ),
    "forecast_newer": "여유 공간 기록이 더 새 버전의 FileTree로 저장되어 그대로 두었습니다.",
    "forecast_save_failed": "여유 공간 기록을 저장할 수 없습니다: {reason}",
    "forecast_unavailable": "여유 공간 기록을 사용할 수 없습니다: 시스템이 앱 데이터 폴더를 제공하지 않습니다.",
    'action_volumes': '드라이브 개요…',
    'action_volumes_tip': '마운트된 볼륨, 용량, 할당 단위 및 휴지통 총계를 검사합니다.',
    'volume_root': '마운트된 루트',
    'volume_name': '볼륨 이름',
    'volume_fs': '파일 시스템',
    'volume_total': '합계',
    'volume_used': '중고',
    'volume_free': '당신이 사용할 수',
    'volume_cluster': '할당단위',
    'volume_trash': '휴지통 바이트',
    'volume_trash_count': '빈 항목',
    'volume_reading': '마운트된 볼륨 및 휴지통 합계를 읽는 중…',
    'volume_summary': '{count} 중 {shown} 마운트된 볼륨을 표시합니다. 스캔하려면 두 번 클릭하세요.',
    'volume_trash_partial': '알 수 없는 합계({known} 알려짐)',
    'volume_hint': (
        'OS 용량 스냅샷 사용 가능한 공간에는 예약이나 할당량이 제외될 수 있습니다. 반복 마운트는 용량을 공유'
        '할 수 있습니다. 행을 합산하지 마세요. Windows 할당 단위는 클러스터입니다. POSIX 단위는 최적의 전송 '
        '크기가 아닌 파일 시스템 조각입니다. 휴지통에는 회수 가능한 공간이 아닌 OS에서 보고한 Windows 총계 또'
        '는 알려진 POSIX 논리적 페이로드 바이트가 표시됩니다. 디렉터리/작업 기록 메타데이터 및 공유 할당은 제'
        '외됩니다. 오류는 아직 알려지지 않았습니다. 중지는 현재 OS 호출을 기다립니다. 취소된 설문조사는 폐기'
        '됩니다. Ctrl+C는 행을 복사합니다. 여기서는 비우기 작업이 제공되지 않습니다.'
    ),
    'action_disks': '물리 디스크…',
    'action_disks_tip': '물리 드라이브, 상태 및 파티션 구성 보기(읽기 전용)',
    'disks_title': '물리 디스크',
    'disks_hint': '읽기 전용: FileTree는 시스템이 보고하는 각 물리 드라이브 정보만 보여 주며 디스크의 내용은 '
                  '아무것도 바꾸지 않습니다. 일련 번호는 표시하지 않습니다.',
    'disks_reading': '물리 디스크를 읽는 중…',
    'disks_summary': '찾은 물리 디스크: {count}개.',
    'disks_none': '시스템이 물리 디스크를 보고하지 않았습니다.',
    'disks_problem_unsupported': '이 시스템에서는 물리 디스크를 나열할 수 없습니다.',
    'disks_problem_tool_missing': '디스크를 나열하는 시스템 도구를 찾을 수 없습니다.',
    'disks_problem_timeout': '시스템이 디스크를 나열하는 데 너무 오래 걸렸습니다. 새로 고침을 눌러 보세요.',
    'disks_problem_failed': '시스템이 디스크를 나열하지 못했습니다.',
    'disks_problem_malformed': '시스템이 보고한 디스크 목록을 읽을 수 없습니다.',
    'disks_refresh': '새로 고침',
    'disks_select': '디스크를 선택하면 상태와 파티션이 표시됩니다.',
    'disks_col_disk': '디스크',
    'disks_col_model': '모델',
    'disks_col_media': '종류',
    'disks_col_bus': '연결',
    'disks_col_style': '파티션 테이블',
    'disks_col_size': '크기',
    'disks_col_health': '상태',
    'disks_col_number': '#',
    'disks_col_kind': '파티션 종류',
    'disks_col_label': '레이블',
    'disks_col_mounts': '드라이브 문자 / 마운트 지점',
    'disks_col_fs': '파일 시스템',
    'disks_col_offset': '시작 위치',
    'disks_media_ssd': 'SSD',
    'disks_media_hdd': '하드 디스크(HDD)',
    'disks_media_unknown': '알 수 없음',
    'disks_unknown': '알 수 없음',
    'disks_state_healthy': '정상',
    'disks_state_warning': '경고',
    'disks_state_unhealthy': '고장 징후',
    'disks_state_unknown': '알 수 없음',
    'disks_health_line': '상태: {state}. {meaning}',
    'disks_meaning_healthy': '드라이브가 문제를 보고하지 않았습니다. 드라이브는 예고 없이 고장 날 수 있으니 백업은 '
                             '계속하세요.',
    'disks_meaning_warning': '드라이브가 문제를 보고했습니다. 중요한 파일을 곧 백업하고 제조사 도구로 확인하세요.',
    'disks_meaning_unhealthy': '드라이브가 고장 나고 있다고 보고했습니다. 지금 중요한 파일을 백업하고 교체를 '
                               '준비하세요.',
    'disks_meaning_unknown': '시스템이 이 드라이브의 상태를 보고하지 않아 FileTree가 판단할 수 없습니다.',
    'disks_counters': '온도: {temperature} · 마모: {wear} · 전원 켜짐 시간: {hours}',
    'disks_temperature_value': '{degrees} °C',
    'disks_wear_value': '정격 수명의 {percent}% 사용',
    'disks_hours_value': '{hours}시간',
    'disks_not_reported': '사용할 수 없음',
    'disks_counters_denied': '이 시스템에서는 온도, 마모, 전원 켜짐 시간을 읽으려면 관리자 권한이 필요합니다. '
                             '보려면 FileTree를 관리자로 다시 시작하세요. 여기서는 권한을 요청하지 않습니다.',
    'disks_counters_missing': '이 드라이브 또는 드라이버는 온도, 마모, 전원 켜짐 시간을 보고하지 않습니다.',
    'disks_counters_unsupported': '이 시스템에서는 마모와 전원 켜짐 시간을 읽으려면 관리 도구(예: smartctl)가 '
                                  '필요하지만 FileTree는 이를 실행하지 않습니다.',
    'disks_no_partitions': '보고된 파티션이 없습니다.',
    'disks_free_space': '할당되지 않음',
    'disks_bar_name': '파티션 구성',
    'disks_tool_management': '디스크 관리…',
    'disks_tool_optimize': '드라이브 최적화…',
    'disks_tool_volumes': '디스크 및 볼륨 설정…',
    'disks_tool_storage': '저장소 설정…',
    'action_export_report_html': '스캔 보고서(HTML)…',
    'action_export_report_html_tip': '3개의 차트 이미지가 포함된 독립형 보고서 저장',
    'action_export_report_xlsx': '스캔 보고서(Excel)…',
    'action_export_report_xlsx_tip': '보고서 목록을 별도의 Excel 워크시트에 저장',
    'html_filter': 'HTML 보고서(*.html)',
    'xlsx_filter': 'Excel 통합 문서(*.xlsx)',
    'report_title': 'FileTree 스캔 보고서',
    'report_note': (
        '알려진 기록 범위만 해당. 할당은 추정치입니다. 제목의 개수는 표시/총계로 표시됩니다. 상위 폴더가 겹칩'
        '니다. 해당 행을 추가하지 마세요. 가장 큰 파일과 폴더는 1,000개로 제한됩니다. 파일 형식을 10,000으로 '
        '늘립니다. 크기는 바이트입니다. 연령은 마지막 액세스가 아닌 기록된 수정 시간을 사용합니다. 이용할 수 '
        '없는 날짜는 기존의 가장 오래된 연령 그룹에 속합니다. HTML 차트는 제한된 형상으로 전체 스캔 루트를 표'
        '시합니다. Excel 텍스트는 이스케이프되고 제어 문자는 16진수로 표시되며 셀은 32,767자로 제한되고 16자'
        '리 이상의 정수는 정확한 텍스트로 저장됩니다.'
    ),
    'report_bytes': '논리 바이트',
    'report_allocated': '할당된 바이트(예상)',
    'report_created': '보고서가 생성되었습니다.',
    'report_reference': '연령 참고',
    'report_skipped': '건너뛴 폴더',
    'report_denied': '읽을 수 없는 폴더',
    'report_pending': '보류 중인 폴더',
    'report_summary': '요약',
    'report_notes': '메모',
    'report_field': '필드',
    'report_value': '가치',
    'report_top_folders': '가장 큰 폴더(겹침)',
    'report_categories': '카테고리',
    'action_projects': '프로젝트 및 재구성 가능한 데이터…',
    'action_projects_tip': '기록된 프로젝트, Git 및 생성된 데이터 크기 검사',
    'project_path': '프로젝트/관리 매장',
    'project_kind': '감지된 종류',
    'project_other': '출처/기타',
    'project_git': '.git',
    'project_generated': '재구성 가능한 데이터',
    'project_coverage': '적용 범위',
    'project_partial': '미완성',
    'project_recorded': '기록된 범위',
    'project_hint': (
        '알려진 논리 바이트만. 중첩된 프로젝트가 겹칩니다. Git 포인터 파일에는 외부 메타데이터가 생략되어 있'
        '습니다. 생성된 데이터에는 사용자 정의 파일이 포함될 수 있습니다. 이동하기 전에 검토하세요. Maven, 글'
        '로벌 Gradle 및 Docker 스토어는 별도로 표시됩니다. 그 내용물은 일회용이 아닌 것으로 추정됩니다.'
    ),
    'project_reading': '기록된 프로젝트 데이터를 검사하는 중…',
    'project_summary': '감지된 {count} 중에서 가장 큰 프로젝트/매장 {shown}개를 표시합니다.',
    'project_review': '재구축 가능한 적격 항목을 검토하세요…',
    'project_review_count': (
        '현재 연령, 적용 범위 및 청소 정책에 따라 적격한 {count} 항목 중 최대 {shown} 항목을 검토하세요. 중지'
        '된 스캔은 항목을 제안할 수 없습니다.'
    ),
    'project_git_kind': '힘내',
    'project_python': '파이썬',
    'project_node': 'Node.js',
    'project_rust': '녹',
    'project_jvm': 'JVM',
    'project_conda': '콘다 프로젝트',
    'project_python_environment': 'Python 환경',
    'project_conda_environment': '콘다 환경',
    'project_maven_store': '메이븐 스토어',
    'project_gradle_store': '글로벌 Gradle 스토어',
    'project_docker_store': '도커 데이터',
    'action_git_history': 'Git 기록…',
    'action_git_history_tip': '모든 Git 참조에서 연결할 수 있는 가장 큰 개체를 검사합니다.',
    'git_oid': '개체 ID',
    'git_kind': '객체 유형',
    'git_length': '비압축 길이',
    'git_type_blob': '파일 콘텐츠(BLOB)',
    'git_type_tree': '디렉토리 목록(트리)',
    'git_type_commit': '커밋',
    'git_type_tag': '주석이 달린 태그',
    'git_hint': (
        '읽기 전용 Git 배관은 모든 참조를 검사하여 최대 1,000개의 개체를 유지합니다. 크기는 디스크 할당이나 '
        '복구 가능한 공간이 아닌 압축되지 않은 길이입니다. Git의 객체 이름 힌트가 모호할 수 있으므로 이름은 '
        '생략됩니다. Ctrl+C는 개체 ID/행을 복사합니다. 선택적 잠금, 자동 유지 관리 및 지연 네트워크 가져오기'
        '가 비활성화됩니다. Git은 --no-lazy-fetch를 지원해야 합니다. 저장소 소유권 오류는 우회되지 않습니다. '
        '중지는 취소됩니다. 여기서는 gc가 실행되지 않습니다.'
    ),
    'git_reading': 'Git 기록을 조사하는 중…',
    'git_summary': '{count} 연결 가능한 객체 중 {shown} 표시 중; 압축되지 않은 총계 {size}.',
    'git_gc_loose': (
        'Git gc는 {count} 느슨한 개체를 통합할 수 있지만 이러한 가장 큰 개체는 참조에서 계속 연결할 수 있으며'
        ' 제거되지 않습니다. 실제 절감액 및 기타 접근할 수 없는/재로그 데이터는 알 수 없습니다.'
    ),
    'git_gc_packed': (
        '통합할 느슨한 개체가 없습니다. Git gc는 참조가 유지하는 동안 이러한 객체를 제거하지 않습니다. 기타 '
        '연결할 수 없는/재로그 데이터 및 실제 절감액은 측정되지 않았습니다.'
    ),
    'git_failed': 'Git 검사 실패: {reason}',
    'tree_filter_placeholder': '펼친 폴더 필터…',
    'tree_filter_hint': (
        '이미 확장된 폴더 내에서만 이름을 일치시킵니다(대소문자 구분 안 함). 조상은 계속 보입니다. 접힌 내용'
        '은 검색되지 않습니다. 트리를 복원하려면 필터를 지우세요. 차트/목록에서 숨겨진 항목을 선택하면 필터가'
        ' 지워집니다. 스캔 합계 및 내보내기는 변경되지 않습니다.'
    ),
    'action_live_compare': '두 폴더 비교…',
    'action_live_compare_tip': '새로운 상대 경로를 비교하고 요청된 파일 쌍만 확인합니다.',
    'compare_choose_left': '왼쪽 폴더를 선택하세요',
    'compare_choose_right': '올바른 폴더를 선택하세요',
    'compare_relative': '상대 경로',
    'compare_state': '비교',
    'compare_left_size': '왼쪽 사이즈',
    'compare_right_size': '적당한 크기',
    'compare_left_time': '왼쪽 수정됨',
    'compare_right_time': '오른쪽 수정됨',
    'compare_roots': '왼쪽: {left}\n오른쪽: {right}',
    'compare_hint': (
        '읽기 전용: 정확한 유니코드/대소문자 이름이 일치합니다. 링크는 따라가지 않습니다. 동일한 크기/시간은 '
        '동일한 내용을 증명하지 않습니다. 파일 쌍을 선택하고 중지 기능을 사용하여 전체 해시를 확인하세요. 변'
        '경되어 읽을 수 없으며 알려진 클라우드 파일은 계속 사용할 수 없습니다. 결과는 이 스캔/검증 시간을 나'
        '타냅니다. 복사, 이동 또는 동기화가 수행되지 않습니다. Ctrl+C는 행을 복사합니다. CSV은 표시된 행만 최'
        '대 10,000개까지 내보냅니다.'
    ),
    'compare_reading': '두 폴더를 모두 검사하는 중…',
    'compare_error': '비교 또는 내보내기 실패: {reason}',
    'compare_hashing': '선택한 파일 쌍을 확인하는 중…',
    'compare_verify': '선택한 내용을 확인하세요',
    'compare_summary': '{count} 상대 경로 중 {shown} 표시 중(10,000개 제한)',
    'compare_incomplete': '보장이 불완전합니다. 읽을 수 없는 범위의 누락된 경로는 알 수 없는 상태로 남아 있습니다.',
    'compare_unavailable': '사용할 수 없거나 변경됨',
    'compare_link': '링크; 읽지 않은 내용',
    'compare_only_left': '왼쪽에만',
    'compare_only_right': '오른쪽에만',
    'compare_different_kind': '다양한 항목 유형',
    'compare_folder': '양쪽에 폴더',
    'compare_different_size': '다양한 크기',
    'compare_different_time': '다른 시간; 체크되지 않은 내용',
    'compare_unchecked': '확인되지 않은 내용',
    'compare_identical': '전체 해시 일치',
    'compare_different_bytes': '다양한 콘텐츠',
    'problem_mount_boundary': '마운트 경계: 콘텐츠가 스캔되지 않음',
    'action_special_files': '클라우드와 특수 파일…',
    'action_special_files_tip': '기록된 리콜, 오프라인, 압축 및 스파스 파일 상태 검사',
    'special_states': '기록된 상태',
    'special_content_size': '전체 콘텐츠 크기',
    'special_recall': '액세스 시 기억할 수 있음',
    'special_offline': '오프라인',
    'special_compressed': '압축',
    'special_sparse': '스파스',
    'special_allocation_low': '더 낮은 할당; 원인불명',
    'special_reading': '녹음된 파일 메타데이터를 읽는 중…',
    'special_hint': (
        '이 목록은 검색 메타데이터만 사용하며 파일이 열리거나 다운로드되지 않습니다. 리콜/오프라인 플래그는 O'
        'neDrive, Dropbox 또는 기타 제공자를 설명할 수 있습니다. 공급자와 이미 현지에 얼마가 있는지 추론할 수'
        ' 없습니다. 전체 콘텐츠 크기는 온라인 콘텐츠를 포함한 논리적 길이입니다. 다운로드 후 할당을 알 수 없'
        '습니다. 희박한 구멍, 압축 및 상주 데이터로 인해 할당이 줄어들 수 있습니다. 리콜/오프라인 항목에 대한'
        ' 디스크 0은 측정된 클라우드 할당이 아니라 추정치입니다. 두 번 클릭하면 스캔한 항목이 선택됩니다. Ctr'
        'l+C는 선택한 행을 복사합니다.'
    ),
    'special_summary': (
        '{count} 일치하는 파일 중 {shown}을 표시합니다. 전체 콘텐츠 {size}; 기록된 할당 {allocated}. 사용할 '
        '수 없는 파일 메타데이터: {unknown}. 최대 1,000개가 유지됩니다.'
    ),
    'special_partial': '스캔 범위가 불완전합니다. 보이지 않는 파일은 알 수 없는 상태로 남아 있습니다.',
    'action_shell_integration': '탐색기 통합…',
    'action_shell_integration_tip': '탐색기 폴더 메뉴에서 FileTree를 사용하여 스캔을 추가하거나 제거합니다.',
    'shell_enabled': '탐색기의 폴더 메뉴에 FileTree를 사용하여 스캔 추가',
    'shell_scan': 'FileTree로 스캔',
    'shell_hint': (
        '변경 사항은 계정의 폴더 메뉴에만 저장하세요. 관리자 권한이 필요하지 않습니다. Windows 11에서 추가 옵'
        '션 표시 아래를 살펴보세요. 항목을 제거하려면 여기에서 이 기능을 끄세요. 실행 파일 이동 또는 소스 체'
        '크아웃 후 다시 등록하세요. 이미 시작한 저장을 마친 후 닫힙니다.'
    ),
    'shell_failed': 'Explorer 통합을 변경할 수 없습니다.\n{reason}',
    'menu_properties': '속성',
    'properties_failed': 'Windows은(는) 다음에 대한 속성을 열 수 없습니다:\n{path}',
    'menu_theme': '테마',
    'theme_system': '시스템',
    'theme_light': '밝게',
    'theme_dark': '어둡게',
    'menu_text_size': '글자 크기',
    'text_size_larger': '크게',
    'text_size_smaller': '작게',
    'text_size_reset': '시스템 크기로 되돌리기',
    'text_size_percent': '{percent}%',
    'text_size_default': '{percent}%(시스템 크기)',
    'chart_access_keys': (
        '화살표 키는 렌더링된 항목을 선택합니다. Enter를 누르면 폴더가 열립니다. 백스페이스가 올라갑니다. 그'
        '룹화된 항목이나 숨겨진 항목에는 폴더 트리를 사용하세요.'
    ),
    'chart_access_tree_keys': (
        '위/아래는 카드를 선택합니다. 오른쪽/왼쪽은 폴더를 확장/축소합니다. Enter를 누르면 폴더가 열립니다. '
        '백스페이스가 올라갑니다.'
    ),
    'chart_access_folder': '표시 폴더: {path}',
    'chart_access_selected': '선택됨: {path}. 크기 {size}; 디스크 {allocated}; {files} 파일, {folders} 폴더.',
    'system_file_hibernate': (
        '최대 절전 모드 및 빠른 시작 상태. Windows이 이 파일을 관리합니다. 관리자는 powercfg /hibernate off를'
        ' 사용하여 최대 절전 모드를 비활성화할 수 있습니다. 이렇게 하면 최대 절전 모드도 제거되고 빠른 시작에'
        ' 영향을 미칠 수 있습니다. FileTree은 전원 설정만 엽니다.'
    ),
    'system_file_pagefile': (
        '가상 메모리 백업 파일. Windows은 크기를 자동으로 관리할 수 있습니다. 고급 탭의 성능 설정에서 가상 메'
        '모리를 검토하세요. 이를 줄이면 애플리케이션과 크래시 덤프에 영향을 미칠 수 있습니다.'
    ),
    'system_file_swapfile': (
        'Windows 정지된 앱 데이터를 포함한 스왑 백업 파일. Windows은 가상 메모리와 함께 관리합니다. 시스템 메'
        '모리 설정을 제거하는 대신 검토하십시오.'
    ),
    'system_file_old': (
        '이전 Windows 설치. 디스크 정리 → 시스템 파일 정리에서 이전 Windows 설치를 검토합니다. 이를 제거하면 '
        '해당 설치로 돌아갈 수 없습니다.'
    ),
    'system_file_recycle': (
        '삭제된 항목은 휴지통이 비워질 때까지 여전히 디스크 공간을 차지합니다. 휴지통이나 스토리지 센스를 검'
        '토하세요. 비우는 것은 영구적입니다.'
    ),
    'system_file_restore': (
        '시스템 메타데이터, 복원 지점 및 섀도 복사본. 시스템 보호 → 구성을 검토하여 복원 지점 제한을 설정합니'
        '다. 백업 소유의 섀도 복사본에는 자체 백업 도구가 필요할 수 있습니다. 읽지 않은 바이트는 알 수 없는 '
        '상태로 남아 있습니다.'
    ),
    'system_file_winsxs': (
        'Windows 구성요소 저장소. 많은 항목이 Windows 파일과 하드 링크를 공유하므로 이름별 총계가 개별 저장소'
        '를 과장할 수 있습니다. 디스크 정리에서 Windows 업데이트 정리 사용 → 시스템 파일 정리; 구성 요소를 수'
        '동으로 제거하지 마십시오.'
    ),
    'system_file_updates': (
        'Windows 다운로드 데이터를 업데이트합니다. 디스크 정리 → 시스템 파일 정리를 사용하여 Windows 업데이트'
        ' 및 임시 파일을 검토합니다. 활성 다운로드를 관리하려면 업데이트 서비스를 종료하세요.'
    ),
    'system_file_delivery': (
        'Windows 업데이트 및 앱에 대한 배달 최적화 다운로드 캐시입니다. 디스크 정리에서 배달 최적화 파일을 검'
        '토합니다. Windows은 활성 전송을 관리합니다.'
    ),
    'system_tool_power': '전원 설정 열기…',
    'system_tool_memory': '고급 시스템 설정 열기…',
    'system_tool_cleanup': '디스크 정리 열기…',
    'system_tool_storage': '오픈 스토리지 센스…',
    'system_tool_restore': '개방형 시스템 보호…',
    'system_tool_failed': 'Windows 도구를 열 수 없습니다.',
    'trash_skip_system_managed': 'Windows이 이 항목을 관리합니다. 대신 세부정보의 시스템 도구를 사용하세요.',
    'type_locations_title': '폴더 포함(최대 1,000개)',
    'type_location_size': '어울리는 사이즈',
    'type_locations_tip': (
        '총계에는 각 폴더에 직접 일치하는 파일이 포함됩니다. 하위 폴더는 겹치지 않고 분리되어 있습니다.'
    ),
    'action_export_list': '현재 목록(CSV)…',
    'action_export_list_tip': '표시된 필터 및 정렬 순서에 따라 활성 목록의 모든 행을 저장합니다.',
    'list_changed': '캡처 중에 목록이 변경되었습니다. 다시 내보내거나 복사해 보세요.',
    'details_title': '세부정보',
    'details_empty': '세부정보를 보려면 항목을 선택하세요.',
    'details_live': '스캔이 완료되면 배포가 가능합니다.',
    'details_loading': '유형 및 연령 분포를 계산하는 중…',
    'details_recorded': (
        '녹음된 파일 합계만; 읽지 않은 항목은 이러한 배포판 외부에 있습니다. 폴더 수정은 가장 최근에 녹음된 '
        '날짜입니다.'
    ),
    'details_bucket': '{label}: {size} · {count} 파일',
    'breadcrumbs_back': '뒤로(Alt+왼쪽)',
    'breadcrumbs_forward': '앞으로(Alt+오른쪽)',
    'breadcrumbs_more': '…',
    'breadcrumbs_more_tip': '이전 조상 표시',
    'action_print_view': '현재 보기 인쇄…',
    'action_print_view_tip': '시스템 인쇄 대화 상자를 통해 한 페이지에 보이는 결과를 인쇄합니다.',
    'action_export_view_pdf': '현재 보기(PDF)…',
    'action_export_view_pdf_tip': '하나의 적합한 PDF 페이지에 눈에 보이는 결과를 저장하세요.',
    'pdf_filter': 'PDF 문서(*.pdf)',
    'view_pdf_exported': '저장된 현재 보기: {path}',
    'print_failed': '뷰를 인쇄할 수 없습니다: {reason}',
    'print_submitted': '프린터에 제출된 보기',
    'action_export_chart_png': '화면 위의 차트(PNG)…',
    'action_export_chart_png_tip': '현재 뷰포트를 포함하여 보이는 차트를 저장합니다.',
    'action_export_chart_svg': '막대 또는 선버스트(SVG)…',
    'action_export_chart_svg_tip': '전체 경계 막대 또는 링을 벡터 모양 및 텍스트로 저장',
    'png_filter': 'PNG 이미지(*.png)',
    'svg_filter': 'SVG 이미지(*.svg)',
    'graphic_exported': '저장된 차트: {path}',
    'treemap_colours_age': '수정된 연령별',
    'age_colour_unknown': '날짜를 알 수 없음',
    'age_colour_tip': (
        '수정 이후 시간입니다. 폴더 색상은 가장 최근에 기록된 수정 사항을 사용합니다. 회색은 사용 가능한 날짜'
        '가 없음을 의미합니다. 그룹화된 타일은 회색으로 유지됩니다.'
    ),
    'action_gentle': '부하가 적은 스캔',
    'action_gentle_tip': '새로운 스캔에 대해서는 CPU 및 I/O 우선순위를 낮춥니다. 더 오래 걸릴 수 있습니다',
    'scan_priority_warning': '스캔 참고 사항: {reason}',
    'scan_pause': '일시중지',
    'scan_resume': '이력서',
    'scan_pause_tip': (
        '새 폴더 읽기를 일시 중지합니다. 현재 읽기가 완료되었습니다. 중지는 일시 정지된 동안 작동합니다.'
    ),
    'scan_paused': '일시중지됨 — {progress}',
    'scan_analysing': '폴더 읽기가 완료되었습니다. 결과 분석 중…',
    'column_drive_share': '드라이브 %',
    'columns_reset': '열 재설정',
    'drive_share_tip': (
        '논리 바이트를 총 볼륨 용량으로 나눈 값입니다. 하드 링크 이름은 별도로 계산됩니다. 이는 할당되거나 복'
        '구 가능한 공간이 아닙니다. 용량을 사용할 수 없거나 오래된 동안에는 알 수 없습니다.'
    ),
    'action_recent_actions': '최근 작업…',
    'action_recent_actions_tip': '보관된 작업 메타데이터를 검사하고 수정된 감사 보고서를 내보냅니다.',
    'journal_time': '시간(UTC)',
    'journal_source': '원래 경로',
    'journal_identity': '장치/파일 ID',
    'journal_result': '결과',
    'journal_detail': '세부정보',
    'journal_destination': '휴지통 목적지',
    'journal_reason_duplicates': '명시적 중복 결정',
    'journal_status_approved': '알 수 없는 결과(승인된 경우에만)',
    'journal_status_moved': '휴지통으로 이동됨',
    'journal_status_skipped': '건너뛰었습니다.',
    'journal_status_failed': '플랫폼 이동 실패',
    'journal_reading': '보관된 작업을 읽는 중…',
    'journal_hint': (
        '최근 500개 작업; 메타데이터만, 90일/50MB 동안 보관됩니다. 승인 전용 이벤트에는 알 수 없는 최종 결과'
        '가 있습니다. 기록된 휴지통 경로는 복원을 보장하지 않습니다.'
    ),
    'journal_summary': '{count} 작업이 표시됩니다. {invalid} 손상된 레코드 및 {unavailable} 사용할 수 없는 세그먼트.',
    'journal_read_failed': '작업 일지를 읽을 수 없습니다: {reason}',
    'journal_write_failed': (
        '저널 작성 또는 보관에 실패했습니다. 가능한 경우 나머지 동작은 중지되었습니다. 최근 작업이 완료되지 '
        '않았을 수 있습니다.\n\n{reason}'
    ),
    'trash_skip_journal': '승인된 조치를 기록할 수 없습니다. 아무것도 움직이지 않았어',
    'journal_export': '수정된 CSV 내보내기…',
    'journal_exported': '홈 디렉토리 접두사가 수정되어 저장된 감사 보고서입니다.',
    'duplicate_folder_match': '{copy} = {original} ({size}, {files} 파일; 일치하는 검색 스냅샷)',
    'duplicate_folder_tip': '이름, 크기, 검증된 해시 및 빈 폴더 구조가 일치합니다. 읽기 전용; 청소 승인이 아닙니다.',
    'duplicates_keep_selected': '선택한 사본 유지',
    'duplicates_kept_name': '유지: {name}',
    'duplicates_kept_path': '유지한 사본: {path}.',
    'duplicates_choose_keeper': '추가 항목을 선택하기 전에 이 그룹에 보관된 사본을 선택하세요.',
    'duplicates_group_blocked': '그룹은 그대로 유지됩니다. 재검색 필요: {reason}',
    'trash_skip_duplicate_choose': '보관된 사본을 선택한 다음 그룹을 다시 검토하세요.',
    'trash_skip_duplicate_keep': '보관된 사본이 선택되었습니다. 그룹은 그대로 유지되었습니다. 다시 스캔',
    'trash_skip_duplicate_unverified': '이 그룹에 대해 확인된 해시가 없습니다. 다시 스캔하고 다시 검색해 보세요.',
    'trash_skip_duplicate_hard_links': '복사본에는 하드링크 별칭이 있습니다. 그룹은 그대로 유지되었습니다. 다시 스캔',
    'trash_skip_duplicate_content': (
        '그룹 콘텐츠가 변경되었거나 다시 해시될 수 없습니다. 다시 스캔하고 다시 검색해 보세요.'
    ),
    'menu_options': '옵션',
    'action_cleanup_policy': '정리 정책…',
    'action_cleanup_policy_tip': '규칙을 활성화하고, 최소 기간을 변경하고, 정리 제안에서 경로를 제외하세요.',
    'policy_enabled': '활성화됨',
    'policy_age': '최소 연령(일)',
    'policy_age_for': '{rule}의 최소 연령',
    'policy_enabled_for': '{rule} 활성화',
    'policy_hint': (
        '정책 변경사항은 제안에만 영향을 미칩니다. 수동 위험 규칙은 선택되지 않은 상태로 유지됩니다. 저장하기'
        ' 전에 미리 보세요.'
    ),
    'policy_exclusions': (
        '이러한 경로나 이름을 제안하지 마십시오(한 줄에 하나씩, 경로는 절대 경로여야 함). 스캔은 변경되지 않'
        '습니다.'
    ),
    'policy_preview': '변경사항 미리보기',
    'policy_import': '가져오기 정책 JSON…',
    'policy_preview_needed': '저장하기 전에 현재 설정을 미리 봅니다.',
    'policy_preview_running': '후보 수와 논리적 크기 비교…',
    'policy_preview_result': (
        '{added} 후보({size})를 추가합니다. {removed} 후보({removed_size})를 제거합니다. 아무것도 움직이지 않'
        '았습니다.'
    ),
    'policy_preview_partial': '스캔이 불완전합니다. 보이지 않는 후보와 바이트는 알 수 없는 상태로 남아 있습니다.',
    'policy_no_scan': '스캔이 완료되지 않음: 효과를 측정할 수 없습니다. 이 설정은 향후 제안에 적용됩니다.',
    'policy_invalid': (
        '정책이 잘못되었습니다. 지원되는 규칙 키, 예/아니요 플래그, 연령 0~36500 및 절대 경로 또는 이름 패턴'
        '을 사용하세요.'
    ),
    'policy_saved': '정리 정책이 저장되었습니다. 제안사항을 새로고침하는 중입니다.',
    'policy_saved_invalid': '저장된 정리 정책이 잘못되었습니다. 옵션에서 정책을 검토할 때까지 제안이 비활성화됩니다.',
    'cleanup_review_manual': '직접 검토',
    'cleanup_evidence': (
        '카테고리: {category}; 최소 연령: {days}일; 위험: {risk}. 증거: {evidence} 재구축/결과: {rebuild}'
    ),
    'cleanup_category_temporary': '임시 파일',
    'cleanup_category_cache': '다운로드/생성된 캐시',
    'cleanup_category_application_state': '애플리케이션 상태',
    'cleanup_category_build': '프로젝트 빌드 출력',
    'cleanup_category_downloads': '사용자 다운로드',
    'cleanup_risk_low': '위험 감소; 이사하기 전에 확인하세요',
    'cleanup_risk_manual': '수동 검토; 선택하지 않은 채 시작됩니다',
    'cleanup_rebuild_temp': '소유 애플리케이션을 닫습니다. 임시 데이터는 반드시 다시 생성될 수 없습니다.',
    'cleanup_rebuild_browser_cache': (
        '브라우저를 닫습니다. 캐시된 페이지를 다시 다운로드합니다. 프로필과 북마크는 제외됩니다.'
    ),
    'cleanup_rebuild_thumbnails': '파일 관리자를 닫습니다. 필요할 때 미리보기가 다시 생성됩니다.',
    'cleanup_rebuild_crash_dumps': '필요한 충돌 증거를 보관하십시오. 과거 크래시 덤프를 다시 생성할 수 없습니다.',
    'cleanup_rebuild_package_caches': (
        '다시 다운로드하려면 패키지 관리자를 사용하세요. 네트워크 액세스를 확인하세요. 패키지 매장은 제외됩니'
        '다.'
    ),
    'cleanup_rebuild_build_output': (
        '프로젝트 내용과 종속성 잠금을 확인한 다음 문서화된 프로젝트 명령을 사용하여 다시 빌드하세요. 작성된 '
        '파일을 보관하세요.'
    ),
    'cleanup_rebuild_old_installers': (
        '설치 프로그램을 오프라인으로 유지하거나 사용할 수 없게 합니다. 아직 사용 가능한 경우 게시자로부터 다'
        '운로드하세요.'
    ),
    'cleanup_rebuild_empty_folders': (
        '응용프로그램에서는 여전히 빈 폴더가 나타날 것으로 예상할 수 있습니다. 먼저 목적을 확인하십시오.'
    ),
    'trash_holder': '{name} (PID {pid})',
    'trash_holders': (
        '{path}: {programs}에서 열려 있는 것으로 관찰되었습니다. 해당 프로그램을 직접 종료하고 다시 시도해 보'
        '세요.'
    ),
    'trash_holders_limited': (
        '{path}: 프로세스 가시성이 제한됩니다. 다른 보유자 또는 원인이 알려지지 않았을 수 있습니다.'
    ),
    'duplicates_savings': '고유 할당 추정치 {allocated}; 휴지통 {recoverable}을 비운 후 복구 가능한 파일 데이터.',
    'duplicates_estimating': '고유 할당 및 복구 가능한 파일 데이터 추정 중…',
    'duplicates_estimate_unavailable': (
        '예상 할당량을 확인할 수 없습니다. 추가 항목을 선택하기 전에 검색을 다시 실행하세요.'
    ),
    'duplicates_estimate_assumption': (
        '견적은 명시적인 보관 사본 선택을 사용합니다. 미정 그룹은 알 수 없습니다. 이동하기 전에 각 그룹을 확'
        '인하고 완전히 다시 해시합니다. 하드 링크 별칭은 결정을 차단합니다. 공유 범위와 디렉터리 메타데이터는'
        ' 아직 알려지지 않았습니다. 휴지통으로 이동해도 공간이 확보되지 않습니다.'
    ),
    'capacity_details': '용량 세부정보',
    'capacity_summary': 'OS 사용량 {used}; 여유 공간 {free}; 중복 제외 할당량 추정 {unique}. {status}',
    'capacity_estimated': '전체 볼륨의 추정치입니다. 설명되지 않은 공간은 세부 정보에 표시합니다.',
    'capacity_folder_only': '폴더만 스캔했습니다. 전체 볼륨 용량과 대조할 수 없습니다.',
    'capacity_incomplete': '스캔이 불완전합니다. 전체 볼륨 용량과 대조할 수 없습니다.',
    'capacity_identity_unknown': '파일 ID가 없습니다. 전체 볼륨 용량과 대조할 수 없습니다.',
    'capacity_capacity_unavailable': 'OS 용량을 확인할 수 없습니다. 전체 볼륨 용량과 대조할 수 없습니다.',
    'capacity_root_changed': '스캔한 루트가 변경되었습니다. 용량을 대조하기 전에 다시 스캔하세요.',
    'capacity_allocation_exceeds_used': '할당량 추정치가 OS 사용량을 초과하여 용량을 대조할 수 없습니다.',
    'capacity_coverage': '건너뛴 {skipped}; 읽을 수 없음 {inaccessible}; {pending} 보류 중',
    'capacity_bin_partial': '휴지통을 완전히 식별하거나 읽지 못했습니다. 표시된 용량은 확인된 데이터만 포함합니다.',
    'capacity_explanation': (
        '알려진 파일 할당에는 표시된 휴지통 데이터가 포함됩니다. 하드링크 이름은 한 번만 계산됩니다. 다른 마'
        '운트된 볼륨은 제외됩니다. 생략된 데이터와 파일 시스템 메타데이터는 알 수 없으며 0이 아닙니다. 설명되'
        '지 않은 항목에는 액세스할 수 없는 데이터, 메타데이터, 스냅샷, 공유 범위 및 할당 추정치가 포함될 수 '
        '있습니다. OS 용량과 파일은 다양한 순간에 측정됩니다. 파일 시스템은 스캔 중에 변경될 수 있습니다. 사'
        '용할 수 없는 여유 공간은 측정된 메타데이터 총계가 아니라 보고된 총계, 사용된 공간 및 사용 가능한 여'
        '유 공간 간의 차이입니다. 이는 NTFS, ext4 및 APFS 볼륨 검증이 보류 중인 추정치입니다.'
    ),
    'capacity_row_total': 'OS 전체',
    'capacity_row_used': 'OS 사용량',
    'capacity_row_free': 'OS 사용 가능한 여유 공간',
    'capacity_row_unavailable_free': '사용할 수 없는 여유 공간',
    'capacity_row_named_allocated': '이름별 할당량 추정',
    'capacity_row_unique_allocated': '중복 제외 할당량 추정',
    'capacity_row_hard_link_overcount': '제외된 하드 링크 중복 집계',
    'capacity_row_recycle_bin_seen': '휴지통 할당 확인(포함)',
    'capacity_row_foreign_allocated_seen': '기타 볼륨 파일 할당 확인(제외)',
    'capacity_row_unaccounted': '설명되지 않음',
    'capacity_row_metadata_bytes': '파일 시스템 메타데이터 / 예약됨',
    'capacity_row_omitted_bytes': '생략된 데이터',
    'capacity_row_other_volumes_bytes': '기타 마운트된 볼륨',
    'capacity_row_mounts': '다른 장치의 마운트 경계',
    'capacity_row_coverage': '적용 범위',
    'review_title': '청소 제안 검토',
    'review_logical_size': '논리 크기',
    'review_risk': '위험',
    'review_risk_low': '낮은 위험',
    'review_risk_manual': '수동 검토 필요',
    'review_details_label': '항목 세부 정보',
    'review_scope': '스캔 범위',
    'review_details': (
        '{path}\n'
        '규칙: {rule}\n'
        '수정 시간: {modified}\n'
        '논리 크기: {logical}; 할당 추정치: {allocated}\n'
        '위험: {risk}\n'
        '보호: {protection}\n'
        '\n'
        '{consequence}'
    ),
    'review_hint': '모든 경로와 결과를 검토하십시오. 항목을 유지하려면 선택을 취소하세요. 계속 확인이 열립니다.',
    'review_select': '이동',
    'review_rule': '규칙',
    'review_reason': '이유',
    'review_protection': '보호',
    'review_consequence': '결과',
    'review_manual': '수동 선택',
    'review_manual_reason': (
        '사용자가 선택한 항목 이를 제거하면 이에 의존하는 파일이나 프로그램에 영향을 미칠 수 있습니다.'
    ),
    'review_not_protected': '보호된 경로 일치 없음',
    'review_open_folder': '포함된 폴더 열기',
    'review_continue': '계속해서 확인하세요',
    'review_estimating': '{count} 항목이 선택되었습니다. 할당 추정 중…',
    'review_summary': (
        '{count}개 항목; 논리 크기 {logical}; 할당량 추정 {allocated}; 휴지통을 비운 후 회수 가능한 파일 데이'
        '터: {recoverable}; 지금 확보되는 여유 공간 {free}. 공유 영역과 디렉터리 메타데이터는 알 수 없습니다.'
        ' 휴지통으로 이동하는 것만으로는 여유 공간이 늘어나지 않습니다.'
    ),
    'size_unknown': '알 수 없음',
    'trash_running': '승인된 항목을 재검증하고 이동하는 중... 중지를 누르면 나머지 항목이 취소됩니다.',
    'trash_batch_done': '{moved} 이동, {skipped} 건너뛰기, {failed} 실패; {size}이(가) 휴지통으로 이동되었습니다.',
    'trash_skipped': '이 항목은 건너뛰었습니다. 다시 시도하기 전에 폴더를 다시 검사하세요.\n{names}',
    'trash_skip_outside': '현재 스캔 외부',
    'trash_skip_unverified': '확인된 스캔 ID 없음',
    'trash_skip_incomplete': '불완전한 스캔 범위',
    'trash_skip_missing': '항목 또는 상위 항목이 누락되었습니다.',
    'trash_skip_unreadable': '항목을 읽을 수 없습니다',
    'trash_skip_link': '항목 또는 상위가 링크가 되었습니다.',
    'trash_skip_kind': '항목 종류가 변경됨',
    'trash_skip_identity': '항목이 교체되었습니다',
    'trash_skip_changed': '크기, 타임스탬프 또는 폴더 내용이 변경됨',
    'trash_skip_protected': '확인된 경로에는 다른 보호 기능이 있습니다.',
    'trash_skip_cancelled': '작업이 취소되었습니다',
    'coverage_complete': (
        '적용 범위: {size}은 {known} 폴더에 알려져 있습니다. {skipped}을 건너뛰고, {denied}에 액세스할 수 없'
        '으며, {pending} 보류 중입니다.'
    ),
    'coverage_partial': (
        '불완전한 적용 범위: {size}은 {known} 폴더에 알려져 있습니다. {skipped}을 건너뛰고, {denied}에 액세스'
        '할 수 없으며, {pending} 보류 중입니다. 생략된 바이트를 알 수 없습니다. 정리하기 전에 불완전한 가지를'
        ' 다시 검사하십시오. 모두 선택이 비활성화됩니다.'
    ),
    'problem_hidden_omitted': '숨겨진 항목은 생략되었습니다. 그들의 크기는 알려져 있지 않습니다.',
    'problem_partial_folder': '일부 항목을 읽을 수 없습니다. 이 폴더는 불완전합니다.',
    'app_title': 'FileTree',
    'about_text': (
        '<h3>FileTree {version}</h3><p>디스크 공간이 어디로 가는지 확인하세요.</p><p>MIT 라이센스 · © 2026 JE'
        '-Chen</p>'
    ),
    'menu_file': '파일(&F)',
    'menu_export': '내보내기(&E)',
    'menu_view': '보기(&V)',
    'menu_unit': '크기 단위(&U)',
    'menu_language': '언어(&L)',
    'menu_help': '도움말(&H)',
    'action_open': '폴더 선택…',
    'action_open_tip': '스캔할 폴더나 드라이브를 선택하세요.',
    'action_rescan': '다시 스캔',
    'action_rescan_tip': '변경 사항을 적용하려면 동일한 폴더를 다시 스캔하세요.',
    'action_stop': '중지',
    'action_stop_tip': '실행 중인 검사를 중지합니다.',
    'action_export_folders': '폴더 목록(CSV)…',
    'action_export_folders_tip': 'Excel 또는 기타 스프레드시트용으로 모든 폴더를 크기와 함께 저장하세요.',
    'action_export_largest': '가장 큰 파일(CSV)…',
    'action_export_largest_tip': '가장 큰 파일 목록 저장',
    'action_export_json': '폴더 트리(JSON)…',
    'action_export_json_tip': '스크립트 및 기타 프로그램을 위한 폴더 트리 저장',
    'action_trash': '휴지통으로 이동',
    'action_trash_tip': '선택한 파일 및 폴더를 휴지통으로 이동합니다(먼저 묻는 메시지가 표시됨).',
    'action_find': '찾기…',
    'action_find_tip': '스캔 내 어디에서나 이름으로 파일 및 폴더 찾기',
    'action_quit': '종료',
    'action_quit_tip': 'FileTree 닫기',
    'action_hidden': '숨겨진 파일 포함',
    'action_exclusions': '스캔할 때 건너뛰기…',
    'action_exclusions_tip': 'node_modules와 같이 검사하는 폴더 및 폴더 이름은 생략합니다.',
    'exclusions_title': '스캔하는 동안 건너뛰기',
    'exclusions_hint': (
        '스캔 시 이러한 폴더는 제외됩니다. 해당 폴더는 회색으로 표시되며 크기는 0입니다. node_modules 또는 *.'
        'cache와 같은 이름은 해당 이름의 모든 폴더를 건너뜁니다. 폴더 경로는 해당 폴더 하나를 건너뜁니다. 목'
        '록은 다음 스캔부터 적용됩니다.'
    ),
    'exclusions_add_name': '이름을 추가하세요…',
    'exclusions_add_folder': '폴더 추가…',
    'exclusions_remove': '제거',
    'exclusions_name_prompt': '폴더 이름, * 및 ? 허용됨:',
    'exclusions_saved': '{count} 제외 항목이 저장되었습니다. 다음 스캔부터 적용됩니다.',
    'tooltip_excluded': '{path}\n건너뛰기: 보기 → 스캔 중 건너뛰기 상태입니다.',
    'action_hidden_tip': '숨겨진 파일 및 폴더 수 계산(다음 검사에 적용)',
    'action_help': '사용 방법',
    'action_help_tip': 'FileTree에 대한 간략한 가이드',
    'action_about': 'FileTree 정보',
    'action_about_tip': '버전 및 라이센스',
    'app_title_admin': 'FileTree(관리자)',
    'action_elevate': '관리자로 다시 시작',
    'action_elevate_tip': '관리자 권한으로 FileTree를 다시 시작하면 모든 폴더를 읽을 수 있습니다.',
    'action_ask_admin': '시작 시 관리자 권한 요청',
    'action_ask_admin_tip': 'Windows은 FileTree이 시작될 때 권한을 요청하므로 보호된 폴더도 읽을 수 있습니다.',
    'problems_hint': (
        '일부 폴더에는 관리자 권한이 필요합니다. 해당 내용을 읽으려면 FileTree를 관리자로 다시 시작하세요.'
    ),
    'elevate_declined': 'FileTree가 여전히 관리자 권한 없이 실행 중입니다.',
    "startup_invalid": "요청한 작업 공간을 복원하지 못했습니다: {reason}",
    "elevate_waiting": "Windows 권한 요청을 승인하거나 닫으세요. 이 창을 닫아도 요청이 끝날 때까지 기다립니다.",
    "elevate_failed": "관리자로 FileTree를 다시 시작하지 못했습니다: {reason}",
    'unit_auto': '자동',
    'path_placeholder': '폴더 경로를 입력하거나 붙여넣고 Enter를 누르세요.',
    'choose_folder_title': '스캔할 폴더를 선택하세요',
    'welcome_title': '디스크 공간이 어디로 가는지 확인하세요',
    'welcome_subtitle': (
        '폴더 또는 전체 드라이브를 선택하십시오. FileTree은 그 안에 있는 모든 파일을 합산하고 가장 큰 폴더와 '
        '파일을 먼저 표시합니다.'
    ),
    'welcome_choose': '폴더를 선택하세요…',
    'welcome_drives': '드라이브',
    'welcome_drive_tip': '{path} 스캔',
    'welcome_drive_free': '전체 {total}, 여유 공간 {free}',
    'welcome_drive_used': '사용률 {percent}',
    'welcome_recent': '최근에 스캔됨',
    'welcome_tip': (
        '팁: 파일 관리자에서 폴더를 이 창으로 끌어서 놓을 수도 있습니다. Windows(\\\\server\\share)에 절대 UN'
        'C 공유 경로를 붙여넣습니다. 액세스는 현재 계정을 사용합니다. 스캔 작업자는 옵션에서 조정할 수 있습니'
        '다. 거부되거나 연결이 끊긴 분기는 비어 있지 않고 불완전한 상태로 유지됩니다.'
    ),
    'scan_starting': '시작 중…',
    'scan_progress': '검색 중… {files} 파일 {folders} 폴더 · {size} · {time}',
    'scan_stop': '중지',
    'scan_stopping': '중지 중…',
    'scan_cancelled': '스캔이 중지되었습니다.',
    'scan_stopped_partial': '스캔 중지됨: 결과에는 지금까지 읽은 내용이 표시됩니다.',
    'scan_failed_title': '스캔할 수 없습니다',
    'scan_mount_changed': '마운트 경계가 변경되었거나 확인할 수 없습니다. 이 결과를 사용하기 전에 다시 스캔하세요.',
    'scan_failed': 'FileTree는 {path}을(를) 읽을 수 없습니다.\n\n이유: {reason}',
    'not_a_folder': '{path}은(는) 존재하는 폴더가 아닙니다.',
    'duration_seconds': '{value}초',
    'duration_minutes': '{minutes} 분 {seconds} 초',
    'summary': '<b>{path}</b> — {files} 파일 및 {folders} 폴더의 {size}(디스크의 {allocated})({time}에서 스캔됨)',
    'summary_live': '<b>{path}</b> — 지금까지 {files} 파일 및 {folders} 폴더의 {size}(디스크의 {allocated})',
    'summary_partial': (
        '<b>{path}</b> — {files} 파일 및 {folders} 폴더의 {size}(디스크의 {allocated}) · <b>불완전</b>: {time'
        '} 이후 검사가 중지되었습니다.'
    ),
    'tab_chart': '차트',
    'chart_treemap': '트리맵',
    'treemap_levels': '레벨',
    'treemap_levels_all': '모두',
    'treemap_colours': '색상',
    'treemap_colours_type': '파일 유형별',
    'treemap_colours_folder': '폴더별',
    'chart_treemap_tip': '모든 파일은 차지하는 공간에 따라 크기가 결정되는 직사각형입니다.',
    'chart_bars': '막대 그래프',
    'chart_sunburst': '선버스트',
    'chart_tree': '트리',
    'chart_tree_tip': '폴더 계층 구조: 분기 확장, 확대/축소하려면 Ctrl+휠, 초점을 맞추려면 두 번 클릭',
    'tree_orientation': '방향',
    'tree_orientation_horizontal': '왼쪽에서 오른쪽으로',
    'tree_orientation_vertical': '위에서 아래로',
    'tree_more': '{count} 추가 폴더 · {size}',
    'tree_unavailable': '스캔되지 않음',
    'chart_sunburst_tip': (
        '중앙에 있는 폴더는 더 깊은 레벨마다 링으로 구성되어 있습니다. 중앙을 클릭하면 위로 올라갑니다'
    ),
    'chart_bars_tip': '폴더 항목당 하나의 막대(크기 및 공유 포함)(가장 큰 것부터)',
    'bars_empty_folder': '이 폴더는 비어 있습니다.',
    'bars_more': '{count} 더보기: {size}',
    'tab_largest': '가장 큰 파일',
    'scope_folder': '선택한 폴더만',
    'scope_folder_named': '{name}에서만',
    'scope_folder_tip': '전체 스캔 대신 트리에서 선택한 폴더의 가장 큰 파일, 유형 및 기간을 표시합니다.',
    'tab_search': '검색',
    'tab_changes': '변경 사항',
    'action_compare': '저장된 스캔과 비교…',
    'action_compare_tip': '내보내기 → 폴더 트리(JSON)로 저장된 스캔을 열고 이후 성장한 내용을 확인하세요.',
    'compare_title': '저장된 스캔과 비교',
    'compare_failed': '이 파일은 FileTree:\n{reason}에 의해 저장된 스캔이 아닙니다.',
    'column_before': '이전',
    'column_now': '지금',
    'column_change': '변경',
    'changes_new': '새로운',
    'changes_gone': '사라졌다',
    'changes_whole_scan': '(스캔한 폴더)',
    'changes_stop': '비교 끝내기',
    'changes_running': '비교 중…',
    'changes_waiting': '스캔이 완료되면 비교가 이루어집니다.',
    'changes_unknown_time': '알 수 없는 시간에',
    'changes_summary': (
        '{path}과 비교하여 {when}을 저장했습니다: {before}, 현재 {now}({change}); {count} 폴더가 변경되었습니'
        '다.'
    ),
    'tab_duplicates': '중복 파일',
    'tab_cleanup': '정리',
    'cleanup_suggestions': '제안',
    'cleanup_select_all': '모두 선택',
    'cleanup_select_group': '이 그룹 선택',
    'cleanup_running': '청소할 물건을 찾고 있습니다…',
    'cleanup_hint': '스캔 후 콘텐츠가 일반적으로 갈 수 있는 장소가 여기에 나타납니다.',
    'cleanup_none': '이 스캔에는 제안할 내용이 없습니다.',
    'cleanup_summary': (
        '{size} {groups} 그룹의 논리적 크기. 휴지통으로 이동하기 전에 경로 및 할당을 검토할 항목을 선택하십시'
        '오. 이동해도 즉시 공간이 확보되지는 않습니다.'
    ),
    'cleanup_group': '{title} — {size} ({count})',
    'cleanup_temp': '임시 파일',
    'cleanup_temp_tip': '한동안 남겨진 파일 프로그램; 아직 실행 중인 프로그램에는 일부가 필요할 수 있습니다.',
    'cleanup_browser_cache': '브라우저 캐시',
    'cleanup_browser_cache_tip': '웹페이지 및 사진 사본 브라우저는 필요에 따라 다시 다운로드합니다.',
    'cleanup_thumbnails': '썸네일 캐시',
    'cleanup_thumbnails_tip': '사진의 작은 미리보기; 폴더를 열 때 다시 만들어집니다.',
    'cleanup_crash_dumps': '크래시 덤프',
    'cleanup_crash_dumps_tip': '프로그램이 충돌할 때 저장된 메모리는 충돌을 보고하는 데에만 유용합니다.',
    'cleanup_package_caches': '패키지 다운로드 캐시(pip, npm…)',
    'cleanup_package_caches_tip': '다운로드한 패키지는 다음 설치를 위해 보관됩니다. 필요할 때 다시 다운로드됩니다.',
    'cleanup_build_output': '빌드 출력(재구축 가능)',
    'cleanup_build_output_tip': '설치된 종속성 및 프로젝트의 컴파일된 파일 프로젝트를 다시 빌드하면 다시 생성됩니다.',
    'cleanup_old_installers': '다운로드의 설치 프로그램',
    'cleanup_old_installers_tip': '오래 전에 실행되었을 가능성이 가장 높은 설정 파일. 다시 설치한 것을 유지하세요.',
    'cleanup_empty_folders': '빈 폴더',
    'cleanup_empty_folders_tip': '아무것도 없는 폴더 또는 다른 빈 폴더만 있습니다.',
    'duplicates_min_size': '비교할 최소 크기',
    'duplicates_any_size': '모든 크기',
    'duplicates_find': '중복 파일 찾기',
    'duplicates_stop': '중지',
    'duplicates_select_extra': '여분의 사본 선택',
    'duplicates_select_extra_tip': (
        '선택한 유지할 파일와 성공적인 확인을 통해 그룹에서 추가 항목을 선택합니다. 그런 다음 삭제를 누르세요'
    ),
    'duplicates_hint': (
        '스캔의 어느 위치에서나 동일한 내용이 포함된 파일을 찾습니다. 같은 크기의 파일만 읽어오는데 읽는 데 '
        '시간이 걸리기 때문에 더 작은 크기를 선택하지 않으면 작은 파일은 제외됩니다.'
    ),
    'duplicates_starting': '같은 크기의 파일을 찾는 중…',
    'duplicates_running': '{total} 파일 중 {files}({bytes} 중 {read}) 읽기…',
    'duplicates_stopped': '검색이 중지되었습니다.',
    'duplicates_none': '중복 파일을 찾지 못했습니다.',
    'duplicates_summary': '{groups} 중복 그룹: {extra} 추가 복사본의 논리적 크기.',
    'duplicates_limited': '추가 공간이 가장 많은 {shown} 그룹이 나열됩니다.',
    'duplicates_skipped': '파일 {count}개를 읽을 수 없습니다.',
    'duplicates_group': '{count} 복사본 × {size}: {extra} 논리적 추가 복사본 크기.',
    'search_placeholder': '이름 또는 패턴의 일부: 백업, *.mp4, *.iso;*.zip',
    'search_hint': (
        '* 및 ?를 사용하여 이름이나 패턴의 일부를 입력하고 조건을 선택하거나 둘 다를 선택하여 스캔의 어느 위'
        '치에서나 파일과 폴더를 찾습니다.'
    ),
    'search_running': '검색 중…',
    'search_larger': '최소 크기(포함)',
    'search_smaller': '최대 크기(포함)',
    'search_custom_ranges': '범위 지정…',
    'search_changed_custom': '날짜 지정',
    'search_exact_bytes': '{value} B(정확)',
    'search_date_format': 'YYYY-MM-DD',
    'search_date_start': '시작 날짜(포함)',
    'search_date_through': '종료 날짜(포함)',
    'search_range_hint': ('비워 두면 제한이 없습니다. 크기는 정확한 바이트 '
        '수이며 날짜는 현지 시간(YYYY-MM-DD)입니다.'),
    'search_range_size_error': ('0 이상 9223372036854775807 B 이하의 정수 '
        '바이트를 입력하세요. 1바이트 미만의 소수는 허용되지 않습니다.'),
    'search_range_order_error': '최소 크기는 최대 크기를 초과할 수 없습니다.',
    'search_range_date_error': ('유효한 현지 날짜를 YYYY-MM-DD 형식으로 입'
        '력하고 시작 날짜를 종료 날짜 이전으로 지정하세요.'),
    'search_range_invalid': ('검색 범위가 잘못되었습니다. 검색하거나 저장'
        '하기 전에 크기 또는 날짜 범위를 수정하세요.'),
    'search_no_limit': '제한 없음',
    'search_changed': '변경됨',
    'search_changed_any': '언제든지',
    'search_changed_week': '지난주에',
    'search_changed_month': '지난달에',
    'search_changed_year': '작년에',
    'search_changed_stale_year': '1년이 아니라',
    'search_changed_stale_2y': '아니 2년동안',
    'search_changed_stale_5y': '아니 5년동안',
    'search_type': '유형',
    'search_type_any': '모든 유형',
    'search_show': '쇼',
    'search_kind_any': '파일 및 폴더',
    'search_kind_files': '파일만',
    'search_kind_folders': '폴더만',
    'search_saved': '저장된 검색',
    'search_saved_none': '(없음)',
    'search_save': '저장…',
    'search_delete': '삭제',
    'search_save_title': '이 검색 저장',
    'search_save_prompt': '이름:',
    'search_none': '일치하는 항목이 없습니다.',
    'problems_none': '이번 스캔의 모든 항목을 읽었습니다. 확인할 문제가 없습니다.',
    'largest_none': '표시할 파일이 없습니다.',
    'search_summary': '{count}개 일치, 총 {size}개.',
    'search_limited': '가장 큰 {shown}이 나열됩니다.',
    'tab_types': '파일 형식',
    'tab_age': '경과 기간',
    'column_age': '마지막 변경',
    'age_month': '한 달 이내',
    'age_half_year': '1~6개월 전',
    'age_year': '6~12개월 전',
    'age_two_years': '1~2년 전',
    'age_older': '2년 이상 전',
    'largest_focus': '표시 항목: {what}',
    'largest_show_all': '모두 표시',
    'list_files_tip': '가장 큰 파일을 나열하려면 행을 두 번 클릭하세요.',
    'tab_problems': '문제',
    'tab_problems_count': '문제({count})',
    'column_name': '이름',
    'column_size': '크기',
    'column_allocated': '디스크 사용량',
    'column_share': '상위 %',
    'column_share_total': '전체의 %',
    'column_files': '파일',
    'column_folders': '폴더',
    'column_modified': '수정한 날짜',
    'column_folder': '폴더',
    'column_extension': '확장자',
    'column_type': '유형',
    'column_path': '경로',
    'column_problem': '문제',
    'problem_access_denied': '액세스가 거부되었습니다.',
    'problem_not_found': '더 이상 거기엔 없어',
    'problem_path_too_long': '경로가 너무 깁니다.',
    'problem_not_scanned': '검사되지 않음: 검사가 먼저 중지되었습니다.',
    'no_extension': '(확장자 없음)',
    'tooltip_unreadable': '{path}\n읽을 수 없습니다: {reason}',
    'tooltip_link': '{path}\n링크: 표시되었지만 팔로우되지 않음',
    'tooltip_not_scanned': '{path}\n스캔되지 않음: 스캔이 먼저 중지되었습니다.',
    'treemap_empty': '표시할 내용 없음',
    'treemap_up': '↑ 위로',
    'treemap_up_tip': '위 폴더를 보여주세요',
    'treemap_tooltip': '<b>{name}</b><br>{size} (이 보기의 {share})<br>{path}',
    'treemap_more': '{count} 더 보기',
    'treemap_more_tooltip': (
        '<b>{count} 더 작은 항목</b> of {name}, 각각 너무 작아서 그릴 수 없음<br>{size}(이 보기의 {share})'
    ),
    'treemap_more_open': '이 폴더를 자체적으로 표시하려면 두 번 클릭하세요.',
    'largest_filter': '이름이나 폴더로 필터링…',
    'types_all': '모든 유형',
    'category_images': '사진',
    'category_video': '동영상',
    'category_audio': '음악 및 오디오',
    'category_documents': '문서',
    'category_archives': '아카이브 및 디스크 이미지',
    'category_code': '코드와 데이터',
    'category_programs': '프로그램',
    'category_other': '기타',
    'status_selected': '{name}: {size}(해당 폴더의 {share})',
    'status_selected_root': '{name}: {size}',
    'menu_open_item': '열기',
    'menu_reveal': '파일 관리자에서 보기',
    'menu_copy_path': '경로 복사',
    'menu_show_chart': '차트에서 보기',
    'menu_scan_here': '이 폴더만 스캔',
    'menu_rescan_here': '이 폴더 다시 스캔',
    'rescan_done': '다시 스캔됨 {name}: {before} → {after}',
    'refresh_notice': '이 스캔 이후 스캔한 폴더 {count}개의 내용이 변경되어 그곳에 표시된 크기가 '
                      '최신이 아닐 수 있습니다. FileTree는 요청하지 않는 한 다시 스캔하지 않습니다.',
    'refresh_now': '변경된 폴더 다시 스캔',
    'refresh_now_tip': '변경된 폴더만 다시 읽어 결과를 업데이트합니다',
    'trash_confirm_title': '휴지통으로 이동',
    'protected_title': '시스템 또는 프로그램 폴더',
    'protected_question': (
        '항목 중 {count}은 시스템 또는 프로그램 폴더입니다. 이동하면 시스템이나 프로그램의 작동이 중지될 수 '
        '있습니다.\n\n{names}\n\n그래도 이동하시겠습니까?'
    ),
    'protected_system': '운영 체제의 일부',
    'protected_programs': '설치된 프로그램',
    'protected_settings': '프로그램 설정 및 데이터',
    'protected_profile': '사용자의 프로필 폴더',
    'trash_confirm': '“{name}”({size})을 휴지통으로 이동하시겠습니까?\n\n휴지통에서 복원할 수 있습니다.',
    'trash_failed': '"{name}"을(를) 휴지통으로 이동할 수 없습니다. 사용 중이거나 읽기 전용일 수 있습니다.',
    'trash_done': '“{name}”을 휴지통으로 이동했습니다: {size}이 해제되었습니다.',
    'action_trash_many': '항목 {count}개를 휴지통으로 이동',
    'trash_confirm_many': (
        '이 {count} 항목(총 {size})을 휴지통으로 이동하시겠습니까?\n\n{names}\n\n여기에서 복원할 수 있습니다.'
    ),
    'trash_more': '...그리고 {count} 더보기',
    'trash_failed_many': (
        '{count} 항목을 휴지통으로 이동할 수 없습니다. 사용 중이거나 읽기 전용일 수 있습니다. \n\n{names}'
    ),
    'trash_done_many': '{count} 항목을 휴지통으로 이동했습니다: {size}이 해제되었습니다.',
    'permanent_delete': '영구 삭제',
    'permanent_delete_tip': (
        '선택한 파일과 폴더를 휴지통을 거치지 않고 영구 삭제합니다'
        '(먼저 확인하며 되돌릴 수 없습니다)'
    ),
    'permanent_menu_many': '항목 {count}개 영구 삭제',
    'permanent_not_suggestions': (
        '영구 삭제는 폴더 트리, 가장 큰 파일, 검색 결과에서 고른 항목에만 사용할 수 있으며 '
        '정리나 중복 제안에는 사용할 수 없습니다.'
    ),
    'permanent_title': '영구 삭제',
    'permanent_confirm': (
        '“{name}”({size})을(를) 영구 삭제하시겠습니까?\n\n{path}\n\n'
        '휴지통으로 이동하지 않으며 되돌릴 수 없습니다.'
    ),
    'permanent_confirm_many': (
        '이 항목 {count}개(총 {size})를 영구 삭제하시겠습니까?\n\n{names}\n\n'
        '휴지통으로 이동하지 않으며 되돌릴 수 없습니다.'
    ),
    'permanent_confirm_folders': (
        '폴더는 스캔할 때 기록된 내용과 함께 삭제됩니다. '
        '스캔 후 추가되거나 바뀐 항목은 그대로 남습니다.'
    ),
    'permanent_protected_question': (
        '항목 중 {count}개는 시스템 또는 프로그램 폴더입니다. 영구 삭제하면 시스템이나 프로그램이 '
        '작동하지 않을 수 있습니다.\n\n{names}\n\n그래도 삭제하시겠습니까?'
    ),
    'permanent_managed': (
        '이 항목은 Windows가 관리하므로 FileTree가 삭제하지 않습니다. '
        '대신 세부 정보에 표시된 시스템 도구를 사용하세요.\n\n{names}'
    ),
    'permanent_running': '영구 삭제 중… 항목 {count}개를 삭제했습니다. 중지하려면 Esc를 누르세요.',
    'permanent_done': (
        '항목 {removed}개({size})를 영구 삭제했습니다. '
        '남긴 항목: {refused}, 실패: {failed}.'
    ),
    'permanent_report_title': '영구 삭제: 남긴 항목',
    'permanent_failed': '시스템이 삭제하지 않았습니다: {reason}',
    'permanent_pending': '삭제 대기 중: 다른 프로그램이 아직 열어 두고 있습니다',
    'permanent_journal_reason': '명시적 영구 삭제',
    'permanent_journal_deleted': '영구 삭제됨',
    'permanent_journal_partial': '일부 삭제됨(폴더 유지)',
    'permanent_skip_outside': '현재 스캔 범위 밖이므로 삭제하지 않음',
    'permanent_skip_unverified': '확인된 스캔 식별 정보가 없어 삭제하지 않음',
    'permanent_skip_incomplete': '스캔에서 이 폴더 전체를 읽지 못해 들어가지 않음',
    'permanent_skip_missing': '항목 또는 해당 폴더가 없음',
    'permanent_skip_unreadable': '항목을 읽을 수 없어 삭제하지 않음',
    'permanent_skip_link': '항목 또는 상위 폴더가 링크로 바뀌어 삭제하지 않음',
    'permanent_skip_kind': '항목 종류가 바뀌어 삭제하지 않음',
    'permanent_skip_identity': '스캔 후 항목이 교체되어 삭제하지 않음',
    'permanent_skip_changed': '스캔 후 크기나 시간이 바뀌어 삭제하지 않음',
    'permanent_skip_protected': '승인 범위에 없는 시스템 또는 프로그램 폴더이므로 삭제하지 않음',
    'permanent_skip_system_managed': 'Windows가 관리하는 항목이므로 삭제하지 않음',
    'permanent_skip_cancelled': '이 항목 전에 중지되어 삭제하지 않음',
    'permanent_skip_journal': '승인한 작업을 기록할 수 없어 아무것도 삭제하지 않음',
    'permanent_skip_read_only': '읽기 전용입니다. FileTree는 속성을 해제하지 않으므로 삭제하지 않음',
    'permanent_skip_mount_point': '마운트된 볼륨 또는 마운트 지점이므로 삭제하지 않음',
    'permanent_skip_other_volume': '다른 볼륨에 있어 삭제하지 않음',
    'permanent_skip_arrived': '스캔 후 추가되어 그대로 둠',
    'permanent_skip_not_empty': '안에 남은 항목이 있어 폴더를 유지함',
    'permanent_skip_failed': '안의 항목 삭제를 시스템이 거부함',
    'status_selected_many': '{count} 선택한 항목: {size}',
    'export_title': '수출',
    'export_running': '{path}에 저장 중…',
    'csv_filter': 'CSV 파일(*.csv)',
    'json_filter': 'JSON 파일(*.json)',
    'export_done': '{count} 행을 {path}에 저장했습니다.',
    'export_failed': '파일을 저장할 수 없습니다.\n\n이유: {reason}',
    'help_title': 'FileTree 사용 방법',
    'help_html': HELP,
    "budget_close": "닫기",
    "action_folder_budgets": "폴더 용량 예산…", "action_folder_budgets_tip": "폴더 한도와 마지막 스캔 사용량 관리",
    "budget_title": "폴더 용량 예산", "budget_name": "이름", "budget_path": "폴더 경로",
    "budget_limit": "한도", "budget_usage": "최근 사용량", "budget_excess": "초과량",
    "budget_status": "상태", "budget_add": "추가", "budget_update": "업데이트", "budget_delete": "삭제",
    "budget_new": "새 규칙", "budget_waiting": "전체 스캔 대기", "budget_unknown": "알 수 없음",
    "budget_over": "한도 초과", "budget_within": "한도 이내", "budget_alerted": "{status}, 알림 기록됨",
    "budget_dated_usage": "{when}: {usage}", "budget_invalid_limit": "정확한 바이트 한도를 입력하세요",
    "budget_summary": "예산: 초과 {over}개, 알 수 없음 {unknown}개",
    "budget_save_error": "폴더 예산을 저장할 수 없습니다: {reason}",
    "budget_unknown_reason": "알 수 없음: {reason}", "budget_reason_missing": "스캔에서 폴더를 찾을 수 없음",
    "budget_reason_linked": "링크된 폴더", "budget_reason_not_folder": "폴더가 아님",
    "budget_reason_incomplete": "검사 범위가 불완전함",
    "budget_invalid_input": "유효한 이름, 절대 경로와 정확한 한도를 입력하세요",
    "budget_invalid_data": "저장된 예산 데이터가 올바르지 않습니다",
    "budget_duplicate_path": "이 경로에는 이미 예산이 있습니다",
    "budget_missing_rule": "이 예산은 더 이상 없습니다", "budget_too_many": "예산이 너무 많습니다",
    "budget_settings_locked": "예산 설정이 사용 중입니다",
    "budget_storage_unavailable": "예산 저장소를 사용할 수 없습니다",
    "budget_read_failed": "예산 설정을 읽을 수 없습니다", "budget_write_failed": "예산 설정을 저장할 수 없습니다",
    "budget_observed": "관측 시간",
    "budget_not_scanned": "아직 스캔하지 않음",
    "budget_changed_limit": "한도 변경됨, 전체 스캔 대기 중",
    "budget_input_unit": "한도 단위(이진)",
    "budget_choose": "폴더 선택…",
    "budget_empty": "폴더 예산이 없습니다. 폴더를 선택하고 이름과 한도를 입력한 다음 추가하세요.",
    "budget_edit_hint": (
        '한도는 정확한 이진 단위를 사용합니다. 추가나 편집은 스캔을 시작하지 않습니다. 사용량은 마지막 관'
        '측값이며 실시간 값이 아닙니다. 한도 변경 후 새 전체 스캔이 필요합니다.'
    ),
    "budget_keep_draft": "저장하지 않은 입력을 유지했습니다. 저장하거나 새 규칙을 선택한 후 다른 대상을 선택하세요.",
    "budget_editing": "선택한 예산 편집 중",
    "budget_creating": "새 예산",
    "budget_exact": "정확한 크기: {value}",
    "budget_invalid_name": "예산 이름을 입력하세요",
    'search_edit_conditions': '조건 편집',
    'date_accept': '확인', 'date_cancel': '취소', 'date_choose': '날짜 선택…',
    'date_clear': '날짜 지우기',
    'search_fix_field': '표시된 입력을 수정한 후 범위를 적용하세요.',
    'search_size_unit': '크기 단위(이진)',
    'search_condition_name': '이름: {value}',
    'search_condition_value': '{label}: {value}',
    'search_condition_dates': '날짜(양 끝 포함): {start}부터 {through}까지',
    'search_scope_none': '검색 범위: 완료된 스캔 없음',
    'search_scope_root': '전체 스캔: {path}',
    'search_scope_multi': '전체 스캔: 결합된 모든 원본',
    'search_scope': '검색 범위',
    'search_clear_all': '모든 조건 지우기',
    'search_no_conditions': '전체 스캔을 검색하려면 이름이나 조건을 입력하세요。',
    'search_clear_condition': '지우기',
    'search_remove_condition': '조건 지우기: {condition}',
    "action_settings": "설정…",
    "action_settings_tip": "검색할 수 있는 한 창에서 모든 설정을 바꾸고 내보내거나 가져옵니다",
    "settings_title": "설정",
    "settings_search": "설정 검색",
    "settings_none": "일치하는 설정이 없습니다.",
    "settings_appearance": "모양",
    "settings_scanning": "스캔",
    "settings_recording": "스캔할 때 기록할 정보",
    "settings_following": "따라가기와 감시",
    "settings_cleaning": "정리와 기록",
    "settings_system": "Windows",
    "settings_export": "설정 내보내기…",
    "settings_import": "설정 가져오기…",
    "settings_file_tip": (
        "모양, 스캔 선택, 건너뛸 폴더가 포함됩니다. 최근 폴더, 자주 쓰는 스캔 설정, 용량"
        " 예산, 백그라운드 스캔, 정리 정책은 포함되지 않습니다."
    ),
    "settings_invalid": "사용할 수 있는 FileTree 설정 파일이 아닙니다. 아무 설정도 바꾸지 않았습니다.",
    "settings_same": "이미 이 설정을 사용하고 있습니다.",
    "settings_confirm": "설정 {count}개를 이 파일의 값으로 바꾸시겠습니까?",
    "treemap_colours_change": "변화별",
    "change_colour_new": "새로 생김",
    "change_colour_grew_lot": "25% 넘게 커짐",
    "change_colour_grew": "커짐",
    "change_colour_same": "변화 없음",
    "change_colour_shrank": "작아짐",
    "change_colour_shrank_lot": "25% 넘게 작아짐",
    "change_colour_none": "저장된 스캔과 비교하면 변화가 색으로 표시됩니다",
    "change_colour_tip": (
        "폴더는 저장된 스캔 이후의 변화로 색을 정합니다. 저장된 스캔은 폴더만 기록하므로"
        " 파일은 들어 있는 폴더의 색을 따릅니다"
    ),
    "cleanup_custom": "내 규칙: {name}",
    "cleanup_custom_tip": "직접 만든 규칙과 일치합니다. 내용이 아직 필요한지는 FileTree가 알 수 없습니다.",
    "cleanup_category_custom": "내 규칙",
    "cleanup_rebuild_custom": "알 수 없음. 옮기기 전에 하나씩 확인하세요.",
    "custom_rules_button": "내 규칙({count})…",
    "custom_rules_title": "내 정리 규칙",
    "custom_rules_hint": (
        "이 규칙으로 찾은 항목은 항상 검토 목록에만 표시하며, 미리 선택하거나 백그라운드"
        " 스캔에서 제안하지 않습니다. 시스템, 프로그램, 프로필 폴더는 제외합니다."
    ),
    "custom_rules_add": "추가",
    "custom_rules_update": "업데이트",
    "custom_rules_remove": "제거",
    "custom_rules_name": "이름",
    "custom_rules_name_tip": "그룹 제목으로 표시됩니다",
    "custom_rules_folders": "폴더",
    "custom_rules_folders_tip": "Cache 또는 MyApp/logs처럼 경로의 끝부분. 여러 개는 ;로 구분합니다",
    "custom_rules_files": "파일",
    "custom_rules_files_tip": "*.bak 같은 이름. 여러 개는 ;로 구분합니다",
    "custom_rules_in_folder": "이 폴더에서만",
    "custom_rules_in_folder_tip": (
        "이 이름의 폴더 바로 안에 있는 파일만 대상으로 합니다. 비워 두면 모든 폴"
        "더가 대상입니다"
    ),
    "custom_rules_days": "변경 없는 일수",
    "custom_rules_days_tip": "더 최근 항목은 제외합니다",
    "custom_rules_invalid": (
        "이 규칙은 사용할 수 없습니다. 겹치지 않는 이름과 충분히 구체적인 패턴을 하나"
        " 이상 지정하세요(글자나 숫자 3개 이상, 드라이브나 백슬래시 불가, 폴더는 일반"
        " 이름으로 끝나야 함)."
    ),
    "action_problem_files": "문제 파일 확인…",
    "action_problem_files_tip": (
        "빈 파일, 끊어진 링크와 바로 가기, 너무 긴 경로, Windows에서 쓸 수 없는 이"
        "름을 찾습니다"
    ),
    "problem_files_found": "발견한 문제",
    "problem_files_target": "가리키는 곳",
    "problem_files_all": "모든 문제",
    "problem_files_empty": "빈 파일",
    "problem_files_dead_link": "끊어진 링크",
    "problem_files_long_path": "너무 긴 경로",
    "problem_files_bad_name": "쓸 수 없는 이름",
    "problem_files_hint": (
        "화면의 스캔을 확인합니다. 디스크에서 읽는 것은 링크와 로컬의 작은 바로 가기뿐이"
        "며 따라가지 않습니다. 대상이 네트워크나 연결되지 않은 드라이브에 있으면 알 수 "
        "없음으로 남습니다. 여기서는 아무것도 바꾸지 않으며, 두 번 클릭하면 트리에서 항"
        "목을 선택합니다."
    ),
    "problem_files_reading": "확인 중…",
    "problem_files_summary": (
        "항목 {shown}개를 표시하며 문제는 {count}개입니다. 판단할 수 없는 링크: {unknown}."
        " 종류마다 처음 1,000개를 표시합니다."
    ),
}
