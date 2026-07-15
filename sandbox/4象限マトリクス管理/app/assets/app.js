/* =========================================================
   Neuro Matrix Task OS — app.js
   既存 タスク管理.html の JS を v2 DOM 向けに再移植する。
   このファイルは現時点で「データ層 + 純粋関数」のみ確定版。
   DOM 描画層とイベント配線は Phase C で追加する。
   ========================================================= */
(() => {
  'use strict';

  // ---- Constants -------------------------------------------------
  const KEY_DATA = 'neuro_matrix_v6_data';
  const KEY_STATE = 'neuro_matrix_v6_state';
  const LEGACY_DATA = 'neuro_matrix_v5_data';
  const LEGACY_STATE = 'neuro_matrix_v5_state';
  const CURRENT_SCHEMA_VERSION = 6;

  const ACTIVE_ZONES = ['q1', 'q2', 'q3', 'q4', 'survival-picker', 'slot-must', 'slot-should'];
  const NORMAL_ZONES = ['q1', 'q2', 'q3', 'q4'];
  const SURVIVAL_SLOTS = ['survival-picker', 'slot-must', 'slot-should'];

  const UNDO_STACK_MAX = 5;
  const UNDO_TOAST_MS = 5000;
  const INPUT_DEBOUNCE_MS = 300;

  // ---- Runtime state (module-level) ------------------------------
  let tasks = [];
  let uiState = {
    isSurvival: false,
    targetTime: '17:30',
    completedPanelOpen: false,
    survivalSlots: {}   // { taskId: 'survival-picker' | 'slot-must' | 'slot-should' }
  };
  let deletedStack = [];
  let undoTimer = null;
  let dataCorrupted = false;

  // ---- Time helpers ---------------------------------------------
  function nowIso() {
    return new Date().toISOString();
  }

  function formatDateTime(value) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return '—';
    return new Intl.DateTimeFormat('ja-JP', {
      year: 'numeric', month: '2-digit', day: '2-digit',
      hour: '2-digit', minute: '2-digit'
    }).format(date);
  }

  function formatDueDate(value) {
    if (!value) return null;
    const d = new Date(value + 'T00:00:00');
    if (Number.isNaN(d.getTime())) return null;
    return new Intl.DateTimeFormat('ja-JP', { month: '2-digit', day: '2-digit', weekday: 'short' }).format(d);
  }

  function todayString() {
    const d = new Date();
    const y = d.getFullYear();
    const m = String(d.getMonth() + 1).padStart(2, '0');
    const day = String(d.getDate()).padStart(2, '0');
    return `${y}-${m}-${day}`;
  }

  // 相対時間 (「2時間前」「3日前」等) — UI のメタ表示用
  function formatRelative(iso) {
    if (!iso) return '';
    const then = new Date(iso).getTime();
    if (Number.isNaN(then)) return '';
    const diffSec = Math.max(0, Math.floor((Date.now() - then) / 1000));
    if (diffSec < 60) return 'たった今';
    if (diffSec < 3600) return `${Math.floor(diffSec / 60)}分前`;
    if (diffSec < 86400) return `${Math.floor(diffSec / 3600)}時間前`;
    if (diffSec < 604800) return `${Math.floor(diffSec / 86400)}日前`;
    if (diffSec < 2592000) return `${Math.floor(diffSec / 604800)}週間前`;
    return `${Math.floor(diffSec / 2592000)}ヶ月前`;
  }

  // ---- Task model / pure functions ------------------------------
  function baseTask(overrides = {}) {
    const createdAt = nowIso();
    return {
      schemaVersion: Number.isInteger(overrides.schemaVersion) ? overrides.schemaVersion : CURRENT_SCHEMA_VERSION,
      id: overrides.id || `card-${Date.now()}-${Math.random().toString(16).slice(2, 7)}`,
      title: overrides.title || '',
      note: overrides.note || '',
      zone: overrides.zone && ACTIVE_ZONES.includes(overrides.zone) ? overrides.zone : 'q4',
      normalZone: overrides.normalZone && NORMAL_ZONES.includes(overrides.normalZone)
        ? overrides.normalZone
        : (NORMAL_ZONES.includes(overrides.zone) ? overrides.zone : 'q4'),
      status: overrides.status === 'completed' ? 'completed' : 'active',
      dueDate: overrides.dueDate || '',
      createdAt: overrides.createdAt || createdAt,
      updatedAt: overrides.updatedAt || overrides.createdAt || createdAt,
      completedAt: overrides.completedAt || '',
      activityLog: Array.isArray(overrides.activityLog) ? overrides.activityLog : []
    };
  }

  function sortTasks(activeTasks) {
    return [...activeTasks].sort((a, b) => {
      const aDue = a.dueDate || '9999-99-99';
      const bDue = b.dueDate || '9999-99-99';
      if (aDue !== bDue) return aDue.localeCompare(bDue);
      return new Date(b.updatedAt) - new Date(a.updatedAt);
    });
  }

  function dueBadge(task) {
    if (!task.dueDate) return { label: '締切なし', className: 'none' };
    const today = todayString();
    if (task.dueDate < today) return { label: `期限超過 ${formatDueDate(task.dueDate) || task.dueDate}`, className: 'overdue' };
    if (task.dueDate === today) return { label: `今日 ${formatDueDate(task.dueDate) || task.dueDate}`, className: 'today' };
    return { label: `締切 ${formatDueDate(task.dueDate) || task.dueDate}`, className: 'due' };
  }

  function logEvent(task, type, detail = {}) {
    const entry = { type, at: nowIso(), detail };
    task.activityLog = Array.isArray(task.activityLog) ? task.activityLog : [];
    task.activityLog.unshift(entry);
    task.activityLog = task.activityLog.slice(0, 30);
    task.updatedAt = entry.at;
    return entry;
  }

  function cloneTask(task) {
    return JSON.parse(JSON.stringify(task));
  }

  // ---- Persistence layer ----------------------------------------
  function safeParse(json, fallback) {
    try { return JSON.parse(json) || fallback; } catch (_) { return fallback; }
  }

  function backupCorrupted(key, rawValue, reason) {
    const backupKey = `neuroMatrix.legacy_backup.${key}.${Date.now()}`;
    try {
      localStorage.setItem(backupKey, rawValue);
      console.warn(`[neuro-matrix] 壊れた ${key} を ${backupKey} に退避しました:`, reason);
    } catch (e) {
      console.error('[neuro-matrix] 退避にも失敗:', e);
    }
    dataCorrupted = true;
    try {
      window.setTimeout(() => {
        alert(`[Neuro Matrix] 保存データ(${key})の読み込みに失敗しました。\n元のデータは "${backupKey}" に退避してあります。DevTools → Application → LocalStorage で救出してください。\nこのまま編集すると空状態で上書きされるので、先に救出が必要です。`);
      }, 0);
    } catch (_) { /* alert不能環境 */ }
  }

  function readPersisted(key, fallback) {
    const raw = localStorage.getItem(key);
    if (raw === null || raw === '') return fallback;
    try {
      const parsed = JSON.parse(raw);
      return (parsed === null || parsed === undefined) ? fallback : parsed;
    } catch (e) {
      backupCorrupted(key, raw, e && e.message);
      return fallback;
    }
  }

  function saveData() {
    if (dataCorrupted) return;
    localStorage.setItem(KEY_DATA, JSON.stringify(tasks));
  }

  function saveState() {
    if (dataCorrupted) return;
    localStorage.setItem(KEY_STATE, JSON.stringify(uiState));
  }

  function saveAll() {
    saveData();
    saveState();
  }

  function migrateLegacyIfNeeded() {
    const existing = localStorage.getItem(KEY_DATA);
    if (existing) return;
    const legacyDataJson = localStorage.getItem(LEGACY_DATA);
    if (!legacyDataJson) return;

    const legacyItems = readPersisted(LEGACY_DATA, []);
    const legacyState = readPersisted(LEGACY_STATE, {});
    if (dataCorrupted) return;

    const migrated = legacyItems.map(item => {
      const zone = ACTIVE_ZONES.includes(item.zone) ? item.zone : 'q4';
      const normalZone = NORMAL_ZONES.includes(zone) ? zone : 'q4';
      const task = baseTask({ id: item.id, title: item.text || '', zone, normalZone });
      task.activityLog = [{ type: 'created', at: task.createdAt, detail: { migrated: true } }];
      return task;
    });
    tasks = migrated;
    uiState = {
      isSurvival: !!legacyState.isSurvival,
      targetTime: legacyState.targetTime || '17:30',
      completedPanelOpen: false,
      survivalSlots: {}
    };
    saveAll();
  }

  function loadAll() {
    migrateLegacyIfNeeded();
    const rawTasks = readPersisted(KEY_DATA, []);
    tasks = Array.isArray(rawTasks) ? rawTasks.map(item => baseTask(item)) : [];
    const state = readPersisted(KEY_STATE, null);
    if (state) {
      const rawSlots = state.survivalSlots && typeof state.survivalSlots === 'object' ? state.survivalSlots : {};
      const slots = {};
      Object.keys(rawSlots).forEach(taskId => {
        const slot = rawSlots[taskId];
        if (SURVIVAL_SLOTS.includes(slot)) slots[taskId] = slot;
      });
      uiState = {
        isSurvival: !!state.isSurvival,
        targetTime: state.targetTime || '17:30',
        completedPanelOpen: !!state.completedPanelOpen,
        survivalSlots: slots
      };
    }
  }

  // ---- Utility: debounce ----------------------------------------
  function debounce(fn, delay) {
    let timerId = null;
    let lastArgs = null;
    let lastThis = null;
    const debounced = function (...args) {
      lastArgs = args;
      lastThis = this;
      if (timerId) clearTimeout(timerId);
      timerId = setTimeout(() => { timerId = null; fn.apply(lastThis, lastArgs); }, delay);
    };
    debounced.flush = function () {
      if (timerId) { clearTimeout(timerId); timerId = null; fn.apply(lastThis, lastArgs || []); }
    };
    debounced.cancel = function () {
      if (timerId) { clearTimeout(timerId); timerId = null; }
    };
    return debounced;
  }

  // ---- Query helpers -------------------------------------------
  function getTask(taskId) { return tasks.find(t => t.id === taskId); }
  function activeTasks() { return tasks.filter(t => t.status === 'active'); }
  function completedTasks() {
    return [...tasks.filter(t => t.status === 'completed')]
      .sort((a, b) => new Date(b.completedAt || 0) - new Date(a.completedAt || 0));
  }
  function tasksInZone(zone) {
    return sortTasks(activeTasks().filter(t => t.zone === zone));
  }
  function countActiveInZone(zone) {
    return activeTasks().filter(t => t.zone === zone).length;
  }
  function countToday() {
    const d = todayString();
    return activeTasks().filter(t => t.dueDate === d).length;
  }
  function countOverdue() {
    const d = todayString();
    return activeTasks().filter(t => t.dueDate && t.dueDate < d).length;
  }

  // ---- Mutations (DOM 非依存) -----------------------------------
  function addTask(options = {}) {
    const targetZone = options.zone || (uiState.isSurvival ? 'survival-picker' : 'q4');
    const task = baseTask({
      zone: targetZone,
      normalZone: NORMAL_ZONES.includes(targetZone) ? targetZone : 'q4',
      title: options.title || '',
    });
    logEvent(task, 'created');
    tasks.unshift(task);
    saveAll();
    return task;
  }

  function completeTask(taskId) {
    const task = getTask(taskId);
    if (!task) return null;
    if (NORMAL_ZONES.includes(task.zone)) task.normalZone = task.zone;
    task.status = 'completed';
    task.completedAt = nowIso();
    logEvent(task, 'completed');
    if (uiState.survivalSlots) delete uiState.survivalSlots[taskId];
    saveAll();
    return task;
  }

  function reopenTask(taskId) {
    const task = getTask(taskId);
    if (!task) return null;
    task.status = 'active';
    task.completedAt = '';
    task.zone = task.normalZone && NORMAL_ZONES.includes(task.normalZone) ? task.normalZone : 'q4';
    logEvent(task, 'reopened');
    saveAll();
    return task;
  }

  function deleteTask(taskId) {
    const task = getTask(taskId);
    if (!task) return null;
    logEvent(task, 'deleted');
    const snapshot = cloneTask(task);
    tasks = tasks.filter(t => t.id !== taskId);
    if (uiState.survivalSlots) delete uiState.survivalSlots[taskId];
    pushUndoSnapshot(snapshot);
    saveAll();
    return snapshot;
  }

  function undoDelete() {
    const snapshot = deletedStack.shift();
    if (!snapshot) return null;
    const restored = baseTask(snapshot);
    logEvent(restored, 'restored');
    tasks.unshift(restored);
    saveAll();
    return restored;
  }

  function pushUndoSnapshot(snapshot) {
    deletedStack.unshift(snapshot);
    if (deletedStack.length > UNDO_STACK_MAX) deletedStack.length = UNDO_STACK_MAX;
  }

  function moveTask(taskId, targetZone) {
    const task = getTask(taskId);
    if (!task || !ACTIVE_ZONES.includes(targetZone) || task.status !== 'active') return null;
    const from = task.zone;
    task.zone = targetZone;
    if (NORMAL_ZONES.includes(targetZone)) task.normalZone = targetZone;
    if (uiState.isSurvival && SURVIVAL_SLOTS.includes(targetZone)) {
      if (!uiState.survivalSlots) uiState.survivalSlots = {};
      uiState.survivalSlots[taskId] = targetZone;
    }
    if (from !== targetZone) logEvent(task, 'moved', { from, to: targetZone });
    saveAll();
    return task;
  }

  // タスクの本体（title/note/dueDate/zone）をまとめて更新する。
  // 変更前後を activityLog に記録。zone を変えた場合は normalZone も同期。
  function updateTask(taskId, updates) {
    const task = getTask(taskId);
    if (!task || task.status !== 'active') return null;
    const diff = {};

    if (typeof updates.title === 'string') {
      const v = updates.title.trim();
      if (v && v !== task.title) { diff.title = { from: task.title, to: v }; task.title = v; }
    }
    if (typeof updates.note === 'string') {
      const v = updates.note.trim();
      if (v !== (task.note || '')) { diff.note = { from: task.note || '', to: v }; task.note = v; }
    }
    if (typeof updates.dueDate === 'string') {
      const v = updates.dueDate; // '' で「締切なし」
      if (v !== (task.dueDate || '')) { diff.dueDate = { from: task.dueDate || '', to: v }; task.dueDate = v; }
    }
    if (typeof updates.zone === 'string' && ACTIVE_ZONES.includes(updates.zone)) {
      if (updates.zone !== task.zone) {
        diff.zone = { from: task.zone, to: updates.zone };
        task.zone = updates.zone;
        if (NORMAL_ZONES.includes(updates.zone)) task.normalZone = updates.zone;
      }
    }

    if (Object.keys(diff).length > 0) {
      logEvent(task, 'edited', diff);
      saveAll();
    }
    return task;
  }

  function enterSurvival() {
    uiState.isSurvival = true;
    const slots = uiState.survivalSlots || {};
    const nextSlots = {};
    tasks.forEach(task => {
      if (task.status !== 'active') return;
      if (NORMAL_ZONES.includes(task.zone)) task.normalZone = task.zone;
      const previous = slots[task.id];
      const restored = (previous === 'slot-must' || previous === 'slot-should') ? previous : 'survival-picker';
      task.zone = restored;
      nextSlots[task.id] = restored;
    });
    uiState.survivalSlots = nextSlots;
    saveAll();
  }

  function exitSurvival() {
    uiState.isSurvival = false;
    tasks.forEach(task => {
      if (task.status !== 'active') return;
      task.zone = task.normalZone && NORMAL_ZONES.includes(task.normalZone) ? task.normalZone : 'q4';
    });
    // survivalSlots は保持（次 enter で復元）
    saveAll();
  }

  // ---- Public API (Phase C で DOM バインディングが利用) --------
  window.NeuroMatrix = {
    // constants
    KEY_DATA, KEY_STATE, ACTIVE_ZONES, NORMAL_ZONES, SURVIVAL_SLOTS,
    UNDO_STACK_MAX, UNDO_TOAST_MS, INPUT_DEBOUNCE_MS, CURRENT_SCHEMA_VERSION,

    // state accessors
    getTasks: () => tasks.slice(),
    getUiState: () => ({ ...uiState, survivalSlots: { ...(uiState.survivalSlots || {}) } }),
    getDeletedStack: () => deletedStack.slice(),
    isDataCorrupted: () => dataCorrupted,

    // pure utilities
    baseTask, sortTasks, dueBadge, logEvent, cloneTask,
    nowIso, formatDateTime, formatDueDate, formatRelative, todayString,
    debounce,

    // persistence
    loadAll, saveAll, saveData, saveState,

    // queries
    getTask, activeTasks, completedTasks, tasksInZone, countActiveInZone,

    // mutations
    addTask, completeTask, reopenTask, deleteTask, undoDelete, moveTask, updateTask,
    enterSurvival, exitSurvival,
  };

  // =============================================================
   // DOM rendering layer (index.html 専用、ダッシュボード画面)
   // =============================================================

  function $(sel, root) { return (root || document).querySelector(sel); }
  function $$(sel, root) { return Array.from((root || document).querySelectorAll(sel)); }

  function createTaskCard(task) {
    const card = document.createElement('article');
    card.className = `task-card ${task.zone}-card`;
    card.dataset.taskId = task.id;
    card.draggable = true;

    card.addEventListener('dragstart', (e) => {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', task.id);
      card.classList.add('is-dragging');
    });
    card.addEventListener('dragend', () => card.classList.remove('is-dragging'));

    // Drag handle
    const handle = document.createElement('div');
    handle.className = 'task-handle';
    handle.innerHTML = '<span class="material-symbols-outlined">drag_indicator</span>';
    card.appendChild(handle);

    // Body
    const body = document.createElement('div');
    body.className = 'task-body';

    const title = document.createElement('h3');
    title.className = 'task-title';
    title.textContent = task.title || '(無題タスク)';
    body.appendChild(title);

    // Note (本文を直接表示。長文は3行で省略 + hover で全文ツールチップ)
    if (task.note && task.note.trim()) {
      const noteEl = document.createElement('p');
      noteEl.className = 'task-note';
      noteEl.textContent = task.note.trim();
      noteEl.title = task.note.trim();
      body.appendChild(noteEl);
    }

    // Meta row
    const meta = document.createElement('div');
    meta.className = 'task-meta';
    const due = dueBadge(task);
    const dueEl = document.createElement('span');
    dueEl.className = `badge badge-${due.className}`;
    if (due.className === 'overdue') {
      dueEl.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px;font-variation-settings:\'FILL\' 1;">warning</span>';
    } else if (due.className === 'today') {
      dueEl.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px">schedule</span>';
    } else if (due.className === 'due') {
      dueEl.innerHTML = '<span class="material-symbols-outlined" style="font-size:14px">event</span>';
    }
    dueEl.appendChild(document.createTextNode(' ' + due.label));
    meta.appendChild(dueEl);

    const time = document.createElement('span');
    time.className = 'task-time';
    time.textContent = '更新 ' + formatRelative(task.updatedAt);
    meta.appendChild(time);
    body.appendChild(meta);

    // Actions
    const actions = document.createElement('div');
    actions.className = 'task-actions';
    actions.innerHTML = `
      <button class="action-btn action-complete" data-act="complete" aria-label="完了にする">
        <span class="material-symbols-outlined" style="font-size:18px">check_circle</span>完了
      </button>
      <button class="action-btn" data-act="detail" aria-label="詳細">
        <span class="material-symbols-outlined" style="font-size:18px">edit_note</span>詳細
      </button>
      <button class="action-btn action-delete" data-act="delete" aria-label="削除">
        <span class="material-symbols-outlined" style="font-size:18px">delete</span>
      </button>
    `;
    body.appendChild(actions);
    card.appendChild(body);

    // Events
    actions.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-act]');
      if (!btn) return;
      e.stopPropagation();
      const act = btn.dataset.act;
      if (act === 'complete') handleComplete(task.id);
      else if (act === 'delete') handleDelete(task.id);
      else if (act === 'detail') openTaskModal(task);
    });

    return card;
  }

  function renderZone(zoneId) {
    const bodyEl = $(`[data-zone-body="${zoneId}"]`);
    if (!bodyEl) return;
    bodyEl.innerHTML = '';
    const zoneTasks = tasksInZone(zoneId);
    if (zoneTasks.length === 0) {
      const hint = document.createElement('div');
      hint.className = 'empty-hint-v2';
      hint.textContent = zoneId === 'q4'
        ? '未仕分けタスクの一時置き場。＋ボタンで追加'
        : 'まだタスクはありません。＋ボタンかドラッグで追加';
      bodyEl.appendChild(hint);
      return;
    }
    zoneTasks.forEach(task => bodyEl.appendChild(createTaskCard(task)));
  }

  function renderAll() {
    NORMAL_ZONES.forEach(renderZone);
    renderCounts();
    renderSidebarCounts();
    renderStatusBar();
  }

  function renderCounts() {
    NORMAL_ZONES.forEach(zone => {
      const target = $(`[data-count-for="${zone}"]`);
      if (target) target.textContent = countActiveInZone(zone);
    });
  }

  function renderSidebarCounts() {
    const completed = completedTasks().length;
    const today = countToday();
    const overdue = countOverdue();

    const completedEl = $('[data-sidebar-count="completed"]');
    if (completedEl) completedEl.textContent = completed;

    const todayEl = $('[data-sidebar-count="today"]');
    if (todayEl) todayEl.textContent = today;

    const overdueEl = $('[data-sidebar-count="overdue"]');
    if (overdueEl) {
      overdueEl.textContent = overdue;
      // 0 件なら通常表示、1件以上なら警告ピル
      if (overdue > 0) {
        overdueEl.className = 'ml-auto text-[11px] font-mono px-1.5 rounded bg-q1/15 text-q1';
      } else {
        overdueEl.className = 'ml-auto text-[11px] font-mono text-text-3';
      }
    }
  }

  function renderStatusBar() {
    const footerLeft = document.querySelector('footer .flex.items-center.gap-4');
    if (!footerLeft) return;
    const activeCount = activeTasks().length;
    const completedCount = completedTasks().length;
    footerLeft.innerHTML = `
      <span class="flex items-center gap-1.5">
        <span class="w-1.5 h-1.5 rounded-full bg-q2"></span>
        ${activeCount} 件 進行中
      </span>
      <span>·</span>
      <span>${completedCount} 件 完了</span>
    `;
  }

  // ---- Action handlers -----------------------------------------
  function handleComplete(taskId) {
    completeTask(taskId);
    renderAll();
  }

  function handleDelete(taskId) {
    const snapshot = deleteTask(taskId);
    if (!snapshot) return;
    renderAll();
    showUndoToast();
  }

  function handleUndo() {
    undoDelete();
    renderAll();
    hideUndoToast();
  }

  function showUndoToast() {
    const toast = $('#undo-toast');
    const msg = $('#undo-message');
    if (!toast || !msg) return;
    msg.textContent = deletedStack.length > 1
      ? `タスクを削除しました (残り ${deletedStack.length} 件戻せる)`
      : 'タスクを削除しました (5秒以内なら取り消せます)';
    toast.classList.add('visible');
    if (undoTimer) clearTimeout(undoTimer);
    undoTimer = setTimeout(() => {
      hideUndoToast();
      deletedStack = [];
    }, UNDO_TOAST_MS);
  }

  function hideUndoToast() {
    const toast = $('#undo-toast');
    if (toast) toast.classList.remove('visible');
    if (undoTimer) { clearTimeout(undoTimer); undoTimer = null; }
  }

  // ---- Modal (new task / edit existing) -------------------------
  // モーダルは index.html にベタ書きされているが、サブページには無い。
  // どのページでも detail / quick-add から開けるよう、必要なら body 末尾に動的注入。
  let _modalRefreshHook = null; // モーダル送信後に呼ぶ再描画関数（ページごと）

  function ensureTaskModal() {
    let modal = $('#task-modal');
    if (modal) return modal;
    const wrap = document.createElement('div');
    wrap.innerHTML = `
<div id="task-modal" class="modal-backdrop hidden" role="dialog" aria-modal="true" aria-labelledby="task-modal-title">
  <div class="modal-panel">
    <header class="modal-header">
      <div class="flex items-center gap-2">
        <span id="task-modal-icon" class="material-symbols-outlined text-text-2 text-[20px]">add_task</span>
        <h2 id="task-modal-title" class="text-base font-bold text-text-0">新規タスクを追加</h2>
      </div>
      <button id="task-modal-close" class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-2 text-text-2" aria-label="閉じる">
        <span class="material-symbols-outlined text-[18px]">close</span>
      </button>
    </header>
    <form id="task-form" class="modal-body">
      <div>
        <label class="modal-label" for="task-title-input">タスク名 <span class="text-q1">*</span></label>
        <input id="task-title-input" type="text" required autofocus class="modal-input" placeholder="例: 提案書レビュー、買い出し" maxlength="200">
      </div>
      <div>
        <label class="modal-label">象限</label>
        <div id="quadrant-picker" class="quadrant-picker">
          <button type="button" class="q-pick" data-zone="q1" data-selected="false">
            <span class="q-pick-dot bg-q1"></span>
            <div class="q-pick-body"><div class="q-pick-title">Q1 重要・緊急</div><div class="q-pick-sub">DO FIRST</div></div>
          </button>
          <button type="button" class="q-pick" data-zone="q2" data-selected="false">
            <span class="q-pick-dot bg-q2"></span>
            <div class="q-pick-body"><div class="q-pick-title">Q2 重要・非緊急</div><div class="q-pick-sub">SCHEDULE</div></div>
          </button>
          <button type="button" class="q-pick" data-zone="q3" data-selected="false">
            <span class="q-pick-dot bg-q3"></span>
            <div class="q-pick-body"><div class="q-pick-title">Q3 非重要・緊急</div><div class="q-pick-sub">DELEGATE</div></div>
          </button>
          <button type="button" class="q-pick" data-zone="q4" data-selected="true">
            <span class="q-pick-dot bg-q4"></span>
            <div class="q-pick-body"><div class="q-pick-title">Q4 あとで</div><div class="q-pick-sub">LATER</div></div>
          </button>
        </div>
      </div>
      <div>
        <label class="modal-label" for="task-due-input">締切日 <span class="text-text-3 font-normal">(任意)</span></label>
        <input id="task-due-input" type="date" class="modal-input" style="max-width: 220px;">
      </div>
      <div>
        <label class="modal-label" for="task-note-input">メモ <span class="text-text-3 font-normal">(任意・複数行可)</span></label>
        <textarea id="task-note-input" class="modal-input modal-textarea" placeholder="背景・次の一手・参考リンクなど" maxlength="1000" rows="4"></textarea>
      </div>
      <div class="modal-footer">
        <div class="text-[11px] text-text-3 font-mono flex items-center gap-1.5">
          <kbd class="kbd">Esc</kbd> <span>取消</span>
          <span class="mx-1">·</span>
          <kbd class="kbd">⌘</kbd><kbd class="kbd">Enter</kbd> <span>保存</span>
        </div>
        <div class="flex gap-2">
          <button type="button" id="task-modal-cancel" class="btn-ghost">キャンセル</button>
          <button type="submit" id="task-modal-submit" class="btn-primary">
            <span class="material-symbols-outlined text-[18px]">check</span>
            <span data-submit-label>追加</span>
          </button>
        </div>
      </div>
    </form>
  </div>
</div>`;
    document.body.appendChild(wrap.firstElementChild);
    return $('#task-modal');
  }

  // モーダル単一インスタンスの状態（編集 vs 新規）
  let modalEditTaskId = null;

  function openTaskModal(task = null) {
    const modal = ensureTaskModal();
    const form = $('#task-form');
    const titleInput = $('#task-title-input');
    const dueInput = $('#task-due-input');
    const noteInput = $('#task-note-input');
    const picker = $('#quadrant-picker');
    const titleEl = $('#task-modal-title');
    const iconEl = $('#task-modal-icon');
    const submitLabel = modal.querySelector('[data-submit-label]');

    form.reset();
    $$('.q-pick', picker).forEach(b => b.dataset.selected = 'false');

    if (task) {
      // 編集モード
      modalEditTaskId = task.id;
      if (titleEl) titleEl.textContent = 'タスクを編集';
      if (iconEl) iconEl.textContent = 'edit_note';
      if (submitLabel) submitLabel.textContent = '保存';
      titleInput.value = task.title || '';
      dueInput.value = task.dueDate || '';
      noteInput.value = task.note || '';
      // zone: survival中は normalZone で象限選択（survival スロットには戻せない）
      const zoneForPick = NORMAL_ZONES.includes(task.zone) ? task.zone : (task.normalZone || 'q4');
      const targetBtn = picker.querySelector(`.q-pick[data-zone="${zoneForPick}"]`);
      if (targetBtn) targetBtn.dataset.selected = 'true';
    } else {
      // 新規モード
      modalEditTaskId = null;
      if (titleEl) titleEl.textContent = '新規タスクを追加';
      if (iconEl) iconEl.textContent = 'add_task';
      if (submitLabel) submitLabel.textContent = '追加';
      const defaultBtn = picker.querySelector('.q-pick[data-zone="q4"]');
      if (defaultBtn) defaultBtn.dataset.selected = 'true';
    }

    modal.classList.remove('hidden');
    setTimeout(() => titleInput.focus(), 20);
  }

  function closeTaskModal() {
    const modal = $('#task-modal');
    if (modal) modal.classList.add('hidden');
    modalEditTaskId = null;
  }

  // モーダルの一回限りの初期化（イベント配線）。ページごとに rerender hook を渡す。
  let _modalInitialized = false;
  function setupModal(rerenderHook) {
    _modalRefreshHook = rerenderHook || renderAll;
    if (_modalInitialized) return;

    const modal = ensureTaskModal();
    const form = $('#task-form');
    const titleInput = $('#task-title-input');
    const dueInput = $('#task-due-input');
    const noteInput = $('#task-note-input');
    const picker = $('#quadrant-picker');
    const closeBtn = $('#task-modal-close');
    const cancelBtn = $('#task-modal-cancel');
    const openBtn = $('#quick-add-btn');

    if (openBtn) openBtn.addEventListener('click', (e) => { e.preventDefault(); openTaskModal(null); });
    closeBtn.addEventListener('click', closeTaskModal);
    cancelBtn.addEventListener('click', closeTaskModal);
    modal.addEventListener('click', (e) => { if (e.target === modal) closeTaskModal(); });

    picker.addEventListener('click', (e) => {
      const b = e.target.closest('.q-pick');
      if (!b) return;
      $$('.q-pick', picker).forEach(x => x.dataset.selected = 'false');
      b.dataset.selected = 'true';
    });

    form.addEventListener('submit', (e) => {
      e.preventDefault();
      const title = titleInput.value.trim();
      if (!title) return;
      const zone = picker.querySelector('.q-pick[data-selected="true"]')?.dataset.zone || 'q4';
      const due = dueInput.value || '';
      const note = noteInput.value.trim();

      if (modalEditTaskId) {
        updateTask(modalEditTaskId, { title, zone, dueDate: due, note });
      } else {
        const newTask = addTask({ title, zone });
        if (due) { newTask.dueDate = due; logEvent(newTask, 'due_updated', { from: 'なし', to: due }); }
        if (note) { newTask.note = note; logEvent(newTask, 'note_updated'); }
        saveAll();
      }

      closeTaskModal();
      if (typeof _modalRefreshHook === 'function') _modalRefreshHook();
      renderSidebarCounts();
      renderStatusBar();
    });

    document.addEventListener('keydown', (e) => {
      const isInput = e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA';
      const modalOpen = !modal.classList.contains('hidden');

      // N: 新規タスク（入力欄外、モーダル閉時のみ）
      if ((e.key === 'n' || e.key === 'N') && !isInput && !modalOpen) {
        e.preventDefault();
        openTaskModal(null);
      }
      // Esc: モーダルを閉じる
      if (e.key === 'Escape' && modalOpen) {
        closeTaskModal();
      }
      // Cmd/Ctrl+Enter: 送信
      if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && modalOpen) {
        form.requestSubmit();
      }
      // Cmd/Ctrl+Z: undo（モーダル外、入力欄外）
      if ((e.metaKey || e.ctrlKey) && (e.key === 'z' || e.key === 'Z') && !isInput && !modalOpen) {
        if (deletedStack.length > 0) {
          e.preventDefault();
          handleUndo();
        }
      }
      // ?: ショートカットヘルプ（Shift+/。日本語IME中は弾く）
      if (e.key === '?' && !isInput && !e.isComposing) {
        e.preventDefault();
        toggleShortcutsHelp();
      }
    });

    _modalInitialized = true;
  }

  // ---- Shortcuts help overlay ----------------------------------
  function toggleShortcutsHelp() {
    let overlay = $('#shortcuts-help');
    if (overlay) { overlay.remove(); return; }
    overlay = document.createElement('div');
    overlay.id = 'shortcuts-help';
    overlay.className = 'modal-backdrop';
    overlay.setAttribute('role', 'dialog');
    overlay.innerHTML = `
      <div class="modal-panel" style="max-width: 420px;">
        <header class="modal-header">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-text-2 text-[20px]">keyboard</span>
            <h2 class="text-base font-bold text-text-0">キーボードショートカット</h2>
          </div>
          <button class="w-7 h-7 flex items-center justify-center rounded-md hover:bg-surface-2 text-text-2" aria-label="閉じる" data-close>
            <span class="material-symbols-outlined text-[18px]">close</span>
          </button>
        </header>
        <div class="modal-body" style="gap: 8px;">
          ${shortcutRow(['N'], '新規タスクを追加')}
          ${shortcutRow(['Esc'], 'モーダルを閉じる')}
          ${shortcutRow(['⌘', 'Enter'], 'モーダルを保存（Ctrl+Enter も可）')}
          ${shortcutRow(['⌘', 'Z'], '削除を取り消す（Ctrl+Z も可）')}
          ${shortcutRow(['?'], 'このヘルプを開閉')}
          <div class="text-[11px] text-text-3 mt-2">タスクカードをドラッグして象限間を移動できます。</div>
        </div>
      </div>`;
    overlay.addEventListener('click', (e) => {
      if (e.target === overlay || e.target.closest('[data-close]')) overlay.remove();
    });
    document.body.appendChild(overlay);
  }
  function shortcutRow(keys, desc) {
    const parts = keys.map(k => `<kbd class="kbd">${escapeHtml(k)}</kbd>`).join('<span class="text-text-3 text-xs px-0.5">+</span>');
    return `<div class="flex items-center justify-between gap-3 py-1">
      <div class="text-sm text-text-1">${escapeHtml(desc)}</div>
      <div class="flex items-center">${parts}</div>
    </div>`;
  }

  function setupUndoButton() {
    const undoBtn = $('#undo-btn');
    if (undoBtn) undoBtn.addEventListener('click', handleUndo);
  }

  // ---- Matrix D&D（4象限間でカード移動） ------------------------
  function setupMatrixDnD() {
    NORMAL_ZONES.forEach(zone => {
      const body = $(`[data-zone-body="${zone}"]`);
      if (!body) return;
      body.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        body.classList.add('drop-target');
      });
      body.addEventListener('dragleave', (e) => {
        // 子要素間移動で leave が発火するので contains で判定
        if (!body.contains(e.relatedTarget)) body.classList.remove('drop-target');
      });
      body.addEventListener('drop', (e) => {
        e.preventDefault();
        body.classList.remove('drop-target');
        const taskId = e.dataTransfer.getData('text/plain');
        if (!taskId) return;
        const task = getTask(taskId);
        if (!task || task.zone === zone) return;
        moveTask(taskId, zone);
        renderAll();
      });
    });
  }


  // =============================================================
  // Survival mode view (pages/survival.html)
  // =============================================================

  const SURVIVAL_LIMITS = { 'slot-must': 2, 'slot-should': 3 };
  let countdownInterval = null;

  function createSurvivalCard(task, context) {
    const card = document.createElement('article');
    card.draggable = true;
    card.dataset.taskId = task.id;
    card.dataset.zone = task.zone;

    if (context === 'picker') {
      card.className = 'flex-shrink-0 w-64 bg-[#0f0f0f] border border-neon-cyan/25 rounded p-3 cursor-grab hover:border-neon-cyan/60 hover:bg-[#141414] transition-all';
      card.innerHTML = `
        <div class="flex items-start justify-between gap-2">
          <h4 class="font-semibold text-white text-sm leading-snug truncate flex-1">${escapeHtml(task.title || '(無題)')}</h4>
          <span class="material-symbols-outlined text-neon-cyan/40 text-[16px] flex-shrink-0">drag_indicator</span>
        </div>
        <div class="flex items-center gap-2 mt-2.5 font-mono text-[10px]">
          ${survivalDueBadge(task)}
          <span class="text-panic-dim">·</span>
          <span class="text-panic-dim tracking-widest">${task.normalZone ? task.normalZone.toUpperCase() : 'Q4'}</span>
        </div>
      `;
    } else {
      // slot-must / slot-should
      const color = context === 'slot-must' ? 'neon-red' : 'neon-yellow';
      card.className = `bg-${color}/10 border border-${color}/30 rounded p-3.5 cursor-grab hover:bg-${color}/15 transition-colors`;
      card.innerHTML = `
        <div class="flex items-start gap-3">
          <span class="material-symbols-outlined text-${color} mt-0.5 flex-shrink-0" style="font-variation-settings: 'FILL' 1;">${context === 'slot-must' ? 'priority_high' : 'schedule'}</span>
          <div class="flex-1 min-w-0">
            <h3 class="font-bold text-white text-sm leading-snug">${escapeHtml(task.title || '(無題)')}</h3>
            <div class="flex items-center gap-3 mt-2 font-mono text-[10px] tracking-widest">
              ${survivalDueBadge(task)}
              <span class="text-${color}/40">·</span>
              <span class="text-${color}/50">${task.normalZone ? task.normalZone.toUpperCase() : 'Q4'}</span>
            </div>
          </div>
        </div>
      `;
    }

    card.addEventListener('dragstart', (e) => {
      e.dataTransfer.effectAllowed = 'move';
      e.dataTransfer.setData('text/plain', task.id);
      card.classList.add('opacity-40');
    });
    card.addEventListener('dragend', () => card.classList.remove('opacity-40'));

    return card;
  }

  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }

  function survivalDueBadge(task) {
    if (!task.dueDate) return '<span class="text-panic-dim tracking-widest">NO DUE</span>';
    const today = todayString();
    if (task.dueDate < today) return `<span class="text-neon-red tracking-widest">OVERDUE ${task.dueDate.slice(5).replace('-','/')}</span>`;
    if (task.dueDate === today) return `<span class="text-neon-yellow tracking-widest">TODAY</span>`;
    return `<span class="text-neon-cyan/70 tracking-widest">DUE ${task.dueDate.slice(5).replace('-','/')}</span>`;
  }

  function renderSurvivalView() {
    const must = $('[data-zone-body="slot-must"]');
    const should = $('[data-zone-body="slot-should"]');
    const picker = $('[data-zone-body="survival-picker"]');
    if (!must || !should || !picker) return;

    const mustTasks = activeTasks().filter(t => t.zone === 'slot-must');
    const shouldTasks = activeTasks().filter(t => t.zone === 'slot-should');
    const pickerTasks = activeTasks().filter(t => t.zone === 'survival-picker');

    must.innerHTML = '';
    if (mustTasks.length === 0) {
      must.innerHTML = '<div class="border border-dashed border-neon-red/30 rounded h-20 flex items-center justify-center"><span class="font-mono text-[10px] tracking-widest text-neon-red/40 uppercase">ドロップで追加</span></div>';
    } else {
      mustTasks.forEach(t => must.appendChild(createSurvivalCard(t, 'slot-must')));
    }

    should.innerHTML = '';
    if (shouldTasks.length === 0) {
      should.innerHTML = '<div class="border border-dashed border-neon-yellow/30 rounded h-20 flex items-center justify-center"><span class="font-mono text-[10px] tracking-widest text-neon-yellow/40 uppercase">ドロップで追加</span></div>';
    } else {
      shouldTasks.forEach(t => should.appendChild(createSurvivalCard(t, 'slot-should')));
    }

    picker.innerHTML = '';
    if (pickerTasks.length === 0) {
      picker.innerHTML = '<div class="flex-shrink-0 w-full flex items-center justify-center min-h-[80px]"><span class="font-mono text-[10px] tracking-widest text-panic-dim uppercase">未割り当てのタスクはありません</span></div>';
    } else {
      pickerTasks.forEach(t => picker.appendChild(createSurvivalCard(t, 'picker')));
    }

    // Counts
    const setCount = (zone, cur) => {
      const el = document.querySelector(`[data-survival-count="${zone}"]`);
      if (!el) return;
      if (zone === 'survival-picker') {
        el.textContent = `${cur} PENDING`;
      } else {
        const limit = SURVIVAL_LIMITS[zone];
        el.textContent = `${cur}/${limit}`;
      }
    };
    setCount('slot-must', mustTasks.length);
    setCount('slot-should', shouldTasks.length);
    setCount('survival-picker', pickerTasks.length);
  }

  function setupSurvivalDnD() {
    const zones = $$('[data-drop-zone]');
    zones.forEach(zone => {
      zone.addEventListener('dragover', (e) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        zone.classList.add('ring-2', 'ring-neon-cyan', 'ring-offset-2', 'ring-offset-black');
      });
      zone.addEventListener('dragleave', (e) => {
        if (!zone.contains(e.relatedTarget)) {
          zone.classList.remove('ring-2', 'ring-neon-cyan', 'ring-offset-2', 'ring-offset-black');
        }
      });
      zone.addEventListener('drop', (e) => {
        e.preventDefault();
        zone.classList.remove('ring-2', 'ring-neon-cyan', 'ring-offset-2', 'ring-offset-black');
        const taskId = e.dataTransfer.getData('text/plain');
        const target = zone.dataset.dropZone;
        if (!taskId || !target) return;

        // MUST 上限チェック
        if (target === 'slot-must') {
          const cur = activeTasks().filter(t => t.zone === 'slot-must' && t.id !== taskId).length;
          if (cur >= SURVIVAL_LIMITS['slot-must']) {
            alert(`MUST は ${SURVIVAL_LIMITS['slot-must']} 件までに絞ってください。1件 SHOULD か未割り当てに戻してからドロップしてください。`);
            return;
          }
        }
        moveTask(taskId, target);
        renderSurvivalView();
      });
    });
  }

  // Countdown timer
  function parseTime(str) {
    const m = /^(\d{1,2}):(\d{2})$/.exec(str || '');
    if (!m) return null;
    return { h: Number(m[1]), m: Number(m[2]) };
  }
  function updateCountdown() {
    const input = $('#target-time');
    const display = $('#countdown');
    const target = $('#target-label');
    const targetDisp = $('#countdown-target');
    const status = $('#countdown-status');
    if (!input || !display) return;
    const pref = parseTime(input.value);
    if (!pref) { display.textContent = '--:--'; return; }
    if (target) target.textContent = input.value;
    if (targetDisp) targetDisp.textContent = input.value;

    const now = new Date();
    const tgt = new Date();
    tgt.setHours(pref.h, pref.m, 0, 0);
    let diff = Math.floor((tgt - now) / 1000);
    if (diff < 0) {
      display.textContent = '00:00';
      display.classList.add('timer-pulse');
      if (status) status.innerHTML = '<span class="w-2 h-2 rounded-full bg-neon-red animate-pulse"></span><span class="tracking-widest">TIME UP</span>';
      return;
    }
    const hh = Math.floor(diff / 3600);
    const mm = Math.floor((diff % 3600) / 60);
    const ss = diff % 60;
    display.textContent = hh > 0
      ? `${hh}:${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')}`
      : `${String(mm).padStart(2,'0')}:${String(ss).padStart(2,'0')}`;

    // Color state
    if (diff < 15 * 60) {
      display.style.color = '';
      display.classList.add('timer-pulse');
      if (status) status.innerHTML = '<span class="w-2 h-2 rounded-full bg-neon-red animate-pulse"></span><span class="tracking-widest text-neon-red">CRITICAL</span>';
    } else if (diff < 30 * 60) {
      display.classList.remove('timer-pulse');
      display.style.color = '#ffe347';
      display.style.textShadow = '0 0 10px #ffe347, 0 0 20px rgba(255,227,71,.5)';
      if (status) status.innerHTML = '<span class="w-2 h-2 rounded-full bg-neon-yellow animate-pulse"></span><span class="tracking-widest text-neon-yellow">WARNING</span>';
    } else {
      display.classList.remove('timer-pulse');
      display.style.color = '';
      display.style.textShadow = '';
      if (status) status.innerHTML = '<span class="w-2 h-2 rounded-full bg-neon-cyan animate-pulse"></span><span class="tracking-widest text-neon-cyan">ACTIVE</span>';
    }
  }

  function setupCountdown() {
    const input = $('#target-time');
    if (!input) return;
    input.value = uiState.targetTime || '17:30';
    input.addEventListener('change', () => {
      uiState.targetTime = input.value || '17:30';
      saveState();
      updateCountdown();
    });
    updateCountdown();
    if (countdownInterval) clearInterval(countdownInterval);
    countdownInterval = setInterval(updateCountdown, 1000);
  }

  // =============================================================
  // Sub-pages rendering (completed / today / overdue)
  // =============================================================

  const ZONE_LABELS = {
    q1: 'Q1 重要・緊急', q2: 'Q2 重要・非緊急',
    q3: 'Q3 非重要・緊急', q4: 'Q4 あとで',
  };

  function formatDateJP(isoOrDate) {
    const d = isoOrDate ? new Date(isoOrDate) : new Date();
    if (Number.isNaN(d.getTime())) return '—';
    return new Intl.DateTimeFormat('ja-JP', { year: 'numeric', month: '2-digit', day: '2-digit' }).format(d);
  }
  function formatHM(iso) {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return '';
    return `${String(d.getHours()).padStart(2,'0')}:${String(d.getMinutes()).padStart(2,'0')}`;
  }
  function dayOffsetLabel(completedAt) {
    const today = new Date(); today.setHours(0,0,0,0);
    const c = new Date(completedAt); c.setHours(0,0,0,0);
    const diffDays = Math.round((today - c) / 86400000);
    if (diffDays === 0) return { key: 'today', label: `今日 · ${formatDateJP(c)}`, order: 0 };
    if (diffDays === 1) return { key: 'yesterday', label: `昨日 · ${formatDateJP(c)}`, order: 1 };
    if (diffDays <= 7) return { key: 'this-week', label: '今週', order: 2 };
    if (diffDays <= 30) return { key: 'this-month', label: '今月', order: 3 };
    return { key: 'earlier', label: 'それ以前', order: 4 };
  }

  // ---- Completed page ------------------------------------------
  function renderCompletedPage() {
    const list = $('#completed-list');
    if (!list) return;
    const all = completedTasks();
    list.innerHTML = '';

    // Stats
    const now = Date.now();
    const weekMs = 7 * 86400000;
    const weekCount = all.filter(t => (now - new Date(t.completedAt).getTime()) < weekMs).length;
    const weekStat = document.querySelector('[data-stat="this-week"]');
    const totalStat = document.querySelector('[data-stat="total"]');
    if (weekStat) weekStat.textContent = weekCount;
    if (totalStat) totalStat.textContent = all.length;

    if (all.length === 0) {
      list.innerHTML = `
        <div class="empty-hint-v2" style="max-width: 480px; margin: 40px auto;">
          まだ完了タスクはありません。<br>
          タスクを完了すると、ここに履歴が残ります。
        </div>`;
      return;
    }

    // Group by day offset
    const groups = {};
    all.forEach(t => {
      const g = dayOffsetLabel(t.completedAt || t.updatedAt);
      if (!groups[g.key]) groups[g.key] = { ...g, tasks: [] };
      groups[g.key].tasks.push(t);
    });

    Object.values(groups)
      .sort((a, b) => a.order - b.order)
      .forEach(g => {
        const wrap = document.createElement('div');
        wrap.className = 'mb-6';
        wrap.innerHTML = `
          <div class="flex items-center gap-2 mb-3 text-xs font-mono tracking-widest text-text-3 uppercase">
            <span>${g.label}</span>
            <div class="flex-1 h-px bg-border-muted"></div>
            <span>${g.tasks.length}件</span>
          </div>
          <div class="space-y-2" data-completed-group></div>
        `;
        const groupList = wrap.querySelector('[data-completed-group]');
        g.tasks.forEach(task => groupList.appendChild(createCompletedCard(task)));
        list.appendChild(wrap);
      });
  }

  function createCompletedCard(task) {
    const art = document.createElement('article');
    art.className = 'completed-card';
    art.dataset.taskId = task.id;
    const normalZone = task.normalZone || 'q4';
    const zoneLabel = ZONE_LABELS[normalZone] || 'Q4 あとで';
    const noteHtml = (task.note && task.note.trim())
      ? `<p class="completed-note">${escapeHtml(task.note)}</p>`
      : '';
    art.innerHTML = `
      <div class="completed-check"><span class="material-symbols-outlined" style="font-variation-settings: 'FILL' 1;">check_circle</span></div>
      <div class="completed-body">
        <div class="completed-meta-top">
          <span class="completed-time">${formatHM(task.completedAt)}</span>
          <span class="completed-origin ${normalZone}-origin">
            <span class="w-1.5 h-1.5 rounded-full bg-${normalZone}"></span>
            ${zoneLabel}
          </span>
        </div>
        <h3 class="completed-title">${escapeHtml(task.title || '(無題)')}</h3>
        ${noteHtml}
        <div class="completed-actions">
          <button class="action-btn" data-act="reopen" data-task="${task.id}">
            <span class="material-symbols-outlined text-[16px]">undo</span>未完了に戻す
          </button>
          <button class="action-btn action-delete" data-act="delete" data-task="${task.id}">
            <span class="material-symbols-outlined text-[16px]">delete</span>
          </button>
        </div>
      </div>
    `;
    return art;
  }

  function setupCompletedPageEvents() {
    const list = $('#completed-list');
    if (!list) return;
    list.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-act]');
      if (!btn) return;
      const id = btn.dataset.task;
      if (btn.dataset.act === 'reopen') {
        reopenTask(id);
        renderCompletedPage();
        renderSidebarCounts();
        renderStatusBar();
      } else if (btn.dataset.act === 'delete') {
        deleteTask(id);
        renderCompletedPage();
        renderSidebarCounts();
        renderStatusBar();
      }
    });
  }

  // ---- Today page ----------------------------------------------
  function renderTodayPage() {
    const overdueList = $('#today-overdue-list');
    const dueList = $('#today-due-list');
    if (!overdueList && !dueList) return;

    const today = todayString();
    const overdueTasks = sortTasks(activeTasks().filter(t => t.dueDate && t.dueDate < today));
    const todayTasks = sortTasks(activeTasks().filter(t => t.dueDate === today));

    if (overdueList) {
      overdueList.innerHTML = '';
      if (overdueTasks.length === 0) {
        overdueList.innerHTML = '<div class="empty-hint-v2">期限超過のタスクはありません</div>';
      } else {
        overdueTasks.forEach(t => overdueList.appendChild(createListCard(t)));
      }
    }
    if (dueList) {
      dueList.innerHTML = '';
      if (todayTasks.length === 0) {
        dueList.innerHTML = '<div class="empty-hint-v2">今日締切のタスクはありません</div>';
      } else {
        todayTasks.forEach(t => dueList.appendChild(createListCard(t)));
      }
    }

    // Stats
    const overdueStat = document.querySelector('[data-stat="today-overdue"]');
    const dueStat = document.querySelector('[data-stat="today-due"]');
    const overdueGroupCount = document.querySelector('[data-stat="today-overdue-count"]');
    const dueGroupCount = document.querySelector('[data-stat="today-due-count"]');
    if (overdueStat) overdueStat.textContent = overdueTasks.length;
    if (dueStat) dueStat.textContent = todayTasks.length;
    if (overdueGroupCount) overdueGroupCount.textContent = `${overdueTasks.length}件`;
    if (dueGroupCount) dueGroupCount.textContent = `${todayTasks.length}件`;
  }

  // ---- Overdue page --------------------------------------------
  function renderOverduePage() {
    const list = $('#overdue-list');
    if (!list) return;

    const today = todayString();
    const todayDate = new Date(today + 'T00:00:00');
    const overdue = activeTasks()
      .filter(t => t.dueDate && t.dueDate < today)
      .map(t => {
        const d = new Date(t.dueDate + 'T00:00:00');
        const daysOver = Math.round((todayDate - d) / 86400000);
        return { ...t, daysOver };
      })
      .sort((a, b) => b.daysOver - a.daysOver);

    const countEl = document.querySelector('[data-stat="overdue-count"]');
    const oldestEl = document.querySelector('[data-stat="overdue-oldest"]');
    if (countEl) countEl.textContent = overdue.length;
    if (oldestEl) oldestEl.textContent = overdue.length === 0 ? '—' : overdue[0].daysOver;

    // Call out: 件数次第で差し替え
    const callout = document.querySelector('[data-stat="overdue-callout"]');
    if (callout) callout.textContent = `${overdue.length} 件のタスクが期限を過ぎています`;

    list.innerHTML = '';
    if (overdue.length === 0) {
      list.innerHTML = `
        <div class="empty-hint-v2" style="max-width: 520px; margin: 40px auto;">
          🎉 期限超過のタスクはありません。<br>
          この状態を維持しましょう。
        </div>`;
      return;
    }

    // Group by severity
    const severe = overdue.filter(t => t.daysOver >= 2);
    const recent = overdue.filter(t => t.daysOver < 2);

    if (severe.length > 0) {
      const group = document.createElement('div');
      group.className = 'mb-6';
      group.innerHTML = `
        <div class="flex items-center gap-2 mb-3 text-xs font-mono tracking-widest text-text-3 uppercase">
          <span>2日以上経過</span>
          <div class="flex-1 h-px bg-border-muted"></div>
          <span>${severe.length}件</span>
        </div>
        <div class="space-y-2" data-group></div>
      `;
      const body = group.querySelector('[data-group]');
      severe.forEach(t => body.appendChild(createListCard(t, { daysOver: t.daysOver })));
      list.appendChild(group);
    }
    if (recent.length > 0) {
      const group = document.createElement('div');
      group.className = 'mb-6';
      group.innerHTML = `
        <div class="flex items-center gap-2 mb-3 text-xs font-mono tracking-widest text-text-3 uppercase">
          <span>1日前</span>
          <div class="flex-1 h-px bg-border-muted"></div>
          <span>${recent.length}件</span>
        </div>
        <div class="space-y-2" data-group></div>
      `;
      const body = group.querySelector('[data-group]');
      recent.forEach(t => body.appendChild(createListCard(t, { daysOver: t.daysOver })));
      list.appendChild(group);
    }
  }

  // ---- Generic list card (today / overdue page 共通) ----------
  function createListCard(task, opts = {}) {
    const art = document.createElement('article');
    art.className = `task-card ${task.zone}-card`;
    art.dataset.taskId = task.id;
    const due = dueBadge(task);
    const dueLabel = opts.daysOver
      ? `期限超過 ${task.dueDate.slice(5).replace('-','/')}（${opts.daysOver}日前）`
      : due.label;
    const noteText = (task.note && task.note.trim()) || '';
    const noteHtml = noteText
      ? `<p class="task-note" title="${escapeHtml(noteText)}">${escapeHtml(noteText)}</p>`
      : '';
    const originZone = task.normalZone || 'q4';
    art.innerHTML = `
      <div class="task-handle"><span class="material-symbols-outlined">drag_indicator</span></div>
      <div class="task-body">
        <h3 class="task-title">${escapeHtml(task.title || '(無題)')}</h3>
        ${noteHtml}
        <div class="task-meta">
          <span class="badge badge-${due.className}">${dueBadgeIcon(due.className)}${escapeHtml(dueLabel)}</span>
          <span class="badge badge-note">${ZONE_LABELS[originZone] || 'Q4 あとで'}</span>
          <span class="task-time">更新 ${formatRelative(task.updatedAt)}</span>
        </div>
        <div class="task-actions">
          <button class="action-btn action-complete" data-act="complete" data-task="${task.id}"><span class="material-symbols-outlined text-[18px]">check_circle</span>完了</button>
          ${opts.daysOver ? '<button class="action-btn" data-act="detail" data-task="' + task.id + '"><span class="material-symbols-outlined text-[18px]">edit_calendar</span>締切再設定</button>' : ''}
          <button class="action-btn" data-act="detail" data-task="${task.id}"><span class="material-symbols-outlined text-[18px]">edit_note</span>詳細</button>
          <button class="action-btn action-delete" data-act="delete" data-task="${task.id}"><span class="material-symbols-outlined text-[18px]">delete</span></button>
        </div>
      </div>
    `;
    return art;
  }

  function dueBadgeIcon(cls) {
    if (cls === 'overdue') return '<span class="material-symbols-outlined" style="font-size:14px;font-variation-settings:\'FILL\' 1;">warning</span> ';
    if (cls === 'today') return '<span class="material-symbols-outlined" style="font-size:14px">schedule</span> ';
    if (cls === 'due') return '<span class="material-symbols-outlined" style="font-size:14px">event</span> ';
    return '';
  }

  function setupListPageEvents(listRoot, rerender) {
    if (!listRoot) return;
    listRoot.addEventListener('click', (e) => {
      const btn = e.target.closest('button[data-act]');
      if (!btn) return;
      const id = btn.dataset.task;
      const act = btn.dataset.act;
      if (act === 'complete') completeTask(id);
      else if (act === 'delete') deleteTask(id);
      else if (act === 'detail') {
        const t = getTask(id);
        if (t) openTaskModal(t);
        return; // モーダル送信側で再描画される
      }
      rerender();
      renderSidebarCounts();
      renderStatusBar();
    });
  }

  function setupSurvival() {
    // Survival ページに入ったら、まだ Survival 状態じゃなければ突入処理
    if (!uiState.isSurvival) {
      enterSurvival();
    }
    renderSurvivalView();
    setupSurvivalDnD();
    setupCountdown();

    // Exit button
    const exitBtn = $('#exit-survival');
    if (exitBtn) {
      exitBtn.addEventListener('click', (e) => {
        exitSurvival();
      });
    }
  }

  // ---- Boot -----------------------------------------------------
  loadAll();
  console.info('[NeuroMatrix] data layer ready.', { tasks: tasks.length, survival: uiState.isSurvival });

  // index.html 専用: マトリクスが DOM にあればセットアップ
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', bootUI);
  } else {
    bootUI();
  }

  function bootUI() {
    // どの画面でも常に更新: サイドバーの件数とStatusBar
    renderSidebarCounts();
    renderStatusBar();

    // ダッシュボード画面: 象限の再描画とモーダル/Undo/D&Dの配線
    if ($('[data-zone-body="q1"]')) {
      renderAll();
      setupModal(renderAll);
      setupUndoButton();
      setupMatrixDnD();
      console.info('[NeuroMatrix] dashboard UI bound.');
      return;
    }

    // Survivalモード画面: スロット描画 + D&D + カウントダウン
    if ($('[data-zone-body="slot-must"]')) {
      setupSurvival();
      console.info('[NeuroMatrix] survival UI bound.');
      return;
    }

    // Completed / Today / Overdue ページ
    if ($('#completed-list')) {
      renderCompletedPage();
      setupCompletedPageEvents();
      // 完了一覧では編集モーダルは呼ばない（reopen→詳細編集の動線なので）
      console.info('[NeuroMatrix] completed UI bound.');
      return;
    }
    if ($('#today-overdue-list') || $('#today-due-list')) {
      renderTodayPage();
      setupListPageEvents($('#today-overdue-list'), renderTodayPage);
      setupListPageEvents($('#today-due-list'), renderTodayPage);
      setupModal(renderTodayPage);
      console.info('[NeuroMatrix] today UI bound.');
      return;
    }
    if ($('#overdue-list')) {
      renderOverduePage();
      setupListPageEvents($('#overdue-list'), renderOverduePage);
      setupModal(renderOverduePage);
      console.info('[NeuroMatrix] overdue UI bound.');
      return;
    }

    console.info('[NeuroMatrix] sub-page sidebar bound.');
  }
})();
