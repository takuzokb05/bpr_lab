import json, shutil, openpyxl, os

SRC = '/root/.claude/uploads/54b845d3-b34b-5735-ba7a-d98ad5a184da/29ed86ec-________URL__.xlsx'
SCR = '/tmp/claude-0/-home-user-bpr-lab/54b845d3-b34b-5735-ba7a-d98ad5a184da/scratchpad'
OUTDIR = '/home/user/bpr_lab/sandbox/横浜市公示送達URL確認'
os.makedirs(OUTDIR, exist_ok=True)
DST = os.path.join(OUTDIR, '横浜市_公示送達URL一覧_確認済み_20260824.xlsx')

results = {(r['sheet'], r['row']): r for r in json.load(open(os.path.join(SCR,'results.json')))}

shutil.copyfile(SRC, DST)          # 書式・シート構成を保持したまま上書き編集
wb = openpyxl.load_workbook(DST)

summary = {}
anomalies = []
for ws in wb.worksheets:
    for r in range(6, 24):
        rec = results[(ws.title, r)]
        code, err, kw = rec['code'], rec['err_page'], rec['has_kw']

        if code == 200 and not err and kw:
            state = 'あり'
            note = f"HTTP {code}／title「{rec['title']}」／本文に「公示送達」{rec['kw_count']}件"
        elif code == 404:
            state = 'なし'
            note = f"HTTP {code}（横浜市共通エラーページ：title「{rec['title']}」）"
        elif code == 200 and err:
            state = 'なし'
            note = f"HTTP 200 だが本文はエラーページ（title「{rec['title']}」）＝ソフト404判定"
            anomalies.append((ws.title, rec['ward'], 'ソフト404（200＋エラーページ）'))
        else:
            state = 'なし'
            note = f"HTTP {code}／title「{rec.get('title','')}」／要確認"
            anomalies.append((ws.title, rec['ward'], f'想定外 HTTP {code}'))

        # 末尾スラッシュ正規化以外のリダイレクトは異常として記録
        if rec.get('effective') and rec['effective'] != rec['url'] + '/':
            anomalies.append((ws.title, rec['ward'], f"想定外リダイレクト先 {rec['effective']}"))
        if rec.get('attempts', 1) > 1:
            note += f"／初回取得失敗のためリトライ{rec['attempts']-1}回（結果は再検証で同一）"
            anomalies.append((ws.title, rec['ward'], f"取得リトライ {rec['attempts']-1}回"))

        ws.cell(r, 3).value = state
        ws.cell(r, 4).value = note
        summary.setdefault(ws.title, {'あり':0,'なし':0})[state] += 1

wb.save(DST)
print('saved:', DST)
for s, c in summary.items():
    print(f"{s}: あり={c['あり']} なし={c['なし']}")
print('anomalies:', anomalies if anomalies else 'なし')
