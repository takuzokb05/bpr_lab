/* =========================================================
   Neuro Matrix Task OS — theme.js
   Light / Dark / Auto の切替を全画面で一元管理する。
   FOUC 防止のため各 HTML の <head> で最初に読み込むこと。
   ========================================================= */
(() => {
  'use strict';
  const KEY = 'neuro_matrix_theme';
  const VALID = ['light', 'dark', 'auto'];

  function getPref() {
    const stored = localStorage.getItem(KEY);
    return VALID.includes(stored) ? stored : 'light';
  }

  function resolve(pref) {
    if (pref === 'auto') {
      return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }
    return pref;
  }

  function apply(pref) {
    const resolved = resolve(pref);
    document.documentElement.classList.toggle('dark', resolved === 'dark');
    document.documentElement.dataset.themePref = pref;
    document.documentElement.dataset.themeResolved = resolved;
  }

  function setPref(pref) {
    if (!VALID.includes(pref)) return;
    localStorage.setItem(KEY, pref);
    apply(pref);
    window.dispatchEvent(new CustomEvent('neuro-theme-change', { detail: { pref, resolved: resolve(pref) } }));
  }

  // Initial apply (before paint to avoid FOUC)
  apply(getPref());

  // Auto mode reacts to OS change
  if (window.matchMedia) {
    try {
      window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', () => {
        if (getPref() === 'auto') apply('auto');
      });
    } catch (_) { /* Safari < 14 */ }
  }

  // Public API
  window.NeuroTheme = {
    get: getPref,
    set: setPref,
    apply: () => apply(getPref()),
    resolve: () => resolve(getPref()),
  };
})();
