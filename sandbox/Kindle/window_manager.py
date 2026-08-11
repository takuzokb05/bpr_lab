"""
Window Manager for Kindle Auto-Capture Tool

Kindle for PC のウィンドウ検出・アクティブ化・クライアント領域の取得を担当する。
検出はタイトルの部分一致ではなく「所有プロセスの実行ファイル名」を主判定に使う
（本ツールを Kindle フォルダから起動した際にターミナルウィンドウを誤検出しないため）。
"""

import ctypes
from ctypes import wintypes
import os
import time
from typing import Any

import pygetwindow as gw


# --- Win32 API バインディング -------------------------------------------------

_user32 = ctypes.WinDLL("user32", use_last_error=True)
_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# OpenProcess のアクセス権。実行ファイル名の取得だけなら LIMITED で十分
# （PROCESS_QUERY_INFORMATION と違い、権限の高いプロセスにも開ける場合がある）
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

_user32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
_user32.GetWindowThreadProcessId.restype = wintypes.DWORD

_user32.SetForegroundWindow.argtypes = [wintypes.HWND]
_user32.SetForegroundWindow.restype = wintypes.BOOL

_user32.GetForegroundWindow.argtypes = []
_user32.GetForegroundWindow.restype = wintypes.HWND

_user32.GetClientRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
_user32.GetClientRect.restype = wintypes.BOOL

_user32.ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.POINT)]
_user32.ClientToScreen.restype = wintypes.BOOL

_user32.GetWindowTextW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
_user32.GetWindowTextW.restype = ctypes.c_int

_user32.IsWindow.argtypes = [wintypes.HWND]
_user32.IsWindow.restype = wintypes.BOOL

_user32.IsWindowVisible.argtypes = [wintypes.HWND]
_user32.IsWindowVisible.restype = wintypes.BOOL

_kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
_kernel32.OpenProcess.restype = wintypes.HANDLE

_kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
_kernel32.QueryFullProcessImageNameW.restype = wintypes.BOOL

_kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
_kernel32.CloseHandle.restype = wintypes.BOOL

_kernel32.GetCurrentProcessId.argtypes = []
_kernel32.GetCurrentProcessId.restype = wintypes.DWORD


# Kindle 本体の実行ファイル名（最優先で採用する）
KINDLE_PROCESS_NAME = "kindle.exe"

# タイトル一致でフォールバック検出する際、絶対に採用してはいけないプロセス群。
# 本ツールの作業フォルダ名が「Kindle」のため、ターミナル（起動元シェル）も
# エクスプローラー（フォルダを開いた窓は「Kindle - エクスプローラー」になる）も
# タイトルに "kindle" を含んでしまい、実測で誤検出することを確認済み。
EXCLUDED_PROCESS_NAMES = frozenset(
    {
        # コンソール・エディタ系
        "windowsterminal.exe",
        "conhost.exe",
        "cmd.exe",
        "powershell.exe",
        "pwsh.exe",
        "wt.exe",
        "code.exe",
        # ファイルマネージャ（Kindle for PC のウィンドウがこれに属することはない）
        "explorer.exe",
    }
)


class WindowManager:
    """Kindle for PC のウィンドウ検出・前面化・撮影領域の取得を管理する"""

    def __init__(self) -> None:
        # pygetwindow の Win32Window（型スタブが無いため Any 扱い）
        self.kindleWindow: Any | None = None
        self.hwnd: int | None = None
        self.windowTitle: str | None = None

    # --- 内部ヘルパー ---------------------------------------------------------

    @staticmethod
    def _getWindowPid(hwnd: int) -> int | None:
        """ウィンドウを所有するプロセスIDを返す（取得失敗時 None）"""
        pid = wintypes.DWORD(0)
        _user32.GetWindowThreadProcessId(wintypes.HWND(hwnd), ctypes.byref(pid))
        return int(pid.value) if pid.value else None

    @staticmethod
    def _getProcessImageName(pid: int) -> str | None:
        """
        プロセスIDから実行ファイル名（basename・小文字）を返す

        Args:
            pid: プロセスID

        Returns:
            Optional[str]: "kindle.exe" のような小文字のファイル名。取得失敗時 None
        """
        handle = _kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not handle:
            # 権限不足・プロセス終了済みなど。呼び出し側で None を許容する
            return None

        try:
            bufferSize = wintypes.DWORD(1024)
            buffer = ctypes.create_unicode_buffer(bufferSize.value)
            ok = _kernel32.QueryFullProcessImageNameW(
                handle, 0, buffer, ctypes.byref(bufferSize)
            )
            if not ok:
                return None
            return os.path.basename(buffer.value).lower()
        finally:
            _kernel32.CloseHandle(handle)

    def _adoptWindow(self, window: Any, hwnd: int, title: str) -> None:
        """検出したウィンドウを採用して内部状態に保持する"""
        self.kindleWindow = window
        self.hwnd = hwnd
        self.windowTitle = title

    @staticmethod
    def _getForegroundHwnd() -> int:
        """現在アクティブなウィンドウのhwndを返す（無い場合は0）"""
        return int(_user32.GetForegroundWindow() or 0)

    @staticmethod
    def _getWindowArea(window: Any) -> int:
        """ウィンドウの面積を返す（取得できなければ0）"""
        try:
            return int(window.width) * int(window.height)
        except Exception:
            return 0

    # --- 公開API -------------------------------------------------------------

    def findKindleWindow(self) -> bool:
        """
        Kindle for PC のウィンドウを検出して保持する

        判定順:
          1. 所有プロセスが kindle.exe のウィンドウ（最優先）。複数ある場合
             （ライブラリ画面と本文ビューアが別ウィンドウで開いている等）は、
             アクティブなウィンドウ → なければ面積最大のウィンドウを採用する
          2. フォールバック: タイトルに "kindle" を含み、かつ自プロセスでも
             除外プロセス（EXCLUDED_PROCESS_NAMES）でもないウィンドウ

        Returns:
            bool: 検出できたら True
        """
        try:
            windows = gw.getAllWindows()
        except Exception as e:
            print(f"❌ ウィンドウ列挙エラー: {e}")
            return False

        currentPid = int(_kernel32.GetCurrentProcessId())
        kindleCandidates: list[tuple[Any, int, str]] = []
        fallbackCandidate: tuple[Any, int, str, str | None] | None = None

        for window in windows:
            hwnd = getattr(window, "_hWnd", None)
            if not hwnd:
                continue

            # 非表示ウィンドウ（隠しヘルパー等）は対象外。最小化は IsWindowVisible=True なので残る
            if not _user32.IsWindowVisible(wintypes.HWND(hwnd)):
                continue

            try:
                title = window.title or ""
            except Exception:
                continue

            if not title.strip():
                continue

            pid = self._getWindowPid(hwnd)
            exeName = self._getProcessImageName(pid) if pid else None

            # 1. プロセス名による確実な判定（複数ありうるので全部集めて後で選ぶ）
            if exeName == KINDLE_PROCESS_NAME:
                kindleCandidates.append((window, hwnd, title))
                continue

            # 2. フォールバック候補（最初の1件のみ保持）
            if fallbackCandidate is None and "kindle" in title.lower():
                if pid == currentPid:
                    continue  # 自分自身のウィンドウ
                if exeName in EXCLUDED_PROCESS_NAMES:
                    continue  # ターミナル・エディタ・エクスプローラーの類
                fallbackCandidate = (window, hwnd, title, exeName)

        if kindleCandidates:
            # 本文ビューアとライブラリ画面が同時に開いていることがあるため、
            # 「いま操作している窓」を優先し、判断材料が無ければ面積最大を選ぶ
            foregroundHwnd = self._getForegroundHwnd()
            for window, hwnd, title in kindleCandidates:
                if hwnd == foregroundHwnd:
                    self._adoptWindow(window, hwnd, title)
                    print(f"✅ Kindleウィンドウを検出: {title}（アクティブなウィンドウ）")
                    return True

            window, hwnd, title = max(kindleCandidates, key=lambda c: self._getWindowArea(c[0]))
            self._adoptWindow(window, hwnd, title)
            if len(kindleCandidates) > 1:
                print(
                    f"✅ Kindleウィンドウを検出: {title}"
                    f"（{len(kindleCandidates)}個の候補から最大のものを採用）"
                )
            else:
                print(f"✅ Kindleウィンドウを検出: {title}")
            return True

        if fallbackCandidate is not None:
            window, hwnd, title, exeName = fallbackCandidate
            self._adoptWindow(window, hwnd, title)
            print(
                f"⚠️ kindle.exe が見つからないため、タイトル一致で採用します: "
                f"{title} ({exeName or '不明なプロセス'})"
            )
            return True

        print("❌ Kindleウィンドウが見つかりません。Kindle for PCを起動してください。")
        return False

    def activateWindow(self) -> bool:
        """
        Kindleウィンドウを前面に出す

        pygetwindow の activate() は Windows で例外を投げることがあるため、
        失敗時は Win32 の SetForegroundWindow にフォールバックし、計3回まで再試行する。

        成否は API の戻り値ではなく GetForegroundWindow で事後確認する。Windows は
        フォアグラウンドロック（他プロセスが操作中など）で前面化を黙って拒否することが
        あり、戻り値だけを信じるとフォーカスの無いまま撮影を始めてしまうため。

        Returns:
            bool: 実際に前面化できたら True
        """
        if self.kindleWindow is None and not self.findKindleWindow():
            return False

        window = self.kindleWindow
        hwndValue = self.hwnd
        if window is None or hwndValue is None:
            return False

        for attempt in range(1, 4):
            try:
                # 最小化されていれば元に戻す
                if window.isMinimized:
                    window.restore()
            except Exception as e:
                print(f"⚠️ ウィンドウ復元に失敗 (試行 {attempt}/3): {e}")

            try:
                window.activate()
            except Exception as e:
                # pygetwindow の activate() は SetForegroundWindow 失敗時に例外を投げる
                print(f"⚠️ activate() 失敗 (試行 {attempt}/3): {e}")

            if self._getForegroundHwnd() != hwndValue:
                _user32.SetForegroundWindow(wintypes.HWND(hwndValue))

            # 事後条件: 本当に前面に出たか確認する
            if self._getForegroundHwnd() == hwndValue:
                print("✅ Kindleウィンドウをアクティブ化しました")
                return True

            print(f"⚠️ 前面化を確認できませんでした (試行 {attempt}/3)")
            time.sleep(0.3)

        print("❌ Kindleウィンドウをアクティブ化できませんでした")
        return False

    def getClientRect(self) -> tuple[int, int, int, int] | None:
        """
        クライアント領域（タイトルバー・枠を除いた描画領域）のスクリーン座標を返す

        Returns:
            Optional[Tuple[int, int, int, int]]: (x, y, width, height)。失敗時 None
        """
        if self.hwnd is None and not self.findKindleWindow():
            return None

        hwndValue = self.hwnd
        if hwndValue is None:
            return None

        hwnd = wintypes.HWND(hwndValue)

        rect = wintypes.RECT()
        if not _user32.GetClientRect(hwnd, ctypes.byref(rect)):
            print("❌ クライアント領域の取得に失敗しました (GetClientRect)")
            return None

        # GetClientRect は左上が (0, 0) のクライアント座標を返すのでスクリーン座標に変換する
        origin = wintypes.POINT(0, 0)
        if not _user32.ClientToScreen(hwnd, ctypes.byref(origin)):
            print("❌ クライアント座標の変換に失敗しました (ClientToScreen)")
            return None

        width = int(rect.right - rect.left)
        height = int(rect.bottom - rect.top)

        return (int(origin.x), int(origin.y), width, height)

    def getWindowTitle(self) -> str | None:
        """
        現在のウィンドウタイトルを取り直して返す（書名抽出用）

        保持しているタイトルは検出時点のものなので、本を切り替えた場合に備えて
        毎回 Win32 から読み直す。

        Returns:
            Optional[str]: 現在のタイトル。取得できなければ None
        """
        hwndValue = self.hwnd
        if hwndValue is None:
            return None

        hwnd = wintypes.HWND(hwndValue)
        if not _user32.IsWindow(hwnd):
            return None

        buffer = ctypes.create_unicode_buffer(1024)
        length = _user32.GetWindowTextW(hwnd, buffer, len(buffer))
        if length <= 0:
            return None

        self.windowTitle = buffer.value
        return buffer.value

    def isWindowValid(self) -> bool:
        """
        保持しているウィンドウ参照がまだ有効か確認する

        Returns:
            bool: 有効なら True
        """
        hwndValue = self.hwnd
        if hwndValue is not None and not _user32.IsWindow(wintypes.HWND(hwndValue)):
            return False

        try:
            if not self.kindleWindow:
                return False

            # プロパティにアクセスできるかで生存を確認する
            _ = self.kindleWindow.title
            return True

        except Exception:
            return False
