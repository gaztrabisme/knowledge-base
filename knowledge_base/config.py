import os
from pathlib import Path

from .embedder import model_dim

ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = ROOT / "knowledge-base" / "applied-ml"
SOURCE_DIRS = {
    "applied-ml": ROOT / "knowledge-base" / "applied-ml",
    "advanced-ml": ROOT / "knowledge-base" / "advanced-ml",
    "databases": ROOT / "knowledge-base" / "databases",
    "security": ROOT / "knowledge-base" / "security",
    "distributed-systems": ROOT / "knowledge-base" / "distributed-systems",
    "rust": ROOT / "knowledge-base" / "rust",
    "ai-engineering": ROOT / "knowledge-base" / "ai-engineering",
    "software-engineering": ROOT / "knowledge-base" / "software-engineering",
    "systems-ops": ROOT / "knowledge-base" / "systems-ops",
    "architecture": ROOT / "knowledge-base" / "architecture",
}
MARKDOWN_DIR = ROOT / "data" / "markdown"
CHUNKS_DIR = ROOT / "data" / "chunks"

# Experiment knobs (env-overridable so a candidate index can be built/eval'd into its
# own collection+dir without code edits). Defaults = the shipped v6.2 production index.
QDRANT_DIR = Path(os.environ.get("KB_QDRANT_DIR", str(ROOT / "data" / "qdrant")))
COLLECTION_NAME = os.environ.get("KB_COLLECTION", "developer_knowledge")
EMBEDDING_MODEL = os.environ.get("KB_EMBEDDING_MODEL", "jinaai/jina-embeddings-v5-text-small-retrieval")
# Dim derives from the model registry unless explicitly overridden.
EMBEDDING_DIM = int(os.environ.get("KB_EMBEDDING_DIM", str(model_dim(EMBEDDING_MODEL))))

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_MODEL = "qwen3.6-35b-a3b-mlx"
BM25_MODEL = "Qdrant/bm25"
RERANKER_MODEL = "cross-encoder/ettin-reranker-150m-v1"

RERANKER_SCORE_FLOOR = 4.0
RERANKER_MIN_RESULTS = 3

# Thresholds are real tokens (tiktoken cl100k_base ≈ Jina v5 tokenizer).
# v6: children tightened to a true 250 for sharper match units; parents kept
# near their prior effective size (~1900 real tokens) to preserve returned context.
PARENT_MAX_TOKENS = 1900
CHILD_MAX_TOKENS = 250
CHILD_MIN_TOKENS = 75

BOOKS = {
    "kagglebook_secondedition": "Kaggle Book, 2nd Edition",
    "machinelearningwithpytorchandscikit-learn": "Machine Learning with PyTorch and Scikit-Learn",
    "masteringpytorch_secondedition": "Mastering PyTorch, 2nd Edition",
    "bayesiananalysiswithpython_thirdedition": "Bayesian Analysis with Python, 3rd Edition",
    "moderntimeseriesforecastingwithpython_secondedition": "Modern Time Series Forecasting with Python, 2nd Edition",
    "causalinferenceanddiscoveryinpython": "Causal Inference and Discovery in Python",
    "deepreinforcementlearninghands-on_thirdedition": "Deep Reinforcement Learning Hands-On, 3rd Edition",
    "graphmachinelearning_secondedition": "Graph Machine Learning, 2nd Edition",
    "machinelearningengineeringwithpython_secondedition": "Machine Learning Engineering with Python, 2nd Edition",
    "scikit-learncookbook_thirdedition": "Scikit-Learn Cookbook, 3rd Edition",
    "pythonmachinelearningbyexample_fourthedition": "Python Machine Learning by Example, 4th Edition",
    "mathematicsofmachinelearning": "Mathematics of Machine Learning",
    "pandascookbook_thirdedition": "Pandas Cookbook, 3rd Edition",
    "machinelearningforalgorithmictradingsecondedition": "Machine Learning for Algorithmic Trading, 2nd Edition",
    "artificialintelligenceforcybersecurity": "Artificial Intelligence for Cybersecurity",
    "hands-onartificialintelligenceforiot_secondedition": "Hands-On AI for IoT, 2nd Edition",
    "azureai-102certificationessentials": "Azure AI-102 Certification Essentials",
    "hands-onmachinelearningwithcplusplus_secondedition": "Hands-On Machine Learning with C++, 2nd Edition",
    "optimization-algorithms": "Optimization Algorithms (Khamis)",
    # Advanced ML / Deep Learning (theory canon)
    "bishop-prml": "Pattern Recognition and Machine Learning (Bishop)",
    "probml-intro": "Probabilistic Machine Learning: An Introduction (Murphy)",
    "probml-advanced": "Probabilistic Machine Learning: Advanced Topics (Murphy)",
    "understanding-deep-learning": "Understanding Deep Learning (Prince)",
    "d2l-en": "Dive into Deep Learning",
    "lbdl": "The Little Book of Deep Learning (Fleuret)",
    "cuda-programming-guide": "NVIDIA CUDA C++ Programming Guide",
    # Databases
    "postgresql-14-internals": "PostgreSQL 14 Internals",
    "postgresql-internals-interdb": "The Internals of PostgreSQL (Suzuki)",
    "use-the-index-luke": "Use The Index, Luke — SQL Indexing",
    "database-design-2nd-ed": "Database Design, 2nd Edition",
    "redis-for-dummies": "Redis for Dummies",
    "little-redis-book": "The Little Redis Book",
    "digitalocean-redis": "DigitalOcean Redis Guide",
    # Distributed Systems
    "designing-distributed-systems": "Designing Distributed Systems",
    "distributed-systems-fun-profit": "Distributed Systems for Fun and Profit",
    # Security
    "boneh-shoup-applied-cryptography": "Applied Cryptography (Boneh & Shoup)",
    "crypto-101": "Crypto 101",
    "joy-of-cryptography": "The Joy of Cryptography",
    "owasp-developer-guide": "OWASP Developer Guide",
    "owasp-wstg-v4.2": "OWASP Web Security Testing Guide v4.2",
    "owasp-asvs-v5": "OWASP ASVS v5",
    "oauth-rfcs-book": "OAuth RFCs Book",
    "owasp-cheat-sheets": "OWASP Cheat Sheet Series",
    # Rust
    "asynchronousprogramminginrust": "Asynchronous Programming in Rust",
    "creativeprojectsforrustprogrammers": "Creative Projects for Rust Programmers",
    "designpatternsandbestpracticesinrust": "Design Patterns and Best Practices in Rust",
    "gamedevelopmentwithrustandwebassembly": "Game Development with Rust and WebAssembly",
    "hands-onconcurrencywithrust": "Hands-On Concurrency with Rust",
    "practicalsystemprogrammingforrustdevelopers": "Practical System Programming for Rust Developers",
    "rust_ebook": "Rust Programming (Nouman Azam)",
    "rustforblockchainapplicationdevelopment": "Rust for Blockchain Application Development",
    "rustforcplusplusdeveloper": "Rust for C++ Developers",
    "rustprogramminghandbook": "The Rust Programming Handbook",
    "rustwebdevelopmentwithrocket": "Rust Web Development with Rocket",
    "rustwebprogramming": "Rust Web Programming",
    "speedupyourpythonwithrust": "Speed Up Your Python with Rust",
    # AI Engineering
    "ai-engineering-huyen": "AI Engineering: Building Applications with Foundation Models (Huyen)",
    "designing-ml-systems-huyen": "Designing Machine Learning Systems (Huyen)",
    "agentic-design-patterns": "Agentic Design Patterns (Gulli)",
    "ai-powered-search": "AI-Powered Search (Grainger, Turnbull, Irwin)",
    "llms-in-production": "LLMs in Production (Brousseau & Sharp)",
    "building-reliable-ai-systems": "Building Reliable AI Systems (Shahani)",
    "generative-ai-in-action": "Generative AI in Action (Bahree)",
    "transformers-in-action": "Transformers in Action (Koenigstein)",
    "illustrated-guide-ai-agents": "An Illustrated Guide to AI Agents (Grootendorst & Alammar)",
    "human-in-the-loop-ml": "Human-in-the-Loop Machine Learning (Monarch)",
    "interpretable-ai": "Interpretable AI (Thampi)",
    "ml-platform-engineering": "Build a Machine Learning Platform (From Scratch) (Tan, Padmanabha)",
    "effective-conversational-ai": "Effective Conversational AI (Freed, Jacobs, Rozsa)",
    "coding-with-ai": "Coding with AI (Morgan)",
    "software-testing-with-genai": "Software Testing with Generative AI (Winteringham)",
    "art-of-ai-product-development": "The Art of AI Product Development (Lipenkova)",
    "financial-ai-in-practice": "Financial AI in Practice (Kim, MEAP)",
    # Software Engineering / Architecture (classic canon)
    "clean-architecture": "Clean Architecture (Martin)",
    "clean-code": "Clean Code (Martin)",
    "domain-driven-design-evans": "Domain-Driven Design (Evans)",
    "patterns-enterprise-application-architecture": "Patterns of Enterprise Application Architecture (Fowler)",
    "design-patterns-gof": "Design Patterns: Elements of Reusable OO Software (Gang of Four)",
    "enterprise-integration-patterns": "Enterprise Integration Patterns (Hohpe)",
    "refactoring": "Refactoring: Improving the Design of Existing Code (Fowler)",
    "software-architecture-patterns": "Software Architecture Patterns (Richards)",
    "microservices-design-to-deploy": "Microservices: From Design to Deployment",
    "production-ready-microservices": "Production-Ready Microservices",
    "release-it": "Release It! Design and Deploy Production-Ready Software (Nygard)",
    "site-reliability-engineering": "Site Reliability Engineering (Google SRE)",
    "continuous-delivery": "Continuous Delivery (Humble & Farley)",
    "nosql-distilled": "NoSQL Distilled (Fowler & Sadalage)",
    "rest-in-practice": "REST in Practice (Webber, Parastatidis, Robinson)",
    "designing-great-web-apis": "Designing Great Web APIs",
    "growing-oo-software-by-tests": "Growing Object-Oriented Software, Guided by Tests",
    "tdd-by-example": "Test-Driven Development by Example (Beck)",
    "swebok": "Guide to the Software Engineering Body of Knowledge (SWEBOK)",
    "intro-to-algorithms-clrs": "Introduction to Algorithms (CLRS)",
    "ai-modern-approach": "Artificial Intelligence: A Modern Approach (Russell & Norvig)",
    "pro-git": "Pro Git, 2nd Edition (Chacon & Straub)",
    "effective-platform-engineering": "Effective Platform Engineering (Chankramath, Cheneweth et al.)",
    "looks-good-to-me": "Looks Good to Me: Constructive Code Reviews (Braganza)",
    # Databases (added to existing domain)
    "sql-relational-theory": "SQL and Relational Theory, 3rd Edition (Date)",
    # Systems / Ops
    "seriouspython": "Serious Python (Danjou)",
    "ultimatelinuxshellscriptingguide": "The Ultimate Linux Shell Scripting Guide",
    "masteringlinuxsecurityandhardening": "Mastering Linux Security and Hardening, 3rd Edition",
    "linuxservicemanagement-systemd": "Linux Service Management Made Easy with systemd",
    "ultimateubuntuhandbook": "The Ultimate Ubuntu Handbook",
    "masteringlinuxadministration": "Mastering Linux Administration",
    "masteringpythonnetworking": "Mastering Python Networking, 4th Edition",
    "linuxkernelprogramming": "Linux Kernel Programming, 2nd Edition",
    "modernnetworkobservability": "Modern Network Observability",
    # Architecture (O'Reilly architecture shelf)
    "software-architect-elevator": "The Software Architect Elevator (Hohpe)",
    "software-architecture-hard-parts": "Software Architecture: The Hard Parts (Ford, Richards, Sadalage, Dehghani)",
    "building-evolutionary-architectures": "Building Evolutionary Architectures, 2nd Edition (Ford, Parsons, Kua, Sadalage)",
    "software-architecture-metrics": "Software Architecture Metrics (Ciceri, Farley, Ford et al.)",
    "facilitating-software-architecture": "Facilitating Software Architecture (Harmel-Law)",
    "fundamentals-enterprise-architecture": "Fundamentals of Enterprise Architecture (McCabe)",
    "semantic-software-design": "Semantic Software Design (Hewitt)",
    "learning-systems-thinking": "Learning Systems Thinking (Montalion)",
    "architecture-patterns-with-python": "Architecture Patterns with Python (Percival & Gregory)",
    "learning-domain-driven-design": "Learning Domain-Driven Design (Khononov)",
    "building-microservices-2e": "Building Microservices, 2nd Edition (Newman)",
    "building-event-driven-microservices": "Building Event-Driven Microservices, 2nd Edition (Bellemare)",
    "designing-distributed-systems-2e": "Designing Distributed Systems, 2nd Edition (Burns)",
    "building-multi-tenant-saas": "Building Multi-Tenant SaaS Architectures (Golding)",
    "building-medallion-architectures": "Building Medallion Architectures (Strengholt)",
    "flow-architectures": "Flow Architectures (Urquhart)",
    "mastering-api-architecture": "Mastering API Architecture (Gough, Bryant, Auburn)",
    "learning-api-styles": "Learning API Styles (Dynowski & Dulak)",
    "building-green-software": "Building Green Software (Currie, Hsu, Bergman)",
}
