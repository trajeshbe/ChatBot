# Theme System - Test Plan

## 🧪 Pre-Test Setup

### 1. Start the Application

```bash
# Terminal 1: Start backend
cd backend
docker-compose up

# Terminal 2: Start frontend
cd frontend
npm run dev
```

### 2. Open Browser
Navigate to: `http://localhost:3001`

---

## ✅ Test Checklist

### **Test 1: Initial Load**
- [ ] Page loads successfully
- [ ] Default light mode is active
- [ ] Sage green colors visible in Sidebar
- [ ] Logo gradient shows sage green to teal
- [ ] No console errors

### **Test 2: Theme Toggle - Light to Dark**
- [ ] Locate ThemeToggle button (sun/moon icon) in Sidebar header
- [ ] Click the toggle button
- [ ] Background changes to dark slate
- [ ] Text becomes light colored
- [ ] Transition is smooth (not jarring)
- [ ] All components visible in dark mode

### **Test 3: Theme Toggle - Dark to Light**
- [ ] Click toggle again
- [ ] Returns to light mode
- [ ] Transition is smooth
- [ ] All colors return to light variants

### **Test 4: Theme Persistence**
- [ ] Switch to dark mode
- [ ] Refresh the page (F5)
- [ ] Dark mode persists
- [ ] Switch to light mode
- [ ] Refresh the page
- [ ] Light mode persists

### **Test 5: Sidebar Colors**
- [ ] Logo gradient: sage green to teal ✓
- [ ] Active tab: sage green background
- [ ] Hover tab: light gray background
- [ ] User avatar: sage green background
- [ ] Admin link: visible in both modes

### **Test 6: Chat Interface**
- [ ] Click "Chat" tab
- [ ] Send button: sage green background
- [ ] User message bubble: sage green
- [ ] User avatar: sage green gradient
- [ ] File upload area visible
- [ ] All text readable in both modes

### **Test 7: All Tabs Work**
Navigate through each tab and verify colors:
- [ ] Chat - sage green buttons
- [ ] Upload Files - sage green accents
- [ ] Web Scraping - sage green buttons
- [ ] Data Extraction - sage green elements
- [ ] Project Estimator - sage green buttons
- [ ] Evaluation - charts and metrics visible
- [ ] Tool Usage - dashboard readable
- [ ] Weights Config - sliders and controls work

### **Test 8: Dark Mode Across All Tabs**
Switch to dark mode and verify:
- [ ] All tabs readable
- [ ] No white/light flashes
- [ ] Sage green accents visible
- [ ] Text has good contrast
- [ ] Buttons clearly visible

### **Test 9: Interactive Elements**
- [ ] Buttons hover: darker sage green
- [ ] Input focus: sage green border
- [ ] Dropdown menus: correct colors
- [ ] Modals/dialogs: readable
- [ ] Tooltips: visible

### **Test 10: Accessibility**
- [ ] Text is readable (good contrast)
- [ ] Focus states are visible
- [ ] Tab navigation works
- [ ] No color-only information
- [ ] Works with browser zoom (100%, 150%, 200%)

---

## 🐛 Common Issues & Fixes

### Issue: Theme toggle not visible
**Fix**: Clear browser cache, hard refresh (Ctrl+Shift+R)

### Issue: Colors not changing
**Fix**:
```bash
cd frontend
npm run build
npm run dev
```

### Issue: Dark mode stuck
**Fix**:
```javascript
// Browser console
localStorage.removeItem('chatbot-theme')
location.reload()
```

### Issue: Tailwind colors not working
**Fix**:
```bash
cd frontend
rm -rf .next
npm run dev
```

---

## 📊 Expected Results

### Light Mode
- Background: White
- Text: Dark gray
- Primary buttons: Sage green (#6b9080)
- Active states: Light sage green
- Borders: Light gray

### Dark Mode
- Background: Dark slate (#0f172a)
- Text: Light gray
- Primary buttons: Light sage green (#85c4a6)
- Active states: Dark sage green
- Borders: Dark gray

---

## ✅ Test Complete

Once all checkboxes are marked:
- [ ] All tests passed
- [ ] Ready for production
- [ ] Proceed to Enhancement 1-4 (RBAC)

---

## 📸 Screenshot Checklist (Optional)

Capture screenshots for documentation:
1. Light mode - Sidebar
2. Dark mode - Sidebar
3. Light mode - Chat interface
4. Dark mode - Chat interface
5. Theme toggle button location

---

## 🎯 Success Criteria

**Must Pass:**
- Theme toggle works
- Both modes are readable
- Theme persists on refresh
- No console errors
- All tabs accessible

**Nice to Have:**
- Smooth transitions
- No visual glitches
- Fast switching (<200ms)

---

**Ready to Test!** Start the application and work through this checklist.
