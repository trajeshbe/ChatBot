# British Council POC - User Guide

## Introduction

Welcome to the British Council Profile Matcher User Guide. This document provides comprehensive instructions for using the system to find personalized course recommendations and get answers to your questions about British Council courses and programs.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Using the Web Interface](#using-the-web-interface)
3. [Using the Chatbot](#using-the-chatbot)
4. [Understanding Recommendations](#understanding-recommendations)
5. [Asking Questions](#asking-questions)
6. [Troubleshooting](#troubleshooting)
7. [FAQs](#faqs)

## Getting Started

### System Requirements

#### For Web Interface
- Modern web browser (Chrome, Firefox, Safari, Edge)
- Internet connection
- JavaScript enabled

#### For Chatbot
- Microsoft Teams account (if using Teams channel)
- Bot Framework Emulator (for testing/development)
- Or access to integrated web chat widget

### Access Information

**Web Application URL**: `http://<host>:<port>` (provided by administrator)

**Chatbot Endpoint**: Accessible through integrated channels or Bot Framework Emulator

### First-Time Setup

1. **Access the System**: Navigate to the provided URL
2. **No Login Required**: POC version uses HTTP Basic Auth (handled automatically)
3. **Browser Compatibility**: Ensure your browser is up to date

## Using the Web Interface

### Profile Matching Interface

#### Step 1: Launch the Application

1. Open your web browser
2. Navigate to the Profile Matcher URL
3. The "Profile Matcher" page will load

![Interface Screenshot - Landing Page]

#### Step 2: Select a Learner Profile

1. Locate the **"Please choose the Learner Name"** dropdown
2. Click to expand the list of available learners
3. Select the learner whose profile you want to analyze
4. The dropdown shows all pre-registered learners

**Example**:
```
Dropdown Options:
- John Smith
- Jane Doe
- Ahmed Al-Rashid
- Maria Garcia
```

#### Step 3: Submit the Request

1. After selecting a learner, click the **"Submit"** button
2. A loading spinner will appear with the message "Please Wait..."
3. The system is now analyzing the profile (typically 3-5 seconds)

#### Step 4: Review Learner Information

Once processing completes:

1. The **"Learner Information"** section appears
2. Click the **"View Student Information"** expander to see:
   - Educational background
   - Current skills and competencies
   - Interests and career goals
   - Language proficiency
   - Previous learning experience

**Sample Output**:
```
Name: John Smith
Background: Bachelor's in Business Administration
Skills: Project Management, Data Analysis, Basic Python
Interests: Digital Marketing, Business Analytics
Career Goal: Become a Digital Marketing Specialist
Language: English (Native), Spanish (Intermediate)
```

#### Step 5: Review Course Recommendations

Below the learner information, the **"Suitable Course"** section displays:

1. A table with recommended courses containing:
   - **Course Name**: Official course title
   - **Description**: Brief course overview
   - **Match Score**: Percentage match (e.g., 92%)
   - **Reasoning**: Why this course is recommended
   - **Duration**: Course length
   - **Level**: Beginner, Intermediate, Advanced

**Sample Recommendations Table**:

| Course Name | Match Score | Reasoning | Level |
|-------------|-------------|-----------|-------|
| Digital Marketing Fundamentals | 92% | Aligns with career goal and builds on business background | Intermediate |
| Data Analytics for Business | 88% | Leverages existing data analysis skills and Python knowledge | Intermediate |
| Advanced Python Programming | 85% | Develops existing Python skills for analytics applications | Advanced |

#### Step 6: Take Action

Based on recommendations:
1. Note the courses of interest
2. Contact your academic advisor for enrollment
3. Access course details through official channels

### Tips for Best Results

- **Complete Profiles**: Ensure learner profiles are comprehensive
- **Regular Updates**: Update profiles as skills and interests evolve
- **Multiple Views**: Try the analysis at different stages of learning journey

## Using the Chatbot

### Accessing the Chatbot

#### Via Microsoft Teams
1. Search for "British Council Course Assistant" in Teams
2. Click to open the bot conversation
3. Start chatting

#### Via Bot Framework Emulator (Development)
1. Launch Bot Framework Emulator
2. Enter Bot URL: `http://localhost:3978/api/messages`
3. Leave App ID and Password fields empty (for local testing)
4. Click "Connect"

### Interacting with the Bot

#### Starting a Conversation

**Type a greeting**:
```
You: Hello
Bot: Hello! I'm here to help you find courses and answer questions about British Council programs. How can I assist you today?
```

#### Asking About Courses

**General Questions**:
```
You: What courses do you offer in digital marketing?
Bot: British Council offers several digital marketing courses including:
1. Digital Marketing Fundamentals - A beginner-friendly introduction
2. Advanced Social Media Marketing - For experienced marketers
3. SEO and Content Marketing - Focused on organic growth strategies

Would you like more details on any specific course?
```

**Specific Questions**:
```
You: What are the prerequisites for the Advanced Python Programming course?
Bot: The Advanced Python Programming course requires:
- Completion of Python Fundamentals or equivalent knowledge
- Basic understanding of data structures
- Familiarity with object-oriented programming concepts

The course builds on these foundations to cover advanced topics like decorators, generators, and asynchronous programming.
```

#### Multi-Turn Conversations

The bot maintains context:
```
You: Tell me about Data Analytics courses
Bot: We offer several Data Analytics courses...

You: What's the duration of the first one?
Bot: The Data Analytics Fundamentals course runs for 8 weeks, with approximately 5-6 hours of study per week.
```

#### Getting Recommendations

```
You: I have a background in business and want to learn about data science. What do you recommend?
Bot: Based on your business background and interest in data science, I recommend:
1. Start with "Data Analytics for Business" - bridges business and analytics
2. Follow with "Python for Data Science" - builds technical skills
3. Then "Business Intelligence and Visualization" - applies skills to business contexts

This learning path typically takes 6-9 months at a comfortable pace.
```

### Chatbot Commands

| Command | Description | Example |
|---------|-------------|---------|
| "Help" | Get help and available commands | `help` |
| "Courses" | List available courses | `show me all courses` |
| "Recommend" | Get course recommendations | `recommend courses for me` |
| "Prerequisites" | Check course requirements | `prerequisites for [course name]` |

### Best Practices

- **Be Specific**: The more details you provide, the better the recommendations
- **Ask Follow-ups**: Don't hesitate to ask clarifying questions
- **Natural Language**: Type naturally; the bot understands conversational language
- **One Topic at a Time**: Focus on one course or topic per conversation thread

## Understanding Recommendations

### Match Score Explained

The **Match Score** (e.g., 92%) indicates how well a course aligns with the learner's profile:

- **90-100%**: Excellent match - highly recommended
- **80-89%**: Very good match - strongly recommended
- **70-79%**: Good match - recommended
- **60-69%**: Moderate match - may be suitable
- **Below 60%**: Not shown (filtered out)

### Score Calculation Factors

The match score considers:
1. **Prerequisite Alignment** (30%): Does the learner meet requirements?
2. **Interest Relevance** (25%): Does the course match stated interests?
3. **Career Goal Alignment** (25%): Does it support career objectives?
4. **Skill Development** (20%): Will it build relevant skills?

### Recommendation Reasoning

Each recommendation includes an explanation such as:
- "Aligns with your career goal in digital marketing"
- "Builds on your existing Python skills"
- "Fills identified gap in data visualization competencies"

### Course Levels

- **Beginner**: No prior knowledge required
- **Intermediate**: Some foundational knowledge expected
- **Advanced**: Solid background and prerequisites required

## Asking Questions

### Types of Questions You Can Ask

#### 1. Course Information
- "What is covered in the Digital Marketing course?"
- "How long is the Python Programming course?"
- "What's the difference between Course A and Course B?"

#### 2. Prerequisites and Requirements
- "Do I need any prerequisites for this course?"
- "What background is required for advanced courses?"
- "Can beginners take this course?"

#### 3. Learning Outcomes
- "What will I learn in this course?"
- "What skills will I gain?"
- "What can I do after completing this course?"

#### 4. Logistics
- "When does the course start?"
- "Is the course online or in-person?"
- "How much does the course cost?"

#### 5. Career and Pathways
- "Which courses lead to data science careers?"
- "What's the recommended learning path for marketing?"
- "Which course should I take after completing Course X?"

### Question Writing Tips

**Good Questions**:
- "What are the prerequisites for Advanced Python Programming?"
- "How does the Digital Marketing Fundamentals course differ from the Advanced course?"
- "What career opportunities are available after completing the Data Analytics program?"

**Less Effective Questions**:
- "Tell me everything" (too broad)
- "Course?" (too vague)
- Questions about topics not in the knowledge base

### Getting Better Answers

1. **Be Specific**: Include course names, topics, or contexts
2. **Provide Context**: Mention your background or goals if relevant
3. **One Question at a Time**: Break complex queries into parts
4. **Use Clear Language**: Avoid abbreviations unless commonly used

## Troubleshooting

### Common Issues and Solutions

#### Issue: "Server busy...Try again..." Message

**Cause**: System is temporarily overloaded or experiencing connectivity issues

**Solution**:
1. Wait 30 seconds
2. Click "Submit" again
3. If problem persists, contact support

#### Issue: No Recommendations Appear

**Possible Causes**:
- Learner profile is incomplete
- No suitable courses match the profile
- System error

**Solution**:
1. Check that a learner was selected
2. Verify the learner profile is complete
3. Try a different learner
4. Contact administrator if issue continues

#### Issue: Chatbot Not Responding

**Solution**:
1. Check internet connection
2. Refresh the bot window/page
3. Restart the conversation
4. Verify bot service is running (for local deployments)

#### Issue: Inaccurate Recommendations

**Cause**: Profile data may be outdated or incomplete

**Solution**:
1. Review and update learner profile
2. Ensure all skills, interests, and goals are documented
3. Provide feedback to improve the system

#### Issue: "I don't have information about that" Response

**Cause**: Question is about content not in the knowledge base

**Solution**:
1. Rephrase your question
2. Ask about available courses first
3. Contact a human advisor for specialized queries

### Performance Issues

**Slow Response Times**:
- Check internet connection speed
- Try during off-peak hours
- Contact administrator if consistently slow

**Page Not Loading**:
- Clear browser cache
- Try a different browser
- Verify the correct URL
- Check with administrator about system status

## FAQs

### General Questions

**Q: Do I need to create an account?**
A: No, the POC version doesn't require user accounts. Authentication is handled automatically.

**Q: Can I use this on mobile devices?**
A: Yes, the Streamlit interface is responsive and works on tablets and smartphones.

**Q: How often is the course information updated?**
A: Course data is updated by administrators. Contact them for the latest update schedule.

**Q: Can I save my recommendations?**
A: Currently, recommendations are session-based. Take screenshots or notes. Future versions may include save functionality.

### Recommendation Questions

**Q: Why am I seeing only 5 recommendations?**
A: The system shows the top 5 best matches by default. This can be configured by administrators.

**Q: Can I request recommendations for multiple learners?**
A: Yes, select each learner individually to see their recommendations.

**Q: How accurate are the recommendations?**
A: The system has been trained on historical data and uses advanced AI. However, always consult with an academic advisor for final decisions.

**Q: Can I influence the recommendations?**
A: Recommendations are based on the learner profile. Update the profile to reflect current skills and interests for better matches.

### Technical Questions

**Q: What browsers are supported?**
A: Modern versions of Chrome, Firefox, Safari, and Edge. Internet Explorer is not supported.

**Q: Is my data secure?**
A: Yes, data is handled securely with authentication and encryption. See the privacy policy for details.

**Q: Can I use this offline?**
A: No, an internet connection is required to access the LLM services and databases.

**Q: What happens to my chat history?**
A: Chat sessions are logged for quality improvement but are not permanently stored with personal identifiers.

## Getting Help

### Support Contacts

**Technical Issues**:
- Email: [technical-support@example.com]
- Phone: [support number]

**Academic Advising**:
- Email: [advising@example.com]
- Office Hours: [schedule]

**System Administrators**:
- For system access and configuration issues
- Email: [admin@example.com]

### Providing Feedback

Your feedback helps improve the system:
1. **Recommendation Quality**: Did the suggestions make sense?
2. **Answer Accuracy**: Were chatbot responses helpful and accurate?
3. **User Experience**: Was the interface easy to use?
4. **Feature Requests**: What would make this more useful?

**Submit Feedback**: [feedback form URL or email]

## Appendix

### Glossary

- **LLM**: Large Language Model - AI system that generates natural language
- **RAG**: Retrieval-Augmented Generation - technique for grounding AI responses in documents
- **Match Score**: Percentage indicating how well a course aligns with learner profile
- **Vector Database**: Storage system for semantic search
- **Embedding**: Numerical representation of text for similarity matching

### Keyboard Shortcuts

- **Tab**: Navigate form fields
- **Enter**: Submit form (when in text input)
- **Ctrl+R**: Refresh page
- **F5**: Reload application

### Version Information

- **POC Version**: 1.0
- **Last Updated**: [Date]
- **Documentation Version**: 1.0

---

**End of User Guide**

For additional assistance, please contact the support team or refer to the technical documentation.
