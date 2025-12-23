# Where to Find the "Merge & Deploy to Ollama" Button

> **Quick Navigation Guide**

---

## ✅ Frontend Restarted

The frontend has been restarted and is now running with the new components:
- URL: http://localhost:3001
- Status: ✓ Compiled successfully
- Components loaded: MergeAndDeployButton, GovernanceAudit, EvaluationHub

---

## 📍 Location 1: Pending Model Approvals

### Navigation Path:
1. Open browser: **http://localhost:3001**
2. Login (if needed)
3. Click **"Admin"** in navigation bar
4. Click **"Fine-Tuning Hub"** tab
5. Click **"Governance & Audit"** sub-tab
6. Scroll to **"Pending Model Approvals"** section

### What to Look For:
You should see a **highlighted section** with:
- Light blue/purple gradient background
- ⚡ Lightning bolt icon
- Text: **"Quick Deployment"**
- Subtitle: "Approve → Merge → Deploy to Ollama in one click (takes 5-15 min)"
- Button: **"Merge & Deploy to Ollama"** (purple/indigo gradient)

### Screenshot Description:
```
┌──────────────────────────────────────────────────────┐
│ Pending Model Approvals                              │
├──────────────────────────────────────────────────────┤
│                                                      │
│ ┌────────────────────────────────────────────────┐   │
│ │ ⚡ Quick Deployment                           │   │
│ │ Approve → Merge → Deploy to Ollama            │   │
│ │ (takes 5-15 min)                               │   │
│ │                                                │   │
│ │ [⚡ Merge & Deploy to Ollama]                 │   │
│ └────────────────────────────────────────────────┘   │
│                                                      │
│ ─── Or use traditional approval: ───                 │
│ [Approve] [Reject]                                   │
└──────────────────────────────────────────────────────┘
```

---

## 📍 Location 2: Evaluation Hub

### Navigation Path:
1. Open browser: **http://localhost:3001**
2. Login (if needed)
3. Click **"Admin"** in navigation bar
4. Click **"Fine-Tuning Hub"** tab
5. Click **"Evaluation Hub"** sub-tab
6. Find your model in the table (e.g., "choles-qa-real-training38")

### What to Look For:
In the **Actions** column, you should see:
- **[Evaluate]** button (green) - if not evaluated yet
- **[⚡ Merge & Deploy to Ollama]** button (purple/indigo gradient)
- **[Details]** button (gray)

For **deployed** models, you'll see:
- Model name badge (e.g., "choles-qa-real-training38-v1")
- **[Undeploy]** button (red)
- **[View Results]** button (blue) - if evaluated
- **[Details]** button (gray)

### Screenshot Description:
```
| Model Name                  | Status     | Actions                                          |
|-----------------------------|------------|--------------------------------------------------|
| choles-qa-real-training38   | registered | [Evaluate] [⚡ Merge & Deploy] [Details]        |
| my-deployed-model           | deployed   | model-v1 [Undeploy] [View Results] [Details]    |
```

---

## 🔍 Troubleshooting: "I Don't See the Button"

### Check 1: Is There a Pending Model?
The button only appears for models with specific statuses:
- ✅ `registered` - needs approval, merge, deploy
- ✅ `approved` - needs merge, deploy
- ✅ `adapter_only` - needs merge, deploy
- ❌ `deployed` - already deployed (shows "Undeploy" instead)
- ❌ `training` - still training (not ready yet)

**How to Check**:
```sql
-- Run this in PostgreSQL
SELECT name, status FROM finetuned_models ORDER BY created_at DESC LIMIT 10;
```

### Check 2: Are You Looking at the Right Tab?
The button appears in **two locations**:
1. **Governance & Audit** tab → Pending Model Approvals section
2. **Evaluation Hub** tab → Model table Actions column

Make sure you're in the **Fine-Tuning Hub** parent tab first.

### Check 3: Browser Cache
If you don't see changes, hard refresh:
- **Windows/Linux**: `Ctrl + Shift + R`
- **Mac**: `Cmd + Shift + R`

Or clear cache:
- Open Developer Tools (F12)
- Right-click refresh button → "Empty Cache and Hard Reload"

### Check 4: Check Browser Console for Errors
1. Press `F12` to open Developer Tools
2. Go to **Console** tab
3. Look for errors (red text)
4. If you see import errors related to `MergeAndDeployButton`, the component didn't load

**Common Error**:
```
Error: Cannot find module './MergeAndDeployButton'
```

**Solution**: The file might not be in the Docker container. Check:
```bash
docker-compose exec frontend ls -la /app/src/components/finetuning/ | grep Merge
```

### Check 5: Verify Component Files Exist
```bash
# On your host machine
ls -la /mnt/c/AIML/ClaudeCode/chatbot/ChatBot/frontend/src/components/finetuning/ | grep -E "(Merge|Governance|Evaluation)"

# Should show:
# -rwxrwxrwx 1 aiml aiml 16245 Dec 22 07:51 MergeAndDeployButton.tsx
# -rwxrwxrwx 1 aiml aiml 24648 Dec 22 07:53 GovernanceAudit.tsx
# -rwxrwxrwx 1 aiml aiml 36579 Dec 22 07:59 EvaluationHub.tsx
```

---

## 🧪 Test Scenario: Create a Model to See the Button

If you don't have any pending models, let's create one:

### Option A: Use Your Existing Model
You mentioned "choles-qa-real-training38" - check its status:
```bash
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
SELECT
  name,
  status,
  finetuning_method,
  base_model
FROM finetuned_models
WHERE name LIKE '%choles%' OR job_id LIKE '%choles%'
ORDER BY created_at DESC;
"
```

If status is `registered` or `approved`, the button should appear.

### Option B: Manually Set Status to Test
```bash
# Set your model to 'registered' to trigger the button
docker-compose exec postgres psql -U postgres -d ragchatbot -c "
UPDATE finetuned_models
SET status = 'registered'
WHERE name LIKE '%choles%'
RETURNING name, status;
"
```

Then refresh the UI and navigate to Governance & Audit.

---

## 📸 What You Should See

### When Model Status = 'registered':
**Governance & Audit** → Pending Approvals:
- Highlighted "Quick Deployment" box with gradient background
- Button text: "⚡ Merge & Deploy to Ollama"
- Button color: Purple/indigo gradient

**Evaluation Hub** → Model Table:
- Compact button: "⚡ Merge & Deploy to Ollama"
- Same purple/indigo gradient color

### When You Click the Button:
1. Button changes to: "🔄 Processing... 0%"
2. Progress bar appears (0-100%)
3. Step indicators show:
   - ✓ 1. Approve Model (completed/skipped)
   - 🔄 2. Merge LoRA Adapter (running)
   - ⏳ 3. Deploy to Ollama (pending)
4. After 5-15 minutes:
   - ✅ "Successfully Deployed!" message
   - Button changes to: "✅ Deployed!"

---

## 🆘 Still Can't See It?

### Last Resort: Check Docker Container
```bash
# Enter the frontend container
docker-compose exec frontend sh

# Check if file exists
ls -la /app/src/components/finetuning/MergeAndDeployButton.tsx

# Check if GovernanceAudit imports it
grep -n "MergeAndDeploy" /app/src/components/finetuning/GovernanceAudit.tsx

# Exit container
exit
```

If the file doesn't exist in the container, the Docker volume might not be mounted correctly.

### Force Rebuild:
```bash
# Stop frontend
docker-compose stop frontend

# Remove container
docker-compose rm -f frontend

# Rebuild and start
docker-compose build frontend --no-cache
docker-compose up -d frontend

# Check logs
docker-compose logs -f frontend
```

---

## 📞 Quick Checklist

Before asking for help, verify:
- [ ] Frontend is running: `docker-compose ps frontend` shows "Up"
- [ ] No errors in browser console (F12 → Console tab)
- [ ] Refreshed browser with `Ctrl+Shift+R`
- [ ] At correct URL: http://localhost:3001/admin (Fine-Tuning Hub tab)
- [ ] Model exists with status `registered`, `approved`, or `adapter_only`
- [ ] Checked both locations: Governance & Audit AND Evaluation Hub

---

## 🎯 Expected URLs

- **Main App**: http://localhost:3001
- **Login**: http://localhost:3001/login
- **Admin Panel**: http://localhost:3001/admin
- **Fine-Tuning Hub**: Click tab in Admin Panel (client-side routing, URL stays /admin)

---

**If you still don't see the button after checking all of the above, please let me know:**
1. Which page are you on? (screenshot helps)
2. What model status do you see? (from database query)
3. Any errors in browser console?
4. Output of: `docker-compose logs frontend --tail 20`

---

**End of Guide**
