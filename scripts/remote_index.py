#!/usr/bin/env python3
"""Standalone indexing script for running on a remote GPU machine.
Reads chunk JSONs, embeds the dense vector via the shared embedder adapter
(rsync `knowledge_base/embedder.py` to ~/kb-work/embedder.py beside this script),
writes a Qdrant file-based index.

Model + output dir + collection are env-overridable so each candidate builds in
isolation (same contract as the package's config.py):
    KB_EMBEDDING_MODEL  default jina v5-small
    KB_QDRANT_DIR       default <work_dir>/qdrant
    KB_COLLECTION       default developer_knowledge
"""

import hashlib
import json
import os
import sys
from pathlib import Path

from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

from embedder import encode_texts, load_model, model_dim

EMBEDDING_MODEL = os.environ.get("KB_EMBEDDING_MODEL", "jinaai/jina-embeddings-v5-text-small-retrieval")
EMBEDDING_DIM = model_dim(EMBEDDING_MODEL)
COLLECTION_NAME = os.environ.get("KB_COLLECTION", "developer_knowledge")

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
    # v8 technical shelf START
    "3d-data-science-python": "3D Data Science with Python (Florent Poux)",
    "apis-a-strategy-guide": "APIs: A Strategy Guide (Daniel Jacobson, Greg Brail, Dan Woods)",
    "advanced-analytics-pyspark": "Advanced Analytics with Pyspark (Akash Tandon, Sandy Ryza, Uri Laserson etc.)",
    "advanced-apple-debugging": "Advanced Apple Debugging and Reverse Engineering (Derek Selander)",
    "analytics-tools-optimizing-ux": "Analytics Tools for Optimizing UX (Simon Mackie)",
    "angular-up-and-running": "Angular: Up and Running : Learning Angular, Step by Step (Shyam Seshadri)",
    "architecting-data-ml-platforms": "Architecting Data and Machine Learning Platforms (Marco Tranquillin)",
    "arm-assembly-internals": "Blue Fox: Arm Assembly Internals & Reverse Engineering (Maria Markstedter)",
    "articulating-design-decisions": "Articulating Design Decisions (Tom Greever)",
    "assembly-language-x86-processors": "Assembly Language for x86 Processors (Sixth edition) (Kip Irvine)",
    "automating-data-quality-monitoring": "Automating Data Quality Monitoring (Jeremy Stanley, Paige Schwartz)",
    "build-reasoning-model": "Build a Reasoning Model (From Scratch) (Sebastian Raschka)",
    "build-text-to-image-generator": "Build a Text-to-Image Generator (from Scratch) (Mark Liu)",
    "building-applications-ai-agents": "Building Applications with AI Agents (Michael Albada)",
    "building-design-systems": "Building Design Systems (Sarrah Vesselov)",
    "building-genai-services-fastapi": "Building Generative AI Services with FastAPI A Practical Approach to Developing Context-Rich Generative AI Applications (Alireza Parandeh)",
    "building-knowledge-graphs": "Building Knowledge Graphs (Jesus Barrasa, Maya Natarajan, Jim Webber)",
    "building-machine-learning-pipelines": "Building Machine Learning Pipelines (Hannes Hapke)",
    "building-micro-frontends": "Building Micro-Frontends (Luca Mezzalira)",
    "building-secure-reliable-systems": "Building Secure and Reliable Systems (Heather Adkins, Betsy Beyer etc.)",
    "building-event-driven-data-mesh": "Building an Event-Driven Data Mesh (Adam Bellemare)",
    "css-definitive-guide": "CSS: The Definitive Guide (Eric A. Meyer, Estelle Weyl)",
    "css-in-depth-2e": "CSS in Depth, Second Edition (Keith J. Grant)",
    "certified-ethical-hacker": "Certified Ethical Hacker (CEH) Study Guide (Matt Walker)",
    "chaos-engineering": "Chaos Engineering (Casey Rosenthal Nora Jones)",
    "cloud-native-devops-kubernetes": "Cloud Native DevOps with Kubernetes (John Arundel, Justin Domingus)",
    "cloud-native-security-cookbook": "Cloud Native Security Cookbook (Josh Armitage)",
    "cockroachdb-definitive-guide": "CockroachDB: The Definitive Guide (Guy Harrison, Jesse Seldess, Ben Darnell)",
    "continuous-api-management": "Continuous API Management (Mehdi Medjaoui, Erik Wilde, Ronnie Mitra etc.)",
    "creating-web-animations": "Creating Web Animations (Kirupa Chinnathambi)",
    "d3js-in-action": "D3.js in Action Data visualization with JavaScript (Elijah Meeks)",
    "data-governance-definitive-guide": "Data Governance: the Definitive Guide (Evren Eryurek, Uri Gilad etc.)",
    "data-governance-unity-catalog": "Data Governance with Unity Catalog on Databricks (Kiran Sreekumar, Karthik Subbarao)",
    "data-management-at-scale": "Data Management at Scale: Modern Data Architecture with Data Mesh and Data Fabric (Piethein Strengholt)",
    "data-quality-fundamentals": "Data Quality Fundamentals (Barr Moses, Lior Gavish, Molly Vorwerck)",
    "data-science-hard-parts": "Data Science: The Hard Parts (Daniel Vaughan)",
    "data-science-for-business": "Data Science for Business (Foster Provost, Tom Fawcett)",
    "data-science-from-scratch": "Data Science from Scratch (Joel Grus)",
    "database-internals": "Database Internals A Deep-Dive into How Distributed Data Systems Work (Alex Petrov)",
    "deciphering-data-architectures": "Deciphering Data Architectures (James Serra)",
    "delta-lake-definitive-guide": "Delta Lake The Definitive Guide (Denny Lee, Tristen Wentling etc.)",
    "design-for-how-people-think": "Design for How People Think (John Whalen)",
    "designing-autonomous-ai": "Designing Autonomous AI (Kence Anderson)",
    "designing-data-intensive-applications": "Designing Data-Intensive Applications (Martin Kleppmann)",
    "designing-interfaces": "Designing Interfaces Patterns for Effective Interaction Design (Jenifer Tidwell, Charles Brewer etc.)",
    "designing-llm-applications": "Designing Large Language Model Applications A Holistic Approach to LLMs (Suhas Pai)",
    "domain-specific-small-language-models": "Domain-Specific Small Language Models Efficient AI for local deployment (Guglielmo Iozzia)",
    "effective-typescript": "Effective TypeScript (Dan Vanderkam)",
    "effective-ui": "Effective UI The Art of Building Great User Experience in Software (Jonathan Anderson, John McRee, Robb Wilson)",
    "efficient-linux-command-line": "Efficient Linux at the Command Line (Daniel J. Barrett)",
    "efficient-nodejs": "Efficient Node.js (Samer Buna)",
    "essential-graphrag": "Essential GraphRAG (Tomaž Bratanič, Oskar Hane)",
    "essential-math-ai": "Essential Math for AI (Hala Nelson)",
    "excel-for-accountants": "Excel for Accountants: Tips, Tricks & Techniques (Conrad Carlberg)",
    "exploratory-data-analysis-visualization": "Exploratory Data Analysis Descriptive Analysis, Visualization, and Dashboard Design (with Code Snippets in Python) (Leandro Nunes de Castro)",
    "financial-data-engineering": "Financial Data Engineering (Tamer Khraisha)",
    "fluent-react": "Fluent React (Tejas Kumar)",
    "foundations-scalable-systems": "Foundations of Scalable Systems (Ian Gorton)",
    "fundamentals-computer-graphics": "Fundamentals of Computer Graphics, Fourth Edition (Steve Marschner, Peter Shirley)",
    "fundamentals-data-engineering": "Fundamentals of Data Engineering (Joe Reis, Matt Housley)",
    "fundamentals-metadata-management": "Fundamentals of Metadata Management Uncover the Meta Grid and Unlock IT, Data, Information, and Knowledge Management (Ole Olesen-Bagneux)",
    "fundamentals-microsoft-fabric": "Fundamentals of Microsoft Fabric (Nikola Ilic, Ben Weissman)",
    "generative-deep-learning": "Generative Deep Learning (David Foster)",
    "http-definitive-guide": "HTTP - The Definitive Guide (David Gourley, Brian Totty, Marjorie Sayer etc.)",
    "hands-on-large-language-models": "Hands-On Large Language Models (Jay Alammar, Maarten Grootendorst)",
    "hands-on-rag-production": "Hands-On RAG for Production (Ofer Mendelevitch, Forrest Sheng Bao)",
    "hands-on-selenium-webdriver": "Hands-On Selenium WebDriver with Java (Boni Garcia)",
    "hands-on-unsupervised-learning": "Hands-On Unsupervised Learning Using Python (Ankur A. Patel)",
    "head-first-statistics-analysis": "Head First Statistics for Data Analysis (Dawn Griffiths)",
    "holacracy": "Holacracy (Brian J. Robertson)",
    "implementing-data-mesh": "Implementing Data Mesh (Jean-Georges Perrin Eric Broda)",
    "infrastructure-as-code": "Infrastructure as Code (Kief Morris)",
    "inside-cyber-warfare": "Inside Cyber Warfare (Jeffrey Caruso)",
    "intelligence-driven-incident-response": "Intelligence-Driven Incident Response (Rebekah Brown, Scott Roberts)",
    "data-visualization-storytelling": "Introduction to Data Visualization & Storytelling (Jose Berengueres, Marybeth Sandell & Ali Fenwick)",
    "kafka-definitive-guide": "Kafka: The Definitive Guide (Neha Narkhede, Gwen Shapira, Todd Palino)",
    "kubernetes-security-observability": "Kubernetes Security and Observability (Brendan Creane, Amit Gupta)",
    "llmops": "LLMOps (Abi Aryan)",
    "langchain-life-sciences-healthcare": "LangChain for Life Sciences and Healthcare (Ivan Reznikov)",
    "laws-of-ux": "Laws of UX (Jon Yablonski)",
    "lean-ux": "Lean UX (Jeff Gothelf, Josh Seiden)",
    "learning-agile": "Learning Agile (Andrew Stellman, Jennifer Greene)",
    "learning-git": "Learning Git (Anna Skoulikari)",
    "learning-github-actions": "Learning GitHub Actions (Brent Laster)",
    "learning-javascript-design-patterns": "Learning JavaScript Design Patterns (Addy Osmani)",
    "learning-modern-linux": "Learning Modern Linux (Michael Hausenblas)",
    "learning-opentelemetry": "Learning OpenTelemetry (Ted Young, Austin Parker)",
    "learning-spark": "Learning Spark Lightning-Fast Big Data Analysis (Holden Karau, Andy Konwinski etc.)",
    "learning-test-driven-development": "Learning Test-Driven Development (Saleem Siddiqui)",
    "learning-threejs": "Learning Three.js programming 3D animations and visualizations for the web with HTML5 and WebGL (Jos Dirksen)",
    "learning-vue": "Learning Vue (Maya Shavin)",
    "machine-learning-production-systems": "Machine Learning Production Systems (Robert Crowe, Hannes Hapke etc.)",
    "machine-learning-econometrics": "Machine Learning for Econometrics (Christophe Gaillac, Jérémy LHour)",
    "making-sense-of-data": "Making Sense of Data: A Practical Guide to Exploratory Data Analysis and Data Mining (Glenn J. Myatt)",
    "microservice-architecture": "Microservice Architecture (Irakli Nadareishvili, Ronnie Mitra etc.)",
    "modern-data-analytics-excel": "Modern Data Analytics in Excel (George Mount)",
    "monolith-to-microservices": "Monolith to Microservices Evolutionary Patterns to Transform Your Monolith (Sam Newman)",
    "nginx-cookbook": "NGINX Cookbook (Derek DeJonghe)",
    "natural-language-processing-transformers": "Natural Language Processing with Transformers (Lewis Tunstall etc.)",
    "policy-as-code": "Policy as Code (Jimmy Ray)",
    "practical-lakehouse-architecture": "Practical Lakehouse Architecture (Gaurav Ashok Thalpati)",
    "practical-linear-algebra-data-science": "Practical Linear Algebra for Data Science (Cohen, Mike X.)",
    "practical-web-accessibility": "Practical Web Accessibility (Ashley Firth)",
    "practical-reverse-engineering": "Practical Reverse Engineering (Bruce Dang, Alexandre Gazet etc.)",
    "predictive-analytics-modern-enterprise": "Predictive Analytics for the Modern Enterprise (Nooruddin Abbas Ali)",
    "project-management-with-ai": "Project Management with AI For Dummies (Daniel Stanton)",
    "rest-api-design-rulebook": "REST API Design Rulebook (Mark Masse)",
    "restful-web-apis": "RESTful Web APIs (Leonard Richardson, Mike Amundsen, Sam Ruby)",
    "real-world-svelte": "Real-World Svelte (Tan Li Hau)",
    "refactoring-ui": "Refactoring UI (Adam Wathan, Steve Schoger)",
    "reinforcement-learning-finance": "Reinforcement Learning for Finance (Yves Hilpisch)",
    "reverse-engineering-cybersecurity": "Reverse Engineering for Cybersecurity (Felix K. Jackson)",
    "reverse-engineering-for-beginners": "Reverse Engineering for Beginners (Yurichev D.)",
    "sql-server-advanced-troubleshooting": "SQL Server Advanced Troubleshooting and Performance Tuning (Dmitri Korotkevitch)",
    "scaling-machine-learning-with-spark": "Scaling Machine Learning with Spark (Adi Polak)",
    "software-supply-chain-security": "Software Supply Chain Security (Cassie Crossley)",
    "spark-definitive-guide": "Spark: The Definitive Guide (Bill Chambers, Matei Zaharia)",
    "statistics-by-simulation": "Statistics by Simulation (Carsten F. Dormann, Aaron M. Ellison)",
    "storytelling-in-design": "Storytelling in Design (Anna Dahlström)",
    "strategic-writing-for-ux": "Strategic Writing for UX (Torrey Podmajersky)",
    "strengthening-deep-neural-networks": "Strengthening Deep Neural Networks (Katy Warr)",
    "testing-javascript-applications": "Testing JavaScript Applications (Lucas da Costa)",
    "llm-security-playbook": "The Developer’s Playbook for Large Language Model Security (Steve Wilson)",
    "enterprise-big-data-lake": "The Enterprise Big Data Lake (Gorelik, Alex)",
    "ghidra-book": "The Ghidra Book The Definitive Guide (Chris Eagle Kara Nance)",
    "practitioners-guide-graph-data": "The Practitioner's Guide to Graph Data (Denise Koessler Gosnell etc.)",
    "scrum-masters-path": "The Scrum Master’s Path: 2 in 1 Bundle. A Guide for Servant Leaders Navigating Growth and Change Using SCRUM and the Agile Project Management (Liam Taylor [Taylor, Liam])",
    "webgpu-sourcebook": "The WebGPU Sourcebook: High-Performance Graphics and Machine Learning in the Browser (Matthew Scarpino)",
    "think-like-ux-researcher": "Think Like a UX Researcher : How to Observe Users, Influence Design, and Shape Business Strategy (David Travis Philip Hodgson)",
    "think-stats-3e": "Think Stats (Allen B. Downey)",
    "training-data-for-machine-learning": "Training Data for Machine Learning (Anthony Sarkis)",
    "typescript-cookbook": "TypeScript Cookbook (Stefan Baumgartner)",
    "ui-design-principles": "UI Design Principles Learn to create beautiful and usable interfaces from scratch (Michael Filipiuk)",
    "ux-for-lean-startups": "UX for Lean Startups (Laura Klein)",
    "unifying-business-data-code": "Unifying Business, Data, and Code (Ron Itelman, Juan Cruz Viotti)",
    "user-story-mapping": "User Story Mapping: Discover the Whole Story, Build the Right Product (Jeff Patton)",
    "vector-databases-introduction": "Vector Databases A Practical Introduction (Nitin Borwankar)",
    "web-accessibility-cookbook": "Web Accessibility Cookbook (Manuel Matuzovic)",
    "web-performance-engineering": "Web Performance Engineering in the Age of AI Mastering Speed and Quality for AI-Generated Applications (Addy Osmani)",
    "web-performance-in-action": "Web Performance in Action Building Faster Web Pages (Jeremy Wagner)",
    "web-scraping-with-python": "Web Scraping with Python (Ryan Mitchell)",
    "writing-excel-macros-vba": "Writing Excel Macros with VBA (Steven Roman)",
    "zero-trust-networks-2e": "Zero Trust Networks (Razi Rais, Christina Morillo, Evan Gilman etc.)",
    "asynchronousprogrammingwithcplusplus": "Asynchronous Programming with C++ (Javier Reguera-Salgado | Juan Antonio Rufes)",
    "bare-metalembeddedcprogramming": "Bare-Metal Embedded C Programming (Israel Gbati)",
    "buildinglowlatencyapplicationswithc": "Building Low Latency Applications with C++ (Sourav Ghosh)",
    "candalgorithmicthinkingforthecompletebeginner": "CPP and Algorithmic Thinking for the Complete Beginner - Third Edition (Aristides S. Bouras)",
    "cmakebestpractices": "CMake Best Practices (Dominik Berner and Mustafa Kemal Gilor)",
    "cplusplus20stlcookbook2e": "C++23 STL Cookbook (Bill Weinman)",
    "cplusplusmemorymanagement": "C++ Memory Management (Patrice Roy)",
    "cplusplusprogrammersmindset": "The C++ Programmer's Mindset (Sam Morley)",
    "datastructuresandalgorithmswiththecplusplusstl": "Data Structures and Algorithms with the C++ STL (John E. Farrier)",
    "debunkingcplusplusmyths": "Debunking C++ Myths (Alexandru Bolboacă | Ferenc-Lajos Deák)",
    "gpuprogrammingwithcplusplusandcuda": "GPU Programming with C++ and CUDA (Paulo Motta)",
    "hands-ondesignpatternswithcplusplus2e": "Hands-On Design Patterns with C++ (Fedor G. Pikus)",
    "learnllvm17secondedition": "Learn LLVM 17 (Kai Nacke and Amy Kwan)",
    "llvmcodegeneration": "LLVM Code Generation (Quentin Colombet)",
    "moderncmakeforcplusplus2e": "Modern CMake for C++ (Rafał Świdziński)",
    "moderncplusplusprogrammingcookbook3eepub": "Modern C++ Programming Cookbook (Marius Bancila)",
    "qt6cplusplusguiprogrammingcookbook": "Qt 6 C++ GUI Programming Cookbook (Lee Zhi Eng)",
    "refactoringwithcplusplus": "Refactoring with C++ (Dmitry Danilov)",
    "softwarearchitecturewithcplusplussecondedition": "Software Architecture with C++ (Mr. Andrey Gavrilin | Mr. Adrian Ostrowski | Mr. Piotr Gaczkowski)",
    "storytelling-with-data": "Storytelling with Data (Cole Nussbaumer Knaflic)",
    "templatemetaprogrammingwithc": "Template Metaprogramming with C++ (Marius Bancila)",
    "x86-software-reverse-engineering": "X86 Software Reverse-Engineering, Cracking, and Counter-Measures (Stephanie Domas, Christopher Domas)",
    # v8 technical shelf END
    # v9 intake START
    "agentic-mesh": "Agentic Mesh: The GenAI-Powered Autonomous Agent Ecosystem (Eric Broda, Davis Broda)",
    "art-of-assembly-language": "The Art of Assembly Language (Randall Hyde)",
    "bargaining-for-advantage": "Bargaining for Advantage: Negotiation Strategies for Reasonable People (G. Richard Shell)",
    "challenger-sale": "The Challenger Sale: Taking Control of the Customer Conversation (Matthew Dixon, Brent Adamson)",
    "container-security": "Container Security: Fundamental Technology Concepts That Protect Containerized Applications (Liz Rice)",
    "critical-thinking-about-research": "Critical Thinking About Research: Psychology and Related Fields (Julian Meltzoff, Harris M. Cooper)",
    "designing-ai-interfaces": "Designing AI Interfaces: Design Principles for Creative and Autonomous AI (Louise Macfadyen)",
    "flawless-consulting": "Flawless Consulting: A Guide to Getting Your Expertise Used, 3rd Edition (Peter Block)",
    "flawless-consulting-fieldbook-companion-2e": "The Flawless Consulting Fieldbook Companion: A Guide to Understanding Your Expertise, 2nd Edition (Peter Block)",
    "getting-to-yes": "Getting to Yes: Negotiating Agreement Without Giving In (Roger Fisher, William Ury, Bruce Patton)",
    "hands-on-site-reliability-engineering": "Hands-On Site Reliability Engineering",
    "hbr-guide-business-writing": "HBR Guide to Better Business Writing (Bryan A. Garner)",
    "high-performance-browser-networking": "High Performance Browser Networking (Ilya Grigorik)",
    "how-to-read-a-paper": "How to Read a Paper: The Basics of Evidence-Based Healthcare (Trisha Greenhalgh, Paul Dijkstra)",
    "key-account-management": "Key Account Management: The Definitive Guide, 2nd Edition (Malcolm McDonald, Diana Woodburn)",
    "meddicc": "MEDDICC: The Ultimate Guide to Staying One Step Ahead in the Complex Sale (Andy Whyte)",
    "new-ethics-of-journalism": "The New Ethics of Journalism: Principles for the 21st Century (Kelly McBride, Tom Rosenstiel)",
    "practical-cloud-security": "Practical Cloud Security: A Guide for Secure Design and Deployment (Chris Dotson)",
    "privacy-in-context": "Privacy in Context: Technology, Policy, and the Integrity of Social Life (Helen Nissenbaum)",
    "project-planning-scheduling-control": "Project Planning, Scheduling, and Control (James P. Lewis)",
    "python-for-devops": "Python for DevOps: Learn Ruthlessly Effective Automation (Noah Gift, Kennedy Behrman, Alfredo Deza et al.)",
    "real-world-software-development": "Real-World Software Development (Raoul-Gabriel Urma, Richard Warburton)",
    "research-ethics-integrity-social-scientists": "Research Ethics and Integrity for Social Scientists, 2nd Edition (Mark Israel)",
    "research-methods-psychology": "Research Methods in Psychology (Beth Morling)",
    "selling-to-big-companies": "Selling to Big Companies (Jill Konrath)",
    "software-engineering-at-google": "Software Engineering at Google (Hyrum Wright, Tom Manshreck, Titus Winters)",
    "value-based-fees": "Value-Based Fees: How to Charge What You're Worth and Get What You Charge (Alan Weiss)",
    # v9 intake END

}


def text_to_sparse_vector(text: str, sparse_model: SparseTextEmbedding) -> models.SparseVector:
    """Convert text to a sparse vector using FastEmbed's Qdrant/bm25 model."""
    results = list(sparse_model.embed([text]))
    if not results:
        return models.SparseVector(indices=[0], values=[0.0])
    sparse = results[0]
    return models.SparseVector(
        indices=sparse.indices.tolist(),
        values=sparse.values.tolist(),
    )


def main():
    work_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(".")
    chunks_dir = work_dir / "chunks"
    qdrant_dir = Path(os.environ.get("KB_QDRANT_DIR", str(work_dir / "qdrant")))
    qdrant_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading dense model {EMBEDDING_MODEL} (dim {EMBEDDING_DIM}) -> {qdrant_dir} [{COLLECTION_NAME}]")
    model = load_model(EMBEDDING_MODEL)
    print("Loading sparse model Qdrant/bm25...")
    sparse_model = SparseTextEmbedding("Qdrant/bm25")
    print("Models loaded.")

    client = QdrantClient(path=str(qdrant_dir))
    collections = [c.name for c in client.get_collections().collections]
    if COLLECTION_NAME not in collections:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=models.VectorParams(size=EMBEDDING_DIM, distance=models.Distance.COSINE),
            sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )

    batch_size = int(os.environ.get("KB_INDEX_BATCH", "48"))  # was 4 (starved the 5080); 128 OOMs Jina on 15GB
    total_indexed = 0

    for chunk_file in sorted(chunks_dir.glob("*.json")):
        slug = chunk_file.stem
        print(f"Indexing: {slug}")

        existing = client.scroll(
            collection_name=COLLECTION_NAME,
            scroll_filter=models.Filter(must=[
                models.FieldCondition(key="book", match=models.MatchValue(value=slug))
            ]),
            limit=1,
        )
        if existing[0]:
            print("  Already indexed, skipping.")
            continue

        with open(chunk_file) as f:
            data = json.load(f)

        parent_map = {p["parent_id"]: p["text"] for p in data["parents"]}
        children = data["children"]
        if not children:
            print("  No children, skipping.")
            continue

        for i in range(0, len(children), batch_size):
            batch = children[i:i + batch_size]
            enriched_texts = []
            for child in batch:
                heading = child.get("metadata", {}).get("heading_path", "")
                ctx = child.get("context_text", "")
                text = child["text"]
                parts = [p for p in [heading, ctx, text] if p]
                enriched_texts.append("\n\n".join(parts))

            dense_vectors = encode_texts(model, EMBEDDING_MODEL, enriched_texts, is_query=False, batch_size=batch_size)

            points = []
            for j, child in enumerate(batch):
                parent_text = parent_map.get(child["parent_id"], "")
                sparse = text_to_sparse_vector(enriched_texts[j], sparse_model)
                meta = child.get("metadata", {})

                point = models.PointStruct(
                    id=int.from_bytes(hashlib.sha256(child["child_id"].encode()).digest()[:8], "big") >> 1,
                    vector={"": dense_vectors[j], "bm25": sparse},
                    payload={
                        "child_id": child["child_id"],
                        "parent_id": child["parent_id"],
                        "child_text": child["text"],
                        "context_text": child.get("context_text", ""),
                        "parent_text": parent_text,
                        "book": meta.get("book", slug),
                        "book_title": meta.get("book_title", BOOKS.get(slug, slug)),
                        "chapter": meta.get("chapter", ""),
                        "chapter_title": meta.get("chapter_title", ""),
                        "section": meta.get("section", ""),
                        "heading_path": meta.get("heading_path", ""),
                        "chunk_type": meta.get("chunk_type", "prose"),
                    },
                )
                points.append(point)

            client.upsert(collection_name=COLLECTION_NAME, points=points)
            total_indexed += len(points)
            print(f"  {min(i + batch_size, len(children))}/{len(children)}")

    client.close()
    print(f"\nDone. {total_indexed} vectors indexed in {qdrant_dir}")


if __name__ == "__main__":
    main()
