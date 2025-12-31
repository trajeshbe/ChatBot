# Table-extraction - Data Extraction Module

**Tier**: 2 | **Module**: data-extraction | **Complexity**: 🟢 Tier A (Prompt-Only)
**Source**: `prototypes/docu-extract.md`, `prototypes/maritime-report-generation.md`

## Overview
Extract structured data from documents using GPT-4o Vision + prompts.

## Prompt
See: `prompt_engineering/prompt/extraction_prompts.yaml` → `table-extraction_prompt`

## Pattern
Document → LLM (with schema) → Validated JSON

## Source Material
- Document Extract: `.claude/skills/prototypes/docu-extract.md`
- Maritime Reports: `.claude/skills/prototypes/maritime-report-generation.md`
