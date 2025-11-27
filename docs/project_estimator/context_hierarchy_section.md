
---

## Context Hierarchy - The Foundation

All agents now follow an **EXPLICIT CONTEXT HIERARCHY** that ensures every decision is grounded in the project scope and supporting context:

### The Hierarchy Flow:

```
┌─────────────────────────────────────────────────────────────┐
│ 1. PROJECT SCOPE DOCUMENT (User Input - PRIMARY SOURCE)     │
│    "What problem needs to be solved?"                        │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. SAMPLE DATA COMPLEXITY (Calibrates Effort & Scale)       │
│    "How complex is the data? What scale should we plan for?"│
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. TECH STACK REQUIREMENTS (Derived from Scope + Complexity)│
│    "What technologies are ACTUALLY needed?"                  │
│    - Scraping? Only if scope mentions web data collection   │
│    - ML/AI? Only if scope mentions predictions/NLP          │
│    - Real-time? Only if scope mentions live updates         │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. ENGINEERING TEAMS (Based on Tech Stack)                  │
│    "Which teams are ESSENTIAL for these technologies?"      │
│    - If no ML in tech stack → NO ML Engineering team        │
│    - If no scraping → NO Scraping team                      │
└────────────────────┬─────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. PROJECT TASKS (Based on Teams + Scope + Complexity)      │
│    "What specific tasks solve THIS project's challenges?"   │
│    - Tasks reference features from scope                    │
│    - Effort calibrated by complexity                        │
│    - Technologies match tech stack                          │
└─────────────────────────────────────────────────────────────┘
```

### Key Principles:

1. **No Decisions Without Context**: Every output (teams, tasks, tech stack) must be justifiable by pointing back to the context hierarchy

2. **Explicit References**: Prompts now explicitly reference where information comes from:
   - "From Agent 1 (Analyst)"
   - "From requirements analysis"  
   - "Based on sample complexity"

3. **Step-by-Step Guidance**: Agents are guided through analysis steps:
   - STEP 1: Analyze Project Scope
   - STEP 2: Assess Complexity
   - STEP 3: Determine Tech Stack
   - (etc.)

4. **No Assumptions**: If a technology isn't in the tech stack determined by Agent 1, it shouldn't appear in tasks

