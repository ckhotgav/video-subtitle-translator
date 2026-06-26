# Gemini 翻譯 Prompt 範本

---

## 主翻譯 Prompt（step3_translate.py 使用）

此 Prompt 設計原則：
- **序號保護**：使用 `序號|文字` 格式，讓模型無法混淆哪部分是數字哪部分是文字
- **明確數量**：告訴模型「輸入 N 行，輸出必須恰好 N 行」
- **拒絕退路**：明確說明違規後果（被拒絕重試）

```python
prompt = f"""你是專業字幕翻譯師，請將以下英文字幕逐行翻譯為{target_lang}。

嚴格規則（違反任何一條將導致翻譯被拒絕重新執行）：
1. 每行格式必須是「序號|譯文」，序號與原文完全相同，不得新增或刪除行
2. 輸入有幾行，輸出必須恰好有幾行
3. 只翻譯豎線後的文字，豎線前的序號原封不動
4. 翻譯為自然流暢的{target_lang}，符合口語字幕習慣
5. 不要加任何解釋、備註或額外內容

輸入（共 {len(batch)} 行）：
{numbered_texts}

輸出（必須恰好 {len(batch)} 行）："""
```

---

## 翻譯品質提升 Prompt（可選）

當字幕涉及特殊領域（科技、醫療、法律等）時，可在 Prompt 加入領域提示：

```python
domain_hints = {
    "tech": "本影片為科技/程式設計內容，請使用台灣常用的技術術語（如：伺服器、框架、部署）。",
    "medical": "本影片為醫療健康內容，請使用台灣正體中文醫療術語。",
    "education": "本影片為教育學習內容，請翻譯為適合台灣學生的用語。",
    "business": "本影片為商業內容，請使用台灣商務正式用語。",
}
```

加在主 Prompt 前面：
```python
domain_note = domain_hints.get(config.get("domain", ""), "")
prompt = f"{domain_note}\n\n{main_prompt}" if domain_note else main_prompt
```

---

## 驗證失敗時的重試 Prompt

第二次重試時加強警告：

```python
retry_prompt = f"""上一次翻譯結果驗證失敗，原因：{error_summary}

請重新翻譯，這次必須嚴格遵守以下格式：
- 每行必須是「數字|中文」格式
- 輸入 {len(batch)} 行 → 輸出必須恰好 {len(batch)} 行
- 不得有任何多餘說明

{main_prompt}"""
```

---

## 常見翻譯問題與對策

| 問題 | 對策 |
|------|------|
| Gemini 把多行合併成一行 | 在 Prompt 加「每行必須獨立輸出，禁止合併」 |
| Gemini 輸出多餘說明文字 | 在 Prompt 結尾加「只輸出翻譯結果，不要任何前言或後記」 |
| 數字序號被當成內容翻譯 | 改用 `§序號§` 作為分隔符，避免被誤解 |
| 批次太大導致輸出截斷 | 將 `translation_batch_size` 從 30 改為 15 |
| 專有名詞翻譯不一致 | 在 Prompt 加入術語表 |

---

## 術語表注入（進階）

在 config.yaml 加入自訂術語：

```yaml
glossary:
  "machine learning": "機器學習"
  "neural network": "神經網路"
  "fine-tuning": "微調"
  "prompt": "提示詞"
```

在 Prompt 中注入：

```python
if config.get("glossary"):
    glossary_str = "\n".join(f"- {en} → {zh}" for en, zh in config["glossary"].items())
    glossary_note = f"\n術語對照表（請嚴格遵守）：\n{glossary_str}\n"
else:
    glossary_note = ""

prompt = f"{glossary_note}{main_prompt}"
```
