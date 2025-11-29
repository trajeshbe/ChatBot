# 📚 Prompt Library Management Guide

**Date**: 2025-11-29
**Component**: PromptLibraryManager UI
**Status**: ✅ LIVE AND READY

---

## 🎯 OVERVIEW

The Prompt Library Manager is a comprehensive CRUD interface for managing prompts and output templates. You can now add, edit, and delete prompts directly from the UI!

---

## 🚀 HOW TO ACCESS

### Method 1: Sidebar Navigation
1. Open http://localhost:3001
2. Look at the left sidebar
3. Click on the **"Library"** tab/icon (usually shown as a book or file icon)
4. The Prompt Library Manager will open

### Method 2: Direct Navigation
- The Library tab should be visible in your sidebar navigation
- If you don't see it, it might be labeled as "Prompts" or have a FileText icon

---

## ✨ FEATURES

### 1. VIEW ALL PROMPTS
- **Grid View**: See all prompts in a beautiful card layout
- **Search**: Real-time search across names, descriptions, and tags
- **Filters**:
  - Module filter (Chat, Scraping, Project Estimator, General)
  - Category filter (General, Data Analysis, Business, Technical)
  - Public Only toggle
- **Sort**: By creation date, usage count, or rating

### 2. CREATE NEW PROMPT
Click the **"Create New Prompt"** button (blue button in top-right)

#### Required Fields:
- **Name**: Short, descriptive name (e.g., "Entity Extraction")
- **Description**: What this prompt does
- **Prompt Text**: The actual prompt with variables in `{curly braces}`

#### Optional Fields:
- **Type**: Prompt type (e.g., entity_extraction, summarization)
- **Category**: General, Data Analysis, Business, or Technical
- **Module**: Which app module uses this (Chat, Scraping, etc.)
- **Tags**: Comma-separated tags (e.g., nlp, extraction, entities)
- **Output Format**: Text, JSON, Markdown, or Table
- **Example Input**: Sample input for testing
- **Example Output**: Expected output for the example
- **Public**: Toggle to make visible to all users

#### Example - Creating a Code Review Prompt:
```
Name: Code Review Assistant
Description: Provide detailed code review with suggestions
Prompt Text:
Review the following code and provide feedback on:
1. Code quality and best practices
2. Potential bugs or issues
3. Performance improvements
4. Security concerns

Code: {code_input}

Language: {programming_language}

Output Format: Markdown
Tags: code, review, quality, programming
Module: chat
Category: technical
Public: Yes
```

### 3. EDIT EXISTING PROMPTS
- Click the **Edit icon** (pencil) on any prompt card
- Modify any fields
- Click **"Update Prompt"** to save

### 4. DELETE PROMPTS
- Click the **Delete icon** (trash) on any prompt card
- Confirm deletion
- Prompt is permanently removed

### 5. RATE PROMPTS
- Each prompt card shows a 5-star rating
- Click on stars to rate (1-5)
- Ratings are averaged and displayed
- Helps identify high-quality prompts

---

## 💡 USAGE EXAMPLES

### Example 1: Add a Custom Prompt for Your Workflow

**Scenario**: You want a prompt for analyzing customer feedback

1. Click "Create New Prompt"
2. Fill in:
   ```
   Name: Customer Feedback Analyzer
   Description: Analyze customer feedback and extract sentiment, topics, and actionable insights

   Prompt Text:
   Analyze the following customer feedback:

   {feedback_text}

   Provide:
   1. Overall Sentiment (Positive/Negative/Neutral)
   2. Main Topics mentioned
   3. Pain Points identified
   4. Actionable Recommendations
   5. Priority Level (High/Medium/Low)

   Format the output as JSON with these fields.

   Tags: feedback, sentiment, analysis, customer
   Output Format: JSON
   Module: chat
   Category: business
   Public: No (if you want it private)
   ```
3. Click "Create Prompt"
4. Now you can use `/customer` in chat to load this prompt!

### Example 2: Edit a Seed Prompt

**Scenario**: Improve the "Entity Extraction" prompt

1. Find "Entity Relationship Extraction" card
2. Click the Edit icon (pencil)
3. Update the prompt text to include more instructions
4. Add more example input/output
5. Click "Update Prompt"
6. The prompt is immediately available in slash command

### Example 3: Delete Unused Prompts

**Scenario**: Remove old test prompts

1. Use search to find "test" prompts
2. Click Delete icon (trash) on each
3. Confirm deletion
4. Prompts are removed from database

---

## 🔍 FILTERS AND SEARCH

### Search Bar
- Type anything to filter prompts in real-time
- Searches across: name, description, tags
- Example: Type "entity" to find all entity-related prompts

### Module Filter
- **All Modules**: Show prompts from all modules
- **Chat**: Prompts for chat interface
- **Scraping**: Prompts for web scraping
- **Project Estimator**: Prompts for project estimation
- **General**: General-purpose prompts

### Category Filter
- **All Categories**: Show all
- **General**: General-purpose
- **Data Analysis**: Data processing and analysis
- **Business**: Business and productivity
- **Technical**: Technical and development

### Public Filter
- Toggle to show only public prompts
- Public prompts are visible to all users
- Private prompts are only visible to creator

---

## 📊 PROMPT CARDS

Each prompt card displays:

### Header
- **Name**: Prompt name
- **✓ Badge**: Verified prompt (if is_verified = true)
- **Edit Icon**: Opens edit modal
- **Delete Icon**: Deletes prompt

### Description
- Brief description of what the prompt does
- Truncated to 2 lines

### Metadata Badges
- **Module**: Which app feature uses it (blue)
- **Category**: Classification (gray)
- **Output Format**: Expected output type with icon (color-coded)
  - JSON = Purple with Code icon
  - Table = Orange with Table icon
  - Markdown = Green with FileText icon
  - Text = Gray with Layout icon
- **Public**: Green badge if public

### Tags
- Small gray badges with # prefix
- Click-friendly for future tag-based filtering

### Stats
- **Star Rating**: Average rating with total count
- **Usage Count**: How many times it's been used

### Quick Actions
- **Rate**: Click stars to rate (1-5)

---

## 🎨 UI COMPONENTS

### Create/Edit Modal

The modal is a full-screen overlay with:

#### Header
- Title: "Create New Prompt" or "Edit Prompt"
- Close button (X)

#### Form Fields
Organized in sections:

1. **Basic Info**
   - Name (required)
   - Description (required)

2. **Prompt Content**
   - Prompt Text (required, monospace font for code-like text)
   - Hint: Use {variable} for placeholders

3. **Classification**
   - Type, Category, Module (dropdowns)

4. **Metadata**
   - Tags (comma-separated input)
   - Output Format (dropdown)

5. **Examples**
   - Example Input (textarea)
   - Example Output (textarea)

6. **Visibility**
   - Public checkbox

#### Footer
- **Cancel**: Close without saving
- **Save/Update**: Save changes (disabled if required fields empty)

---

## 🔐 PERMISSIONS & VISIBILITY

### Public Prompts
- `is_public = true`
- Visible to all users in slash command
- Can be used by anyone
- Seed prompts are public by default

### Private Prompts
- `is_public = false`
- Only visible to creator
- Only creator can use in slash command
- Useful for personal/team-specific prompts

### Verified Prompts
- `is_verified = true`
- Shows blue checkmark badge
- Indicates quality/admin-approved prompts
- Seed prompts are verified

---

## 📈 METRICS & ANALYTICS

### Usage Count
- Increments each time prompt is used via slash command
- Helps identify popular prompts
- Displayed on prompt card

### Ratings
- Users can rate 1-5 stars
- Average rating calculated automatically
- Total ratings count shown
- Helps identify high-quality prompts

### Sort Options
- By creation date (newest first)
- By usage count (most used first)
- By average rating (highest first)
- By name (alphabetical)

---

## 🎯 BEST PRACTICES

### 1. Clear Naming
✅ Good: "Entity Relationship Extraction"
❌ Bad: "Prompt1", "Test", "New Prompt"

### 2. Detailed Descriptions
✅ Good: "Extract entities and relationships from text data, format as JSON with entity types and relationship mappings"
❌ Bad: "Extracts stuff", "NLP thing"

### 3. Use Variables
✅ Good: "Analyze {input_text} and provide {output_format}"
❌ Bad: "Analyze this text" (not reusable)

### 4. Provide Examples
- Always add example input/output
- Helps users understand expected format
- Shown in slash command details panel

### 5. Tag Appropriately
✅ Good: "nlp, extraction, entities, json"
❌ Bad: No tags, or irrelevant tags

### 6. Choose Correct Module
- **Chat**: General chat prompts
- **Scraping**: Web scraping instructions
- **Project Estimator**: Estimation templates
- **General**: Multi-purpose

---

## 🔄 WORKFLOW INTEGRATION

### From Slash Command to Library Manager

1. **Discover**: Use `/` in chat to see all prompts
2. **Use**: Select a prompt and use it
3. **Improve**: Go to Library Manager to edit
4. **Rate**: Rate prompts you like
5. **Create**: Add new prompts for specific needs

### Typical User Journey

```
Day 1: User types /entity and uses Entity Extraction prompt
       ↓
Day 2: User goes to Library Manager to see all prompts
       ↓
Day 3: User creates custom "Customer Feedback" prompt
       ↓
Day 4: User edits prompt to improve it
       ↓
Day 5: User rates good prompts with 5 stars
       ↓
Day 6: User shares public prompts with team
```

---

## 🐛 TROUBLESHOOTING

### Prompts Not Showing
1. Check module filter - set to "All Modules"
2. Check public filter - toggle off to see private
3. Check search box - clear any search text
4. Refresh page (Ctrl+Shift+R)

### Can't Edit Prompt
- Editing should work for all prompts
- Check browser console for errors (F12)
- Verify backend is running

### Can't Delete Prompt
- Click trash icon and confirm
- Check if prompt is being used in active chats
- Verify API connection

### Slash Command Not Showing New Prompt
1. Create prompt in Library Manager
2. Go to Chat tab
3. Type `/` to see updated list
4. May need to refresh chat page

---

## 💾 DATA STRUCTURE

### Prompt Object
```typescript
{
  id: "uuid",
  name: "Entity Extraction",
  description: "Extract entities...",
  prompt_text: "Analyze {input_text}...",
  prompt_type: "entity_extraction",
  category: "data-analysis",
  module: "chat",
  tags: ["nlp", "extraction"],
  expected_output_format: "json",
  example_input: "Sample text...",
  example_output: "{\"entities\": [...]}",
  is_public: true,
  is_verified: true,
  usage_count: 42,
  average_rating: 4.8,
  total_ratings: 15,
  created_at: "2025-11-29T...",
  updated_at: "2025-11-29T..."
}
```

---

## 🎓 ADVANCED TIPS

### 1. Variable Placeholders
Use descriptive variable names:
- `{input_text}` not `{text}`
- `{programming_language}` not `{lang}`
- `{max_results}` not `{n}`

### 2. Multi-Step Prompts
Break complex tasks into steps:
```
1. Analyze {input_data}
2. Identify key patterns
3. Generate insights
4. Format as {output_format}
```

### 3. Output Format Consistency
Match output_format to actual output:
- If requesting JSON, set output_format = "json"
- If requesting Markdown, set output_format = "markdown"

### 4. Example Quality
- Use realistic examples
- Show complex cases, not just simple ones
- Include edge cases if relevant

---

## 📝 CURRENT PROMPTS (Seed Data)

These 5 prompts come pre-installed:

1. **Entity Relationship Extraction**
   - Module: chat
   - Format: JSON
   - Extracts entities and relationships

2. **Document Summarization**
   - Module: chat
   - Format: Markdown
   - Creates structured summaries

3. **Comparative Analysis**
   - Module: chat
   - Format: Table
   - Compares items with criteria

4. **Meeting Minutes Extraction**
   - Module: chat
   - Format: JSON
   - Extracts structured meeting data

5. **Data Table Generation**
   - Module: chat
   - Format: Table
   - Creates formatted tables

---

## 🔮 FUTURE ENHANCEMENTS

Planned features:
- [ ] Duplicate prompt functionality
- [ ] Import/Export prompts as JSON
- [ ] Prompt versioning (track changes)
- [ ] Collaborative prompt editing
- [ ] Prompt templates with wizards
- [ ] Analytics dashboard
- [ ] A/B testing for prompts
- [ ] Prompt marketplace
- [ ] AI-assisted prompt improvement

---

## 📚 RELATED DOCUMENTATION

- **Slash Command Guide**: `SLASH_COMMAND_READY_TO_TEST.md`
- **Implementation Status**: `PROMPT_LIBRARY_IMPLEMENTATION_STATUS.md`
- **Database Schema**: `backend/migrations/012_add_prompt_library_and_templates.sql`
- **API Documentation**: Check `/api/docs` for full API reference

---

## 🎉 START MANAGING YOUR PROMPTS!

1. **Open**: http://localhost:3001
2. **Navigate**: Click "Library" in sidebar
3. **Explore**: See all existing prompts
4. **Create**: Click "Create New Prompt"
5. **Test**: Go to Chat tab and use `/` to see your prompt!

---

**Happy Prompt Managing! 🚀**
