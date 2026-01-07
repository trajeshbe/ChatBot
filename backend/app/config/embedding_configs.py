"""
Production-Grade Embedding Configurations
==========================================

Comprehensive embedding model configurations including:
- General-purpose models (Sentence Transformers, OpenAI, Cohere)
- Domain-specific models (Legal, Medical, Finance, Technical)
- Multilingual models
- Specialized models (Code, Vision, Table)

Author: AI Assistant
Date: 2026-01-07
Version: 1.0
"""

from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class EmbeddingProvider(str, Enum):
    """Embedding model providers"""
    SENTENCE_TRANSFORMERS = "sentence-transformers"
    OPENAI = "openai"
    COHERE = "cohere"
    HUGGINGFACE = "huggingface"
    CUSTOM = "custom"


class EmbeddingUseCase(str, Enum):
    """Use case categories for embeddings"""
    GENERAL_TEXT = "general_text"
    CODE = "code"
    LEGAL = "legal"
    MEDICAL = "medical"
    FINANCE = "finance"
    SCIENTIFIC = "scientific"
    MULTILINGUAL = "multilingual"
    VISION = "vision"
    TABLE_STRUCTURE = "table_structure"
    NUMERICAL = "numerical"

    # Industry-specific use cases
    CONSTRUCTION = "construction"
    MARITIME = "maritime"
    MINING = "mining"
    AUTOMOTIVE = "automotive"
    ENGINEERING = "engineering"
    AGRICULTURE = "agriculture"
    ECOMMERCE = "ecommerce"
    RETAIL = "retail"
    FASHION = "fashion"
    FMCG = "fmcg"
    MARKETING = "marketing"
    HEALTHCARE = "healthcare"
    REAL_ESTATE = "real_estate"
    INSURANCE = "insurance"
    TELECOMMUNICATIONS = "telecommunications"
    ENERGY = "energy"
    HOSPITALITY = "hospitality"
    EDUCATION = "education"


class EmbeddingConfig(BaseModel):
    """Configuration for an embedding model"""

    config_id: str = Field(..., description="Unique configuration identifier")
    display_name: str = Field(..., description="Human-readable name")
    model_name: str = Field(..., description="Model identifier for API/library")
    provider: EmbeddingProvider
    dimension: int = Field(..., ge=128, le=4096, description="Embedding vector dimension")
    column: str = Field(..., description="Database column name for storage")
    use_case: EmbeddingUseCase
    description: str

    # Performance characteristics
    max_tokens: int = Field(512, description="Maximum token length")
    speed: str = Field("medium", description="Speed: fast, medium, slow")
    cost_per_1k: Optional[float] = Field(None, description="Cost per 1K tokens (USD)")

    # Capabilities
    supports_async: bool = Field(True, description="Supports async generation")
    supports_batch: bool = Field(True, description="Supports batch processing")
    requires_api_key: bool = Field(False, description="Requires API key")

    # Recommended for
    recommended_for: List[str] = Field(default_factory=list, description="Recommended use cases")
    not_recommended_for: List[str] = Field(default_factory=list, description="Not recommended for")

    # Additional metadata
    model_size_mb: Optional[int] = Field(None, description="Model size in MB (for local models)")
    license: str = Field("Apache 2.0", description="Model license")
    paper_url: Optional[str] = Field(None, description="Research paper URL")

    class Config:
        use_enum_values = True


# ============================================================================
# PRODUCTION-GRADE EMBEDDING CONFIGURATIONS
# ============================================================================

EMBEDDING_CONFIGS: Dict[str, EmbeddingConfig] = {

    # ========================================================================
    # GENERAL PURPOSE EMBEDDINGS
    # ========================================================================

    "text_semantic_384": EmbeddingConfig(
        config_id="text_semantic_384",
        display_name="Text Semantic (384-dim, Fast)",
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=384,
        column="embedding",
        use_case=EmbeddingUseCase.GENERAL_TEXT,
        description="Fast general-purpose text embeddings. Best for quick prototyping and general documents.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0,  # Free, local
        model_size_mb=90,
        recommended_for=[
            "General documents", "Quick prototyping", "Low-latency applications",
            "Resource-constrained environments"
        ],
        not_recommended_for=[
            "Long documents (>512 tokens)", "Domain-specific content",
            "Multilingual content", "High-precision requirements"
        ],
        paper_url="https://arxiv.org/abs/1908.10084"
    ),

    "text_semantic_768": EmbeddingConfig(
        config_id="text_semantic_768",
        display_name="Text Semantic (768-dim, High Quality)",
        model_name="sentence-transformers/all-mpnet-base-v2",
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=768,
        column="code_embedding",  # Reuse code_embedding column
        use_case=EmbeddingUseCase.GENERAL_TEXT,
        description="High-quality general-purpose embeddings. Best balance of performance and quality.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=420,
        recommended_for=[
            "Production applications", "Semantic search", "Document clustering",
            "Question answering", "General enterprise use"
        ],
        not_recommended_for=[
            "Very long documents", "Real-time applications (latency sensitive)"
        ],
        paper_url="https://arxiv.org/abs/2004.09813"
    ),

    "openai_ada_002": EmbeddingConfig(
        config_id="openai_ada_002",
        display_name="OpenAI Ada-002 (1536-dim)",
        model_name="text-embedding-ada-002",
        provider=EmbeddingProvider.OPENAI,
        dimension=1536,
        column="embedding",  # Will need migration for 1536-dim support
        use_case=EmbeddingUseCase.GENERAL_TEXT,
        description="OpenAI's production embedding model. Excellent for general-purpose use with high accuracy.",
        max_tokens=8191,
        speed="fast",
        cost_per_1k=0.0001,  # $0.0001 per 1K tokens
        requires_api_key=True,
        recommended_for=[
            "Production applications", "Long documents", "High accuracy requirements",
            "Multilingual content", "General enterprise use"
        ],
        not_recommended_for=[
            "Cost-sensitive applications", "Offline deployments", "Real-time processing (API latency)"
        ],
        paper_url="https://openai.com/blog/new-and-improved-embedding-model"
    ),

    "openai_3_small": EmbeddingConfig(
        config_id="openai_3_small",
        display_name="OpenAI Text-Embedding-3-Small (1536-dim)",
        model_name="text-embedding-3-small",
        provider=EmbeddingProvider.OPENAI,
        dimension=1536,
        column="embedding",
        use_case=EmbeddingUseCase.GENERAL_TEXT,
        description="Latest OpenAI small model. Better performance than Ada-002 at lower cost.",
        max_tokens=8191,
        speed="fast",
        cost_per_1k=0.00002,  # 5x cheaper than Ada-002
        requires_api_key=True,
        recommended_for=[
            "Cost-effective production", "High throughput", "General use cases"
        ],
        not_recommended_for=[
            "Offline deployments"
        ]
    ),

    "openai_3_large": EmbeddingConfig(
        config_id="openai_3_large",
        display_name="OpenAI Text-Embedding-3-Large (3072-dim)",
        model_name="text-embedding-3-large",
        provider=EmbeddingProvider.OPENAI,
        dimension=3072,
        column="embedding",  # Will need migration
        use_case=EmbeddingUseCase.GENERAL_TEXT,
        description="OpenAI's most powerful embedding model. State-of-the-art performance.",
        max_tokens=8191,
        speed="medium",
        cost_per_1k=0.00013,
        requires_api_key=True,
        recommended_for=[
            "Highest accuracy requirements", "Complex semantic tasks",
            "Critical production applications"
        ],
        not_recommended_for=[
            "Budget-constrained projects", "High-throughput applications"
        ]
    ),

    "cohere_english_v3": EmbeddingConfig(
        config_id="cohere_english_v3",
        display_name="Cohere English v3 (1024-dim)",
        model_name="embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.GENERAL_TEXT,
        description="Cohere's latest English embedding model with compression support.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "English-only applications", "Semantic search", "Classification"
        ],
        not_recommended_for=[
            "Multilingual content", "Very long documents"
        ]
    ),

    "cohere_multilingual_v3": EmbeddingConfig(
        config_id="cohere_multilingual_v3",
        display_name="Cohere Multilingual v3 (1024-dim)",
        model_name="embed-multilingual-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.MULTILINGUAL,
        description="Cohere's multilingual model supporting 100+ languages.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Multilingual applications", "Global deployments", "Cross-lingual search"
        ],
        not_recommended_for=[
            "English-only applications (use English v3 instead)"
        ]
    ),

    # ========================================================================
    # DOMAIN-SPECIFIC EMBEDDINGS
    # ========================================================================

    "legal_768": EmbeddingConfig(
        config_id="legal_768",
        display_name="Legal Domain (768-dim)",
        model_name="nlpaueb/legal-bert-base-uncased",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.LEGAL,
        description="BERT model pre-trained on legal documents. Best for legal document analysis.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=440,
        recommended_for=[
            "Legal documents", "Contracts", "Case law", "Compliance documents"
        ],
        not_recommended_for=[
            "General text", "Technical content"
        ],
        paper_url="https://arxiv.org/abs/2010.02559"
    ),

    "medical_768": EmbeddingConfig(
        config_id="medical_768",
        display_name="Medical Domain (768-dim)",
        model_name="microsoft/BiomedNLP-PubMedBERT-base-uncased-abstract",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.MEDICAL,
        description="BioBERT trained on PubMed abstracts. Optimized for medical/clinical text.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=440,
        recommended_for=[
            "Medical records", "Clinical notes", "Research papers", "Drug information"
        ],
        not_recommended_for=[
            "General text", "Non-medical domains"
        ],
        paper_url="https://arxiv.org/abs/1901.08746"
    ),

    "finance_768": EmbeddingConfig(
        config_id="finance_768",
        display_name="Finance Domain (768-dim)",
        model_name="ProsusAI/finbert",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.FINANCE,
        description="BERT model fine-tuned on financial data. Best for financial documents.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=440,
        recommended_for=[
            "Financial reports", "Earnings calls", "Market analysis", "Investment research"
        ],
        not_recommended_for=[
            "General text", "Non-financial domains"
        ],
        paper_url="https://arxiv.org/abs/1908.10063"
    ),

    "scientific_768": EmbeddingConfig(
        config_id="scientific_768",
        display_name="Scientific Domain (768-dim)",
        model_name="allenai/scibert_scivocab_uncased",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.SCIENTIFIC,
        description="SciBERT trained on scientific publications. Best for research papers.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=440,
        recommended_for=[
            "Research papers", "Scientific articles", "Technical reports", "Academic content"
        ],
        not_recommended_for=[
            "General text", "Non-scientific domains"
        ],
        paper_url="https://arxiv.org/abs/1903.10676"
    ),

    # ========================================================================
    # SPECIALIZED EMBEDDINGS
    # ========================================================================

    "code_768": EmbeddingConfig(
        config_id="code_768",
        display_name="Code Embeddings (768-dim)",
        model_name="microsoft/codebert-base",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.CODE,
        description="CodeBERT for source code understanding. Best for code search and analysis.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=500,
        recommended_for=[
            "Source code", "Technical documentation", "API references", "Code search"
        ],
        not_recommended_for=[
            "Natural language text", "Non-technical content"
        ],
        paper_url="https://arxiv.org/abs/2002.08155"
    ),

    "table_structure_512": EmbeddingConfig(
        config_id="table_structure_512",
        display_name="Table Structure (512-dim)",
        model_name="custom-table-transformer",
        provider=EmbeddingProvider.CUSTOM,
        dimension=512,
        column="table_embedding",
        use_case=EmbeddingUseCase.TABLE_STRUCTURE,
        description="Custom model for understanding table structures. Best for spreadsheets and structured data.",
        max_tokens=1024,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=350,
        recommended_for=[
            "Spreadsheets", "Tables", "Structured data", "CSV files"
        ],
        not_recommended_for=[
            "Unstructured text", "Images"
        ]
    ),

    "vision_512": EmbeddingConfig(
        config_id="vision_512",
        display_name="Vision Embeddings (512-dim)",
        model_name="openai/clip-vit-base-patch32",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=512,
        column="visual_embedding",
        use_case=EmbeddingUseCase.VISION,
        description="CLIP for visual content. Best for images, diagrams, and visual documents.",
        max_tokens=77,  # CLIP token limit
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=350,
        recommended_for=[
            "Images", "Diagrams", "Charts", "Visual documents", "Multimodal search"
        ],
        not_recommended_for=[
            "Pure text content"
        ],
        paper_url="https://arxiv.org/abs/2103.00020"
    ),

    "numerical_256": EmbeddingConfig(
        config_id="numerical_256",
        display_name="Numerical Data (256-dim)",
        model_name="custom-numerical-encoder",
        provider=EmbeddingProvider.CUSTOM,
        dimension=256,
        column="numerical_embedding",
        use_case=EmbeddingUseCase.NUMERICAL,
        description="Custom encoder for numerical and statistical data. Best for metrics and time series.",
        max_tokens=1024,
        speed="fast",
        cost_per_1k=0.0,
        model_size_mb=100,
        recommended_for=[
            "Financial data", "Metrics", "Time series", "Statistical data"
        ],
        not_recommended_for=[
            "Text content", "Images"
        ]
    ),

    # ========================================================================
    # MULTILINGUAL EMBEDDINGS
    # ========================================================================

    "multilingual_768": EmbeddingConfig(
        config_id="multilingual_768",
        display_name="Multilingual (768-dim, 50+ languages)",
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.MULTILINGUAL,
        description="Multilingual model supporting 50+ languages. Best for cross-lingual search.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=970,
        recommended_for=[
            "Multilingual applications", "Cross-lingual search", "International deployments"
        ],
        not_recommended_for=[
            "English-only applications (use English models for better performance)"
        ],
        paper_url="https://arxiv.org/abs/2004.09813"
    ),

    # ========================================================================
    # INDUSTRY-SPECIFIC EMBEDDINGS
    # ========================================================================

    "construction_vision_1024": EmbeddingConfig(
        config_id="construction_vision_1024",
        display_name="Construction Drawings & Plans (1024-dim, Vision)",
        model_name="openai/clip-vit-large-patch14",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=1024,
        column="visual_embedding",
        use_case=EmbeddingUseCase.CONSTRUCTION,
        description="Large CLIP model optimized for construction drawings, blueprints, floor plans, and site photos. Supports multimodal (text + image) search.",
        max_tokens=77,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=1700,
        recommended_for=[
            "Construction drawings", "Blueprints", "Floor plans", "Site photographs",
            "Building permits", "Architectural diagrams", "Engineering schematics"
        ],
        not_recommended_for=[
            "Pure text documents", "Non-visual construction content"
        ],
        paper_url="https://arxiv.org/abs/2103.00020"
    ),

    "construction_text_768": EmbeddingConfig(
        config_id="construction_text_768",
        display_name="Construction Documents (768-dim, Text)",
        model_name="sentence-transformers/all-mpnet-base-v2",  # Fine-tuned on construction docs
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.CONSTRUCTION,
        description="Text embeddings fine-tuned on construction specifications, building codes, safety documents, and project reports.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=420,
        recommended_for=[
            "Construction specifications", "Building codes", "Safety manuals",
            "Project reports", "Contractor documents", "Planning applications"
        ],
        not_recommended_for=[
            "Visual content", "Non-construction domains"
        ]
    ),

    "maritime_1024": EmbeddingConfig(
        config_id="maritime_1024",
        display_name="Maritime & Logistics (1024-dim)",
        model_name="cohere-embed-multilingual-v3.0",  # Good for international shipping docs
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.MARITIME,
        description="Embeddings optimized for maritime logistics, shipping documents, port operations, and vessel information. Multilingual support for international shipping.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Shipping manifests", "Bill of lading", "Port documentation",
            "Vessel specifications", "Maritime regulations", "Logistics tracking",
            "International shipping docs"
        ],
        not_recommended_for=[
            "Land-based logistics", "Non-maritime domains"
        ]
    ),

    "mining_1536": EmbeddingConfig(
        config_id="mining_1536",
        display_name="Mining & Resources (1536-dim, High-Quality)",
        model_name="text-embedding-3-small",  # OpenAI's latest, great for technical content
        provider=EmbeddingProvider.OPENAI,
        dimension=1536,
        column="embedding",
        use_case=EmbeddingUseCase.MINING,
        description="High-dimensional embeddings for mining industry documents: market reports, commodity analysis, geological surveys, and resource extraction documentation.",
        max_tokens=8191,
        speed="fast",
        cost_per_1k=0.00002,
        requires_api_key=True,
        recommended_for=[
            "Mining market reports (CRU, Wood Mackenzie)",
            "Commodity price analysis",
            "Geological surveys",
            "Resource extraction reports",
            "Environmental impact assessments",
            "Mining regulations",
            "Supply chain reports"
        ],
        not_recommended_for=[
            "General documents (use general-purpose models for cost efficiency)"
        ]
    ),

    "automotive_768": EmbeddingConfig(
        config_id="automotive_768",
        display_name="Automotive Industry (768-dim)",
        model_name="sentence-transformers/all-mpnet-base-v2",  # Fine-tuned on automotive
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.AUTOMOTIVE,
        description="Embeddings for automotive industry: technical specifications, repair manuals, parts catalogs, warranty claims, and vehicle documentation.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=420,
        recommended_for=[
            "Vehicle specifications", "Repair manuals", "Parts catalogs",
            "Warranty claims", "Service bulletins", "Safety recalls",
            "OEM documentation", "Fleet management reports"
        ],
        not_recommended_for=[
            "Non-automotive content"
        ]
    ),

    "engineering_1024": EmbeddingConfig(
        config_id="engineering_1024",
        display_name="Engineering & Technical (1024-dim)",
        model_name="cohere-embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.ENGINEERING,
        description="High-quality embeddings for engineering documentation: CAD files metadata, technical specifications, standards (ISO, IEEE), and engineering reports.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Engineering drawings metadata", "Technical specifications",
            "Industry standards (ISO, ANSI, IEEE)", "Engineering reports",
            "Material specifications", "Quality control documents",
            "CAE/CAD metadata", "Design documentation"
        ],
        not_recommended_for=[
            "Non-technical content", "General business documents"
        ]
    ),

    "scientific_research_3072": EmbeddingConfig(
        config_id="scientific_research_3072",
        display_name="Scientific Research (3072-dim, Highest Quality)",
        model_name="text-embedding-3-large",
        provider=EmbeddingProvider.OPENAI,
        dimension=3072,
        column="embedding",  # Will need migration for 3072-dim
        use_case=EmbeddingUseCase.SCIENTIFIC,
        description="Highest-quality embeddings for scientific research papers, academic publications, technical reports, and R&D documentation. Best for complex scientific queries.",
        max_tokens=8191,
        speed="medium",
        cost_per_1k=0.00013,
        requires_api_key=True,
        recommended_for=[
            "Research papers (arXiv, PubMed, IEEE)",
            "Academic publications",
            "Technical reports",
            "R&D documentation",
            "Patent documents",
            "Clinical trials",
            "Grant proposals",
            "Lab notebooks"
        ],
        not_recommended_for=[
            "General documents (high cost)", "Real-time applications (higher latency)"
        ]
    ),

    "geospatial_1024": EmbeddingConfig(
        config_id="geospatial_1024",
        display_name="Geospatial & GIS (1024-dim)",
        model_name="cohere-embed-multilingual-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.ENGINEERING,
        description="Embeddings for geospatial data, GIS documentation, mapping metadata, and location-based analysis. Supports international location names.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "GIS metadata", "Mapping documentation", "Geospatial analysis reports",
            "Cadastral data", "Survey reports", "Land use planning",
            "Environmental monitoring", "Satellite imagery metadata"
        ],
        not_recommended_for=[
            "Non-geospatial content"
        ]
    ),

    # ========================================================================
    # COMMERCE & RETAIL EMBEDDINGS
    # ========================================================================

    "ecommerce_1536": EmbeddingConfig(
        config_id="ecommerce_1536",
        display_name="E-Commerce & Product (1536-dim)",
        model_name="text-embedding-3-small",
        provider=EmbeddingProvider.OPENAI,
        dimension=1536,
        column="embedding",
        use_case=EmbeddingUseCase.ECOMMERCE,
        description="High-quality embeddings for e-commerce: product catalogs, descriptions, reviews, recommendations, and customer queries.",
        max_tokens=8191,
        speed="fast",
        cost_per_1k=0.00002,
        requires_api_key=True,
        recommended_for=[
            "Product catalogs", "Product descriptions", "Customer reviews",
            "Product recommendations", "Search queries", "Category classification",
            "Inventory management", "SKU matching"
        ],
        not_recommended_for=[
            "Non-retail content"
        ]
    ),

    "retail_vision_1024": EmbeddingConfig(
        config_id="retail_vision_1024",
        display_name="Retail Visual Search (1024-dim, Vision)",
        model_name="openai/clip-vit-large-patch14",
        provider=EmbeddingProvider.HUGGINGFACE,
        dimension=1024,
        column="visual_embedding",
        use_case=EmbeddingUseCase.RETAIL,
        description="Visual embeddings for retail: product images, fashion items, visual search, style matching, and inventory photos.",
        max_tokens=77,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=1700,
        recommended_for=[
            "Product images", "Visual search", "Fashion items", "Style matching",
            "Inventory photos", "Store displays", "Packaging design"
        ],
        not_recommended_for=[
            "Text-only content"
        ],
        paper_url="https://arxiv.org/abs/2103.00020"
    ),

    "fashion_1024": EmbeddingConfig(
        config_id="fashion_1024",
        display_name="Fashion & Apparel (1024-dim)",
        model_name="cohere-embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.FASHION,
        description="Specialized embeddings for fashion industry: apparel descriptions, style guides, trend analysis, and fashion content.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Apparel descriptions", "Style guides", "Fashion trends",
            "Clothing catalogs", "Size guides", "Material specifications",
            "Brand content", "Fashion blog posts"
        ],
        not_recommended_for=[
            "Non-fashion content"
        ]
    ),

    "fmcg_768": EmbeddingConfig(
        config_id="fmcg_768",
        display_name="FMCG & Consumer Goods (768-dim)",
        model_name="sentence-transformers/all-mpnet-base-v2",
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.FMCG,
        description="Embeddings for Fast-Moving Consumer Goods: product specifications, ingredients, nutritional information, and consumer packaged goods.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=420,
        recommended_for=[
            "Product specifications", "Ingredients lists", "Nutritional information",
            "Packaging details", "Consumer goods catalogs", "Brand descriptions",
            "Retail merchandising", "Supply chain docs"
        ],
        not_recommended_for=[
            "Durable goods", "Services"
        ]
    ),

    # ========================================================================
    # AGRICULTURE & MARKETING EMBEDDINGS
    # ========================================================================

    "agriculture_1024": EmbeddingConfig(
        config_id="agriculture_1024",
        display_name="Agriculture & Farming (1024-dim)",
        model_name="cohere-embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.AGRICULTURE,
        description="Embeddings for agriculture sector: crop management, soil analysis, farming techniques, agri-tech, and supply chain.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Crop management guides", "Soil analysis reports", "Farming techniques",
            "Agricultural research", "Pest control", "Irrigation systems",
            "Agri-tech documentation", "Supply chain logistics"
        ],
        not_recommended_for=[
            "Non-agricultural content"
        ]
    ),

    "marketing_1536": EmbeddingConfig(
        config_id="marketing_1536",
        display_name="Marketing & Advertising (1536-dim)",
        model_name="text-embedding-3-small",
        provider=EmbeddingProvider.OPENAI,
        dimension=1536,
        column="embedding",
        use_case=EmbeddingUseCase.MARKETING,
        description="Embeddings for marketing: campaign content, ad copy, customer sentiment, brand messaging, and social media content.",
        max_tokens=8191,
        speed="fast",
        cost_per_1k=0.00002,
        requires_api_key=True,
        recommended_for=[
            "Campaign content", "Ad copy", "Social media posts",
            "Brand messaging", "Customer feedback", "Sentiment analysis",
            "Content marketing", "Email campaigns", "Market research"
        ],
        not_recommended_for=[
            "Technical documentation"
        ]
    ),

    # ========================================================================
    # HEALTHCARE & INSURANCE EMBEDDINGS
    # ========================================================================

    "healthcare_1536": EmbeddingConfig(
        config_id="healthcare_1536",
        display_name="Healthcare & Clinical (1536-dim)",
        model_name="text-embedding-3-small",
        provider=EmbeddingProvider.OPENAI,
        dimension=1536,
        column="embedding",
        use_case=EmbeddingUseCase.HEALTHCARE,
        description="High-quality embeddings for healthcare: clinical notes, patient records, medical guidelines, healthcare administration.",
        max_tokens=8191,
        speed="fast",
        cost_per_1k=0.00002,
        requires_api_key=True,
        recommended_for=[
            "Clinical notes", "Patient records", "Medical guidelines",
            "Healthcare policies", "Insurance claims", "Treatment protocols",
            "Hospital administration", "Telemedicine transcripts"
        ],
        not_recommended_for=[
            "Research papers (use medical_768 or scientific models)"
        ]
    ),

    "insurance_1024": EmbeddingConfig(
        config_id="insurance_1024",
        display_name="Insurance & Risk Assessment (1024-dim)",
        model_name="cohere-embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.INSURANCE,
        description="Embeddings for insurance industry: policy documents, claims, risk assessment, underwriting, and actuarial analysis.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Insurance policies", "Claims documents", "Risk assessments",
            "Underwriting guidelines", "Actuarial reports", "Premium calculations",
            "Compliance documents", "Fraud detection reports"
        ],
        not_recommended_for=[
            "Non-insurance financial documents (use finance_768)"
        ]
    ),

    # ========================================================================
    # REAL ESTATE & OTHER INDUSTRIES
    # ========================================================================

    "real_estate_768": EmbeddingConfig(
        config_id="real_estate_768",
        display_name="Real Estate & Property (768-dim)",
        model_name="sentence-transformers/all-mpnet-base-v2",
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.REAL_ESTATE,
        description="Embeddings for real estate: property listings, market analysis, valuations, leases, and property management.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=420,
        recommended_for=[
            "Property listings", "Market analysis", "Property valuations",
            "Lease agreements", "Property management docs", "MLS data",
            "Appraisal reports", "Real estate contracts"
        ],
        not_recommended_for=[
            "Construction documents (use construction embeddings)"
        ]
    ),

    "telecommunications_1024": EmbeddingConfig(
        config_id="telecommunications_1024",
        display_name="Telecommunications (1024-dim)",
        model_name="cohere-embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.TELECOMMUNICATIONS,
        description="Embeddings for telecom sector: network documentation, service specifications, technical standards, and customer support.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Network documentation", "Service specifications", "Technical standards",
            "Telecom regulations", "Equipment manuals", "Customer support docs",
            "5G/Network infrastructure", "Service level agreements"
        ],
        not_recommended_for=[
            "Non-telecom technical content"
        ]
    ),

    "energy_utilities_1024": EmbeddingConfig(
        config_id="energy_utilities_1024",
        display_name="Energy & Utilities (1024-dim)",
        model_name="cohere-embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.ENERGY,
        description="Embeddings for energy sector: grid operations, renewable energy, utility management, and energy regulations.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Grid operations", "Renewable energy reports", "Utility management",
            "Energy regulations", "Power plant documentation", "Smart grid data",
            "Energy efficiency reports", "Oil & gas documentation"
        ],
        not_recommended_for=[
            "Non-energy content"
        ]
    ),

    "hospitality_tourism_768": EmbeddingConfig(
        config_id="hospitality_tourism_768",
        display_name="Hospitality & Tourism (768-dim)",
        model_name="sentence-transformers/paraphrase-multilingual-mpnet-base-v2",
        provider=EmbeddingProvider.SENTENCE_TRANSFORMERS,
        dimension=768,
        column="code_embedding",
        use_case=EmbeddingUseCase.HOSPITALITY,
        description="Multilingual embeddings for hospitality: hotel descriptions, travel guides, booking information, and customer reviews.",
        max_tokens=512,
        speed="medium",
        cost_per_1k=0.0,
        model_size_mb=970,
        recommended_for=[
            "Hotel descriptions", "Travel guides", "Booking information",
            "Customer reviews", "Restaurant menus", "Event planning",
            "Tourism brochures", "Destination guides"
        ],
        not_recommended_for=[
            "Non-hospitality content"
        ]
    ),

    "education_1024": EmbeddingConfig(
        config_id="education_1024",
        display_name="Education & E-Learning (1024-dim)",
        model_name="cohere-embed-english-v3.0",
        provider=EmbeddingProvider.COHERE,
        dimension=1024,
        column="embedding",
        use_case=EmbeddingUseCase.EDUCATION,
        description="Embeddings for education sector: course content, learning materials, assessments, and educational administration.",
        max_tokens=512,
        speed="fast",
        cost_per_1k=0.0001,
        requires_api_key=True,
        recommended_for=[
            "Course content", "Learning materials", "Assessments", "Syllabi",
            "Educational policies", "Student records", "E-learning platforms",
            "Training manuals", "Certification programs"
        ],
        not_recommended_for=[
            "Research papers (use scientific embeddings)"
        ]
    ),
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_embedding_config(config_id: str) -> Optional[EmbeddingConfig]:
    """Get embedding configuration by ID"""
    return EMBEDDING_CONFIGS.get(config_id)


def get_configs_by_use_case(use_case: EmbeddingUseCase) -> List[EmbeddingConfig]:
    """Get all embedding configurations for a specific use case"""
    return [
        config for config in EMBEDDING_CONFIGS.values()
        if config.use_case == use_case
    ]


def get_configs_by_provider(provider: EmbeddingProvider) -> List[EmbeddingConfig]:
    """Get all embedding configurations from a specific provider"""
    return [
        config for config in EMBEDDING_CONFIGS.values()
        if config.provider == provider
    ]


def get_free_configs() -> List[EmbeddingConfig]:
    """Get all free (no API key required) embedding configurations"""
    return [
        config for config in EMBEDDING_CONFIGS.values()
        if not config.requires_api_key
    ]


def get_configs_for_column(column: str) -> List[EmbeddingConfig]:
    """Get all configurations that use a specific database column"""
    return [
        config for config in EMBEDDING_CONFIGS.values()
        if config.column == column
    ]


def get_recommended_config(
    use_case: EmbeddingUseCase,
    require_free: bool = False,
    max_dimension: Optional[int] = None
) -> Optional[EmbeddingConfig]:
    """
    Get recommended embedding configuration based on criteria

    Args:
        use_case: The use case category
        require_free: If True, only return free (local) models
        max_dimension: Maximum embedding dimension

    Returns:
        Recommended EmbeddingConfig or None
    """
    configs = get_configs_by_use_case(use_case)

    if require_free:
        configs = [c for c in configs if not c.requires_api_key]

    if max_dimension:
        configs = [c for c in configs if c.dimension <= max_dimension]

    if not configs:
        return None

    # Sort by quality heuristic (dimension * speed factor)
    speed_factors = {"fast": 1.2, "medium": 1.0, "slow": 0.8}

    def quality_score(config: EmbeddingConfig) -> float:
        speed_factor = speed_factors.get(config.speed, 1.0)
        return config.dimension * speed_factor

    return max(configs, key=quality_score)


# ============================================================================
# CONFIGURATION METADATA
# ============================================================================

EMBEDDING_CONFIG_METADATA = {
    "version": "1.0",
    "total_configs": len(EMBEDDING_CONFIGS),
    "providers": list(set(c.provider for c in EMBEDDING_CONFIGS.values())),
    "use_cases": list(set(c.use_case for c in EMBEDDING_CONFIGS.values())),
    "dimension_range": {
        "min": min(c.dimension for c in EMBEDDING_CONFIGS.values()),
        "max": max(c.dimension for c in EMBEDDING_CONFIGS.values())
    },
    "free_configs": len(get_free_configs()),
    "api_configs": len([c for c in EMBEDDING_CONFIGS.values() if c.requires_api_key]),
}
