#!/usr/bin/env python3
"""
Fix the indentation bug in scraper_service.py

The bug: Lines 122-261 are incorrectly indented inside the except block
when they should be at the same level as the try/except.
"""

with open('/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend/app/services/scraper_service.py', 'r') as f:
    lines = f.readlines()

# Lines 122-261 (0-indexed: 121-260) need to be dedented by 4 spaces
# But we need to be careful - only dedent if they start with correct indentation

fixed_lines = []
for i, line in enumerate(lines):
    line_num = i + 1

    # Lines 122-261 should be dedented by 4 spaces (move from except block to method level)
    if 122 <= line_num <= 261:
        # Only dedent lines that start with at least 12 spaces (3 levels of indentation)
        if line.startswith('            '):  # 12 spaces
            # Remove 4 spaces
            fixed_lines.append(line[4:])
        else:
            # Keep as is (blank lines, comments with different indentation, etc.)
            fixed_lines.append(line)
    else:
        fixed_lines.append(line)

with open('/mnt/c/AIML/ClaudeCode/chatbot/ChatBot/backend/app/services/scraper_service.py', 'w') as f:
    f.writelines(fixed_lines)

print("✅ Fixed indentation in scraper_service.py")
print("   Dedented lines 122-261 by 4 spaces")
