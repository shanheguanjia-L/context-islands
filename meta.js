// 脈絡群島：課程的「演化紀錄」。四種語言共用這一份（不用翻譯，畫面上只用到日期）。
// 說明見 docs/演化機制.md。tools/check.py 會檢查這個檔的格式。
//
// 改了內容要做的事：
//   1. 改到的島把 changed 改成今天；重新驗證過（實際跑過實驗、確認說法還成立）就把 checked 改成今天。
//   2. CONTENT_VERSION 改成今天。學員航海圖上「有更新」就是比這兩個日期。
//   3. 更新紀錄.md 加一行。
//
// watch：這座島裡「依賴當下工具」的說法。工具一變它就可能過時，所以有 watch 的島 90 天就該重看一次，其他 365 天。
// 2026-11 的 checked 是內容寫成的日期，不是事後另外重新驗證的日期。
window.CONTENT_VERSION = "2026-11-27";
window.REPO = "shanheguanjia-L/context-islands";

window.FRESHNESS = {
  trunk: { checked: "2026-11-27", changed: "2026-11-27", watch: ["四層名稱對應的業界用語（context engineering、harness、goal）"] },
  1:  { checked: "2026-11-26", changed: "2026-11-26", watch: ["能調 temperature 的地方（各家 Playground／API）"] },
  2:  { checked: "2026-11-27", changed: "2026-11-27", watch: ["自訂指示、CLAUDE.md／AGENTS.md 這類專案說明檔"] },
  3:  { checked: "2026-11-26", changed: "2026-11-26", watch: [] },
  4:  { checked: "2026-11-26", changed: "2026-11-26", watch: ["逐步思考與 effort 的設定方式"] },
  5:  { checked: "2026-11-26", changed: "2026-11-26", watch: ["各家結構化輸出（schema）功能"] },
  6:  { checked: "2026-11-27", changed: "2026-11-27", watch: ["Agent 工具的自動壓縮與清理", "長期記憶的做法"] },
  7:  { checked: "2026-11-26", changed: "2026-11-26", watch: [] },
  8:  { checked: "2026-11-27", changed: "2026-11-27", watch: ["MCP", "子 Agent 與長任務交接"] },
  9:  { checked: "2026-11-27", changed: "2026-11-27", watch: ["SKILL.md 與工具的漸進載入", "提示詞快取"] },
  10: { checked: "2026-11-27", changed: "2026-11-27", watch: ["LLM 評審的偏差"] },
  11: { checked: "2026-11-27", changed: "2026-11-27", watch: ["Agent 工具的權限模式與 hook"] },
  12: { checked: "2026-11-26", changed: "2026-11-26", watch: [] }
};
