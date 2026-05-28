from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EPUB_DIR = ROOT / "knowledge-base" / "applied-ml"
SOURCE_DIRS = {
    "applied-ml": ROOT / "knowledge-base" / "applied-ml",
    "databases": ROOT / "knowledge-base" / "databases",
    "security": ROOT / "knowledge-base" / "security",
    "distributed-systems": ROOT / "knowledge-base" / "distributed-systems",
}
RAG_GUIDE_DIR = ROOT / "knowledge-base" / "production-rag-guide"
MARKDOWN_DIR = ROOT / "data" / "markdown"
CHUNKS_DIR = ROOT / "data" / "chunks"
QDRANT_DIR = ROOT / "data" / "qdrant"

COLLECTION_NAME = "developer_knowledge"
EMBEDDING_DIM = 1024

LM_STUDIO_BASE_URL = "http://localhost:1234/v1"
LM_STUDIO_MODEL = "qwen3.6-35b-a3b-mlx"

EMBEDDING_MODEL = "jinaai/jina-embeddings-v5-text-small-retrieval"
BM25_MODEL = "Qdrant/bm25"
RERANKER_MODEL = "cross-encoder/ettin-reranker-150m-v1"

RERANKER_SCORE_FLOOR = 4.0
RERANKER_MIN_RESULTS = 3

PARENT_MAX_TOKENS = 1200
CHILD_MAX_TOKENS = 250
CHILD_MIN_TOKENS = 50

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
    "production-rag-guide": "Production RAG Guide",
    # Databases
    "postgresql-14-internals": "PostgreSQL 14 Internals",
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
}
