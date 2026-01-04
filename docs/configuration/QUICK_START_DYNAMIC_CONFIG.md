# Quick Start: Dynamic Configuration System

**Time to Complete:** 15 minutes
**Difficulty:** Easy

---

## 🚀 Get Started in 3 Steps

### Step 1: Run the Setup Script (5 minutes)

```bash
cd /mnt/c/AIML/ClaudeCode/chatbot/ChatBot

# Make the script executable
chmod +x scripts/setup_dynamic_config.sh

# Run the setup
./scripts/setup_dynamic_config.sh
```

**What this does:**
- ✅ Runs database migration
- ✅ Creates 6 new tables
- ✅ Verifies API endpoints
- ✅ Creates a sample configuration

---

### Step 2: Create a Module Configuration (5 minutes)

Choose one of your modules and create its configuration:

```bash
curl -X POST http://localhost:8000/api/v1/module-config/modules \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "YOUR_MODULE_NAME",
    "display_name": "Your Module Display Name",
    "module_type": "tier2_domain_vertical",
    "category": "YOUR_CATEGORY",
    "config": {
      "llm": {
        "default": {
          "model": "gpt-4o-mini",
          "temperature": 0.2,
          "max_tokens": 1000
        }
      },
      "prompts": {
        "system": {
          "main": "Your system prompt here..."
        }
      },
      "thresholds": {
        "min_confidence": 0.7
      },
      "features": {
        "enable_caching": true
      }
    }
  }'
```

**Examples:**

<details>
<summary>Click to see example for Talent Search</summary>

```bash
curl -X POST http://localhost:8000/api/v1/module-config/modules \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "talent_search",
    "display_name": "Talent Search & Matching",
    "module_type": "tier2_domain_vertical",
    "category": "hr_talent",
    "config": {
      "llm": {
        "default": {
          "model": "gpt-4o-mini",
          "temperature": 0.2,
          "max_tokens": 1000
        }
      },
      "prompts": {
        "system": {
          "main": "You are an AI assistant specialized in talent search and job matching."
        },
        "user": {
          "query_template": "Find candidates for: {job_description}"
        }
      },
      "thresholds": {
        "min_confidence": 0.7,
        "high_match": 0.9
      },
      "scoring": {
        "weights": {
          "skills_match": 0.6,
          "experience_match": 0.4
        }
      },
      "retrieval": {
        "top_k": 10,
        "rerank_top_k": 5
      },
      "features": {
        "enable_caching": true,
        "enable_semantic_search": true
      }
    }
  }'
```

</details>

<details>
<summary>Click to see example for British Council</summary>

```bash
curl -X POST http://localhost:8000/api/v1/module-config/modules \
  -H "Content-Type: application/json" \
  -d '{
    "module_name": "british_council",
    "display_name": "British Council Course Recommendations",
    "module_type": "tier3_customer_solution",
    "category": "education",
    "config": {
      "llm": {
        "profile_analyzer": {
          "model": "gpt-4o-mini",
          "temperature": 0.0,
          "max_tokens": 500
        },
        "course_recommender": {
          "model": "gpt-4o-mini",
          "temperature": 0.2,
          "max_tokens": 800
        }
      },
      "prompts": {
        "system": {
          "profile_extraction": "Extract a structured user profile focusing on education level, learning format preference, and skills.",
          "course_recommendation": "Based on the user profile, recommend suitable courses."
        }
      },
      "scoring": {
        "weights": {
          "semantic": 0.6,
          "profile": 0.4
        },
        "factors": {
          "education_match": 0.3,
          "format_match": 0.2,
          "availability_match": 0.2,
          "skill_intersection": 0.3
        }
      },
      "thresholds": {
        "match_threshold": 0.8,
        "high_match": 0.9
      },
      "retrieval": {
        "initial_top_k": 10,
        "rerank_top_k": 5,
        "final_recommendations": 5
      },
      "features": {
        "enable_reranking": true,
        "enable_profile_extraction": true,
        "enable_caching": true
      }
    }
  }'
```

</details>

---

### Step 3: Use Configuration in Your Service (5 minutes)

#### A. Import the Service

```python
from app.services.poc_config_service import poc_config_service
```

#### B. Load Configuration

```python
class YourService:
    def __init__(self, db: Session, user_id: Optional[str] = None):
        self.db = db
        self.user_id = user_id
        self.config = None

    async def _load_config(self):
        """Load configuration with user overrides"""
        if not self.config:
            self.config = await poc_config_service.get_config(
                db=self.db,
                module_name="your_module_name",
                user_id=self.user_id
            )
```

#### C. Use Configuration Values

```python
async def your_method(self, query: str):
    await self._load_config()

    # Get LLM settings
    llm_config = self.config['llm']['default']

    # Use in LLM call
    response = await llm_service.generate_response(
        prompt,
        model=llm_config['model'],
        temperature=llm_config['temperature'],
        max_tokens=llm_config['max_tokens']
    )

    # Use thresholds
    min_confidence = self.config['thresholds']['min_confidence']
    if confidence > min_confidence:
        # ...
```

---

## 🎨 Bonus: Add UI Configuration

Add a configuration button to your frontend:

```tsx
import React, { useState } from 'react';
import { POCConfigManager } from '@/components/POCConfigManager';

export const YourModule: React.FC = () => {
  const [showConfig, setShowConfig] = useState(false);

  return (
    <div>
      <div className="header">
        <h1>Your Module</h1>
        <button onClick={() => setShowConfig(true)}>
          ⚙️ Configure
        </button>
      </div>

      {showConfig && (
        <POCConfigManager
          moduleName="your_module_name"
          userId={currentUser.id}
          onClose={() => setShowConfig(false)}
        />
      )}

      {/* Your existing module UI */}
    </div>
  );
};
```

---

## ✅ Verify Everything Works

### 1. Check Configuration Exists

```bash
curl http://localhost:8000/api/v1/module-config/modules/your_module_name
```

### 2. Test Configuration Update

```bash
curl -X PUT http://localhost:8000/api/v1/module-config/modules/your_module_name \
  -H "Content-Type: application/json" \
  -d '{
    "updates": {
      "llm": {
        "default": {
          "temperature": 0.5
        }
      }
    },
    "change_reason": "Testing temperature adjustment"
  }'
```

### 3. View Version History

```bash
curl http://localhost:8000/api/v1/module-config/modules/your_module_name/versions
```

### 4. Test User Overrides

```bash
curl -X POST http://localhost:8000/api/v1/module-config/modules/your_module_name/overrides \
  -H "Content-Type: application/json" \
  -d '{
    "overrides": {
      "llm": {
        "default": {
          "temperature": 0.8
        }
      }
    },
    "variant_name": "experimental"
  }'
```

---

## 🎯 What You Just Accomplished

✅ **Database Migration** - 6 new tables created
✅ **Configuration System** - 3-level hierarchy active
✅ **API Endpoints** - 16 endpoints ready to use
✅ **Module Config** - Your first module is configurable
✅ **Service Integration** - Using dynamic config in backend
✅ **UI Component** - Configuration UI available

---

## 📚 Next Steps

1. **Migrate More Modules** - Repeat Step 2 for all your modules
2. **Refactor Services** - Update service code to use configurations
3. **Add UI Buttons** - Integrate POCConfigManager into all UIs
4. **Test A/B Variants** - Try user overrides for experimentation
5. **Explore Templates** - Create reusable configuration templates

---

## 🆘 Need Help?

### Documentation
- **Full Guide:** `DYNAMIC_CONFIG_IMPLEMENTATION_GUIDE.md`
- **Architecture:** `DYNAMIC_POC_CONFIGURATION_ARCHITECTURE.md`
- **Summary:** `DYNAMIC_CONFIG_IMPLEMENTATION_SUMMARY.md`

### API Documentation
- **Swagger UI:** http://localhost:8000/api/docs
- **Module Config API:** http://localhost:8000/api/v1/module-config/

### Troubleshooting
```bash
# Check backend logs
docker-compose logs backend

# Check database tables
docker-compose exec postgres psql -U postgres -d ragchatbot -c "\dt module_*"

# Test API health
curl http://localhost:8000/api/v1/module-config/health
```

---

## 🎉 Congratulations!

You now have a **production-ready dynamic configuration system** that enables:

- ✅ Zero-code configuration updates
- ✅ A/B testing infrastructure
- ✅ Customer self-service
- ✅ Complete audit trail
- ✅ Version control with rollback

**Time Saved:** From 2-5 days to < 1 hour per module deployment

---

**Ready to configure all 36 modules?** Let's go! 🚀
