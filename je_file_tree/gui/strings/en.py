"""Every text the window shows in English; see ``je_file_tree.gui.i18n``."""

from __future__ import annotations

from je_file_tree.gui.strings.help_en import HELP

EN: dict[str, str] = {
    "busy_scanning": ("“{action}” has to wait for the scan that is running. "
        "Let it finish, or stop it first (Esc)."),
    "busy_operation": ("“{action}” has to wait: another operation on the scanned files is still running. "
        "Try again once it has finished."),
    "budget_filter": "Show budgets",
    "budget_filter_all": "All budgets",
    "budget_filter_over": "Over limit",
    "budget_filter_unknown": "Unknown or not scanned",
    "budget_filter_empty": "No budgets match this filter. Choose All budgets to see every rule.",
    "budget_editing_hidden": "Editing {name}, hidden by this filter. Status: {status}. Your draft is retained.",
    "budget_count_over": "{count} over limit",
    "budget_count_unknown": "{count} unknown",
    "folder_context_target": "Target folder",
    "folder_context_ready": "For a selected file, these actions use its containing folder.",
    "folder_context_history": "View growth trend",
    "folder_context_budget": "Set folder budget",
    "folder_context_empty": "Complete a scan to use folder actions.",
    "folder_context_busy": "Wait for scanning or the current operation to finish.",
    "folder_context_closing": "This scan tab is closing.",
    "folder_context_virtual": "Open an individual source scan to use folder actions.",
    "folder_context_stale": "Select a folder in the current scan.",
    "folder_context_link": "Folder actions are unavailable for links.",
    "trend_choose_folder": "Choose loaded folder…",
    "trend_loaded_folders": "Loaded child folders",
    "trend_full_path": "Full folder path",
    "trend_root": "Return to root",
    "trend_up": "Up",
    "trend_enter": "Open folder",
    "trend_previous": "Previous page",
    "trend_next": "Next page",
    "trend_choose_current": "Use this folder",
    "trend_folder_page": "Folders {first}–{last} of {total}. Only loaded folders are listed.",
    "trend_period": "Period",
    "trend_period_all": "All retained history",
    "trend_period_30": "Last 30 days",
    "trend_period_90": "Last 90 days",
    "trend_period_custom": "Custom dates",
    "trend_date_order": "End date must be on or after start date.",
    "trend_point_details": "Selected observation details",
    "trend_select_point": "Select an observation in the chart or table. Arrow keys visit each observation.",
    "trend_size_reason": "Size unknown: {reason}",
    "trend_change_reason": "Change unknown: {reason}",
    "trend_first_point": "No previous observation in this period",
    "trend_point_value": "{date} · Size {size} ({exact_size}) · Change {change} ({exact_change})",
    "templates_select": "Select a saved template",
    "templates_remove": "Delete template",
    "templates_save_section": "Save opening workspace",
    "templates_save_source": (
        'Add and Update save the tabs and optio'
        'ns captured when this dialog opened. P'
        'review edits below are not saved.'),
    "templates_add_current": "Add opening tabs",
    "templates_update_current": "Update from opening tabs",
    "templates_preview_hint": (
        'Load preview · Edit paths for this loa'
        'd only, then check them. Loaded tabs w'
        'ait for Start.'),
    "templates_preview_modified": (
        'Modified for this load only · Check pa'
        'ths again before replacing tabs.'),
    "templates_active": "Active",
    "templates_scanning": "Scanning",
    "templates_impact": (
        'Replace will close {tabs} tabs, stop {'
        'scans} scans and close {results} resul'
        'ts. Unavailable preview paths: {unavai'
        'lable}.'),
    "templates_saved": 'Saved templates',
    'workspace_templates': 'Workspace templates…',
    'templates_tab': 'Tab',
    'templates_kind': 'Scope',
    'templates_status': 'Availability',
    'templates_single': 'Single folder',
    'templates_check': 'Check paths',
    'templates_replace': 'Replace tabs',
    'templates_hint': (
        'Save the current tabs, or select a tem'
        'plate to preview. Edit paths and check'
        ' them before replacing tabs. Replaceme'
        'nt closes existing scans and results. '
        'Loaded tabs stay idle until Start. Una'
        'vailable roots are retained; repair th'
        'em here and check again. Add and Updat'
        'e save the current workspace.'),
    'templates_invalid': (
        'Invalid template data. Use unique name'
        's and absolute paths. Existing setting'
        's were not changed.'),
    'templates_unchecked': 'Not checked',
    'templates_checking': 'Checking all paths…',
    'templates_ready': 'Ready',
    'templates_checked': (
        'Paths checked. Replace tabs loads all '
        'inputs, including unavailable roots. S'
        'tart stays disabled for tabs with erro'
        'rs.'),
    'templates_not_folder': 'Not a folder',
    "completion_title": 'Last cleanup result',
    "completion_undo": 'Undo available moves',
    "completion_rescan": 'Rescan original folder',
    "completion_dismiss": 'Dismiss summary',
    "completion_source": 'Source: {path}',
    "completion_counts": (
        'Moved: {moved} ({size}); skipp'
        'ed: {skipped}; failed: {failed'
        '}'
    ),
    "completion_space": (
        'Observed free-space change bet'
        'ween scans: {change} (includes'
        ' other activity)'
    ),
    "completion_measurements": (
        'Scan observations: {before} → '
        '{after}'
    ),
    "completion_space_pending": (
        'No later comparable scan obser'
        'vation yet. Unknown is not zer'
        'o.'
    ),
    "completion_reason": '{reason}: {count}',
    "completion_more": (
        'More reasons are available in '
        'the operation records.'
    ),
    "completion_errors": (
        'Journal errors: {journal}; cop'
        'y-finalization errors: {copies'
        '}.'
    ),
    "completion_hint": (
        'Moved bytes are logical data, '
        'not space freed. Emptying the '
        'Recycle Bin is a separate acti'
        'on. Review operation records a'
        'nd failure reports for details'
        '.'
    ),
    "action_scan_presets_tip": "Save and load named paths and scan options without starting a scan",
    "action_scan_presets": 'Scan presets…',
    "presets_empty": 'No saved presets',
    "presets_hint": (
        'Add and Update save the current scan opt'
        'ions with the entered path. Load fills t'
        'he inputs; press Scan path to start. Con'
        'currency and exclusions apply to the wor'
        'kspace.'
    ),
    "presets_saved": 'Saved presets',
    "presets_name": 'Name',
    "presets_add": 'Add current options',
    "presets_update": 'Update selected',
    "presets_rename": 'Rename',
    "presets_remove": 'Delete preset',
    "presets_load": 'Load',
    "presets_options": (
        'Workers: {workers}; exclusions: {exclusi'
        'ons}; enabled: {flags}'
    ),
    "presets_no_flags": 'none',
    "presets_invalid": (
        'Use a unique name (1–80 characters), an '
        'absolute path and valid scan options. At'
        ' most 32 presets are supported.'
    ),
    "presets_read_failed": (
        'Saved presets could not be read. Existin'
        'g data has been retained.'
    ),
    "presets_loaded": 'Loaded {name}. Press Scan path to start.',
    "highlights_title": 'Scan highlights',
    "highlights_waiting": 'Waiting for scan analysis…',
    "highlights_folders": 'Largest direct folders — select one to locate it.',
    "highlights_partial": 'Partial results: sizes describe only the entries read.',
    "highlights_folder": '{name} — {size}',
    "highlights_cleanup_waiting": 'Clean up: analysis pending…',
    "highlights_cleanup": 'Review {count} candidates ({size})',
    "highlights_cleanup_hint": 'Candidate bytes require review and do not represent immediately recoverable space.',
    "highlights_coverage_unknown": 'Coverage not yet available',
    "highlights_coverage": 'Scan limits: {skipped} skipped, {denied} unreadable, {pending} pending',
    "column_advice": 'Removal advice',
    "advice_low": 'Cleanable',
    "advice_review": 'Check first',
    "advice_personal": 'Your call',
    "advice_protected": 'Keep',
    "advice_managed": "OS-managed",
    "advice_pending": 'Checking…',
    "advice_low_tip": (
        'A lower-risk clean-up suggestion: programs can recreate this data. Review it before '
        'moving it.'
    ),
    "advice_review_tip": 'A clean-up suggestion that needs your review: make sure nothing here is still needed.',
    "advice_personal_tip": (
        'No rule covers this entry, so only you can tell whether it is still needed. Nothing '
        'is moved without your confirmation.'
    ),
    "advice_protected_tip": 'Keep it: {reason}. Removing it can break the system or installed programs.',
    "advice_managed_tip": (
        'The operating system manages this space and FileTree never moves it. Details names t'
        'he system tool to use.'
    ),
    "advice_pending_tip": 'The clean-up analysis is still running.',
    "advice_summary": '{label} — {reason}',
    "advice_legend_tip": (
        "Advice from this scan's clean-up rules and the protected places of this computer. It"
        ' is guidance only: every move still asks first.'
    ),
    "highlights_folders_label": 'Largest folders',
    "highlights_files_label": 'Largest files',
    "highlights_files": 'The largest files — select one to locate it. The dot shows the removal advice.',
    "reclaim_action": "Free up space…",
    "reclaim_action_tip": "Plan how to free a chosen amount of space from what this scan found",
    "reclaim_title": "Free up space",
    "reclaim_hint": (
        "Choose how much space you need. FileTree lists what this scan already found, the safest first. Nothing is "
        "selected for you, and nothing is moved until you review it and answer yes."
    ),
    "reclaim_target": "Space to free:",
    "reclaim_custom": "Custom amount",
    "reclaim_share": "Until the drive has this share free",
    "reclaim_drive": "The drive had {free} free of {total} when it was scanned.",
    "reclaim_column_entry": "Step or entry",
    "reclaim_column_total": "Running total",
    "reclaim_step": "{risk}: {title} ({count})",
    "reclaim_duplicates": "Extra copies of duplicates",
    "reclaim_duplicates_tip": (
        "Files with the same content as the copy you chose to keep in the Duplicates tab. The kept copy is never "
        "proposed."
    ),
    "reclaim_options": "Large files no rule covers — only if you are sure",
    "reclaim_running": "{total} of {target}",
    "reclaim_beyond": "{total} of {target} (past the target)",
    "reclaim_more": "{count} more not listed",
    "reclaim_overlap": "{size} on its own; part of it is already counted in an earlier step.",
    "reclaim_reached": "These steps could free about {found}, enough for the {target} you asked for.",
    "reclaim_short": (
        "These steps could free only about {found}, {short} short of {target}. The large files listed last may make "
        "up the rest, if you are sure you no longer need them."
    ),
    "reclaim_empty": "This scan found nothing that can be proposed.",
    "reclaim_waiting": "Clean-up suggestions are still being looked for; the plan fills in when they are ready.",
    "reclaim_undecided": "{count} duplicate groups are left out: choose the copy to keep in the Duplicates tab first.",
    "reclaim_selected": "Selected: {selected} of {target}",
    "reclaim_note": (
        "These are estimates from the scan. What is really freed can differ: hard links, compressed and cloud files "
        "take less space than their size, and the Recycle Bin keeps what is moved there until it is emptied."
    ),
    "reclaim_show": "Show in tree",
    "reclaim_review": "Review and move to Recycle Bin…",
    "shell_reading": "Reading Explorer registration…",
    "shell_saving": "Saving Explorer registration…",
    "shell_waiting": "Waiting for the current Explorer settings request to finish… A started Save continues.",
    "trash_failed_title": "Entries not moved",
    "trash_failed_summary": "Failed entries: {count}. Review the full paths and diagnostic information.",
    "trash_holders_error": "Open-file query error: {reason}",
    "trash_skipped_title": "Skipped entries",
    "trash_skipped_summary": "Skipped entries: {count}. Rescan their folders before trying again.",
    "trash_skipped_hint": "Select a row for its full path and reason. {shortcut} copies selected rows.",
    "closing_workers": "Closing FileTree: stopping background work; waiting for current filesystem calls to finish…",
    "elevate_python_tip": (
        "Running from Python: Windows UAC displays Python, the executable being elevated. "
        "Use the FileTree executable for a FileTree prompt."),
    'overview_empty': 'Choose a folder to begin',
    'overview_live': 'Scan in progress · totals are still growing',
    'overview_complete': 'Scan finished',
    'overview_partial': 'Incomplete results · some entries were not read',
    'overview_size': 'Logical size',
    'overview_allocated': 'Recorded allocation',
    'overview_files': 'Files',
    'overview_folders': 'Folders',
    'overview_problems': 'Review unreadable entries ({count})',
    'overview_navigation': 'Analysis view',
    'overview_coverage_hint': 'Coverage describes this scan. Exclusions and mount boundaries still apply.',
    'overview_allocation_hint': 'Recorded allocation may be estimated or shared. It is not recoverable space.',
    'overview_live_hint': 'Explore the growing tree and charts. Analysis lists populate when scanning finishes.',
    'overview_result_hint': 'Choose an analysis view; select an entry to locate it in the tree.',
    'overview_path': 'Folder or drive path',
    'overview_scan_path': 'Scan path',
    'overview_scan_path_tip': 'Scan the entered folder or drive (Enter). A running scan is replaced safely.',
    'overview_workflow': '1  Choose a folder or drive   →   2  Explore its space usage   →   3  Review before cleanup',
    'overview_scan_running': 'Reading folders in the background. You can explore the growing results.',
    'overview_scan_paused': ('Pause requested; the current filesystem call may finish first. '
                             'Resume or Stop to continue.'),
    'overview_scan_analysing': 'Preparing analysis in the background. Stop remains available.',
    'overview_scan_stopping': 'Waiting for current filesystem work to finish; available partial results are retained.',
    'overview_scan_elapsed': 'Elapsed {time}',
    'recurring_review': 'Rescan and review current candidates…',
    'recurring_validating': 'Validating the dated proposal against the entire fresh scan and current source metadata…',
    'recurring_refused': ('Proposal cannot continue: {status}. '
                         'Run a new scheduled scan to prepare current observations.'),
    'recurring_tabs_full': 'All sixteen scan tabs are in use. Close a tab before reviewing a scheduled proposal.',
    'trash_skip_proposal_changed': ('Source paths or proposal settings/receipt changed or could not be verified; '
                                    'source kept.'),
    'trash_skip_proposal_expired': 'The scheduled proposal expired before this move; source kept.',
    'action_recurring': 'Scheduled scan proposals…',
    'action_recurring_tip': 'View dated scheduled observations and their coverage; no automatic clean-up.',
    'recurring_rule': 'Rule',
    'recurring_unknown': 'Unknown',
    'recurring_new': 'New junk since last scan',
    'recurring_current': 'Current candidates',
    'recurring_growth': 'Largest new growth',
    'recurring_empty': 'No scheduled report in this session. Enable background monitoring and select scan folders.',
    'recurring_hint': ('Observations only; nothing is moved automatically. Up to 100 rows per list. '
                       'Growth is logical bytes, not recoverable space. Unknown comparisons do not prove no new junk. '
                       'Reports appear after a scheduled scan in this session; baselines are kept in local history. '
                       'Review rescans in a new tab and uses the ordinary queue and confirmations.'),
    'recurring_summary': ('Prepared: {prepared}\nPrevious baseline: {previous}\nExpires: {expires}\n'
                          'Candidates shown: {retained} / {total}; coverage: {coverage}; comparison: {comparison}\n'
                          'Status: {status}'),
    'recurring_status_current': 'Observed; fresh source validation required before review',
    'recurring_status_expired': 'Expired (including a missed schedule or clock rollback)',
    'recurring_status_schedule_changed': 'Schedule changed or disabled',
    'recurring_status_stale_scan': 'Scan receipt changed or unavailable',
    'recurring_status_rule_changed': 'Clean-up rules changed',
    'recurring_status_incomplete': 'Incomplete coverage or unknown identity',
    'recurring_status_paths_changed': 'Source paths changed',
    'recurring_status_unavailable': 'Settings or receipt could not be verified',
    'recurring_prepare_failed': 'History saved; scheduled proposal unavailable: {detail}',
    'workspace_new': 'New scan tab',
    'workspace_new_tip': 'Open an independent scan tab (Ctrl+T); close the current tab with Ctrl+W.',
    'workspace_close': 'Close scan tab',
    'workspace_empty': 'Choose a folder',
    'trash_skip_recycle_unverified': (
        'Windows recycling settings, complete source size or native bin metadata could not be verified; source kept.'
    ),
    'trash_skip_recycle_disabled': (
        'Windows recycling is disabled for this scope; source kept.'
    ),
    'trash_skip_recycle_capacity': (
        'Selection and current bin contents exceed the observed recycling limit with headroom; source kept.'
    ),
    'action_check_updates': 'Check for updates daily',
    'action_background_monitor': 'Background monitor…',
    'action_background_monitor_tip': 'Opt in to tray notifications and gentle scheduled folder-history scans.',
    'background_enable': 'Enable background monitoring',
    'background_startup': 'Start this monitor when I sign in',
    'background_startup_hint': ('Separate opt-in for this user only. Uncheck to remove FileTree’s owned login entry. '
                                'Applies to future logins; does not start another copy or close this monitor.'),
    'background_startup_requires_monitor': 'Enable background monitoring before adding a login entry.',
    'background_startup_error': 'Login startup could not be changed: {detail}',
    'background_hint': ('Off by default. Closing keeps FileTree in the available system tray; Quit ends it. '
                        'Check OS available capacity each minute and scan only chosen folders gently. '
                        'Scheduled scans require enabled local history. '
                        'No automatic clean-up or startup registration.'),
    'background_threshold': 'Warn below available space',
    'background_interval': 'Scan interval (hours)',
    'background_roots': 'Scheduled scan folders',
    'background_add': 'Add scan folder…',
    'background_remove': 'Remove selected folders',
    'background_limit': 'Choose at most 32 scheduled folders.',
    'background_show': 'Show FileTree',
    'background_off': 'Background monitoring is off',
    'background_ready': 'Background monitoring is on',
    'background_no_tray': 'System tray unavailable; FileTree stays visible and background monitoring is paused.',
    'background_error': 'Background monitoring: {detail}',
    'background_history_disabled': 'Enable local scan history before scheduled scans can run.',
    'background_scanning': 'Scheduled scan: {detail}',
    'background_saved': 'Scheduled history saved: {detail}',
    'background_saved_partial': 'Scheduled history saved with unread scopes: {detail}',
    'background_canceled': 'Scheduled scan canceled; partial source coverage was not saved: {detail}',
    'background_warning': '{detail}',
    'background_low_space': 'Low available space on {root}: {free} ({percent}%)',
    'action_follow_changes': 'Follow changes',
    'action_follow_changes_tip': ('Off by default. On Windows, Linux and macOS, read again only the folders '
                                  'that changed, keeping their unchanged subfolders.'),
    'follow_refreshed': 'Updated {count} changed folders',
    'follow_refresh_failed': 'Could not update the changed folders: {reason}',
    'follow_waiting': 'Follow changes: waiting for a scan',
    'follow_starting': 'Follow changes: starting…',
    'follow_active': 'Following changes ({detail})',
    'follow_failed': 'Follow changes stopped: {detail}',
    'follow_incomplete': 'Follow changes needs a complete physical scan',
    'follow_unsupported': 'Follow changes supports Windows, Linux and macOS',
    'follow_backend_usn': 'NTFS USN',
    'follow_backend_directory_changes': 'directory notifications',
    'follow_backend_inotify': 'inotify',
    'follow_backend_fsevents': 'FSEvents',
    'action_check_updates_tip': 'Ask PyPI over HTTPS at most once a day; notice only, with no installation.',
    'update_available': 'FileTree {version} is available',
    'multi_roots': 'Multiple roots',
    'action_multi_scan': 'Scan several folders…',
    'action_multi_scan_tip': 'Review explicit folders in one combined scan.',
    'multi_choose': 'Scan several folders',
    'multi_add': 'Add folder…',
    'multi_remove': 'Remove selected roots',
    'scan_all_drives': 'Scan all drives',
    'multi_hint': ('Combine up to 256 selected roots. Results are read-only; scan a source separately '
                   'for file operations. OS capacity stays per volume.'),
    'capacity_multiple_roots': 'Multiple roots: OS capacity is per volume.',
    'vc_title': (
        'Compact selected VHD…'
    ),
    'vc_apply': (
        'Review and compact…'
    ),
    'vc_hint': (
        'Only a detached dynamic VHD/VHDX on fixed local NTFS is eligible. Read-only pr'
        'eparation checks identity, headers and conservative WSL/Docker runtime state. '
        'Guest usage and guaranteed recovery stay unknown. Close this review before usi'
        'ng FileTree’s existing administrator restart for a permission error; a new sca'
        'n and approval are required.'
    ),
    'vc_preparing': (
        'Checking the captured disk and stopped runtime…'
    ),
    'vc_ready': (
        'Review the exact source and confirm its machine stays stopped.'
    ),
    'vc_details': (
        'Source: {path}\nName: {source}\nDisk UUID: {identifier}\nVirtual capacity: {capac'
        'ity}\nProvider bytes: {physical}\n\nBackend: Windows CompactVirtualDisk, detached'
        ' zero-block compaction. No guest attachment, launch or shutdown; guest-used by'
        'tes are unknown.'
    ),
    'vc_confirm': (
        'Compact this exact backing file?\n\n{path}\n\nChoosing Yes confirms that its ownin'
        'g machine is stopped and will stay stopped throughout the operation. Fresh run'
        'time and identity checks still apply. Native zero-block compaction may recover'
        ' nothing or change metadata before a later error. There is no automatic Undo. '
        'Guest usage/free-space recovery are unknown. Stop/close waits for an active na'
        'tive call and reports its actual outcome. Approval is recorded before any writ'
        'able open.'
    ),
    'vc_running': (
        'Rechecking and compacting the reviewed disk…'
    ),
    'vc_waiting': (
        'Waiting for the current native call; its actual result will be reported…'
    ),
    'vc_done': (
        '{status}\nObserved backing allocation: {before} → {after}. This is not guarante'
        'ed OS free recovery. Guest usage remains unknown; attempted writes require a f'
        'resh scan.'
    ),
    'vc_failed': (
        'Compaction: {reason}'
    ),
    'vc_not_compacted': (
        'Not compacted'
    ),
    'vc_stale': (
        'A writable operation was attempted. Recorded observations are stale; close thi'
        's window for a fresh scan before another review.'
    ),
    'vc_audit_refused': (
        'Approval could not be recorded; no native operation was started'
    ),
    'vc_audit_detail': (
        'Backing allocation before: {before}; after: {after}. Error: {error}'
    ),
    'journal_status_compacted': (
        'Native compaction completed'
    ),
    'journal_reason_compaction': (
        'Explicit virtual-disk compaction'
    ),
    'vd_hint': (
        'Read-only inventory; provider labels are location hints. Backing allocation, p'
        'rovider bytes and virtual capacity are separate; guest usage stays unknown. He'
        'ader queries and compaction reviews are explicit. Unsupported formats remain v'
        'isible; no guest starts, stops or mounts automatically.'
    ),
    "vd_name": 'Disk name',
    "vd_source": 'Source',
    'vd_issue_unverified': 'Unverified identity',
    'vd_issue_unavailable': 'Linked, cloud or unavailable',
    'vd_issue_changed': 'File changed',
    'vd_issue_duplicate_hard_links': 'Multiple hard-link names',
    "action_virtual_disks_tip": 'Review recorded virtual disks and explicitly query read-only native VHD information',
    'action_virtual_disks': 'Virtual disks…',
    'vd_kind': 'Format',
    'vd_length': 'Backing-file length',
    'vd_allocation': 'Recorded allocation',
    'vd_capacity': 'Virtual capacity',
    'vd_physical': 'Provider physical bytes',
    'vd_guest': 'Guest used',
    'vd_source_scan': 'Recorded scan',
    'vd_source_wsl': 'WSL registration',
    'vd_source_docker': 'Docker default (inferred)',
    'vd_unsupported': 'Native VHD tools unsupported',
    'vd_not_queried': 'Native header not queried',
    'vd_fixed': 'Fixed',
    'vd_dynamic': 'Dynamic',
    'vd_differencing': 'Differencing',
    'vd_loaded': 'Mounted/in use',
    'vd_detached': 'Not loaded (observation)',
    'vd_inspect': 'Query selected VHD header',
    'vd_select': 'Show recorded entry',
    'vd_reading': 'Discovering virtual backing files…',
    'vd_querying': 'Reading native header: {path}',
    'vd_summary': 'Showing {shown} of {count}; {issues} issues/omissions. Coverage: {coverage}.',
    'vd_failed': 'Virtual-disk information: {reason}',
    'vd_information_hint': (
        'Native observations do not authorize compaction or prove a stopped machine. Provider '
         'physical bytes are not guest-used bytes. Disk UUID is in the row tooltip.'
    ),
    "link_summary": "{total} extra copies: {ready} ready, {skipped} refused.",
    "link_title": "Link the extra copies…",
    "link_hint": (
        "Review exact duplicate files with explicitly kept copies (up to 1,000 extras). "
        "Protected, changed, cloud, linked and unsupported files are refused. No guaranteed freed-space amount."
    ),
    "link_copy": "Extra copy to replace",
    "link_keeper": "Kept file",
    "link_apply": "Link reviewed extra copies…",
    "link_confirm": (
        "Replace {count} extra copies with hard links? {skipped} refused rows will be skipped.\n\n"
        "Old data is not kept in Trash. Every linked name shares future content, metadata and "
        "security/permission changes. This has no automatic Undo. Failures or cancellation may retain "
        "published links and old-copy backups at the paths shown. Stop/close waits for the current native call. "
        "Complete data and named streams are rechecked; concurrent changes remain observational. "
        "Review every pair and refusal in Details."
    ),
    "link_progress": "Rechecking/linking: {path}",
    "link_done": (
        "Hard links: {linked} published, {other} not linked. "
        "Rescan to refresh observations; recovered capacity is unknown."
    ),
    "link_not_linked": "Not linked",
    "link_retained": "Retained paths:\n{paths}",
    "journal_status_linked": "Hard link published",
    "journal_reason_duplicate_links": "Explicit duplicate hard-link replacement",
    "undo_button": "Undo ({count})",
    "undo_running": "Restoring captured Trash items…",
    "undo_done": "Undo: {restored} restored, {failed} failed",
    "undo_title": "Trash restoration",
    "undo_result": "{status}\nOriginal: {source}\nTrash: {trashed}\n{reason}",
    "undo_unavailable": "Undo unavailable for some items: {reason}",
    "journal_status_restored": "Restored from Trash",
    "journal_reason_undo": "Explicit Trash undo",
    "menu_move_drive": "Move to another drive…",
    "copy_hint": ("Choose an existing folder on another drive. Originals stay until a separate Trash confirmation. "
                  "Verify file counts, lengths and SHA-256 below 64 MiB; larger payloads are length-only. "
                  "Failures/cancellation retain partial destinations. Up to 1,000 selected folders."),
    "copy_apply": "Copy and verify reviewed folders…",
    "copy_redirect": "After successful Trash, leave a junction/symbolic link at each original path",
    "copy_finish": "Move verified originals to Recycle Bin…",
    "copy_confirm": ("Copy and verify {count} reviewed folders? {skipped} other pairs will be skipped. "
                     "Existing names are never overwritten. Originals remain until a separate Trash approval; "
                     "partial destinations remain on errors or cancellation."),
    "copy_progress": "Copying/verifying {path}: {done} / {total} files in this folder",
    "copy_done": "Verified copies: {copied}; skipped: {skipped}; failed: {failed}. Originals retained.",
    "copy_partial": "Retained partial destination: {path}",
    "copy_trash_confirm": ("The copied folders will be verified again immediately before each original moves to "
                           "Trash. Counts/lengths are compared; payloads below 64 MiB are SHA-256 checked. "
                           "Larger payloads are length-only. A failed check stops the remaining batch. "
                           "Concurrent changes are not transactional."),
    "copy_errors": "Copy verification or original-path redirect failed. Review the actual paths in Details.",
    "copy_verify_failed": "Original retained: {source}\nCopy: {destination}\nVerification refused: {reason}",
    "copy_redirect_failed": ("Original moved to Trash: {source}\nVerified copy retained: {destination}\n"
                             "Redirect failed (an empty original-path directory may remain): {reason}"),
    "namespace_reason_same_volume": "Same volume; use Move to folder",
    "namespace_source_name": "Source name",
    "namespace_destination_name": "Destination name",
    "namespace_closed_errors": ("The stopped/closed operation reported errors. "
                                "Inspect the source/destination paths in Details."),
    "namespace_refreshed": "Refreshed {path}: {files} files; {errors} scan errors.",
    "namespace_refresh_failed": "Refresh failed at {path}: {reason}",
    "namespace_refreshing": "Refreshing affected destination: {path}",
    'menu_move_folder': 'Move to folder…',
    'menu_rename': 'Rename…',
    'namespace_source': 'Source',
    'namespace_destination': 'Destination',
    'namespace_status': 'Status',
    'namespace_pattern': 'Filename pattern',
    'namespace_rename_hint': ('Review every source and destination. Literal tokens: {name}, {stem}, {ext}, {n}. Same '
     'volume only; no overwriting. Up to 1,000 selected entries.'),
    'namespace_move_hint': ('Choose an existing destination folder and review every pair. Same volume only; no '
     'overwriting. Protected/link/unavailable/incomplete entries are refused. Up to 1,000 '
     'selected entries.'),
    'namespace_collision_skip': 'Existing name: skip',
    'namespace_collision_rename': 'Existing name: preview a numbered suffix',
    'namespace_preview': 'Preview paths',
    'namespace_apply': 'Apply reviewed paths…',
    'namespace_reading': 'Checking source and destination metadata…',
    'namespace_preview_needed': 'Options changed; preview paths again before applying.',
    'namespace_summary': '{total} outermost pairs; {ready} ready; {skipped} refused/unchanged.',
    'namespace_confirm': ('Apply the {count} eligible source/destination pairs from the preview? {skipped} other '
     'pairs will be skipped. Details list every eligible pair. No existing name will be '
     'overwritten. Stop/close waits through the current rename and keeps completed changes.'),
    'namespace_progress': 'Processed {done} / {total} pairs',
    'namespace_done': 'Moved/renamed: {moved}; skipped: {skipped}; failed: {failed}. Close to refresh the scan.',
    'namespace_failed': 'Operation failed: {reason}',
    'namespace_reason_ready': 'Ready',
    'namespace_reason_unverified': 'Unknown identity',
    'namespace_reason_link': 'Link refused',
    'namespace_reason_special': 'Special entry refused',
    'namespace_reason_unavailable': 'Unavailable/cloud entry',
    'namespace_reason_cancelled': 'Stopped',
    'namespace_reason_outside': 'Outside current scan/root',
    'namespace_reason_missing': 'Source missing',
    'namespace_reason_kind': 'Entry type changed',
    'namespace_reason_identity': 'Source replaced',
    'namespace_reason_changed': 'Source changed',
    'namespace_reason_incomplete': 'Incomplete source coverage',
    'namespace_reason_unreadable': 'Unreadable source',
    'namespace_reason_system_managed': 'System-managed source',
    'namespace_reason_protected': 'Protected source',
    'namespace_reason_unchanged': 'Name unchanged',
    'namespace_reason_descendant': 'Destination inside selected source',
    'namespace_reason_protected_destination': 'Protected destination',
    'namespace_reason_volume': 'Different volume; verified copy required',
    'namespace_reason_collision': 'Name already exists',
    "photos_exact": "Exact duplicates",
    "photos_find": "Find similar photos",
    "photos_similar": "Similar photos",
    "photos_distance": "Hash distance (0–16):",
    "photos_hint": ("Visual candidates only: compare thumbnails and originals. Hash collisions are possible; "
                    "no automatic keeper, extra-copy selection or recovery estimate. First animation frame."),
    "photos_group": "{count} images; within {distance} bits of the first image",
    "photos_running": "Reading images: {read}; skipped/failed: {skipped}",
    "photos_summary": "{groups} similar-image groups; {read} images read; {skipped} skipped/failed.",
    "photos_limited": "Limited inventory or display; up to {count} image rows/thumbnails shown.",
    "archive_loading": "Reading archive metadata…",
    "archive_virtual_name": "{name} [virtual]",
    "tree_more_rows": "{count} more entries — click to show the next {page}",
    "tree_more_rows_hint": ("Large folders show {page} entries at a time so the window stays responsive. "
                            "Click this row or press Enter for the next page; an entry picked in a chart "
                            "or list shows the page it is on."),
    "archive_virtual_hint": ("Archive member: declared uncompressed size, outside disk totals. "
                             "No file actions or extraction."),
    "archive_failed": "Preview unavailable: {reason}",
    "archive_rejected": "Omitted {count} unsafe, linked or conflicting members",
    "archive_empty": "No previewable members",
    "archive_stopped": "Archive preview stopped; inventory incomplete",
    "archive_busy": "Two archive reads are already running; rescan to retry",
    "archive_stop": "Stop reading this archive",
    "action_count_hard_links": (
        "Count observed hard links once"
    ),
    "action_count_hard_links_tip": (
        "Off by default; future scans keep named sizes and add counted totals. "
        "Branch/Trash rescans rebuild the full root."
    ),
    "column_accounted_size": (
        "Counted size"
    ),
    "column_accounted_allocated": (
        "Counted disk size"
    ),
    "hard_links_hint": (
        "With hard-link accounting enabled, the lexical first observed name con"
        "tributes bytes; aliases count zero here. Named sizes remain real file "
        "lengths. Unknown/inconsistent records stay estimated; shared extents a"
        "re unknown."
    ),
    "hard_links_summary": (
        "Counted: {size} (disk estimate {allocated}); {aliases} observed aliase"
        "s; {unknown} unknown records. Charts use counted totals; file/type/age"
        " lists keep named sizes."
    ),
    "compression_mode_ntfs": "NTFS compression",
    "compression_mode_xpress8k": "XPRESS8K compression (rarely modified files)",
    "compression_mode_uncompress": "Uncompress (NTFS and executable modes)",
    "compression_apply": "Process listed files…",
    "compression_restore_summary": (
        "{count}/{total} recorded files eligible for review; showing {shown}. Compression state may be "
        "unknown."
    ),
    "compression_confirm": (
        "Scope: {path}\nMode: {mode}\nOnly the {count} listed files ({size} logical), out of {total} "
        "candidates, will be processed.\n\nCurrent NTFS scope and unchanged files are checked again. Links, "
        "cloud/offline, sparse, hidden/system, hard-linked and protected files are refused. Directory "
        "defaults and unlisted files are untouched. Compression can slow writes; XPRESS is for rarely "
        "modified data. Uncompression needs free disk space. Stop/failure can leave partial "
        "changes.\n\nClosing this window cancels any current command, waits for it and rescans this folder "
        "with per-file allocation. Continue?"
    ),
    "compression_progress": "Processing {done}/{total} listed files…",
    "compression_done": (
        "{done}/{attempted} commands completed; {failures} failures. Known matched file allocation: "
        "{before} → {after}; {unknown} measurements unknown. Close to rescan; totals are not guaranteed "
        "freed space. First 20 errors are shown."
    ),
    "compression_canceled": "Stopped; earlier or current files may have changed. Close to rescan.",
    "compression_failed": "Operation failed: {reason}. Partial changes are possible; close to rescan.",
    "action_exact_allocation": "Measure Windows per-file allocation",
    "action_exact_allocation_tip": (
        "Off by default; extra metadata calls for future scans, including XPRESS/WOF files. "
        "Enable and rescan. Known cloud/offline files stay unqueried; failed queries remain estimates."
    ),
    "menu_compression": "NTFS compression…",
    "compression_reading": "Reviewing recorded compression candidates…",
    "compression_summary": (
        "{count}/{total} files are type candidates; showing {shown}; logical {logical}, named allocation {allocated}. "
        "Potential saving: 0–{allocated}; no fixed compression rate is predicted. "
        "{unknown} files have unknown metadata."
    ),
    "compression_volume": "Filesystem: {filesystem}; allocation unit: {unit}",
    "compression_unknown": "Unknown",
    "compression_ntfs_only": "NTFS was not confirmed; native compression is unavailable for this scope.",
    "compression_partial": "Incomplete scan: omitted/unreadable data is outside this estimate.",
    "compression_hint": (
        "Read-only type estimate: logs, text, code and possibly uncompressed image formats. "
        "Extensions do not prove compressibility. Hidden/system, compressed/sparse, reparse/cloud/offline and unknown "
        "records are omitted. Named allocation can be estimated or shared by hard links, so it is not guaranteed "
        "recoverable space. No payload is read. Double-click selects the recorded file; Ctrl+C copies rows."
    ),
    "action_capture_owners": "Capture Windows file owners",
    "action_capture_owners_tip": "Off by default; adds owner metadata queries to future scans; enable and rescan",
    "tab_users": "Users",
    "column_owner": "Owner",
    "column_owner_id": "Owner identity",
    "owner_unknown": "Unknown owner",
    "owners_refresh": "Refresh recorded totals",
    "owners_reading": "Adding recorded owner totals and resolving account names…",
    "owners_unqueried": "Open Users after scanning to query recorded owner totals.",
    "owners_partial": "Incomplete scan: omitted/unreadable bytes and their owners remain unknown.",
    "owners_summary": (
        "{count} owner groups; showing {shown}; {files} files, {size}. "
        "Unknown owners: {unknown_files} files, {unknown_size}."
    ),
    "owners_hint": (
        "Whole scan, file owners only; directory ownership does not assign descendants. "
        "POSIX uid comes from the scan's stat. On Windows enable Options → Capture Windows file owners and rescan. "
        "Disabled, failed, changed or cloud/offline queries stay unknown. Names can fall back to uid/SID. "
        "Named allocation remains estimated and hard links count per name. Ownership does not prove actual use "
        "or removal permission. No cleanup actions are prepared."
    ),
    "bin_labels_refresh": "Refresh bin totals",
    "bin_labels_hint": (
        "Read-only snapshot for up to 256 ready drives, prioritizing the scanned drive. "
        "POSIX totals are logical payload bytes; unavailable or partial totals never mean zero. "
        "Scopes can overlap; do not sum them. Refresh to query; this does not prepare cleanup actions."
    ),
    "bin_label_scope_unknown": "Recycle Bin for this scan's drive: scope not queried",
    "bin_label_unqueried": "{root} Recycle Bin: not queried",
    "bin_label_total": "{root} Recycle Bin: {size}, {count} items",
    "bin_label_partial": "{root} Recycle Bin: total unknown; known {size}, {count} items",
    "action_file_times": "File times…",
    "action_file_times_tip": "Filter recorded access and creation dates in this scan",
    "action_capture_file_times": "Capture file access/creation times",
    "action_capture_file_times_tip": (
        "Off by default; adds 16 bytes per regular file to future scans; rescan after ena"
        "bling"
    ),
    "column_accessed": "Recorded access",
    "column_created": "Created",
    "file_times_hint": (
        "Enable Options → Capture file access/creation times, then rescan. Regular files"
        " only; directory/link and unavailable creation dates remain unknown. Access date"
        "s can be disabled, delayed or updated by background tools; they never prove actu"
        "al use. POSIX ctime is not creation time. This view does not prepare cleanup act"
        "ions."
    ),
    "file_times_accessed": "Not opened since… (recorded access date)",
    "file_times_created": "Created at least… ago",
    "file_times_mode": "Recorded age mode",
    "file_times_days": "Days",
    "file_times_reading": "Filtering recorded file dates…",
    "file_times_summary": (
        "{count} matches, {size}; showing {shown}. {unknown}/{total} files have unavailab"
        "le or future dates."
    ),
    "file_times_policy_disabled": (
        "NTFS reports access updates disabled. Access-age matching is unavailable; creati"
        "on filtering remains available. Registry settings may require a restart and do n"
        "ot describe every filesystem."
    ),
    "file_times_policy_unknown": (
        "NTFS access-update configuration is unknown. Access-age matching is unavailable;"
        " creation filtering remains available."
    ),
    "file_times_policy_enabled": (
        "NTFS registry reports access updates enabled; pending restart, filesystem/provid"
        "er settings and deferred updates may still affect dates."
    ),
    "file_times_policy_platform": (
        "Filesystem/provider settings may defer or suppress access updates. Treat these d"
        "ates as recorded metadata."
    ),
    "action_programs": "Installed programs…",
    "action_programs_tip": "Compare installer/game metadata with installation folders in this scan",
    "program_name": "Program / game",
    "program_source": "Metadata source",
    "program_version": "Version / build",
    "program_publisher": "Publisher",
    "program_reported": "Reported estimate",
    "program_scanned": "Scanned logical bytes",
    "program_allocated": "Scanned named allocation",
    "program_coverage": "Recorded folder coverage",
    "program_location": "Installation folder",
    "program_registry": "Windows registry",
    "program_steam": "Steam manifest",
    "program_epic": "Epic manifest",
    "program_outside": "No exact scanned folder",
    "program_hint": "Windows uninstall registrations and recognized Steam/Epic manifests, matched only to exact "
                    "folders in this scan. Epic's fixed ProgramData manifest folder is also read. Reported sizes "
                    "are estimates; missing metadata stays unknown. Shared/nested folders can overlap: do not sum "
                    "rows or treat them as recoverable space. Portable/packaged apps may be absent. Double-click "
                    "selects a recorded folder; Ctrl+C copies rows. Uninstall only through Windows or the launcher.",
    "program_reading": "Reading installation metadata…",
    "program_summary": "Showing {shown} of {count} installations; "
                       "{issues} unavailable/malformed/omitted metadata items",
    "program_failed": "Cannot read installations: {reason}",
    "program_uninstall_page": "Open Windows installed-app settings",
    "program_open_failed": "Windows could not open the installed-app settings page",
    "action_history": "Scan history…",
    "action_history_tip": "Review this root's size over time and compare with an earlier scan",
    "action_history_settings": "Scan history settings…",
    "action_history_settings_tip": "Enable local scan metadata and set its global retention limit",
    "history_enable": "Keep completed full scans locally",
    "history_settings_hint": "History stores folder names, paths, totals and coverage, never file contents. "
                             "Default: enabled, 1 GiB total across all roots. Only recognized history metadata "
                             "is removed, oldest first. Disabling keeps existing history readable. Changes apply "
                             "to future full scans; a lower limit takes effect on the next save.",
    "history_limit": "Total history limit",
    "history_time": "Scan time",
    "history_logical": "Logical size",
    "history_allocated": "Allocated named bytes",
    "history_coverage": "Coverage",
    "history_incomplete": "Incomplete; known data only",
    "history_complete": "Complete recorded coverage",
    "history_chart": "Logical folder size over time",
    "history_chart_range": "{first}: {before}; {last}: {after}",
    "history_empty": "No retained scans for this root",
    "trend_folder": "Root-relative folder",
    "trend_folder_hint": "Blank means root",
    "trend_start": "From date (inclusive)",
    "trend_end": "Through date (inclusive)",
    "trend_apply": "Apply trend",
    "trend_change": "Change",
    "trend_child": "Direct child",
    "trend_before": "First size",
    "trend_after": "Last size",
    "trend_direct_files": "Direct files",
    "trend_unknown": "Unknown",
    "trend_net": "Period net change: {change}",
    "trend_net_unknown": "Period net change unknown",
    "trend_summary": "Showing {shown} of {count} dated scans; {invalid} invalid headers. "
                     "Direct items: {children} of {child_count}. {cap}",
    "trend_capped": "Period capped; full-period net change unavailable",
    "trend_invalid": "Invalid trend query: {reason}",
    "trend_reason_legacy": "Legacy scan rules unknown",
    "trend_reason_incomplete": "Incomplete scan",
    "trend_reason_incompatible": "Incompatible scan rules or root",
    "trend_reason_missing": "Folder missing",
    "trend_reason_corrupt": "Damaged scan body",
    "trend_chart_known": "{known} of {total} sizes known; gaps break the line",
    "trend_chart_unknown": "No comparable folder sizes",
    "trend_net_reason": "Period net change unknown: {reason}",
    "trend_reason_truncated": "Period capped",
    "trend_reason_insufficient": "Fewer than two observations",
    "trend_tab_sizes": "Folder sizes",
    "trend_tab_sources": "Direct contributors",
    "trend_tab_compare": "Full-root comparison",
    "history_compare": "Compare selected scan with current results",
    "history_reading": "Reading local scan history…",
    "history_hint": "The latest 1,000 retained full scans for this root. Stopped scans and branch rescans are "
                    "not saved. Incomplete scans describe known data only: missing folders do not prove deletion. "
                    "Totals count hard-link names separately; differences are metadata, not content verification.",
    "history_summary": "Showing {shown} of {count} scans; {invalid} invalid/unavailable metadata files",
    "history_failed": "Cannot read history: {reason}",
    "history_save_failed": "The scan completed, but history could not be saved: {reason}",
    "action_scan_workers": "Scan workers…",
    "action_scan_workers_tip": "Choose concurrency for new scans; higher is not always faster",
    "workers_prompt": "Workers for new scans (1–32). The default is {default}. Slow network shares may benefit "
                      "from more workers; excessive concurrency can overload a disk/server. Running scans retain "
                      "their existing workers. Real UNC performance depends on your share.",
    "action_auto_cpu": "Adjust scan threads to processor use",
    "action_auto_cpu_tip": "New scans read with fewer threads while other programs are using the processors, "
                           "and return to the chosen number when they are free",
    "action_mft_scan": "Read NTFS drives from the file table",
    "action_mft_scan_tip": "When FileTree runs as administrator and scans a folder on an NTFS drive, read the drive's "
                           "master file table instead of listing every folder; other scans list folders as before",
    "action_bins": "Recycle Bins…",
    "action_bins_tip": "Review bin totals and explicit scoped OS emptying",
    "bin_finder_empty": "Empty Finder Trash on all mounted volumes…",
    "bin_finder_all": "all mounted volumes (Finder-wide Trash)",
    "bin_finder_scopes": "Current-user Trash scopes:\n{scopes}\n\nMounted volumes:\n{roots}",
    "bin_finder_first": "Empty the current user's Finder Trash across ALL mounted volumes?\n\n{root}\n\n"
                        "Logical payload: {size}\nItems: {count}",
    "bin_finder_irreversible": "Permanently empty the current user's Finder Trash on ALL mounted volumes?\n\n"
                               "{root}\n\nLogical payload: {size}\nItems: {count}\n\nThis cannot be undone. Finder can "
                               "also remove items arriving during its operation. This affects every mounted bin, "
                               "regardless of the selected row. The OS operation cannot be canceled. Automation or "
                               "permission failures can leave partial results, and Finder may still be working.",
    "bin_preparing": "Reviewing exact Trash scopes on {root}…",
    "bin_no_approval": "No complete nonempty Trash approval; refresh and review again.",
    "bin_scope_first": "Empty these current-user Trash payload/receipt scopes?\n\n{root}\n\n"
                       "Logical payload: {size}\nItems: {count}",
    "bin_scope_irreversible": "Permanently remove the reviewed contents of these exact scopes?\n\n{root}\n\n"
                              "Logical payload: {size}\nItems: {count}\n\nThis cannot be undone. "
                              "Payload links are removed without following their targets. Changed entries are refused; "
                              "failures can leave partial results. Emptying cannot be canceled once started.",
    "bin_partial": "Removed {count} reviewed items; remaining failures: {reason}",
    "bin_empty": "Empty selected drive's Recycle Bin…",
    "bin_first": "Empty the Recycle Bin on {root}?\n\nReported size: {size}\nItems: {count}",
    "bin_irreversible": "Permanently remove all items currently in the Recycle Bin on {root}?\n\n"
                        "Reported size: {size}\nItems: {count}\n\nThis cannot be undone. New items arriving during "
                        "the OS operation may also be removed. The native operation cannot be canceled once started.",
    "bin_running": "Emptying the Recycle Bin on {root}; waiting for the OS operation…",
    "bin_failed": "Emptying did not complete: {reason}",
    "bin_hint": "Select one mounted volume. Windows empties its current-user OS bin; Linux inventories recognized "
                "files/info scopes. Two questions show exact scope and totals before permanent removal. "
                "Stop cancels surveys; active emptying must finish. macOS empties ALL mounted Finder Trash after "
                "global review (native validation pending). Capacity/bin "
                "values refresh afterwards; rescan to update the main tree.",
    "forecast_column": "Free-space forecast",
    "forecast_record": "Record used space for the forecast",
    "forecast_record_tip": (
        "Each time this overview opens, FileTree keeps the time and the used and total bytes of each drive in its "
        "local data folder: at most one sample per drive every {hours} hours and {count} per drive. Nothing about "
        "files is stored."
    ),
    "forecast_growing": "About {rate} per day — full around {date}",
    "forecast_not_soon": "About {rate} per day — not full within {years} years",
    "forecast_stable": "Not growing",
    "forecast_not_enough": "Not enough history yet (needs a few days)",
    "forecast_off": "Recording is off",
    "forecast_unknown": "Unknown (used space not reported)",
    "forecast_off_tip": "Turn on recording below to build a history of used space for this drive.",
    "forecast_unknown_tip": "The system did not report used space for this drive, so nothing was recorded.",
    "forecast_not_enough_tip": (
        "{count} samples over {days} days so far; a forecast needs at least {needed} samples over {needed_days} "
        "days. A sample is recorded when this overview opens, at most every few hours."
    ),
    "forecast_estimate_tip": (
        "An estimate from {count} samples over {days} days of used space (at most the last {window} days, since "
        "the total size last changed). It assumes the recent rate continues and is not a guarantee."
    ),
    "forecast_newer": "The free-space history was saved by a newer FileTree version; it is kept unchanged.",
    "forecast_save_failed": "The free-space history could not be saved: {reason}",
    "forecast_unavailable": "The free-space history is unavailable: the system reports no application data folder.",
    "action_volumes": "Drive overview…",
    "action_volumes_tip": "Inspect mounted volumes, capacity, allocation units and Recycle Bin totals",
    "volume_root": "Mounted root",
    "volume_name": "Volume name",
    "volume_fs": "Filesystem",
    "volume_total": "Total",
    "volume_used": "Used",
    "volume_free": "Available to you",
    "volume_cluster": "Allocation unit",
    "volume_trash": "Recycle Bin bytes",
    "volume_trash_count": "Bin items",
    "volume_reading": "Reading mounted volumes and Recycle Bin totals…",
    "volume_summary": "Showing {shown} mounted volumes out of {count}. Double-click to scan.",
    "volume_trash_partial": "Unknown total ({known} known)",
    "volume_hint": "OS capacity snapshot; available space may exclude reservations or quotas. "
                   "Repeated mounts can share capacity: do not sum rows. Windows allocation units are clusters; "
                   "POSIX units are filesystem fragments, not optimal transfer sizes. Trash shows OS-reported "
                   "Windows totals or known POSIX logical payload bytes, not reclaimable space; directory/receipt "
                   "metadata and shared allocation are excluded. Errors remain unknown. Stop waits for current OS "
                   "calls; canceled surveys are discarded. Ctrl+C copies rows. No emptying action is provided here.",
    "action_disks": "Physical disks…",
    "action_disks_tip": "See the physical drives, their health and partition layout (read-only)",
    "disks_title": "Physical disks",
    "disks_hint": "Read-only: FileTree shows what the system reports about each physical drive and changes nothing "
                  "on it. Serial numbers are not shown.",
    "disks_reading": "Reading physical disks…",
    "disks_summary": "Physical disks found: {count}.",
    "disks_none": "The system reported no physical disks.",
    "disks_problem_unsupported": "Physical disks cannot be listed on this system.",
    "disks_problem_tool_missing": "The system tool that lists disks was not found.",
    "disks_problem_timeout": "The system took too long to list the disks. Try Refresh.",
    "disks_problem_failed": "The system could not list the disks.",
    "disks_problem_malformed": "The system's list of disks could not be read.",
    "disks_refresh": "Refresh",
    "disks_select": "Select a disk to see its health and partitions.",
    "disks_col_disk": "Disk",
    "disks_col_model": "Model",
    "disks_col_media": "Type",
    "disks_col_bus": "Connection",
    "disks_col_style": "Partition table",
    "disks_col_size": "Size",
    "disks_col_health": "Health",
    "disks_col_number": "#",
    "disks_col_kind": "Partition type",
    "disks_col_label": "Label",
    "disks_col_mounts": "Drive letters / mount points",
    "disks_col_fs": "File system",
    "disks_col_offset": "Starts at",
    "disks_media_ssd": "SSD",
    "disks_media_hdd": "Hard disk (HDD)",
    "disks_media_unknown": "Unknown",
    "disks_unknown": "Unknown",
    "disks_state_healthy": "Healthy",
    "disks_state_warning": "Warning",
    "disks_state_unhealthy": "Failing",
    "disks_state_unknown": "Unknown",
    "disks_health_line": "Health: {state}. {meaning}",
    "disks_meaning_healthy": "The drive reports no problems. Keep backups anyway: drives can fail without warning.",
    "disks_meaning_warning": "The drive reports a problem. Back up important files soon and check the drive with "
                             "its maker's tool.",
    "disks_meaning_unhealthy": "The drive reports that it is failing. Back up important files now and plan to "
                               "replace it.",
    "disks_meaning_unknown": "The system does not report this drive's health, so FileTree cannot tell.",
    "disks_counters": "Temperature: {temperature} · Wear: {wear} · Powered on: {hours}",
    "disks_temperature_value": "{degrees} °C",
    "disks_wear_value": "{percent}% of rated life used",
    "disks_hours_value": "{hours} hours",
    "disks_not_reported": "not available",
    "disks_counters_denied": "Temperature, wear and power-on hours need administrator rights on this system. "
                             "Restart FileTree as administrator to see them; it does not ask for them here.",
    "disks_counters_missing": "This drive or its driver does not report temperature, wear or power-on hours.",
    "disks_counters_unsupported": "On this system, wear and power-on hours need administrator tools (such as "
                                  "smartctl), which FileTree does not run.",
    "disks_no_partitions": "No partitions were reported.",
    "disks_free_space": "Unallocated",
    "disks_bar_name": "Partition layout",
    "disks_tool_management": "Disk Management…",
    "disks_tool_optimize": "Optimize Drives…",
    "disks_tool_volumes": "Disks and volumes settings…",
    "disks_tool_storage": "Storage settings…",
    "action_export_report_html": "Scan report (HTML)…",
    "action_export_report_html_tip": "Save a self-contained report with three embedded chart images",
    "action_export_report_xlsx": "Scan report (Excel)…",
    "action_export_report_xlsx_tip": "Save the report lists on separate Excel worksheets",
    "html_filter": "HTML reports (*.html)",
    "xlsx_filter": "Excel workbooks (*.xlsx)",
    "report_title": "FileTree scan report",
    "report_note": "Known recorded scope only; allocation is an estimate. Counts in headings show displayed / total. "
                   "Top folders overlap: do not add their rows. Largest files and folders are limited to 1,000; "
                   "file types to 10,000. Sizes are bytes. Ages use recorded modification times, not last access; "
                   "unavailable dates belong to the oldest existing age group. HTML charts show the whole scan root "
                   "with bounded geometry. Excel text is escaped, control characters shown as hex, cells limited "
                   "to 32,767 characters and integers of 16 digits or more stored as exact text.",
    "report_bytes": "Logical bytes",
    "report_allocated": "Allocated bytes (estimate)",
    "report_created": "Report created",
    "report_reference": "Age reference",
    "report_skipped": "Skipped folders",
    "report_denied": "Unreadable folders",
    "report_pending": "Pending folders",
    "report_summary": "Summary",
    "report_notes": "Notes",
    "report_field": "Field",
    "report_value": "Value",
    "report_top_folders": "Largest folders (overlapping)",
    "report_categories": "Categories",
    "action_projects": "Projects and rebuildable data…",
    "action_projects_tip": "Inspect recorded project, Git and generated data sizes",
    "project_path": "Project / managed store",
    "project_kind": "Detected kind",
    "project_other": "Source / other",
    "project_git": ".git",
    "project_generated": "Rebuildable data",
    "project_coverage": "Coverage",
    "project_partial": "Incomplete",
    "project_recorded": "Recorded scope",
    "project_hint": "Known logical bytes only. Nested projects overlap. Git pointer files omit external metadata. "
                    "Generated data may contain custom files: review before moving. Maven, global Gradle and Docker "
                    "stores are shown separately; their contents are not presumed disposable.",
    "project_reading": "Inspecting recorded project data…",
    "project_summary": "Showing {shown} largest projects / stores out of {count} detected.",
    "project_review": "Review eligible rebuildable entries…",
    "project_review_count": "Review up to {shown} entries out of {count} eligible under the current age, coverage "
                            "and clean-up policy. Stopped scans cannot propose entries.",
    "project_git_kind": "Git",
    "project_python": "Python",
    "project_node": "Node.js",
    "project_rust": "Rust",
    "project_jvm": "JVM",
    "project_conda": "Conda project",
    "project_python_environment": "Python environment",
    "project_conda_environment": "Conda environment",
    "project_maven_store": "Maven store",
    "project_gradle_store": "Global Gradle store",
    "project_docker_store": "Docker data",
    "action_git_history": "Git history…",
    "action_git_history_tip": "Inspect the largest objects reachable from all Git references",
    "git_oid": "Object ID",
    "git_kind": "Object type",
    "git_length": "Uncompressed length",
    "git_type_blob": "File contents (blob)",
    "git_type_tree": "Directory listing (tree)",
    "git_type_commit": "Commit",
    "git_type_tag": "Annotated tag",
    "git_hint": ("Read-only Git plumbing inspects all refs, keeping the largest 1,000 objects. Sizes are "
                 "uncompressed lengths, not disk allocation or recoverable space. Names are omitted because "
                 "Git's object-name hints can be ambiguous. Ctrl+C copies object IDs/rows. Optional locks, "
                 "automatic maintenance and lazy network fetching are disabled; Git must support --no-lazy-fetch. "
                 "Repository ownership errors are not bypassed. Stop cancels; gc is never run here."),
    "git_reading": "Inspecting Git history…",
    "git_summary": "Showing {shown} of {count} reachable objects; uncompressed total {size}.",
    "git_gc_loose": ("Git gc may consolidate {count} loose objects, but these largest objects remain reachable "
                     "from refs and will not be removed. "
                     "Actual savings and other unreachable/reflog data are unknown."),
    "git_gc_packed": ("No loose objects to consolidate. Git gc will not remove these objects while refs retain "
                      "them; other unreachable/reflog data and actual savings were not measured."),
    "git_failed": "Git inspection failed: {reason}",
    "tree_filter_placeholder": "Filter expanded folders…",
    "tree_filter_hint": ("Match names (case-insensitive) only inside already expanded folders; ancestors stay visible. "
                         "Collapsed contents are not searched. Clear the filter to restore the tree. "
                         "Choosing a hidden entry in a chart/list clears the filter. "
                         "Scan totals and exports stay unchanged."),
    "action_live_compare": "Compare two folders…",
    "action_live_compare_tip": "Compare fresh relative paths and verify only requested file pairs",
    "compare_choose_left": "Choose the left folder",
    "compare_choose_right": "Choose the right folder",
    "compare_relative": "Relative path",
    "compare_state": "Comparison",
    "compare_left_size": "Left size",
    "compare_right_size": "Right size",
    "compare_left_time": "Left modified",
    "compare_right_time": "Right modified",
    "compare_roots": "Left: {left}\nRight: {right}",
    "compare_hint": ("Read-only: exact Unicode/case names are matched; links are not followed. Equal size/time "
                     "does not prove equal contents. Select file pairs and verify their full hashes with Stop "
                     "available; changed, unreadable and known cloud files remain unavailable. Results refer "
                     "to this scan/verification time. No copy, move or synchronization is performed. "
                     "Ctrl+C copies rows; CSV exports only the displayed rows, up to 10,000."),
    "compare_reading": "Scanning both folders…",
    "compare_error": "Comparison or export failed: {reason}",
    "compare_hashing": "Verifying selected file pairs…",
    "compare_verify": "Verify selected contents",
    "compare_summary": "Showing {shown} of {count} relative paths (limit 10,000).",
    "compare_incomplete": "Coverage is incomplete; missing paths in unreadable scopes remain unknown.",
    "compare_unavailable": "Unavailable or changed",
    "compare_link": "Link; contents not read",
    "compare_only_left": "Only on the left",
    "compare_only_right": "Only on the right",
    "compare_different_kind": "Different entry types",
    "compare_folder": "Folder on both sides",
    "compare_different_size": "Different sizes",
    "compare_different_time": "Different times; contents unchecked",
    "compare_unchecked": "Contents not verified",
    "compare_identical": "Matching full hashes",
    "compare_different_bytes": "Different contents",
    "problem_mount_boundary": "Mount boundary: contents not scanned",
    "action_special_files": "Cloud and special files…",
    "action_special_files_tip": "Inspect recorded recall, offline, compressed and sparse file states",
    "special_states": "Recorded state",
    "special_content_size": "Full content size",
    "special_recall": "May recall on access",
    "special_offline": "Offline",
    "special_compressed": "Compressed",
    "special_sparse": "Sparse",
    "special_allocation_low": "Lower allocation; cause unknown",
    "special_reading": "Reading recorded file metadata…",
    "special_hint": ("This list uses scan metadata only: no files are opened or downloaded. Recall/offline flags can "
                     "describe OneDrive, Dropbox or other providers; the provider and how much is already local cannot "
                     "be inferred. Full content size is the logical length, including online content; allocation after "
                     "downloading is unknown. Sparse holes, compression and resident data can reduce allocation. "
                     "Zero on disk for recall/offline entries is an estimate, not measured cloud allocation. "
                     "Double-click selects the scanned entry; Ctrl+C copies selected rows."),
    "special_summary": ("Showing {shown} of {count} matching files. Full content {size}; recorded allocation "
                        "{allocated}. Unavailable file metadata: {unknown}. Largest 1,000 are retained."),
    "special_partial": "Scan coverage is incomplete; unseen files remain unknown.",
    "action_shell_integration": "Explorer integration…",
    "action_shell_integration_tip": "Add or remove Scan with FileTree in your Explorer folder menu",
    "shell_enabled": "Add Scan with FileTree to Explorer's folder menu",
    "shell_scan": "Scan with FileTree",
    "shell_hint": ("Save changes only your account's folder menu; no administrator rights are needed. "
                   "On Windows 11, look under Show more options. Turn this off here to remove the entry. "
                   "Register again after moving the executable or source checkout. "
                   "A started Save finishes before closing."),
    "shell_failed": "Explorer integration could not be changed.\n{reason}",
    "menu_properties": "Properties",
    "properties_failed": "Windows could not open Properties for:\n{path}",
    "menu_theme": "Theme",
    "theme_system": "System",
    "theme_light": "Light",
    "theme_dark": "Dark",
    "menu_text_size": "&Text size",
    "text_size_larger": "&Larger",
    "text_size_smaller": "&Smaller",
    "text_size_reset": "S&ystem size",
    "text_size_percent": "{percent}%",
    "text_size_default": "{percent}% (system size)",

    "chart_access_keys": ("Arrow keys select rendered entries. Enter opens a folder; Backspace goes up. "
                          "Use the folder tree for grouped or hidden entries."),
    "chart_access_tree_keys": ("Up/Down selects cards; Right/Left expands/collapses folders. "
                               "Enter opens a folder; Backspace goes up."),
    "chart_access_folder": "Showing folder: {path}",
    "chart_access_selected": "Selected: {path}. Size {size}; on disk {allocated}; {files} files, {folders} folders.",

    "system_file_hibernate": ("Hibernation and Fast Startup state. Windows manages this file. An "
                              "administrator can disable hibernation with powercfg /hibernate off, which "
                              "also removes Hibernate and may affect Fast Startup. FileTree only opens "
                              "power settings."),
    "system_file_pagefile": ("Virtual memory backing file. Windows can manage its size automatically. "
                             "Review Virtual memory under Performance settings on the Advanced tab; "
                             "reducing it can affect applications and crash dumps."),
    "system_file_swapfile": ("Windows swap backing file, including suspended app data. Windows manages "
                             "it together with virtual memory. Review system memory settings instead of "
                             "removing it."),
    "system_file_old": ("Previous Windows installation. Review Previous Windows installation(s) in "
                        "Disk Cleanup → Clean up system files. Removing it prevents going back to th"
                        "at installation."),
    "system_file_recycle": ("Deleted entries still take disk space until the Recycle Bin is emptied. "
                            "Review the Recycle Bin or Storage Sense; emptying is permanent."),
    "system_file_restore": ("System metadata, restore points and shadow copies. Review System "
                            "Protection → Configure to set the restore-point limit. Backup-owned shadow "
                            "copies may need their own backup tools; unread bytes remain unknown."),
    "system_file_winsxs": ("Windows component store. Many entries share hard links with Windows files, "
                           "so per-name totals can overstate distinct storage. Use Windows Update "
                           "Cleanup in Disk Cleanup → Clean up system files; do not remove components m"
                           "anually."),
    "system_file_updates": ("Windows Update download data. Review Windows Update and temporary files "
                            "using Disk Cleanup → Clean up system files. Leave update services to manage"
                            " active downloads."),
    "system_file_delivery": ("Delivery Optimization download cache for Windows updates and apps. Review "
                             "Delivery Optimization Files in Disk Cleanup; Windows manages active "
                             "transfers."),
    "system_tool_power": "Open power settings…",
    "system_tool_memory": "Open advanced system settings…",
    "system_tool_cleanup": "Open Disk Cleanup…",
    "system_tool_storage": "Open Storage Sense…",
    "system_tool_restore": "Open System Protection…",
    "system_tool_failed": "The Windows tool could not be opened.",
    "trash_skip_system_managed": "Windows manages this entry; use its system tool in Details instead",

    "type_locations_title": "Containing folders (up to 1,000)",
    "type_location_size": "Matching size",
    "type_locations_tip": ("Totals include matching files directly in each folder; "
                           "subfolders are separate, without overlap."),

    "action_export_list": "Current list (CSV)…",
    "action_export_list_tip": "Save every row of the active list in its displayed filter and sort order",
    "list_changed": "The list changed during capture. Try exporting or copying again.",

    "details_title": "Details",
    "details_empty": "Select an entry to see its details",
    "details_live": "Distribution is available when scanning finishes.",
    "details_loading": "Calculating type and age distribution…",
    "details_recorded": ("Recorded file totals only; unread entries are outside these distributions. "
                         "Folder modification is the newest recorded date."),
    "details_bucket": "{label}: {size} · {count} files",

    "breadcrumbs_back": "Back (Alt+Left)",
    "breadcrumbs_forward": "Forward (Alt+Right)",
    "breadcrumbs_more": "…",
    "breadcrumbs_more_tip": "Show earlier ancestors",

    "action_print_view": "Print current view…",
    "action_print_view_tip": "Print the visible results on one page through the system print dialog",
    "action_export_view_pdf": "Current view (PDF)…",
    "action_export_view_pdf_tip": "Save the visible results on one fitted PDF page",
    "pdf_filter": "PDF document (*.pdf)",
    "view_pdf_exported": "Saved current view: {path}",
    "print_failed": "Could not print the view: {reason}",
    "print_submitted": "View submitted to the printer",
    "action_export_chart_png": "Chart on screen (PNG)…",
    "action_export_chart_png_tip": "Save the visible chart, including its current viewport",
    "action_export_chart_svg": "Bars or sunburst (SVG)…",
    "action_export_chart_svg_tip": "Save full bounded bars or rings as vector shapes and text",
    "png_filter": "PNG image (*.png)",
    "svg_filter": "SVG image (*.svg)",
    "graphic_exported": "Saved chart: {path}",
    "treemap_colours_age": "By modified age",
    "age_colour_unknown": "Date unknown",
    "age_colour_tip": ("Time since modification. "
                        "Folder colour uses its newest recorded modification; grey means no usable date. "
                        "Grouped tiles stay grey."),
    "action_gentle": "Gentle scanning",
    "action_gentle_tip": "Lower CPU and I/O priority for new scans; may take longer",
    "scan_priority_warning": "Scan notes: {reason}",
    "scan_pause": "Pause",
    "scan_resume": "Resume",
    "scan_pause_tip": "Pause new folder reads; current reads finish. Stop works while paused.",
    "scan_paused": "Paused — {progress}",
    "scan_analysing": "Folder reads finished; analysing results…",
    "column_drive_share": "% of drive",
    "columns_reset": "Reset columns",
    "drive_share_tip": ("Logical bytes divided by total volume capacity. Hard-link names count separately; "
                        "this is not allocated or recoverable space. Unknown while capacity is unavailable or stale."),
    "action_recent_actions": "Recent actions…",
    "action_recent_actions_tip": "Inspect retained operation metadata and export a redacted audit report",
    "journal_time": "Time (UTC)",
    "journal_source": "Original path",
    "journal_identity": "Device / file identity",
    "journal_result": "Result",
    "journal_detail": "Detail",
    "journal_destination": "Trash destination",
    "journal_reason_duplicates": "Explicit duplicate decision",
    "journal_status_approved": "Unknown outcome (approved only)",
    "journal_status_moved": "Moved to Trash",
    "journal_status_skipped": "Skipped",
    "journal_status_failed": "Platform move failed",
    "journal_reading": "Reading retained actions…",
    "journal_hint": ("Latest 500 actions; metadata only, retained for 90 days / 50 MB. An approved-only event "
                     "has an unknown final outcome. A recorded Trash path does not guarantee restoration."),
    "journal_summary": "{count} actions shown; {invalid} damaged records and {unavailable} unavailable segments.",
    "journal_read_failed": "The operation journal could not be read: {reason}",
    "journal_write_failed": ("Journal writing or retention failed. Remaining moves were stopped where possible; "
                             "recent actions may be incomplete.\n\n{reason}"),
    "trash_skip_journal": "the approved action could not be recorded; nothing was moved",
    "journal_export": "Export redacted CSV…",
    "journal_exported": "Audit report saved with home-directory prefixes redacted.",
    "duplicate_folder_match": "{copy} = {original} ({size}, {files} files; matching search snapshot)",
    "duplicate_folder_tip": ("Matching names, sizes, verified hashes and empty-folder structure. "
                             "Read-only; not a clean-up approval."),
    "duplicates_keep_selected": "Keep selected copy",
    "duplicates_kept_name": "Kept: {name}",
    "duplicates_kept_path": "Kept copy: {path}.",
    "duplicates_choose_keeper": "Choose a kept copy in this group before selecting extras.",
    "duplicates_group_blocked": "Group left untouched; rescan required: {reason}",
    "trash_skip_duplicate_choose": "choose the kept copy, then review the group again",
    "trash_skip_duplicate_keep": "the kept copy was selected; the group was left untouched; rescan",
    "trash_skip_duplicate_unverified": "no verified hash for this group; rescan and search again",
    "trash_skip_duplicate_hard_links": "a copy has hard-link aliases; the group was left untouched; rescan",
    "trash_skip_duplicate_content": "group contents changed or could not be rehashed; rescan and search again",
    "menu_options": "Options",
    "action_cleanup_policy": "Clean-up policy…",
    "action_cleanup_policy_tip": "Enable rules, change minimum ages and exclude paths from clean-up suggestions",
    "policy_enabled": "Enabled",
    "policy_age": "Minimum age (days)",
    "policy_age_for": "Minimum age for {rule}",
    "policy_enabled_for": "Enable {rule}",
    "policy_hint": "Policy changes affect suggestions only. Manual-risk rules remain unchecked. Preview before saving.",
    "policy_exclusions": ("Never propose these paths or names (one per line; paths must be absolute). "
                          "Scanning is unchanged."),
    "policy_preview": "Preview changes",
    "policy_import": "Import policy JSON…",
    "policy_preview_needed": "Preview the current settings before saving.",
    "policy_preview_running": "Comparing candidate counts and logical sizes…",
    "policy_preview_result": ("Adds {added} candidates ({size}); removes {removed} candidates "
                              "({removed_size}). Nothing moved."),
    "policy_preview_partial": "The scan is incomplete; unseen candidates and bytes remain unknown.",
    "policy_no_scan": "No completed scan: effects cannot be measured. These settings apply to future proposals.",
    "policy_invalid": ("Invalid policy. Use supported rule keys, yes/no flags, ages 0–36500 "
                       "and absolute paths or name patterns."),
    "policy_saved": "Clean-up policy saved; suggestions are being refreshed.",
    "policy_saved_invalid": ("Saved clean-up policy is invalid. Suggestions are disabled until "
                             "the policy is reviewed in Options."),
    "cleanup_review_manual": "Review manually",
    "cleanup_evidence": ("Category: {category}; minimum age: {days} days; risk: {risk}. "
                         "Evidence: {evidence} Rebuild / consequence: {rebuild}"),
    "cleanup_category_temporary": "temporary files",
    "cleanup_category_cache": "downloaded / generated cache",
    "cleanup_category_application_state": "application state",
    "cleanup_category_build": "project build output",
    "cleanup_category_downloads": "user downloads",
    "cleanup_risk_low": "lower risk; verify before moving",
    "cleanup_risk_manual": "manual review; starts unchecked",
    "cleanup_rebuild_temp": "Close the owning application; temporary data cannot necessarily be recreated.",
    "cleanup_rebuild_browser_cache": ("Close the browser; it downloads cached pages again. "
                                      "Profiles and bookmarks are excluded."),
    "cleanup_rebuild_thumbnails": "Close the file manager; previews are generated again when needed.",
    "cleanup_rebuild_crash_dumps": "Keep needed crash evidence; a past crash dump cannot be recreated.",
    "cleanup_rebuild_package_caches": ("Use the package manager to download again; confirm network access. "
                                      "Package stores are excluded."),
    "cleanup_rebuild_build_output": ("Verify project contents and dependency locks, then rebuild using the "
                                    "project's documented commands. Keep authored files."),
    "cleanup_rebuild_old_installers": ("Keep offline or unavailable installers; download from the publisher "
                                      "if still available."),
    "cleanup_rebuild_empty_folders": "Empty folders may still be expected by applications; verify their purpose first.",
    "trash_holder": "{name} (PID {pid})",
    "trash_holders": "{path}: observed open in {programs}. Close the relevant program yourself and retry.",
    "trash_holders_limited": "{path}: process visibility is limited; other holders or causes may be unknown.",
    "duplicates_savings": ("Unique allocated estimate {allocated}; recoverable file data after emptying Trash "
                           "{recoverable}."),
    "duplicates_estimating": ('Estimating unique allocation and recover'
        'able file data…'),
    "duplicates_estimate_unavailable": ('Allocation estimate unavailable. Run the'
        ' search again before selecting extras.'),
    "duplicates_estimate_assumption": ("Estimates use your explicit kept-copy choices; undecided groups are unknown. "
                                      "Each group is checked and fully rehashed before moving. Hard-link aliases "
                                      "block a decision. Shared extents and directory metadata remain unknown; "
                                      "moving to Trash does not free space."),
    'capacity_details': 'Capacity details',
    'capacity_summary': 'OS used {used}; free {free}; unique allocated estimate {unique}. {status}',
    'capacity_estimated': 'Whole-volume estimate; unaccounted space is shown in Details.',
    'capacity_folder_only': 'Folder scan: cannot reconcile the volume.',
    'capacity_incomplete': 'Incomplete scan: cannot reconcile the volume.',
    'capacity_identity_unknown': 'Missing file identities: cannot reconcile the volume.',
    'capacity_capacity_unavailable': 'OS capacity is unavailable; cannot reconcile the volume.',
    'capacity_root_changed': 'Scanned root changed; rescan before reconciling.',
    'capacity_allocation_exceeds_used': 'Allocated estimate exceeds OS used space; cannot reconcile.',
    'capacity_coverage': 'Skipped {skipped}; unreadable {inaccessible}; pending {pending}',
    'capacity_bin_partial': 'The Recycle Bin was not fully identified or read; its shown amount is only data seen.',
    "capacity_explanation": ('Known file allocation includes the Recycle'
                             ' Bin data seen. Hard-link names count once'
                             '. Other mounted volumes are excluded. Omit'
                             'ted data and filesystem metadata are unkno'
                             'wn, not zero. Unaccounted may include inac'
                             'cessible data, metadata, snapshots, shared'
                             ' extents and allocation estimates. OS capa'
                             'city and files are measured at different i'
                             'nstants; the filesystem can change during '
                             'scanning. Unavailable free space is the di'
                             'fference between reported total, used and '
                             'available free, not a measured metadata to'
                             'tal. These are estimates pending NTFS, ext'
                             '4 and APFS volume validation.'),
    'capacity_row_total': 'OS total',
    'capacity_row_used': 'OS used',
    'capacity_row_free': 'OS available free',
    'capacity_row_unavailable_free': 'Unavailable free space',
    'capacity_row_named_allocated': 'Named allocated estimate',
    'capacity_row_unique_allocated': 'Unique allocated estimate',
    'capacity_row_hard_link_overcount': 'Hard-link overcount removed',
    'capacity_row_recycle_bin_seen': 'Recycle Bin allocation seen (included)',
    'capacity_row_foreign_allocated_seen': 'Other-volume file allocation seen (excluded)',
    'capacity_row_unaccounted': 'Unaccounted',
    'capacity_row_metadata_bytes': 'Filesystem metadata / reserved',
    'capacity_row_omitted_bytes': 'Omitted data',
    'capacity_row_other_volumes_bytes': 'Other mounted volumes',
    'capacity_row_mounts': 'Different-device mount boundaries',
    'capacity_row_coverage': 'Coverage',
    "review_title": "Review clean-up proposals",
    'review_logical_size': 'Logical size',
    'review_risk': 'Risk',
    'review_risk_low': 'Lower risk',
    'review_risk_manual': 'Review manually',
    'review_details_label': 'Entry details',
    'review_scope': 'Scan scope',
    'review_details': (
        '{path}\n'
        'Rule: {rule}\n'
        'Modified: {modified}\n'
        'Logical size: {logical}; allocated estimate: {allocated}\n'
        'Risk: {risk}\n'
        'Protection: {protection}\n'
        '\n'
        '{consequence}'
    ),
    "review_hint": "Review every path and consequence. Uncheck entries to keep them; Continue opens the confirmations.",
    "review_select": "Move",
    "review_rule": "Rule",
    "review_reason": "Reason",
    "review_protection": "Protection",
    "review_consequence": "Consequence",
    "review_manual": "Manual selection",
    "review_manual_reason": "User-selected entry; removing it may affect files or programs that depend on it.",
    "review_not_protected": "No protected-path match",
    "review_open_folder": "Open containing folder",
    "review_continue": "Continue to confirmation",
    "review_estimating": "{count} entries selected; estimating allocation…",
    "review_summary": ("{count} entries; logical {logical}; allocated estimate {allocated}; recoverable file data "
                       "after emptying the Recycle Bin: {recoverable}; free now {free}. "
                       "Shared extents and directory metadata remain unknown. Moving to Trash does not free space."),
    "size_unknown": "unknown",
    "trash_running": "Revalidating and moving approved entries… Stop cancels remaining entries.",
    "trash_batch_done": "Moved {moved}, skipped {skipped}, failed {failed}; {size} moved to the Recycle Bin.",
    "trash_skipped": "These entries were skipped. Rescan their folders before trying again:\n{names}",
    "trash_skip_outside": "outside the current scan",
    "trash_skip_unverified": "no verified scan identity",
    "trash_skip_incomplete": "incomplete scan coverage",
    "trash_skip_missing": "entry or parent is missing",
    "trash_skip_unreadable": "entry cannot be read",
    "trash_skip_link": "entry or parent became a link",
    "trash_skip_kind": "entry kind changed",
    "trash_skip_identity": "entry was replaced",
    "trash_skip_changed": "size, timestamps or folder contents changed",
    "trash_skip_protected": "resolved path has different protection",
    "trash_skip_cancelled": "operation cancelled",
    "coverage_complete": ("Coverage: {size} known in {known} folders; skipped {skipped}, "
                          "inaccessible {denied}, pending {pending}."),
    "coverage_partial": ("Incomplete coverage: {size} known in {known} folders; skipped {skipped}, inaccessible "
                         "{denied}, pending {pending}. Omitted bytes are unknown. "
                         "Rescan incomplete branches before cleanup; "
                         "Select all is disabled."),
    "problem_hidden_omitted": "Hidden entries were omitted; their size is unknown.",
    "problem_partial_folder": "Some entries could not be read; this folder is incomplete.",
    "app_title": "FileTree",
    "about_text": "<h3>FileTree {version}</h3><p>See where your disk space goes.</p>"
                  "<p>MIT License · © 2026 JE-Chen</p>",
    # menus and actions
    "menu_file": "&File",
    "menu_export": "&Export",
    "menu_view": "&View",
    "menu_unit": "Size &unit",
    "menu_language": "&Language",
    "menu_help": "&Help",
    "action_open": "Choose folder…",
    "action_open_tip": "Pick a folder or drive to scan",
    "action_rescan": "Rescan",
    "action_rescan_tip": "Scan the same folder again to pick up changes",
    "action_stop": "Stop",
    "action_stop_tip": "Stop the scan that is running",
    "action_export_folders": "Folder list (CSV)…",
    "action_export_folders_tip": "Save every folder with its size, for Excel or other spreadsheets",
    "action_export_largest": "Largest files (CSV)…",
    "action_export_largest_tip": "Save the list of the largest files",
    "action_export_json": "Folder tree (JSON)…",
    "action_export_json_tip": "Save the folder tree for scripts and other programs",
    "action_trash": "Move to Recycle Bin",
    "action_trash_tip": "Move the selected files and folders to the Recycle Bin (you are asked first)",
    "action_find": "Find…",
    "action_find_tip": "Find files and folders by name anywhere in the scan",
    "action_quit": "Quit",
    "action_quit_tip": "Close FileTree",
    "action_hidden": "Include hidden files",
    "action_exclusions": "Skip while scanning…",
    "action_exclusions_tip": "Folders and folder names that scans leave out, such as node_modules",
    "exclusions_title": "Skip while scanning",
    "exclusions_hint": ("Scans leave these folders out: they are listed, greyed out, with size 0. A name such as "
                        "node_modules or *.cache skips every folder of that name; a folder path skips that one "
                        "folder. The list applies from the next scan."),
    "exclusions_add_name": "Add a name…",
    "exclusions_add_folder": "Add a folder…",
    "exclusions_remove": "Remove",
    "exclusions_name_prompt": "Folder name, * and ? allowed:",
    "exclusions_saved": "{count} exclusions saved; they apply from the next scan.",
    "tooltip_excluded": "{path}\nSkipped: it is in View → Skip while scanning",
    "action_hidden_tip": "Count hidden files and folders (applies to the next scan)",
    "action_help": "How to use",
    "action_help_tip": "Short guide to FileTree",
    "action_about": "About FileTree",
    "action_about_tip": "Version and license",
    "app_title_admin": "FileTree (Administrator)",
    "action_elevate": "Restart as administrator",
    "action_elevate_tip": "Start FileTree again with administrator rights, so it can read every folder",
    "action_ask_admin": "Ask for administrator rights at start",
    "action_ask_admin_tip": "Windows asks for permission when FileTree starts, so protected folders can be read too",
    "problems_hint": "Some folders need administrator rights. Restart FileTree as administrator to read them too.",
    "elevate_declined": "FileTree is still running without administrator rights.",
    "startup_invalid": "Could not restore the requested workspace: {reason}",
    "elevate_waiting": "Complete or dismiss the Windows permission prompt. Closing this window waits for that request.",
    "elevate_failed": "FileTree could not restart as administrator: {reason}",
    "unit_auto": "Automatic",
    "path_placeholder": "Type or paste a folder path and press Enter",
    "choose_folder_title": "Choose a folder to scan",
    # welcome page
    "welcome_title": "See where your disk space goes",
    "welcome_subtitle": "Pick a folder or a whole drive. FileTree adds up every file inside it and shows "
                        "you the biggest folders and files first.",
    "welcome_choose": "Choose a folder…",
    "welcome_drives": "Drives",
    "welcome_drive_tip": "Scan {path}",
    "welcome_drive_free": "{free} free of {total}",
    "welcome_drive_used": "{percent} used",
    "welcome_recent": "Recently scanned",
    "welcome_tip": "Tip: you can also drag a folder from your file manager onto this window. Paste an absolute "
                   "UNC share path on Windows (\\\\server\\share); access uses your current account. Scan workers "
                   "can be adjusted in Options. Denied/disconnected branches remain incomplete, not empty.",
    # scanning
    "scan_starting": "Starting…",
    "scan_progress": "Scanning… {files} files in {folders} folders · {size} · {time}",
    "scan_stop": "Stop",
    "scan_stopping": "Stopping…",
    "scan_cancelled": "Scan stopped.",
    "scan_stopped_partial": "Scan stopped: the results show what was read so far.",
    "scan_failed_title": "Cannot scan",
    "scan_mount_changed": "Mount boundaries changed or could not be verified. Scan again before using these results.",
    "scan_failed": "FileTree could not read {path}.\n\nReason: {reason}",
    "not_a_folder": "{path} is not a folder that exists.",
    "duration_seconds": "{value} s",
    "duration_minutes": "{minutes} min {seconds} s",
    # results
    "summary": "<b>{path}</b> — {size} ({allocated} on disk) in {files} files and {folders} folders "
               "(scanned in {time})",
    "summary_live": "<b>{path}</b> — {size} ({allocated} on disk) in {files} files and {folders} folders so far",
    "summary_partial": "<b>{path}</b> — {size} ({allocated} on disk) in {files} files and {folders} folders · "
                       "<b>incomplete</b>: the scan was stopped after {time}",
    "tab_chart": "Chart",
    "chart_treemap": "Treemap",
    "treemap_levels": "Levels",
    "treemap_levels_all": "All",
    "treemap_colours": "Colours",
    "treemap_colours_type": "By file type",
    "treemap_colours_folder": "By folder",
    "chart_treemap_tip": "Every file as a rectangle sized by the space it takes",
    "chart_bars": "Bars",
    "chart_sunburst": "Sunburst",
    "chart_tree": "Tree",
    "chart_tree_tip": "Folder hierarchy: expand branches, Ctrl+wheel to zoom, double-click to focus",
    "tree_orientation": "Direction",
    "tree_orientation_horizontal": "Left to right",
    "tree_orientation_vertical": "Top to bottom",
    "tree_more": "{count} more folders · {size}",
    "tree_unavailable": "Not scanned",
    "chart_sunburst_tip": "The folder in the centre, each deeper level a ring; click the centre to go up",
    "chart_bars_tip": "One bar per entry of the folder, largest first, with its size and share",
    "bars_empty_folder": "This folder is empty.",
    "bars_more": "{count} more: {size}",
    "tab_largest": "Largest files",
    "scope_folder": "Selected folder only",
    "scope_folder_named": "Only in {name}",
    "scope_folder_tip": ("Show the largest files, types and ages of the folder selected in the tree instead of "
                         "the whole scan"),
    "tab_search": "Search",
    "tab_changes": "Changes",
    "action_compare": "Compare with a saved scan…",
    "action_compare_tip": "Open a scan saved with Export → Folder tree (JSON) and see what grew since",
    "compare_title": "Compare with a saved scan",
    "compare_failed": "This file is not a scan saved by FileTree:\n{reason}",
    "column_before": "Before",
    "column_now": "Now",
    "column_change": "Change",
    "changes_new": "new",
    "changes_gone": "gone",
    "changes_whole_scan": "(the scanned folder)",
    "changes_stop": "Stop comparing",
    "changes_running": "Comparing…",
    "changes_waiting": "The comparison follows when the scan is done.",
    "changes_unknown_time": "at an unknown time",
    "changes_summary": ("Compared with {path}, saved {when}: {before} then, {now} now ({change}); "
                        "{count} folders changed."),
    "tab_duplicates": "Duplicates",
    "tab_cleanup": "Clean up",
    "cleanup_suggestions": "Suggestions",
    "cleanup_select_all": "Select all",
    "cleanup_select_group": "Select this group",
    "cleanup_running": "Looking for things to clean up…",
    "cleanup_hint": "Places whose contents can usually go appear here after a scan.",
    "cleanup_none": "Nothing to suggest in this scan.",
    "cleanup_summary": ("{size} logical size in {groups} groups. Select entries to review paths and allocation "
                        "before moving to the Recycle Bin; moving does not free space immediately."),
    "cleanup_group": "{title} — {size} ({count})",
    "cleanup_temp": "Temporary files",
    "cleanup_temp_tip": "Files programs left behind for a while; a program that is still running may need some.",
    "cleanup_browser_cache": "Browser caches",
    "cleanup_browser_cache_tip": "Copies of web pages and pictures; browsers download them again as needed.",
    "cleanup_thumbnails": "Thumbnail caches",
    "cleanup_thumbnails_tip": "Small previews of pictures; they are made again when folders are opened.",
    "cleanup_crash_dumps": "Crash dumps",
    "cleanup_crash_dumps_tip": "Memory saved when a program crashed, only useful to report the crash.",
    "cleanup_package_caches": "Package download caches (pip, npm…)",
    "cleanup_package_caches_tip": ("Downloaded packages kept for the next install; they are downloaded again when "
                                   "needed."),
    "cleanup_build_output": "Build output (can be rebuilt)",
    "cleanup_build_output_tip": ("Installed dependencies and compiled files of projects; building the project again "
                                 "recreates them."),
    "cleanup_old_installers": "Installers in Downloads",
    "cleanup_old_installers_tip": ("Setup files that were most likely run long ago; keep the ones you install from "
                                   "again."),
    "cleanup_empty_folders": "Empty folders",
    "cleanup_empty_folders_tip": "Folders with nothing in them, or only other empty folders.",
    "duplicates_min_size": "Compare files from",
    "duplicates_any_size": "any size",
    "duplicates_find": "Find duplicates",
    "duplicates_stop": "Stop",
    "duplicates_select_extra": "Select extra copies",
    "duplicates_select_extra_tip": ("Select extras in groups with a chosen keeper and successful checks; "
                                    "then press Delete"),
    "duplicates_hint": ("Finds files with the same content anywhere in the scan. Only files of the same size are "
                        "read, but reading takes time, so small files are left out unless you choose a smaller size."),
    "duplicates_starting": "Looking for files of the same size…",
    "duplicates_running": "Read {files} of {total} files ({read} of {bytes})…",
    "duplicates_stopped": "The search was stopped.",
    "duplicates_none": "No duplicate files found.",
    "duplicates_summary": ('{groups} groups of duplicates: {extra} l'
        'ogical size in extra copies.'),
    "duplicates_limited": "The {shown} groups with the most extra space are listed.",
    "duplicates_skipped": "{count} files could not be read.",
    "duplicates_group": ('{count} copies × {size}: {extra} logical'
        ' extra-copy size.'),
    "search_placeholder": "Part of a name, or a pattern: backup, *.mp4, *.iso;*.zip",
    "search_hint": ("Type part of a name or a pattern with * and ?, choose conditions, or both, to find files "
                    "and folders anywhere in the scan."),
    "search_running": "Searching…",
    'search_larger': 'At least (inclusive)',
    'search_smaller': 'At most (inclusive)',
    'search_custom_ranges': 'Custom ranges…',
    'search_changed_custom': 'custom dates',
    'search_exact_bytes': '{value} B (exact)',
    'search_date_format': 'YYYY-MM-DD',
    'search_date_start': 'From date (inclusive)',
    'search_date_through': 'Through date (inclusive)',
    'search_range_hint': ('Leave either bound blank for no limit. Sizes use'
        ' exact bytes; dates use local time (YYYY-MM-DD).'),
    'search_range_size_error': ('Enter a nonnegative size in whole bytes, up to 9223'
        '372036854775807 B. Fractional bytes are not allowed.'),
    'search_range_order_error': ('The minimum size must '
        'not exceed the maximum.'),
    'search_range_date_error': ('Enter valid local dates as YYYY-MM-DD,'
        ' with the start no later than the end.'),
    'search_range_invalid': ('Invalid search ranges. Correct the size o'
        'r date bounds before searching or saving.'),
    "search_no_limit": "no limit",
    "search_changed": "Changed",
    "search_changed_any": "any time",
    "search_changed_week": "in the last week",
    "search_changed_month": "in the last month",
    "search_changed_year": "in the last year",
    "search_changed_stale_year": "not for a year",
    "search_changed_stale_2y": "not for 2 years",
    "search_changed_stale_5y": "not for 5 years",
    "search_type": "Type",
    "search_type_any": "any type",
    "search_show": "Show",
    "search_kind_any": "files and folders",
    "search_kind_files": "files only",
    "search_kind_folders": "folders only",
    "search_saved": "Saved searches",
    "search_saved_none": "(none)",
    "search_save": "Save…",
    "search_delete": "Delete",
    "search_save_title": "Save this search",
    "search_save_prompt": "Name:",
    "search_none": "Nothing matches.",
    "problems_none": "Every entry in this scan was read; nothing to review.",
    "largest_none": "No files to list.",
    "search_summary": "{count} matches, {size} in total.",
    "search_limited": "The {shown} largest are listed.",
    "tab_types": "File types",
    "tab_age": "Age",
    "column_age": "Last changed",
    "age_month": "Within a month",
    "age_half_year": "1–6 months ago",
    "age_year": "6–12 months ago",
    "age_two_years": "1–2 years ago",
    "age_older": "Over 2 years ago",
    "largest_focus": "Showing only: {what}",
    "largest_show_all": "Show all",
    "list_files_tip": "Double-click a row to list its largest files",
    "tab_problems": "Problems",
    "tab_problems_count": "Problems ({count})",
    "column_name": "Name",
    "column_size": "Size",
    "column_allocated": "On disk",
    "column_share": "% of parent",
    "column_share_total": "% of total",
    "column_files": "Files",
    "column_folders": "Folders",
    "column_modified": "Modified",
    "column_folder": "Folder",
    "column_extension": "Extension",
    "column_type": "Type",
    "column_path": "Path",
    "column_problem": "Problem",
    "problem_access_denied": "Access denied",
    "problem_not_found": "No longer there",
    "problem_path_too_long": "Path too long",
    "problem_not_scanned": "Not scanned: the scan was stopped first",
    "no_extension": "(no extension)",
    "tooltip_unreadable": "{path}\nCould not be read: {reason}",
    "tooltip_link": "{path}\nLink: shown but not followed",
    "tooltip_not_scanned": "{path}\nNot scanned: the scan was stopped first",
    "treemap_empty": "Nothing to show",
    "treemap_up": "↑ Up",
    "treemap_up_tip": "Show the folder above",
    "treemap_tooltip": "<b>{name}</b><br>{size} ({share} of this view)<br>{path}",
    "treemap_more": "{count} more",
    "treemap_more_tooltip": "<b>{count} smaller entries</b> of {name}, each too small to draw<br>"
                            "{size} ({share} of this view)",
    "treemap_more_open": "Double-click to show this folder on its own",
    "largest_filter": "Filter by name or folder…",
    "types_all": "All types",
    "category_images": "Pictures",
    "category_video": "Videos",
    "category_audio": "Music and audio",
    "category_documents": "Documents",
    "category_archives": "Archives and disk images",
    "category_code": "Code and data",
    "category_programs": "Programs",
    "category_other": "Other",
    "status_selected": "{name}: {size} ({share} of its folder)",
    "status_selected_root": "{name}: {size}",
    # entry menu
    "menu_open_item": "Open",
    "menu_reveal": "Show in file manager",
    "menu_copy_path": "Copy path",
    "menu_show_chart": "Show in chart",
    "menu_scan_here": "Scan this folder",
    "menu_rescan_here": "Rescan this folder",
    "rescan_done": "Rescanned {name}: {before} → {after}",
    "refresh_notice": "Files changed in {count} scanned folder(s) after this scan, so the sizes shown there "
                      "may be out of date. FileTree does not scan again unless you ask.",
    "refresh_now": "Rescan changed folders",
    "refresh_now_tip": "Read only the folders that changed and update the results",
    "trash_confirm_title": "Move to Recycle Bin",
    "protected_title": "System or program folder",
    "protected_question": ("{count} of the entries are system or program folders. Moving them can make the "
                           "system or programs stop working:\n\n{names}\n\nMove them anyway?"),
    "protected_system": "part of the operating system",
    "protected_programs": "installed programs",
    "protected_settings": "programs' settings and data",
    "protected_profile": "a user's profile folder",
    "trash_confirm": "Move “{name}” ({size}) to the Recycle Bin?\n\nYou can restore it from there.",
    "trash_failed": "“{name}” could not be moved to the Recycle Bin. It may be in use or read-only.",
    "trash_done": "Moved “{name}” to the Recycle Bin: {size} freed.",
    "action_trash_many": "Move {count} items to Recycle Bin",
    "trash_confirm_many": ("Move these {count} items ({size} in total) to the Recycle Bin?\n\n{names}\n\n"
                           "You can restore them from there."),
    "trash_more": "…and {count} more",
    "trash_failed_many": ("{count} items could not be moved to the Recycle Bin. "
                          "They may be in use or read-only:\n\n{names}"),
    "trash_done_many": "Moved {count} items to the Recycle Bin: {size} freed.",
    "permanent_delete": "Delete permanently",
    "permanent_delete_tip": ("Delete the selected files and folders permanently, without the Recycle Bin "
                             "(you are asked first; it cannot be undone)"),
    "permanent_menu_many": "Delete {count} items permanently",
    "permanent_not_suggestions": ("Delete permanently works on entries you pick in the folder tree, the largest "
                                  "files or search results, not on Clean up or duplicate suggestions."),
    "permanent_title": "Delete permanently",
    "permanent_confirm": ("Permanently delete “{name}” ({size})?\n\n{path}\n\n"
                          "It does not go to the Recycle Bin. This cannot be undone."),
    "permanent_confirm_many": ("Permanently delete these {count} items ({size} in total)?\n\n{names}\n\n"
                               "They do not go to the Recycle Bin. This cannot be undone."),
    "permanent_confirm_folders": ("Folders are deleted with what the scan recorded inside them. "
                                  "Anything added or changed since the scan is left in place."),
    "permanent_protected_question": ("{count} of the entries are system or program folders. Deleting them "
                                     "permanently can make the system or programs stop working:\n\n{names}\n\n"
                                     "Delete them anyway?"),
    "permanent_managed": ("Windows manages these entries, so FileTree does not delete them. "
                          "Use the system tool shown in Details instead:\n\n{names}"),
    "permanent_running": "Deleting permanently… {count} entries removed. Press Esc to stop.",
    "permanent_done": "Permanently deleted {removed} entries ({size}). Left in place: {refused}; failed: {failed}.",
    "permanent_report_title": "Delete permanently: entries left in place",
    "permanent_failed": "The system did not delete it: {reason}",
    "permanent_pending": "Deletion is pending: another program still has it open",
    "permanent_journal_reason": "Explicit permanent deletion",
    "permanent_journal_deleted": "Permanently deleted",
    "permanent_journal_partial": "Partly deleted (folder kept)",
    "permanent_skip_outside": "outside the current scan; not deleted",
    "permanent_skip_unverified": "no verified scan identity; not deleted",
    "permanent_skip_incomplete": "the scan could not read all of this folder; not entered",
    "permanent_skip_missing": "the entry or its folder is missing",
    "permanent_skip_unreadable": "the entry cannot be read; not deleted",
    "permanent_skip_link": "the entry or a folder above it became a link; not deleted",
    "permanent_skip_kind": "the entry's kind changed; not deleted",
    "permanent_skip_identity": "the entry was replaced since the scan; not deleted",
    "permanent_skip_changed": "size or timestamps changed since the scan; not deleted",
    "permanent_skip_protected": "a system or program folder your approval did not cover; not deleted",
    "permanent_skip_system_managed": "Windows manages this entry; not deleted",
    "permanent_skip_cancelled": "stopped before this entry; not deleted",
    "permanent_skip_journal": "the approved action could not be recorded; nothing was deleted",
    "permanent_skip_read_only": "read-only; FileTree does not clear the attribute, so it was not deleted",
    "permanent_skip_mount_point": "a mounted volume or mount point; not deleted",
    "permanent_skip_other_volume": "on another volume; not deleted",
    "permanent_skip_arrived": "added after the scan; left in place",
    "permanent_skip_not_empty": "folder kept: something inside it was left in place",
    "permanent_skip_failed": "the system refused to delete something inside it",
    "status_selected_many": "{count} items selected: {size}",
    # export
    "export_title": "Export",
    "export_running": "Saving to {path}…",
    "csv_filter": "CSV files (*.csv)",
    "json_filter": "JSON files (*.json)",
    "export_done": "Saved {count} rows to {path}",
    "export_failed": "The file could not be saved.\n\nReason: {reason}",
    # help
    "help_title": "How to use FileTree",
    "help_html": HELP,
    "budget_close": "Close",
    "action_folder_budgets": "Folder budgets…", "action_folder_budgets_tip": "Manage folder limits and dated usage",
    "budget_title": "Folder budgets", "budget_name": "Name", "budget_path": "Folder path",
    "budget_limit": "Limit", "budget_usage": "Last usage", "budget_excess": "Excess",
    "budget_status": "Status", "budget_add": "Add", "budget_update": "Update", "budget_delete": "Delete",
    "budget_new": "New", "budget_waiting": "Waiting for full scan", "budget_unknown": "Unknown",
    "budget_over": "Over limit", "budget_within": "Within limit", "budget_alerted": "{status}, reminder recorded",
    "budget_dated_usage": "{usage} at {when}", "budget_invalid_limit": "Enter an exact byte limit",
    "budget_summary": "Budgets: {over} over, {unknown} unknown",
    "budget_save_error": "Folder budgets could not be saved: {reason}",
    "budget_unknown_reason": "Unknown: {reason}", "budget_reason_missing": "folder not found in scan",
    "budget_reason_linked": "linked folder", "budget_reason_not_folder": "not a folder",
    "budget_reason_incomplete": "incomplete coverage",
    "budget_invalid_input": "Enter a valid name, absolute path and exact limit",
    "budget_invalid_data": "Saved budget data is invalid", "budget_duplicate_path": "This path already has a budget",
    "budget_missing_rule": "This budget no longer exists", "budget_too_many": "Too many budgets",
    "budget_settings_locked": "Budget settings are busy", "budget_storage_unavailable": "Budget storage is unavailable",
    "budget_read_failed": "Could not read budget settings", "budget_write_failed": "Could not save budget settings",
    "budget_observed": "Observed at",
    "budget_not_scanned": "Not scanned yet",
    "budget_changed_limit": "Limit changed; waiting for full scan",
    "budget_input_unit": "Limit unit (binary)",
    "budget_choose": "Choose folder…",
    "budget_empty": "No folder budgets yet. Choose a folder, enter a name and a limit, then select Add.",
    "budget_edit_hint": (
        'Limits use exact binary units. Adding or editing a budg'
        'et does not scan. Usage is the last observation, not li'
        've usage. A changed limit needs a new full scan.'
    ),
    "budget_keep_draft": "Your unsaved input was kept. Save it or select New before choosing another target.",
    "budget_editing": "Editing the selected budget",
    "budget_creating": "New budget",
    "budget_exact": "Exact size: {value}",
    "budget_invalid_name": "Enter a budget name",
    'search_edit_conditions': 'Edit conditions',
    'date_accept': 'OK', 'date_cancel': 'Cancel', 'date_choose': 'Calendar…',
    'date_clear': 'Clear date',
    'search_fix_field': 'Correct the marked field to apply this range.',
    'search_size_unit': 'Size unit (binary)',
    'search_condition_name': 'Name: {value}',
    'search_condition_value': '{label}: {value}',
    'search_condition_dates': 'Dates, inclusive: {start} through {through}',
    'search_scope_none': 'Search scope: no completed scan',
    'search_scope_root': 'Entire scan: {path}',
    'search_scope_multi': 'Entire scan: all combined sources',
    'search_scope': 'Search scope',
    'search_clear_all': 'Clear all conditions',
    'search_no_conditions': 'Add a name or condition to search the entire scan.',
    'search_clear_condition': 'Clear',
    'search_remove_condition': 'Clear condition: {condition}',
    "action_settings": "Settings…",
    "action_settings_tip": "Every setting in one searchable window, with export and import",
    "settings_title": "Settings",
    "settings_search": "Search settings",
    "settings_none": "No setting matches.",
    "settings_appearance": "Appearance",
    "settings_scanning": "Scanning",
    "settings_recording": "What scans record",
    "settings_following": "Following and watching",
    "settings_cleaning": "Clean-up and history",
    "settings_system": "Windows",
    "settings_export": "Export settings…",
    "settings_import": "Import settings…",
    "settings_file_tip": (
        "Appearance, scan choices and skipped folders. Recent folders, presets, budgets,"
        " background scans and the clean-up policy are not included."
    ),
    "settings_invalid": "This is not a usable FileTree settings file. Nothing was changed.",
    "settings_same": "These settings are already in use.",
    "settings_confirm": "Change {count} settings to the values in this file?",
    "treemap_colours_change": "By change",
    "change_colour_new": "New",
    "change_colour_grew_lot": "Grew over 25%",
    "change_colour_grew": "Grew",
    "change_colour_same": "No change",
    "change_colour_shrank": "Shrank",
    "change_colour_shrank_lot": "Shrank over 25%",
    "change_colour_none": "Compare with a saved scan to see what changed",
    "change_colour_tip": (
        "Each folder by its change since the saved scan; a file by the folder that holds"
        " it, because saved scans record folders"
    ),
    "cleanup_custom": "Your rule: {name}",
    "cleanup_custom_tip": "Matches a rule you wrote. FileTree cannot tell whether the contents are still needed.",
    "cleanup_category_custom": "your own rule",
    "cleanup_rebuild_custom": "Unknown; check every entry before moving it.",
    "custom_rules_button": "Your rules ({count})…",
    "custom_rules_title": "Your clean-up rules",
    "custom_rules_hint": (
        "What these rules find is always listed for review, never ticked for you and never"
        " proposed by background scans. System, program and profile folders are left out."
    ),
    "custom_rules_add": "Add",
    "custom_rules_update": "Update",
    "custom_rules_remove": "Remove",
    "custom_rules_name": "Name",
    "custom_rules_name_tip": "Shown as the group title",
    "custom_rules_folders": "Folders",
    "custom_rules_folders_tip": "The end of a path, such as Cache or MyApp/logs; separate several with ;",
    "custom_rules_files": "Files",
    "custom_rules_files_tip": "Names such as *.bak; separate several with ;",
    "custom_rules_in_folder": "Only in folder",
    "custom_rules_in_folder_tip": (
        "Files count only directly inside a folder of this name; leave empty for"
        " any folder"
    ),
    "custom_rules_days": "Unchanged for days",
    "custom_rules_days_tip": "Newer entries are left out",
    "custom_rules_invalid": (
        "This rule cannot be used: give it a name of its own and at least one pattern"
        " that says enough (three letters or digits, no drive or backslash; a folder ends"
        " in a plain name)."
    ),
    "action_problem_files": "Check for problem files…",
    "action_problem_files_tip": (
        "Empty files, dead links and shortcuts, paths too long and names Windows does"
        " not allow"
    ),
    "problem_files_found": "Found",
    "problem_files_target": "Points to",
    "problem_files_all": "All problems",
    "problem_files_empty": "Empty file",
    "problem_files_dead_link": "Dead link",
    "problem_files_long_path": "Path too long",
    "problem_files_bad_name": "Name not allowed",
    "problem_files_hint": (
        "From the scan on screen. Only links and small local shortcuts are looked at on"
        " disk, without following them; targets on networks and absent drives stay unknown."
        " Nothing is changed here: double-click selects an entry in the tree."
    ),
    "problem_files_reading": "Checking…",
    "problem_files_summary": (
        "Showing {shown} entries; {count} problems found. Links that could not be judged:"
        " {unknown}. The first 1,000 of each kind are listed."
    ),
    "search_regex": "Read the name as a regular expression",
    "search_regex_tip": "Found anywhere in a name, ignoring case. Patterns that could take very long are refused.",
    "search_regex_invalid": (
        "This is not a regular expression FileTree can use: check the brackets, and avoid"
        " repeats inside repeats, look-around and references."
    ),
    "search_exclude": "Leave out names",
    "search_exclude_tip": (
        "Like the search box: node_modules; *.tmp. A matching folder is left out with everything"
        " in it."
    ),
    "search_owner": "Owner",
    "search_owner_tip": "Part of a name or identifier. Files only, from scans that recorded owners.",
    "search_min_depth": "At least this deep",
    "search_max_depth": "At most this deep",
    "search_depth_tip": "Entries directly in the scanned folder are at depth 1",
    "search_depth_error": "The smallest depth is greater than the largest.",
    "search_more_error": "A name or owner condition is too long or not text.",
    "search_condition_regex": "Name matches: {value}",
    "search_condition_depth": "Depth: {least} to {most}",
    "theme_contrast": "High contrast",
    "theme_accent": "Accent colour…",
    "theme_accent_platform": "Use the system's accent colour",
    "theme_colour_blind": "Chart colours for colour-blind viewers",
    "preview_show": "Preview contents",
    "preview_show_tip": "Reads the beginning of the selected file. Files kept only online are never downloaded.",
    "preview_none": "Select a file to preview it.",
    "preview_reading": "Reading…",
    "preview_failed": (
        "There is no preview: the file cannot be read, has changed since the scan, is kept only"
        " online or is not supported."
    ),
    "preview_binary": "This file is not text, a picture or an archive that can be previewed.",
    "preview_more": "The beginning is shown; there is more.",
    "preview_whole": "Everything is shown.",
    "action_palette": "Find a command…",
    "action_palette_tip": "Type to find any menu command and run it",
    "action_shortcuts": "Keyboard shortcuts…",
    "action_shortcuts_tip": "Choose the keys of menu commands",
    "palette_title": "Find a command",
    "palette_hint": "Type part of a command",
    "shortcuts_hint": (
        "Click a field and press Ctrl, Alt or a function key with another key. Removing, stopping"
        " and quitting keep their keys."
    ),
    "shortcuts_command": "Command",
    "shortcuts_keys": "Shortcut",
    "shortcuts_reset": "Restore defaults",
    "shortcuts_conflict": "These shortcuts cannot be used, or are used twice: {names}",
    "action_dev_tools": "Development tools…",
    "action_dev_tools_tip": "What Docker, pip, npm, Cargo and others keep, with their own clean-up commands",
    "dev_tools_tool": "Tool",
    "dev_tools_stores": "Folders",
    "dev_tools_inspect": "See what it holds",
    "dev_tools_clean": "Clean up",
    "dev_tools_automatic": "expires by itself",
    "dev_tools_hint": (
        "Sizes are from the scan on screen. FileTree never runs these commands: copy one and"
        " run it in a terminal yourself. A tool's own command skips what is in use and keeps"
        " its records right, which deleting its folders does not."
    ),
    "dev_tools_reading": "Looking…",
    "dev_tools_none": "No known development tool keeps data in this scan.",
    "dev_tools_summary": (
        "{count} tools take {size} on disk. Double-click selects the largest folder of a"
        " tool."
    ),
    "dev_tools_copy_inspect": "Copy the command to look",
    "dev_tools_copy_clean": "Copy the command to clean up",
    "dev_tools_copied": "Copied: {command}",
    "action_scan_overview": "Compare computers…",
    "action_scan_overview_tip": "Put saved scans of several computers side by side",
    "overview_scans_hint": (
        "Add the folder trees (JSON) exported on other computers. Folders are matched by"
        " their path below the scanned folder. Only recorded sizes are shown: nothing here"
        " can be opened, moved or removed."
    ),
    "overview_scans_list": "Scans",
    "overview_scans_add": "Add saved scans…",
    "overview_scans_rename": "Rename…",
    "overview_scans_remove": "Remove",
    "overview_scans_label": "Computer",
    "overview_scans_depth": "Levels:",
    "overview_scans_spread": "Difference",
    "overview_scans_total": "(whole scan)",
    "overview_scans_empty": "Add saved scans to compare them.",
    "overview_scans_reading": "Reading…",
    "overview_scans_summary": (
        "Showing {shown} of {count} folders, the largest first. “—” means a scan does"
        " not have the folder."
    ),
    "overview_scans_limit": "At most {limit} scans can be compared.",
    "overview_scans_failed": "These files could not be read:",
    "overview_scans_item": "{label} — {size} ({saved})",
    "overview_scans_csv": "Save as CSV…",
    "overview_scans_html": "Save as HTML…",
    "menu_zip": "Archive to ZIP…",
    "zip_title": "Archive a folder",
    "zip_filter": "ZIP archives (*.zip)",
    "zip_facts": "Folder: {path}\nArchive: {target}\n{files} files, {size}",
    "zip_hint": (
        "Every file is read back from the archive and compared before it appears. A ZIP keeps names,"
        " contents and modification times, but not owners, permissions or extended attributes. The"
        " folder stays where it is."
    ),
    "zip_start": "Create archive",
    "zip_move": "Move the original to the Recycle Bin…",
    "zip_checking": "Checking the folder…",
    "zip_pack": "Packing…",
    "zip_verify": "Reading back and comparing…",
    "zip_stopped": "Stopped. No archive was left.",
    "zip_failed": "The archive could not be created; none was left.\n{reason}",
    "zip_done": "Done: {files} files, {size}, verified. The archive takes {archive}. The original is untouched.",
    "zip_lost": "The archive is no longer the file that was verified. The original was not moved.",
    "zip_reason_target": "Choose a .zip file in an existing folder.\n{path}",
    "zip_reason_exists": "That file already exists; nothing is overwritten.\n{path}",
    "zip_reason_inside": "The archive cannot be inside the folder it holds.\n{path}",
    "zip_reason_name": "This name cannot be kept exactly in a ZIP.\n{path}",
    "zip_reason_streams": "This file has more data streams, which a ZIP would lose.\n{path}",
    "zip_reason_copy_unsupported": (
        "The folder holds a link, a file kept only online or a special file, or"
        " is a mount point.\n{path}"
    ),
    "zip_reason_folder_required": "Only an ordinary folder can be archived.\n{path}",
    "zip_reason_verify": "The archive did not read back correctly and was removed.\n{path}",
    "zip_reason_changed": "The folder is not as it was scanned: rescan it first.\n{path}",
}
