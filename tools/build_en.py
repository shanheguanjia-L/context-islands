#!/usr/bin/env python3
"""從繁體中文版的 index.html 產生英文版 en/index.html。

- 程式碼只有一份（根目錄 index.html），英文版靠下面的對照表替換介面文字。
- 教學內容在 en/data.js，是人工翻譯的，不由本腳本產生；改了 ../data.js 要記得同步改 en/data.js。
- 腳本會檢查：每一條對照都要在原稿找得到，而且替換完不能殘留任何中文。
  介面文字改了卻沒更新對照表，腳本會直接報錯，不會默默產生半中半英的頁面。

用法：python3 tools/build_en.py
"""
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
OUT = ROOT / "en"

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import langs  # noqa: E402

# (原文, 英文)。依序替換：長的、特定的放前面，短的通用詞放最後。
PAIRS = [
    # ---- head / header ----
    ('lang="zh-Hant-TW"', 'lang="en"'),
    ("<title>脈絡群島｜提示詞工程與脈絡工程：從零到內化</title>", "<title>Context Islands | Prompt & Context Engineering, from Zero to Internalized</title>"),
    ('<div class="sub">提示詞工程與脈絡工程：從零到內化</div>', '<div class="sub">Prompt & context engineering, from zero to internalized</div>'),
    ("go('map')\">脈絡群島</h1>", "go('map')\">Context Islands</h1>"),
    ('<span>徽章 <b id="sBadge">', '<span>Badges <b id="sBadge">'),
    ('<span>預測點 <b id="sPts">', '<span>Prediction pts <b id="sPts">'),
    ('<span>番茄鐘 <b id="sPomo">', '<span>Pomodoros <b id="sPomo">'),
    ("go('map')\">航海圖</button>", "go('map')\">Sea chart</button>"),
    ("go('guide')\">怎麼玩</button>", "go('guide')\">How to play</button>"),
    ("go('book')\">咒語書</button>", "go('book')\">Spellbook</button>"),
    ("go('log')\">紀錄</button>", "go('log')\">Log</button>"),
    # ---- CSS / JS 註解 ----
    ("/* 地圖 */", "/* map */"), ("/* 島內 */", "/* island */"), ("/* 番茄鐘 */", "/* pomodoro */"),
    ("/* ---------- 狀態 ---------- */", "/* ---------- state ---------- */"),
    ("/* ---------- 工具 ---------- */", "/* ---------- helpers ---------- */"),
    ("/* ---------- 通關判定（內化四層次） ---------- */", "/* ---------- pass rules (four levels of internalization) ---------- */"),
    ("/* ---------- 路由 ---------- */", "/* ---------- routing ---------- */"),
    ("/* ---------- 航海圖 ---------- */", "/* ---------- sea chart ---------- */"),
    ("/* ---------- 島內 ---------- */", "/* ---------- island ---------- */"),
    ("/* 黃金集計分表（第 10 島） */", "/* golden set scorecard (Island 10) */"),
    ("/* P6：抽問＋Boss＋黑天鵝 */", "/* P6: quiz + boss + black swan */"),
    ("/* 第 12 島：畢業專案 */", "/* Island 12: capstone */"),
    ("/* 修城（間隔複習） */", "/* castle repair (spaced review) */"),
    ("/* ---------- 怎麼玩 ---------- */", "/* ---------- how to play ---------- */"),
    ("/* ---------- 咒語書 ---------- */", "/* ---------- spellbook ---------- */"),
    ("/* ---------- 紀錄 ---------- */", "/* ---------- log ---------- */"),
    ("/* ---------- 對話框 ---------- */", "/* ---------- dialog ---------- */"),
    ("/* ---------- 番茄鐘 ---------- */", "/* ---------- pomodoro ---------- */"),
    ("/* ---------- 啟動 ---------- */", "/* ---------- boot ---------- */"),
    # ---- 番茄鐘面板 ----
    ('<div class="m" id="pMode">專注 25 分鐘・一次只做一件事</div>', '<div class="m" id="pMode">Focus 25 min · one thing at a time</div>'),
    ('<div class="m" id="pCtx">未綁定回合</div>', '<div class="m" id="pCtx">Not linked to a round</div>'),
    ('id="pStart">開始</button>', 'id="pStart">Start</button>'),
    ('id="pReset">重設</button>', 'id="pReset">Reset</button>'),
    ('title="記下被打斷的原因">被打斷</button>', 'title="Log why you were interrupted">Interrupted</button>'),
    ('style="margin-left:auto">收合</button>', 'style="margin-left:auto">Collapse</button>'),
    # ---- 回合名稱與評分表 ----
    ('["P1","偵察","謎題與預測"]', '["P1","Scout","Puzzle and prediction"]'),
    ('["P2","解碼","原理拆解"]', '["P2","Decode","Principle breakdown"]'),
    ('["P3","實驗室","預測—實驗—對照"]', '["P3","Lab","Predict, test, compare"]'),
    ('["P4","傳授對決","費曼講解"]', '["P4","Teach-off","Feynman explanation"]'),
    ('["P5","補給","補漏與類比"]', '["P5","Resupply","Fill gaps, find analogies"]'),
    ('["P6","Boss 戰","驗收"]', '["P6","Boss fight","Check"]'),
    ('["準確性", ["有重大錯誤","大致正確但含糊","正確","正確且能指出限制"]]', '["Accuracy", ["Major errors","Mostly right but vague","Correct","Correct, and names the limits"]]'),
    ('["簡單性", ["大量未解釋術語","術語多","術語都有解釋","12 歲孩子聽得懂"]]', '["Simplicity", ["Lots of unexplained jargon","Jargon-heavy","All jargon explained","A 12-year-old would get it"]]'),
    ('["類比",   ["無","類比不貼切","類比貼切","貼切且說明何處不適用"]]', '["Analogy",   ["None","Analogy doesn\'t fit","Analogy fits","Fits, and says where it breaks down"]]'),
    ('["因果",   ["只說「是什麼」","有「因為」但跳步","因果鏈完整","完整且能預測變化"]]', '["Cause",   ["Only says what it is","Has a \\"because\\" but skips steps","Complete causal chain","Complete, and predicts changes"]]'),
    ('["追問",   ["答不出","答一半","答得出","答得出且能延伸到新情境"]]', '["Follow-up",   ["Can\'t answer","Half an answer","Answers it","Answers it and extends to new situations"]]'),
    # ---- toast / 小提示 ----
    ('toast("+"+n+" 預測點")', 'toast("+"+n+" prediction pts")'),
    ('toast("已複製，貼到你的 AI 工具試試")', 'toast("Copied — paste it into your AI tool")'),
    ('toast("複製失敗，請手動選取")', 'toast("Copy failed — please select it manually")'),
    # ---- 通關對話框 ----
    ('<h2>通關：${esc(d.name)}</h2><p>你取得了徽章「<b>${esc(d.badge)}</b>」。</p>', '<h2>Island cleared: ${esc(d.name)}</h2><p>You earned the badge <b>${esc(d.badge)}</b>.</p>'),
    ('<p class="muted">提醒：超過 7 天沒複習，徽章會在航海圖上變暗（知識城堡風化）。回來答對一題「修城」就能恢復。</p>', '<p class="muted">Note: if you go more than 7 days without reviewing, the badge fades on the sea chart (your knowledge castle erodes). Come back and answer one \\"castle repair\\" question to restore it.</p>'),
    ('`<p>下一站：${esc((isl(id+1)||{}).name||"")}</p>`', '`<p>Next stop: ${esc((isl(id+1)||{}).name||"")}</p>`'),
    ("go('map')\">回航海圖</button><button class=\"btn ghost\" onclick=\"closeDlg()\">留在這裡</button>", "go('map')\">Back to the sea chart</button><button class=\"btn ghost\" onclick=\"closeDlg()\">Stay here</button>"),
    # ---- 航海圖 ----
    ("<h2>模型之海航海圖</h2>", "<h2>Chart of the Model Sea</h2>"),
    ('<p class="lead">你是一名「AI 馴服師學徒」。王國的人想用 AI，卻不敢信任它。每座島上住著一隻「失效怪物」——一種真實的 AI 失敗方式。<b>打贏的方法只有一個：講得出它為什麼會發生。</b></p>',
     '<p class="lead">You are an apprentice AI tamer. The people of the kingdom want to use AI, but don\'t dare trust it. On every island lives a \\"failure monster\\" — a real way AI goes wrong. <b>There is only one way to beat it: be able to explain why it happens.</b></p>'),
    ('<b>第一次來？</b> 先花兩分鐘看「<a href="#guide" onclick="go(\'guide\');return false">怎麼玩</a>」，再從初始之港出發。每座島約 6 顆番茄鐘（含休息約 3 小時），可以分幾天完成。',
     '<b>First time here?</b> Spend two minutes on <a href="#guide" onclick="go(\'guide\');return false">How to play</a>, then set sail from the Harbor of Beginnings. Each island takes about 6 pomodoros (about 3 hours with breaks) and can be spread over several days.'),
    ('<b>知識城堡風化中：</b>${dims.map(d=>esc(d.name)).join("、")} 超過 7 天沒複習。', '<b>Knowledge castle eroding:</b> ${dims.map(d=>esc(d.name)).join(", ")} not reviewed for over 7 days.'),
    ('repair(${dims[0].id})">修城：答一題</button>', 'repair(${dims[0].id})">Repair: answer one question</button>'),
    ('<span class="pill warn">進行中</span>', '<span class="pill warn">In progress</span>'),
    ('<span class="pill">變灰＝需要複習</span>', '<span class="pill">Greyed out = needs review</span>'),
    (' 自由模式（全部解鎖，適合講師備課）</label>', ' Free mode (unlock everything — for instructors preparing)</label>'),
    ('aria-label="第 ${d.id} 週 ${esc(d.name)}"', 'aria-label="Week ${d.id}: ${esc(d.name)}"'),
    ('<span class="wk">第 ${d.id} 週・${esc(d.stage)}</span>', '<span class="wk">Week ${d.id} · ${esc(d.stage)}</span>'),
    ('<span class="bs">Boss：${esc(d.boss)}</span>', '<span class="bs">Boss: ${esc(d.boss)}</span>'),
    ('`<span class="pill warn">${doneN}/6 回合</span>`', '`<span class="pill warn">${doneN}/6 rounds</span>`'),
    ('`<span class="pill">可出發</span>`', '`<span class="pill">Ready to sail</span>`'),
    ('`<span class="pill warn">需修城</span>`', '`<span class="pill warn">Needs repair</span>`'),
    # ---- 島內 ----
    ("`<p>這座島還沒解鎖。</p>`", "`<p>This island is still locked.</p>`"),
    ("go('map')\">← 航海圖</a>", "go('map')\">← Sea chart</a>"),
    ("<h2>第 ${d.id} 島・${esc(d.name)}</h2>", "<h2>Island ${d.id} · ${esc(d.name)}</h2>"),
    ('${esc(d.topic)}　｜　Boss：<b style="color:var(--coral)">${esc(d.boss)}</b>　｜　徽章：${esc(d.badge)}', '${esc(d.topic)} &nbsp;|&nbsp; Boss: <b style="color:var(--coral)">${esc(d.boss)}</b> &nbsp;|&nbsp; Badge: ${esc(d.badge)}'),
    ('<div class="muted">必須內化：${esc(d.core)}</div>', '<div class="muted">Must internalize: ${esc(d.core)}</div>'),
    ('[["交付物","六個回合都寫完",L.L1],["說明","畢業評分 ≥ 60 分",L.L2],["證據","交付物＋綜合診斷",L.L3],["最終 Boss","綜合診斷 3 題全對",L.L4]]',
     '[["Deliverables","All six rounds written",L.L1],["Rationale","Capstone score ≥ 60",L.L2],["Evidence","Deliverables + combined diagnosis",L.L3],["Final boss","All 3 combined diagnoses right",L.L4]]'),
    ('[["層次 1 複述","抽問 4 題答對 3 題",L.L1],["層次 2 解釋","費曼講解平均 ≥ 2 分",L.L2],["層次 3 預測","預測有理由、落差有原因",L.L3],["層次 4 診斷","Boss 戰診斷成功",L.L4]]',
     '[["Level 1 Recall","3 of 4 quiz questions right",L.L1],["Level 2 Explain","Feynman score averages ≥ 2",L.L2],["Level 3 Predict","Predictions have reasons, gaps have causes",L.L3],["Level 4 Diagnose","Boss diagnosed correctly",L.L4]]'),
    ('setRound(${id},${r-1})">← 上一回合</button>', 'setRound(${id},${r-1})">← Previous round</button>'),
    ('pomoFor(${id},${r})">用番茄鐘專注這一回合</button>', 'pomoFor(${id},${r})">Focus on this round with a pomodoro</button>'),
    ('setRound(${id},${r+1})">下一回合 →</button>', 'setRound(${id},${r+1})">Next round →</button>'),
    # P1
    ('head("P1 偵察","謎題與預測","先猜，再學。<b>預測錯誤是最有價值的學習時刻</b>——前提是你先寫下理由。這一回合不會告訴你答案。")',
     'head("P1 Scout","Puzzle and prediction","Guess first, then learn. <b>A wrong prediction is the most valuable learning moment</b> — as long as you wrote down your reasoning first. This round won\'t tell you the answer.")'),
    ('<span class="tag">怪物現身卡・${esc(d.boss)}</span>', '<span class="tag">Monster card · ${esc(d.boss)}</span>'),
    ('<label class="f" for="p1r">我預測……因為……（寫下你的理由，至少一句）</label>', '<label class="f" for="p1r">I predict… because… (write your reasoning — at least one sentence)</label>'),
    ('placeholder="例如：我猜是 B，因為……"', 'placeholder="e.g. I think it\'s B, because…"'),
    ('lockP1(${id})">押下預測點</button>', 'lockP1(${id})">Lock in my prediction</button>'),
    ('`<span class="pill ok">已押注，到 P2 解碼看答案</span>`', '`<span class="pill ok">Locked in — see the answer in P2 Decode</span>`'),
    # P2
    ('head("P2 解碼","原理拆解","讀完原理後，把因果鏈按順序拼起來，拼出你自己的「原理地圖」。")', 'head("P2 Decode","Principle breakdown","After reading the principle, put the causal chain in order to build your own principle map.")'),
    ('">謎題答案：<b>${esc(p.options[p.answer])}</b><br>你在 P1 選的是：${esc(p.options[st.p1.choice]??"（未作答）")}${st.p1.choice===p.answer?"　→ 預測正確。":"　→ 預測錯了，很好：讀完下面的原理，在 P3 寫下你當初卡在哪。"}',
     '">Answer: <b>${esc(p.options[p.answer])}</b><br>Your pick in P1: ${esc(p.options[st.p1.choice]??"(not answered)")}${st.p1.choice===p.answer?" → Prediction correct.":" → Prediction wrong — good. Read the principle below, then write in P3 where you got stuck."}'),
    ("<h3>拼出原理地圖</h3>", "<h3>Build the principle map</h3>"),
    ('<p class="muted">依因果順序，點選下方的卡片。點錯了按「重排」。</p>', '<p class="muted">Click the cards below in causal order. Made a mistake? Press \\"Reset\\".</p>'),
    ('<div class="muted">待排</div>', '<div class="muted">To place</div>'),
    ('`<span class="empty">全部排完</span>`', '`<span class="empty">All placed</span>`'),
    ('<div class="muted">你的順序</div>', '<div class="muted">Your order</div>'),
    ('`<span class="empty">從左邊點選</span>`', '`<span class="empty">Click from the left</span>`'),
    ('save();render()">重排</button>', 'save();render()">Reset</button>'),
    ('`<span class="pill ok">因果鏈正確</span>`', '`<span class="pill ok">Causal chain correct</span>`'),
    ('`<span class="pill warn">順序不對，想想「先有什麼，才導致什麼」</span>`', '`<span class="pill warn">Not the right order — think about what has to come first to cause what</span>`'),
    # P3
    ('head("P3 實驗室","預測—實驗—對照","打開你平常用的 AI 對話工具，照步驟做。<b>每一步都先預測，再執行。</b>預測準確或寫出落差原因，都有分數。")',
     'head("P3 Lab","Predict, test, compare","Open the AI chat tool you normally use and follow the steps. <b>Predict before every step, then run it.</b> You score either way — for an accurate prediction, or for explaining the gap.")'),
    ('<b>實驗目標：</b>', '<b>Goal:</b> '),
    ('<div class="muted">提示詞 ${i+1}</div>', '<div class="muted">Prompt ${i+1}</div>'),
    ('onclick="copy(${js(p)})">複製</button>', 'onclick="copy(${js(p)})">Copy</button>'),
    ("<h3>實驗記錄表</h3>", "<h3>Lab record</h3>"),
    ('<label class="f">我的預測（跑之前寫）</label>', '<label class="f">My prediction (write before running)</label>'),
    ('placeholder="我預測……因為……"', 'placeholder="I predict… because…"'),
    ('<label class="f">實際結果</label>', '<label class="f">Actual result</label>'),
    ('placeholder="實際上……"', 'placeholder="What actually happened…"'),
    ('<label class="f">落差原因（預測和結果哪裡不同？為什麼？如果完全一樣，寫下是哪個原理讓你猜對）</label>', '<label class="f">Why the gap? (Where did prediction and result differ, and why? If they matched, which principle let you guess right?)</label>'),
    ('placeholder="我原本以為……其實是因為……"', 'placeholder="I thought… but actually it\'s because…"'),
    ('submitP3(${id})">送出實驗記錄</button>', 'submitP3(${id})">Submit lab record</button>'),
    # P4
    ('`你是一位 12 歲的學生，對 AI 完全不懂。我會跟你解釋：「${d.feynman}」\\n請你只用 12 歲孩子的程度，追問我 2 個問題，專挑我講得模糊、用了術語沒解釋、或因果跳步的地方。先不要評價，只問問題。\\n\\n我的講解：\\n${st.p4.text||"（貼上你的講解）"}`',
     '`You are a 12-year-old student who knows nothing about AI. I am going to explain this to you: \\"${d.feynman}\\"\\nAsk me 2 follow-up questions, at a 12-year-old\'s level only. Go after the places where I was vague, used jargon without explaining it, or skipped a step in the cause and effect. Don\'t judge yet — just ask the questions.\\n\\nMy explanation:\\n${st.p4.text||"(paste your explanation)"}`'),
    ('head("P4 傳授對決","費曼講解","<b>教不出來，就是還沒懂。</b>用 12 歲孩子聽得懂的話講一分鐘。有夥伴就互相講、互相評；自學就寫下來，再請 AI 扮演 12 歲孩子追問你。完成後建議長休 20 分鐘。")',
     'head("P4 Teach-off","Feynman explanation","<b>If you can\'t teach it, you don\'t understand it yet.</b> Explain it for one minute in words a 12-year-old would understand. With a partner, take turns explaining and scoring; on your own, write it down and have the AI play a 12-year-old asking follow-up questions. Take a 20-minute long break afterwards.")'),
    ('<span class="tag">費曼題・講給非技術同事聽</span>', '<span class="tag">Feynman question · explain it to a non-technical colleague</span>'),
    ('<label class="f">我的一分鐘講解（約 150 到 250 字；不准用沒解釋的術語）</label>', '<label class="f">My one-minute explanation (about 100–180 words; no unexplained jargon)</label>'),
    ('<div class="muted">字數：<span id="cnt">', '<div class="muted">Characters: <span id="cnt">'),
    ('onclick="copy(${js(ask)})">複製「12 歲孩子追問」提示詞</button><span class="muted">把追問貼回來，試著回答；答不出的地方記到 P5。</span>', 'onclick="copy(${js(ask)})">Copy the \\"12-year-old asks\\" prompt</button><span class="muted">Paste the questions back here and try to answer; note what you couldn\'t answer in P5.</span>'),
    ('<label class="f">追問與我的回答</label>', '<label class="f">Follow-up questions and my answers</label>'),
    ('placeholder="問：……　我答：……"', 'placeholder="Q: …   My answer: …"'),
    ("<h3>評分表（夥伴評，或誠實自評）</h3>", "<h3>Rubric (scored by a partner, or honestly by yourself)</h3>"),
    ('<div class="h">項目</div>${[0,1,2,3].map(n=>`<div class="h">${n} 分</div>`)', '<div class="h">Criterion</div>${[0,1,2,3].map(n=>`<div class="h">${n} pt${n===1?"":"s"}</div>`)'),
    ('">平均：<b>${L.avg>=0?L.avg.toFixed(1):"尚未評完"}</b>（需 ≥ 2，且講解至少 60 字）。${L.L2?"層次 2 通過。":"0 或 1 分的項目，就是 P5 要回頭補的缺口。"}',
     '">Average: <b>${L.avg>=0?L.avg.toFixed(1):"not fully scored"}</b> (needs ≥ 2, and an explanation of at least 60 characters). ${L.L2?"Level 2 passed.":"Any criterion scored 0 or 1 is a gap to go back and fill in P5."}'),
    # P5
    ('head("P5 補給","補漏與簡化","回頭補卡住的地方，再寫一個類比——<b>並說出這個類比在哪裡不適用</b>。這一步是費曼法最容易被跳過、也最重要的一步。")',
     'head("P5 Resupply","Fill gaps and simplify","Go back to where you got stuck, then write an analogy — <b>and say where the analogy breaks down</b>. This is the step of the Feynman technique most often skipped, and the most important.")'),
    ('P4 評分中偏低的項目：<b>${low.map(esc).join("、")}</b>。先回 P2 重讀相關原理。', 'Low-scoring criteria in P4: <b>${low.map(esc).join(", ")}</b>. Go back to P2 and reread the relevant principle first.'),
    ('<label class="f">我卡住的地方（講不清楚、被追問答不出、評分低的部分）</label>', '<label class="f">Where I got stuck (what I couldn\'t explain clearly, couldn\'t answer when asked, or scored low on)</label>'),
    ('<label class="f">我的類比</label>', '<label class="f">My analogy</label>'),
    ('<div class="muted">提示：${esc(d.analogyHint)}　（想自己的會比較記得住）</div>', '<div class="muted">Hint: ${esc(d.analogyHint)} (one you come up with yourself will stick better)</div>'),
    ('placeholder="……就像……"', 'placeholder="…is like…"'),
    ('<label class="f">這個類比在哪裡「不適用」？</label>', '<label class="f">Where does this analogy break down?</label>'),
    ('placeholder="不過不一樣的是……"', 'placeholder="But unlike that…"'),
    ('<label class="f">修正後的一分鐘講解稿（選填，會收進咒語書）</label>', '<label class="f">Revised one-minute explanation (optional — goes into your spellbook)</label>'),
    ('submitP5(${id})">換取補給</button>', 'submitP5(${id})">Claim supplies</button>'),
    ('toast("先選一個答案")', 'toast("Pick an answer first")'),
    ('toast("理由至少寫一句（8 字以上）")', 'toast("Write at least one sentence of reasoning (8+ characters)")'),
    ('toast("「實際結果」和「落差原因」都要寫（各 8 字以上）")', 'toast("Fill in both \\"Actual result\\" and \\"Why the gap\\" (8+ characters each)")'),
    ('toast("實驗記錄已存，層次 3 檢核更新")', 'toast("Lab record saved — Level 3 check updated")'),
    ('toast("三欄都要寫：卡住處、類比、不適用處")', 'toast("Fill in all three: where you got stuck, the analogy, where it breaks down")'),
    ('toast("類比卡已收進咒語書")', 'toast("Analogy card added to your spellbook")'),
    # 黃金集
    ('<h3>黃金集計分表</h3>', '<h3>Golden set scorecard</h3>'),
    ('<th>題目＋正確答案</th><th class="c">v1 對</th><th class="c">v2 對</th>', '<th>Question + correct answer</th><th class="c">v1 ✓</th><th class="c">v2 ✓</th>'),
    ('placeholder="例：箱子壓扁了 → 客訴"', 'placeholder="e.g. Boxes arrived crushed → Complaint"'),
    ('save();render()">加一題</button>', 'save();render()">Add a question</button>'),
    ('<span class="muted">正式的黃金集至少 20 題；這裡先練習。</span>', '<span class="muted">A real golden set has at least 20 questions; this is just practice.</span>'),
    # P6
    ('head("P6 Boss 戰","驗收","先通過層次 1 抽問（4 題對 3 題），再挑戰 Boss：診斷一個沒見過的失效案例。<b>遊戲分數不算通過資格，只有內化層次算。</b>")',
     'head("P6 Boss fight","Check","First pass the Level 1 quiz (3 of 4 right), then take on the boss: diagnose a failure case you haven\'t seen before. <b>Game points don\'t count toward passing — only the levels of internalization do.</b>")'),
    ("<h3>層次 1・核心概念抽問</h3>", "<h3>Level 1 · Core concept quiz</h3>"),
    ('${st.p6.quizScore}/4 ${L.L1?"層次 1 通過":"未過，回 P2 複習後重測"}', '${st.p6.quizScore}/4 ${L.L1?"Level 1 passed":"Not yet — review P2, then retake"}'),
    ('save();render()">重測</button>', 'save();render()">Retake</button>'),
    ('grade(${id})">交卷</button>', 'grade(${id})">Submit answers</button>'),
    ('<h3>層次 4・Boss 戰：${esc(d.boss)}${st.p6.boss===1?"（補打：新案例）":""}</h3>', '<h3>Level 4 · Boss fight: ${esc(d.boss)}${st.p6.boss===1?" (rematch: new case)":""}</h3>'),
    ('`<div class="card muted">先通過上面的抽問，Boss 才會現身。</div>`', '`<div class="card muted">Pass the quiz above and the boss will appear.</div>`'),
    ('<span class="tag">失效案例・診斷它</span>', '<span class="tag">Failure case · diagnose it</span>'),
    ('<b>擊敗 ${esc(d.boss)}！</b>', '<b>You defeated ${esc(d.boss)}!</b>'),
    ('<b>這次診斷錯了。</b>', '<b>That diagnosis was wrong.</b> '),
    ('rematch(${id})">補打 Boss（換一個新案例）</button>', 'rematch(${id})">Rematch (with a new case)</button>'),
    ('`兩個案例都沒過：回 P2 重讀原理、P5 補漏後，<button class="btn coral small" onclick="resetBoss(${id})">重新挑戰</button>`', '`Both cases missed. Reread the principle in P2 and fill gaps in P5, then <button class="btn coral small" onclick="resetBoss(${id})">try again</button>`'),
    ('<div class="tag">黑天鵝事件</div>', '<div class="tag">Black swan event</div>'),
    ('placeholder="寫下你的推論（選填，答了 +1 預測點）"', 'placeholder="Write your reasoning (optional, +1 prediction pt)"'),
    ("toast('多寫一點想法')\">提交</button>", "toast('Write a bit more')\">Submit</button>"),
    ("<h3>層次 1 至 4 自我檢核</h3>", "<h3>Levels 1–4 self-check</h3>"),
    ('[["層次 1 複述",L.L1,"回 P6 抽問"],["層次 2 解釋",L.L2,"回 P4 講解與評分"],["層次 3 預測",L.L3,"回 P1 寫理由、P3 寫落差"],["層次 4 診斷",L.L4,"挑戰 Boss"]]',
     '[["Level 1 Recall",L.L1,"Take the P6 quiz"],["Level 2 Explain",L.L2,"Do the P4 explanation and rubric"],["Level 3 Predict",L.L3,"Reasoning in P1, gap in P3"],["Level 4 Diagnose",L.L4,"Fight the boss"]]'),
    ('${x[1]?"已達成":x[2]}', '${x[1]?"Done":x[2]}'),
    ('`<div class="result ok">四個層次全部達成，這座島已通關。</div>`', '`<div class="result ok">All four levels reached — this island is cleared.</div>`'),
    ('`<div class="muted">未達層次 3 的島不算通過；分數再高也一樣。</div>`', '`<div class="muted">An island isn\'t passed until Level 3 is reached, no matter how many points you have.</div>`'),
    ('toast("四題都要作答")', 'toast("Answer all four questions")'),
    # 第 12 島
    ('`<div class="card muted">十一座島的原理：${ISLANDS.filter(d=>!d.final).map(d=>`第 ${d.id} 島 ${esc(d.badge)}（${esc(d.topic)}）`).join("、")}</div>`',
     '`<div class="card muted">Principles from the eleven islands: ${ISLANDS.filter(d=>!d.final).map(d=>`Island ${d.id} ${esc(d.badge)} (${esc(d.topic)})`).join("; ")}</div>`'),
    ('<h3>畢業評分表（自評，每項 0 到 3 分）</h3>', '<h3>Capstone rubric (self-assessed, 0–3 per item)</h3>'),
    ('<b>${esc(x[0])}（${x[1]}%）</b>　', '<b>${esc(x[0])} (${x[1]}%)</b> '),
    ('">加權總分：<b>${L.score}</b> / 100（需 ≥ 60）', '">Weighted total: <b>${L.score}</b> / 100 (needs ≥ 60)'),
    ("<h3>最終 Boss：綜合診斷</h3>", "<h3>Final boss: combined diagnosis</h3>"),
    ('<p class="muted">從前十一座島隨機抽 3 個失效案例，3 題全對才算擊敗真實世界魔王。</p>', '<p class="muted">Three failure cases are drawn at random from the first eleven islands. Get all 3 right to defeat the Real-World Overlord.</p>'),
    ('<div class="muted">案例 ${n+1}</div>', '<div class="muted">Case ${n+1}</div>'),
    ('<div class="why">來自第 ${iid} 島（${esc(isl(iid).boss)}）：${esc(b.why)}</div>', '<div class="why">From Island ${iid} (${esc(isl(iid).boss)}): ${esc(b.why)}</div>'),
    ('`<span class="pill ok">擊敗真實世界魔王</span>`', '`<span class="pill ok">Real-World Overlord defeated</span>`'),
    ('`<span class="pill warn">未全對</span>', '`<span class="pill warn">Not all correct</span>'),
    ('save();render()">換一組新案例再戰</button>', 'save();render()">Fight again with new cases</button>'),
    ('gradeFinal(${id})">提交診斷</button>', 'gradeFinal(${id})">Submit diagnosis</button>'),
    ('toast("三題都要作答")', 'toast("Answer all three cases")'),
    # 修城
    ('<h2>修城：${esc(d.name)}</h2><p class="muted">不看筆記，回答這一題。</p>', '<h2>Castle repair: ${esc(d.name)}</h2><p class="muted">Answer this without looking at your notes.</p>'),
    ('<h2>城牆修好了</h2>', '<h2>Walls repaired</h2>'),
    ('onclick="closeDlg();render()">好</button>', 'onclick="closeDlg();render()">OK</button>'),
    ('<h2>還沒修好</h2>', '<h2>Not repaired yet</h2>'),
    ('<p class="muted">回這座島的 P2 重讀原理，再來修一次。</p>', '<p class="muted">Go back to this island\'s P2, reread the principle, and try the repair again.</p>'),
    ('setRound(${id},1)">去複習</button><button class="btn ghost" onclick="closeDlg()">稍後</button>', 'setRound(${id},1)">Go review</button><button class="btn ghost" onclick="closeDlg()">Later</button>'),
    # 怎麼玩
    ("<h2>怎麼玩</h2>", "<h2>How to play</h2>"),
    ('<p class="lead">這是一門 12 週、每週約 3 小時的課，帶零基礎的人從「模型為什麼這樣回答」一路學到提示詞、脈絡工程、Agent、評測與安全。它用三套方法，各管一件事：</p>',
     '<p class="lead">This is a 12-week course, about 3 hours a week, that takes complete beginners from \\"why does the model answer like that?\\" all the way to prompts, context engineering, agents, evaluation and safety. It uses three methods, each with one job:</p>'),
    ('<b>八角框架</b>管「想不想學」：島嶼、怪物、徽章、黑天鵝、城堡風化。<br><span class="muted">但徽章只綁在「理解」上，不綁在出席或刷分。</span>',
     '<b>Octalysis</b> handles <i>wanting to learn</i>: islands, monsters, badges, black swans, eroding castles.<br><span class="muted">But badges are tied only to understanding — never to attendance or grinding points.</span>'),
    ('<b>番茄鐘</b>管「能不能專注」：每個回合一顆 25 分鐘，一次只做一件事。右下角就是計時器。', '<b>The Pomodoro technique</b> handles <i>focus</i>: each round is one 25-minute pomodoro, one thing at a time. The timer is in the bottom-right corner.'),
    ('<b>費曼學習法</b>管「有沒有真懂」：每座島都要用 12 歲孩子聽得懂的話講出來，卡住的地方就是缺口。', '<b>The Feynman technique</b> handles <i>real understanding</i>: on every island you explain the idea in words a 12-year-old would understand. Wherever you get stuck is a gap.'),
    ('<b>你需要</b>：任何一種 AI 對話工具（照著實驗室的提示詞去跑）、這個頁面、一點誠實。', '<b>You need</b>: any AI chat tool (to run the lab prompts), this page, and a bit of honesty.'),
    ("<h3>每座島 6 回合＝6 顆番茄鐘</h3>", "<h3>6 rounds per island = 6 pomodoros</h3>"),
    ("<li><b>P1 偵察</b>：看謎題，先寫預測和理由。</li>", "<li><b>P1 Scout</b>: read the puzzle; write your prediction and reasoning first.</li>"),
    ("<li><b>P2 解碼</b>：讀原理，拼出因果鏈。</li>", "<li><b>P2 Decode</b>: read the principle and assemble the causal chain.</li>"),
    ("<li><b>P3 實驗室</b>：到你的 AI 工具跑實驗，記錄「預測、結果、落差原因」。</li>", "<li><b>P3 Lab</b>: run experiments in your AI tool; record prediction, result, and why they differ.</li>"),
    ("<li><b>P4 傳授對決</b>：一分鐘講解，夥伴互評或請 AI 扮演 12 歲孩子追問。之後長休 20 分鐘。</li>", "<li><b>P4 Teach-off</b>: a one-minute explanation, scored by a partner or quizzed by an AI playing a 12-year-old. Then a 20-minute long break.</li>"),
    ("<li><b>P5 補給</b>：補缺口、寫類比，並寫下類比哪裡不適用。</li>", "<li><b>P5 Resupply</b>: fill the gaps, write an analogy, and note where it breaks down.</li>"),
    ("<li><b>P6 Boss 戰</b>：抽問 4 題對 3 題，再診斷一個沒見過的失效案例。</li>", "<li><b>P6 Boss fight</b>: get 3 of 4 quiz questions right, then diagnose a failure case you haven't seen.</li>"),
    ("<h3>「內化」怎麼算</h3>", "<h3>What counts as \"internalized\"</h3>"),
    ("<tr><th>層次</th><th>你能做到</th><th>在哪裡驗</th></tr>", "<tr><th>Level</th><th>You can…</th><th>Checked in</th></tr>"),
    ("<tr><td>1 複述</td><td>說出概念與步驟</td><td>P6 抽問</td></tr>", "<tr><td>1 Recall</td><td>state the concepts and steps</td><td>P6 quiz</td></tr>"),
    ("<tr><td>2 解釋</td><td>用 12 歲孩子聽得懂的話說明「為什麼」</td><td>P4 費曼講解</td></tr>", "<tr><td>2 Explain</td><td>explain the \"why\" so a 12-year-old gets it</td><td>P4 Feynman explanation</td></tr>"),
    ("<tr><td>3 預測</td><td>改動之前先預測結果並說出理由</td><td>P1 預測＋P3 實驗記錄</td></tr>", "<tr><td>3 Predict</td><td>predict the result of a change before making it, with reasons</td><td>P1 prediction + P3 lab record</td></tr>"),
    ("<tr><td>4 診斷</td><td>看到失敗能找出原因</td><td>P6 Boss 戰</td></tr>", "<tr><td>4 Diagnose</td><td>find the cause when you see a failure</td><td>P6 boss fight</td></tr>"),
    ('<p class="muted" style="margin-bottom:0">四層都達成才算通關。預測點、番茄鐘數只是回饋，不算通過資格。</p>', '<p class="muted" style="margin-bottom:0">An island is cleared only when all four levels are reached. Prediction points and pomodoro counts are feedback only; they don\'t count toward passing.</p>'),
    ("<h3>番茄鐘規則</h3>", "<h3>Pomodoro rules</h3>"),
    ("<li>每顆只做一件事，25 分鐘內不查訊息、不換任務。</li>", "<li>One thing per pomodoro: no checking messages, no switching tasks for 25 minutes.</li>"),
    ("<li>小休 5 分鐘；完成 P4 後長休 20 分鐘，休息時不碰課程內容。</li>", "<li>5-minute short breaks; a 20-minute long break after P4. Don't touch course material during breaks.</li>"),
    ("<li>時間到就停，沒做完的記下來留給下一顆。</li>", "<li>Stop when time's up; note what's unfinished and leave it for the next pomodoro.</li>"),
    ("<li>被打斷就按「被打斷」記一筆原因，在「紀錄」頁看最常見的分心來源。</li>", "<li>If interrupted, press \"Interrupted\" to log the reason; see your most common distractions on the Log page.</li>"),
    ("<li>25 分鐘不適合你？核心是「單一任務、不被打斷」，可以改成 15 到 50 分鐘。</li>", "<li>25 minutes not right for you? The core idea is \"one task, uninterrupted\" — anything from 15 to 50 minutes is fine.</li>"),
    ("<li>隔天用 1 顆番茄鐘，不看筆記重講一次上週的原理；超過 7 天沒複習，徽章會變暗，答對一題「修城」就恢復。</li>", "<li>The next day, spend one pomodoro re-explaining last week's principle without notes. Badges fade after 7 days without review; answer one \"castle repair\" question to restore them.</li>"),
    ("<h3>給講師與團體</h3>", "<h3>For instructors and groups</h3>"),
    ('<div class="card">勾選航海圖上的「自由模式」可以解鎖全部島嶼備課。團體上課時，3 到 4 人一組成為「公會」，實驗員、講解員、評審員、記錄員每週輪換；P4 由公會評審員用同一張評分表評分。每個人的進度只存在自己的瀏覽器，可在「紀錄」頁匯出備份。完整課程設計見專案裡的 <code>課程設計.md</code>。</div>',
     '<div class="card">Tick \"Free mode\" on the sea chart to unlock every island for preparation. In a group, form \"guilds\" of 3–4 people and rotate the roles of experimenter, explainer, judge and scribe each week; in P4 the guild\'s judge scores with the same rubric. Each person\'s progress lives only in their own browser and can be exported from the Log page. The full course design (in Traditional Chinese) is <code>課程設計.md</code> in the repository.</div>'),
    ("<h3>資料安全</h3>", "<h3>Data safety</h3>"),
    ('<div class="card">實驗一律使用虛構或去識別化的資料，不要把公司機密、客戶個資貼進 AI 工具。這個頁面不會把你的任何內容傳到網路上。</div>', '<div class="card">Always use made-up or de-identified data in experiments. Don\'t paste company secrets or customers\' personal data into AI tools. This page never sends anything you write over the network.</div>'),
    ('<p class="muted">本課程以 <a href="https://creativecommons.org/licenses/by-sa/4.0/deed.zh-hant" target="_blank" rel="noopener">CC BY-SA 4.0</a> 授權：可自由分享、改編與商用，須標示出處，改編作品也須以相同授權釋出。</p>',
     '<p class="muted">This course is licensed under <a href="https://creativecommons.org/licenses/by-sa/4.0/" target="_blank" rel="noopener">CC BY-SA 4.0</a>: you may share, adapt and use it commercially, as long as you give credit and release adaptations under the same license.</p>'),
    # 咒語書
    ('<h3>第 12 島・王冠島 ${', '<h3>Island 12 · Crown Island ${'),
    ("'<span class=\"empty\">（未寫）</span>'", "'<span class=\"empty\">(not written)</span>'"),
    ('<h3>第 ${d.id} 島・${esc(d.name)}　<span class="pill ${passed(d.id)?"gold":""}">${passed(d.id)?esc(d.badge):"未通關"}</span></h3>', '<h3>Island ${d.id} · ${esc(d.name)} <span class="pill ${passed(d.id)?"gold":""}">${passed(d.id)?esc(d.badge):"Not cleared"}</span></h3>'),
    ('${it("我的預測與理由", st.p1.reason)}${it("實驗：結果", st.p3.result)}${it("實驗：落差原因", st.p3.gap)}', '${it("My prediction and reasoning", st.p1.reason)}${it("Lab: result", st.p3.result)}${it("Lab: why the gap", st.p3.gap)}'),
    ('${it("一分鐘講解", st.p5.final||st.p4.text)}${it("類比", st.p5.analogy)}${it("類比不適用之處", st.p5.limit)}${it("黑天鵝推論", st.swan)}', '${it("One-minute explanation", st.p5.final||st.p4.text)}${it("Analogy", st.p5.analogy)}${it("Where the analogy breaks down", st.p5.limit)}${it("Black swan reasoning", st.swan)}'),
    ('<h2>我的咒語書</h2>', '<h2>My spellbook</h2>'),
    ('exportMd()">下載 Markdown</button><button class="btn ghost" onclick="window.print()">列印</button>', 'exportMd()">Download Markdown</button><button class="btn ghost" onclick="window.print()">Print</button>'),
    ('<p class="lead">你寫下的每一段預測、講解與類比，都收在這裡。這是你的東西，畢業時帶走。</p>', '<p class="lead">Every prediction, explanation and analogy you write is collected here. It\'s yours — take it with you when you graduate.</p>'),
    ("'<p class=\"empty\">還沒有內容。從初始之港出發吧。</p>'", "'<p class=\"empty\">Nothing here yet. Set sail from the Harbor of Beginnings.</p>'"),
    ('let md = "# 我的咒語書（脈絡群島）\\n\\n";', 'let md = "# My spellbook (Context Islands)\\n\\n";'),
    ('md += `## 第 ${d.id} 島・${d.name}${passed(d.id)?`（徽章：${d.badge}）`:""}\\n\\n`;', 'md += `## Island ${d.id} · ${d.name}${passed(d.id)?` (badge: ${d.badge})`:""}\\n\\n`;'),
    ('${st.f[x[0]]||"（未寫）"}', '${st.f[x[0]]||"(not written)"}'),
    ('[["謎題",d.puzzle.text],["我的預測與理由",st.p1.reason],["實驗結果",st.p3.result],["落差原因",st.p3.gap],["一分鐘講解",st.p5.final||st.p4.text],["類比",st.p5.analogy],["類比不適用之處",st.p5.limit],["黑天鵝推論",st.swan]]',
     '[["Puzzle",d.puzzle.text],["My prediction and reasoning",st.p1.reason],["Lab result",st.p3.result],["Why the gap",st.p3.gap],["One-minute explanation",st.p5.final||st.p4.text],["Analogy",st.p5.analogy],["Where the analogy breaks down",st.p5.limit],["Black swan reasoning",st.swan]]'),
    ('${v||"（未寫）"}', '${v||"(not written)"}'),
    ('download("咒語書.md", md, "text/markdown")', 'download("spellbook.md", md, "text/markdown")'),
    # 紀錄
    ("<h2>紀錄</h2>", "<h2>Log</h2>"),
    ('<b>番茄鐘</b><p>已完成 <b>${S.pomos}</b> 顆。</p><b>被打斷</b>', '<b>Pomodoros</b><p>Completed: <b>${S.pomos}</b>.</p><b>Interruptions</b>'),
    ('<li>${esc(r)}：${n} 次</li>', '<li>${esc(r)}: ${n}×</li>'),
    ('<p class="muted">最常見的分心來源就是下次要先排除的。</p>', '<p class="muted">Your most common distraction is the first one to remove next time.</p>'),
    ('`<p class="muted">還沒有紀錄。</p>`', '`<p class="muted">Nothing logged yet.</p>`'),
    ('<b>各島狀態</b>', '<b>Island status</b>'),
    ('<li>${esc(d.name)}：${L?', '<li>${esc(d.name)}: ${L?'),
    (':"未出發"}</li>', ':"Not started"}</li>'),
    ('<b>備份與搬家</b><p class="muted">進度只存在這台電腦的這個瀏覽器。換電腦或清除瀏覽資料前，先匯出。</p>', '<b>Backup and moving</b><p class="muted">Progress is stored only in this browser on this computer. Export it before switching computers or clearing browsing data.</p>'),
    ("download('脈絡群島進度.json', JSON.stringify(S,null,1), 'application/json')\">匯出進度</button>", "download('context-islands-progress.json', JSON.stringify(S,null,1), 'application/json')\">Export progress</button>"),
    ('<label class="btn ghost">匯入進度<input', '<label class="btn ghost">Import progress<input'),
    ("if(confirm('確定清除全部進度？這個動作無法復原。')){S=blank();save();render()}\">清除全部進度</button>", "if(confirm('Clear all progress? This cannot be undone.')){S=blank();save();render()}\">Clear all progress</button>"),
    ('toast("已匯入")', 'toast("Imported")'),
    ('toast("檔案格式不對")', 'toast("That file is not in the right format")'),
    # 番茄鐘 JS
    ('P.mode==="focus" ? "專注 25 分鐘・一次只做一件事" : (P.mode==="long"?"長休 20 分鐘・不碰課程內容":"小休 5 分鐘・起來走走")', 'P.mode==="focus" ? "Focus 25 min · one thing at a time" : (P.mode==="long"?"Long break 20 min · no course material":"Short break 5 min · get up and move")'),
    ('`第 ${P.ctx[0]} 島・${', '`Island ${P.ctx[0]} · ${'),
    (': "未綁定回合";', ': "Not linked to a round";'),
    ('P.running ? "暫停" : "開始"', 'P.running ? "Pause" : "Start"'),
    ('toast(long?"P4 完成，長休 20 分鐘":"時間到，停手。小休 5 分鐘")', 'toast(long?"P4 done — 20-minute long break":"Time\'s up — stop. 5-minute short break")'),
    ('toast("休息結束，開始下一顆")', 'toast("Break over — start the next one")'),
    ('toast("番茄鐘已綁定這一回合")', 'toast("Pomodoro linked to this round")'),
    ('?"展開":"收合"', '?"Expand":"Collapse"'),
    ('<h2>被什麼打斷了？</h2><p class="muted">記一筆就好，不用自責。課後看最常見的原因。</p>', '<h2>What interrupted you?</h2><p class="muted">Just log it — no need to beat yourself up. Look at the most common causes afterwards.</p>'),
    ('["手機通知","訊息或電話","同事找","自己想到別的事","累了","其他"]', '["Phone notification","Message or call","A colleague","My own wandering thoughts","Tired","Other"]'),
    ('toast("已記錄")', 'toast("Logged")'),
    ('$("#pFold").textContent="展開";', '$("#pFold").textContent="Expand";'),
    ('content:attr(data-n) "　"', 'content:attr(data-n) "  "'),
    ('<b>v1：${s1}/${n}　v2：${s2}/${n}</b>', '<b>v1: ${s1}/${n} &nbsp; v2: ${s2}/${n}</b>'),
    # ---- 通用短詞（放最後）----
    ('<span class="pill gold">已通關</span>', '<span class="pill gold">Cleared</span>'),
    ('<span class="pill">未解鎖</span>', '<span class="pill">Locked</span>'),
]

CJK = re.compile(r"[　-〿一-鿿＀-￯]")


def translate(pairs, check_cjk=True) -> str:
    html = (ROOT / "index.html").read_text(encoding="utf-8")
    missing = [a for a, _ in pairs if a not in html]
    if missing:
        sys.exit("原稿裡找不到這些對照（介面改過了？請更新 PAIRS）：\n" + "\n".join(missing))
    for a, b in pairs:
        html = html.replace(a, b)
    return html


def main() -> None:
    html = translate(PAIRS)
    html = langs.apply(html, "en/")
    leftover = []
    for i, line in enumerate(html.splitlines(), 1):
        if "<!--LANG-->" in line:
            continue
        if CJK.search(line) and "課程設計.md" not in line:
            leftover.append(f"{i}: {line.strip()[:120]}")
    if leftover:
        sys.exit("還有沒翻譯的中文：\n" + "\n".join(leftover))

    OUT.mkdir(exist_ok=True)
    (OUT / "index.html").write_text(html, encoding="utf-8")
    print("已產生 en/index.html")


if __name__ == "__main__":
    main()
