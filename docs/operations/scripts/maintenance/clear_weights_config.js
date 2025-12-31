// Clear and reset weights configuration in browser localStorage
// This script sets the optimal defaults for BALANCED mode (GPT-4 tool selection enabled)

const defaultWeights = {
  "strategy_weights": {
    "rag_short_term": 0.30,
    "rag_hybrid": 0.25,
    "tool_navigation": 0.15,
    "tool_ocr": 0.10,
    "tool_docling": 0.15,
    "tool_web_scraping": 0.20,
    "rag_long_term": 0.30,
    "direct_llm": 0.05
  },
  "scoring_formula_weights": {
    "strategy_weight": 0.3,
    "confidence": 0.25,
    "source_quality_score": 0.25,
    "relevance_score": 0.15,
    "completeness_score": 0.05,
    "diversity_bonus": 0.1
  },
  "source_quality_weights": {
    "short_term": 1.2,
    "long_term": 0.9,
    "general": 0.8,
    "scraped": 0.85,
    "ocr": 0.75
  },
  "classification_thresholds": {
    "general_knowledge_skip": 0.85,
    "ai_personal_skip": 0.9,
    "ambiguous_use_rag": 0.6,
    "min_llm_classification_confidence": 0.7
  },
  "similarity_thresholds": {
    "default": 0.6,
    "proper_nouns": 0.5,
    "short_query": 0.65,
    "minimum": 0.4,
    "maximum": 0.95
  },
  "reranking_weights": {
    "semantic": 0.7,
    "keyword": 0.2,
    "recency": 0.1
  },
  "query_preprocessing": {
    "max_length_for_expansion": 5,
    "min_query_length": 3,
    "max_query_length": 500
  },
  "cache": {
    "similarity_threshold": 0.95,
    "ttl_seconds": 3600
  },
  "multi_tool_weights": {
    "document_rag": 0.3,
    "navigation_agent": 0.2,
    "ocr_tool": 0.15,
    "web_scraping": 0.25,
    "docling": 0.1
  },
  "answer_fusion": {
    "best_answer_weight": 0.6,
    "second_best_weight": 0.3,
    "third_best_weight": 0.1
  },
  "rag_settings": {
    "top_k": 5,
    "no_relevant_docs_threshold": 0.35,
    "chunk_size": 800,
    "chunk_overlap": 150
  }
};

console.log("Setting default weights configuration...");
localStorage.setItem('userWeightsConfig', JSON.stringify(defaultWeights));
console.log("✅ Weights reset successfully!");
console.log("\nNew configuration:");
console.log("  rag_short_term: 0.30 (was 1.00)");
console.log("  rag_long_term: 0.30 (was 0.85)");
console.log("\n✅ BALANCED mode enabled - GPT-4 tool selection will now work!");
console.log("\nPlease refresh your chat page (Ctrl+Shift+R)");
