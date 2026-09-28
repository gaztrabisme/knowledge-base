# C2 report: v8 technical shelf ingest, chunk, audit

Date: 2026-09-28

## Outcome

- Ingested and chunked all 166 manifest rows marked `ingest`; no embedding, reranking, retrieval indexing, or GPU model was loaded.
- All 166 slugs have nonempty chunk files. Child and parent token caps pass for every book.
- Strict markdown audit: PASS; 16 books have low page-density flags, and every one has a concrete entry in `audit-exceptions.json`; unexcepted flags: 0.
- Regression ingest: PASS; 15/15 outputs are byte-identical to checked-in markdown.
- Sanity set: 60 JSONL rows from 60 unique new books, covering all 15 domains; every positive child ID resolves to a current chunk.

## Per-book results

PDF page counts are physical pages; reflowable EPUB sources are shown as `n/a`. Totals include 125 PDFs and sum only their physical page counts.

| Slug | Domain | Pages | Markdown chars | Headings | Parents | Children | Audit |
|---|---|---:|---:|---:|---:|---:|---|
| 3d-data-science-python | applied-ml | 690 | 1117000 | 322 | 336 | 1200 | PASS |
| apis-a-strategy-guide | architecture | 148 | 301649 | 170 | 119 | 301 | PASS |
| advanced-analytics-pyspark | data-engineering | 236 | 414350 | 116 | 103 | 439 | PASS |
| advanced-apple-debugging | reverse-engineering | 475 | 704379 | 189 | 206 | 788 | PASS |
| analytics-tools-optimizing-ux | design | 98 | 79566 | 101 | 14 | 85 | Exception: density |
| angular-up-and-running | frontend | 311 | 510800 | 923 | 491 | 758 | PASS |
| architecting-data-ml-platforms | data-engineering | n/a | 770910 | 503 | 231 | 1146 | PASS |
| arm-assembly-internals | reverse-engineering | 476 | 780506 | 267 | 315 | 1103 | PASS |
| articulating-design-decisions | design | 241 | 439113 | 65 | 87 | 398 | PASS |
| assembly-language-x86-processors | cpp | 747 | 1302944 | 466 | 502 | 1852 | PASS |
| automating-data-quality-monitoring | data-engineering | n/a | 440725 | 338 | 234 | 1369 | PASS |
| build-reasoning-model | ai-engineering | 440 | 781043 | 109 | 165 | 844 | PASS |
| build-text-to-image-generator | applied-ml | 362 | 750848 | 187 | 221 | 865 | PASS |
| building-applications-ai-agents | ai-engineering | 559 | 745081 | 223 | 196 | 722 | PASS |
| building-design-systems | design | 345 | 469550 | 596 | 440 | 652 | PASS |
| building-genai-services-fastapi | ai-engineering | 531 | 840723 | 203 | 242 | 853 | PASS |
| building-knowledge-graphs | data-engineering | n/a | 554528 | 538 | 283 | 1510 | PASS |
| building-machine-learning-pipelines | applied-ml | n/a | 701189 | 16 | 277 | 1883 | PASS |
| building-micro-frontends | frontend | 478 | 652185 | 302 | 223 | 684 | PASS |
| building-secure-reliable-systems | security | 557 | 1165148 | 392 | 411 | 1104 | PASS |
| building-event-driven-data-mesh | data-engineering | 262 | 514418 | 171 | 135 | 468 | PASS |
| css-definitive-guide | frontend | 1597 | 1853133 | 578 | 589 | 2159 | PASS |
| css-in-depth-2e | frontend | 545 | 974176 | 326 | 324 | 1184 | PASS |
| certified-ethical-hacker | security | 894 | 990535 | 164 | 224 | 1040 | PASS |
| chaos-engineering | systems-ops | n/a | 672734 | 368 | 379 | 2157 | PASS |
| cloud-native-devops-kubernetes | systems-ops | 344 | 600775 | 453 | 260 | 686 | PASS |
| cloud-native-security-cookbook | security | 516 | 746107 | 487 | 256 | 935 | PASS |
| cockroachdb-definitive-guide | databases | 487 | 756835 | 370 | 382 | 922 | PASS |
| continuous-api-management | architecture | 359 | 817814 | 189 | 202 | 698 | PASS |
| creating-web-animations | frontend | 210 | 225032 | 123 | 114 | 290 | Exception: density |
| d3js-in-action | design | 386 | 654540 | 247 | 261 | 886 | PASS |
| data-governance-definitive-guide | data-engineering | 254 | 494531 | 182 | 149 | 468 | PASS |
| data-governance-unity-catalog | data-engineering | 385 | 622749 | 177 | 166 | 582 | PASS |
| data-management-at-scale | data-engineering | 413 | 863837 | 246 | 191 | 706 | PASS |
| data-quality-fundamentals | data-engineering | 311 | 580151 | 198 | 190 | 588 | PASS |
| data-science-hard-parts | data-science | 315 | 391867 | 213 | 103 | 402 | PASS |
| data-science-for-business | data-science | 409 | 817627 | 202 | 199 | 802 | PASS |
| data-science-from-scratch | data-science | 513 | 616879 | 267 | 180 | 758 | PASS |
| database-internals | databases | 371 | 700908 | 238 | 254 | 709 | PASS |
| deciphering-data-architectures | data-engineering | n/a | 556689 | 322 | 305 | 1655 | PASS |
| delta-lake-definitive-guide | data-engineering | 383 | 701211 | 222 | 226 | 752 | PASS |
| design-for-how-people-think | design | 238 | 293682 | 135 | 137 | 324 | PASS |
| designing-autonomous-ai | ai-engineering | 248 | 372276 | 138 | 144 | 384 | PASS |
| designing-data-intensive-applications | distributed-systems | 613 | 1310180 | 197 | 284 | 1283 | PASS |
| designing-interfaces | design | 602 | 690865 | 275 | 209 | 704 | PASS |
| designing-llm-applications | ai-engineering | 367 | 623962 | 218 | 232 | 654 | PASS |
| domain-specific-small-language-models | ai-engineering | 376 | 655612 | 102 | 166 | 748 | PASS |
| effective-typescript | frontend | 569 | 671492 | 94 | 140 | 676 | PASS |
| effective-ui | design | 314 | 587464 | 136 | 150 | 540 | PASS |
| efficient-linux-command-line | systems-ops | 248 | 353826 | 162 | 159 | 464 | PASS |
| efficient-nodejs | frontend | n/a | 403764 | 289 | 247 | 1361 | PASS |
| essential-graphrag | ai-engineering | 178 | 325729 | 126 | 102 | 403 | PASS |
| essential-math-ai | applied-ml | 603 | 1191034 | 389 | 364 | 1222 | PASS |
| excel-for-accountants | data-science | 289 | 428304 | 628 | 408 | 713 | PASS |
| exploratory-data-analysis-tukey | data-science | 711 | 7445 | 204 | 34 | 34 | Exception: density |
| exploratory-data-analysis-visualization | data-science | 350 | 660515 | 167 | 193 | 839 | PASS |
| financial-data-engineering | data-engineering | 540 | 1001686 | 269 | 268 | 951 | PASS |
| fluent-react | frontend | n/a | 676705 | 289 | 382 | 2020 | PASS |
| foundations-scalable-systems | distributed-systems | 340 | 628245 | 183 | 190 | 582 | PASS |
| fundamentals-computer-graphics | cpp | 737 | 1372476 | 28 | 230 | 1506 | PASS |
| fundamentals-data-engineering | data-engineering | 544 | 906797 | 356 | 299 | 902 | PASS |
| fundamentals-metadata-management | data-engineering | 250 | 343976 | 147 | 147 | 353 | PASS |
| fundamentals-microsoft-fabric | data-engineering | 672 | 511719 | 261 | 173 | 537 | Exception: density |
| generative-deep-learning | applied-ml | 330 | 439674 | 182 | 182 | 523 | PASS |
| http-definitive-guide | frontend | 658 | 1245233 | 817 | 544 | 1543 | PASS |
| hands-on-large-language-models | ai-engineering | n/a | 706418 | 525 | 542 | 2280 | PASS |
| hands-on-rag-production | ai-engineering | 359 | 728209 | 122 | 172 | 797 | PASS |
| hands-on-selenium-webdriver | software-engineering | 422 | 603335 | 250 | 248 | 686 | PASS |
| hands-on-unsupervised-learning | applied-ml | n/a | 616863 | 500 | 262 | 1072 | PASS |
| head-first-statistics-analysis | data-science | n/a | 88745 | 136 | 94 | 112 | PASS |
| holacracy | management | n/a | 368822 | 13 | 63 | 416 | PASS |
| implementing-data-mesh | data-engineering | 515 | 401236 | 176 | 115 | 424 | Exception: density |
| infrastructure-as-code | systems-ops | 430 | 707353 | 359 | 359 | 746 | PASS |
| inside-cyber-warfare | security | 161 | 263090 | 115 | 84 | 273 | PASS |
| intelligence-driven-incident-response | security | 346 | 719270 | 236 | 259 | 672 | PASS |
| data-visualization-storytelling | design | n/a | 111624 | 180 | 32 | 133 | PASS |
| kafka-definitive-guide | data-engineering | 322 | 633816 | 244 | 192 | 610 | PASS |
| kubernetes-security-observability | security | 195 | 337738 | 150 | 109 | 316 | PASS |
| llmops | ai-engineering | 284 | 569305 | 250 | 172 | 563 | PASS |
| langchain-life-sciences-healthcare | ai-engineering | 413 | 830881 | 89 | 179 | 854 | PASS |
| laws-of-ux | design | 153 | 173615 | 75 | 49 | 172 | PASS |
| lean-ux | design | 205 | 291754 | 131 | 92 | 285 | PASS |
| learning-agile | management | 419 | 893567 | 159 | 209 | 918 | PASS |
| learning-git | software-engineering | 399 | 399099 | 123 | 105 | 463 | Exception: density |
| learning-github-actions | software-engineering | 414 | 515560 | 208 | 211 | 599 | PASS |
| learning-javascript-design-patterns | frontend | 199 | 345744 | 192 | 122 | 395 | PASS |
| learning-modern-linux | systems-ops | 261 | 399295 | 171 | 125 | 466 | PASS |
| learning-opentelemetry | systems-ops | 266 | 283250 | 135 | 95 | 252 | Exception: density |
| learning-spark | data-engineering | 274 | 465701 | 189 | 136 | 507 | PASS |
| learning-test-driven-development | software-engineering | 280 | 351952 | 184 | 180 | 436 | PASS |
| learning-threejs | frontend | 517 | 591660 | 210 | 203 | 713 | PASS |
| learning-vue | frontend | 498 | 414664 | 180 | 127 | 505 | Exception: density |
| machine-learning-production-systems | applied-ml | 985 | 844746 | 442 | 272 | 905 | Exception: density |
| machine-learning-econometrics | applied-ml | 353 | 686033 | 235 | 279 | 974 | PASS |
| making-sense-of-data | data-science | 293 | 462782 | 162 | 195 | 835 | PASS |
| microservice-architecture | architecture | 144 | 267565 | 111 | 105 | 265 | PASS |
| modern-data-analytics-excel | data-science | 244 | 253196 | 192 | 193 | 310 | Exception: density |
| monolith-to-microservices | architecture | 273 | 464185 | 218 | 143 | 460 | PASS |
| nginx-cookbook | systems-ops | n/a | 352514 | 535 | 338 | 1761 | PASS |
| natural-language-processing-transformers | ai-engineering | 409 | 702397 | 176 | 204 | 775 | PASS |
| policy-as-code | security | 1171 | 837917 | 210 | 252 | 1095 | Exception: density |
| practical-lakehouse-architecture | data-engineering | 536 | 449142 | 176 | 138 | 425 | Exception: density |
| practical-linear-algebra-data-science | applied-ml | 328 | 511385 | 233 | 150 | 544 | PASS |
| practical-web-accessibility | design | n/a | 996037 | 508 | 358 | 1289 | PASS |
| practical-reverse-engineering | reverse-engineering | 383 | 686525 | 122 | 201 | 945 | PASS |
| predictive-analytics-modern-enterprise | data-science | 361 | 545727 | 123 | 149 | 569 | PASS |
| project-management-with-ai | management | 306 | 586797 | 284 | 286 | 578 | PASS |
| rest-api-design-rulebook | architecture | 114 | 187904 | 164 | 97 | 230 | PASS |
| restful-web-apis | architecture | 404 | 738748 | 388 | 298 | 841 | PASS |
| real-world-svelte | frontend | 282 | 451048 | 187 | 142 | 512 | PASS |
| refactoring-ui | design | 252 | 100975 | 153 | 25 | 123 | Exception: density |
| reinforcement-learning-finance | applied-ml | 386 | 308977 | 78 | 87 | 390 | Exception: density |
| reverse-engineering-cybersecurity | reverse-engineering | n/a | 165839 | 15 | 24 | 145 | PASS |
| reverse-engineering-for-beginners | reverse-engineering | 943 | 1368923 | 727 | 803 | 2640 | PASS |
| sql-server-advanced-troubleshooting | databases | 500 | 863214 | 309 | 248 | 895 | PASS |
| scaling-machine-learning-with-spark | data-engineering | 294 | 555475 | 171 | 153 | 543 | PASS |
| software-supply-chain-security | security | 242 | 413609 | 176 | 138 | 398 | PASS |
| spark-definitive-guide | data-engineering | 601 | 1036988 | 650 | 654 | 1409 | PASS |
| statistics-by-simulation | data-science | 457 | 1210458 | 108 | 315 | 1638 | PASS |
| storytelling-in-design | design | n/a | 724561 | 542 | 252 | 876 | PASS |
| strategic-writing-for-ux | design | 195 | 275970 | 58 | 67 | 289 | PASS |
| strengthening-deep-neural-networks | applied-ml | 247 | 410033 | 109 | 121 | 404 | PASS |
| testing-javascript-applications | software-engineering | 514 | 1044659 | 189 | 249 | 1145 | PASS |
| llm-security-playbook | security | 380 | 386000 | 173 | 119 | 342 | Exception: density |
| enterprise-big-data-lake | data-engineering | n/a | 475406 | 300 | 271 | 1509 | PASS |
| ghidra-book | reverse-engineering | 612 | 1040315 | 350 | 341 | 1148 | PASS |
| practitioners-guide-graph-data | databases | 420 | 690696 | 240 | 211 | 705 | PASS |
| scrum-masters-path | management | n/a | 321632 | 84 | 92 | 361 | PASS |
| webgpu-sourcebook | frontend | 385 | 694268 | 98 | 156 | 800 | PASS |
| think-like-ux-researcher | design | 307 | 562460 | 58 | 107 | 545 | PASS |
| think-stats-3e | data-science | 324 | 380614 | 182 | 100 | 474 | PASS |
| training-data-for-machine-learning | applied-ml | 331 | 593488 | 311 | 216 | 598 | PASS |
| typescript-cookbook | frontend | n/a | 708133 | 533 | 277 | 1648 | PASS |
| ui-design-principles | design | 323 | 203782 | 187 | 157 | 334 | Exception: density |
| ux-for-lean-startups | design | 236 | 367623 | 16 | 64 | 326 | PASS |
| unifying-business-data-code | data-engineering | n/a | 666599 | 558 | 259 | 927 | PASS |
| user-story-mapping | management | 324 | 408609 | 168 | 111 | 416 | PASS |
| vector-databases-introduction | databases | 293 | 423327 | 9 | 78 | 403 | PASS |
| web-accessibility-cookbook | design | 381 | 501066 | 86 | 98 | 537 | PASS |
| web-performance-engineering | frontend | 256 | 498037 | 215 | 219 | 522 | PASS |
| web-performance-in-action | frontend | 378 | 758210 | 817 | 630 | 1117 | PASS |
| web-scraping-with-python | data-engineering | 306 | 542346 | 159 | 175 | 603 | PASS |
| writing-excel-macros-vba | data-science | 490 | 856629 | 974 | 239 | 1033 | PASS |
| zero-trust-networks-2e | security | 486 | 645843 | 286 | 202 | 623 | PASS |
| asynchronousprogrammingwithcplusplus | cpp | n/a | 704600 | 304 | 231 | 848 | PASS |
| bare-metalembeddedcprogramming | cpp | n/a | 645232 | 487 | 235 | 801 | PASS |
| buildinglowlatencyapplicationswithc | cpp | n/a | 981451 | 575 | 306 | 1237 | PASS |
| candalgorithmicthinkingforthecompletebeginner | cpp | n/a | 1075299 | 581 | 404 | 1456 | PASS |
| cmakebestpractices | cpp | n/a | 644722 | 296 | 251 | 773 | PASS |
| cplusplus20stlcookbook2e | cpp | n/a | 367155 | 236 | 132 | 475 | PASS |
| cplusplusmemorymanagement | cpp | n/a | 806835 | 256 | 269 | 1055 | PASS |
| cplusplusprogrammersmindset | cpp | n/a | 715826 | 262 | 239 | 875 | PASS |
| datastructuresandalgorithmswiththecplusplusstl | cpp | n/a | 754110 | 785 | 230 | 822 | PASS |
| debunkingcplusplusmyths | cpp | n/a | 431681 | 124 | 134 | 510 | PASS |
| gpuprogrammingwithcplusplusandcuda | cpp | n/a | 352255 | 159 | 133 | 416 | PASS |
| hands-ondesignpatternswithcplusplus2e | cpp | n/a | 1254947 | 345 | 371 | 1559 | PASS |
| learnllvm17secondedition | cpp | n/a | 733421 | 223 | 226 | 934 | PASS |
| llvmcodegeneration | cpp | n/a | 1273276 | 387 | 403 | 1562 | PASS |
| moderncmakeforcplusplus2e | cpp | n/a | 810803 | 452 | 298 | 942 | PASS |
| moderncplusplusprogrammingcookbook3eepub | cpp | n/a | 1414590 | 84 | 537 | 3596 | PASS |
| qt6cplusplusguiprogrammingcookbook | cpp | n/a | 512327 | 282 | 156 | 661 | PASS |
| refactoringwithcplusplus | cpp | n/a | 648936 | 405 | 209 | 735 | PASS |
| softwarearchitecturewithcplusplussecondedition | cpp | n/a | 1416813 | 682 | 494 | 1598 | PASS |
| storytelling-with-data | design | 284 | 352365 | 165 | 109 | 417 | PASS |
| templatemetaprogrammingwithc | cpp | n/a | 601173 | 153 | 166 | 745 | PASS |
| x86-software-reverse-engineering | reverse-engineering | 317 | 418303 | 395 | 214 | 528 | PASS |

**Totals:** 50,807 PDF pages across 125 PDFs; 104,335,544 Markdown characters; 44,056 headings; 36,910 parents; 134,058 children.

## Audit and density calibration

The minimum PDF density was calibrated on 44 existing books out of 126 registered books. The nearest-rank 5th percentile is 1,093 Markdown characters per physical PDF page. EPUBs are unpaginated and are not density-scored.

Initial audit, before cleanup and hard chunk caps: 165/166 books flagged. It found 5,894 child chunks over 250 tokens across 162 books, 1,373 parents over 1,900 tokens across 136 books, 11 book-end index flags, and 2 low-density flags.

After the first chunk-cap pass and before the full text cleanup, 82/166 books remained flagged: 64 index, 14 density, 3 front-matter, and 1 chapter-structure flags. Subsequent targeted cleanup/re-ingest removed the index, front-matter, and structure flags.

Final strict audit: 16/166 books flagged, all 16 listed in the exception file; 0 unexcepted flags. No heading-count, chapter-structure, garble-ratio, front-matter, trailing-index, empty-chunk, or token-cap flags remain.

### Density exceptions

The listed exceptions are limited to the calibrated text-density heuristic. Each JSON reason records source text extraction and Markdown retention evidence. In particular, the Tukey scan has no PDF text layer and would need OCR to improve.

| Slug | Reason recorded in `audit-exceptions.json` |
|---|---|
| analytics-tools-optimizing-ux | 98-page text PDF: PyMuPDF extracts 89,960 characters (918/page); Markdown retains 79,566 (88.4%). Seven pages have under 100 extracted characters, consistent with the visual, diagram-heavy layout. |
| creating-web-animations | 210-page text PDF: PyMuPDF extracts 252,177 characters (1,201/page); Markdown retains 225,032 (89.2%). Fifteen pages have under 100 extracted characters; the density miss is from sparse illustrated pages, not a missing text layer. |
| exploratory-data-analysis-tukey | Scanned 711-page PDF with no text layer: PyMuPDF extracts zero characters on all 711 pages. The 7,445-character Markdown contains only the available non-page text; OCR would require a separate reviewable source or process. |
| fundamentals-microsoft-fabric | 672-page text PDF: PyMuPDF extracts 596,351 characters (887/page); Markdown retains 511,719 (85.8%). Twenty-three pages have under 100 extracted characters, reflecting sparse diagrams and page layout. |
| implementing-data-mesh | 515-page text PDF: PyMuPDF extracts 462,140 characters (897/page); Markdown retains 401,236 (86.8%). Thirteen pages have under 100 extracted characters; the source itself falls below the calibrated density floor. |
| learning-git | 399-page text PDF: PyMuPDF extracts 416,003 characters (1,043/page); Markdown retains 399,099 (95.9%). Fourteen pages have under 100 extracted characters; nearly all available page text is present. |
| learning-opentelemetry | 266-page text PDF: PyMuPDF extracts 323,110 characters (1,215/page); Markdown retains 283,250 (87.7%). The 1,065-character Markdown density is just below the 1,093 p05 floor, with six sparse pages. |
| learning-vue | 498-page text PDF: PyMuPDF extracts 511,485 characters (1,027/page); Markdown retains 414,664 (81.1%). Nine pages have under 100 extracted characters; source density is below the calibrated floor. |
| machine-learning-production-systems | 985-page text PDF: PyMuPDF extracts 939,561 characters (954/page); Markdown retains 844,746 (89.9%). Seven pages have under 100 extracted characters; source density is below the calibrated floor. |
| modern-data-analytics-excel | 244-page text PDF: PyMuPDF extracts 307,191 characters (1,259/page); Markdown retains 253,196 (82.4%). Fourteen pages have under 100 extracted characters; remaining density loss is from tables and page layout. |
| policy-as-code | 1,171-page text PDF: PyMuPDF extracts 958,669 characters (819/page); Markdown retains 837,917 (87.4%). Nine pages have under 100 extracted characters; source density is below the calibrated floor. |
| practical-lakehouse-architecture | 536-page text PDF: PyMuPDF extracts 546,822 characters (1,020/page); Markdown retains 449,142 (82.1%). Eight pages have under 100 extracted characters; source density is below the calibrated floor. |
| refactoring-ui | 252-page highly visual text PDF: PyMuPDF extracts 102,025 characters (405/page); Markdown retains 100,975 (99.0%). Forty-six pages have under 100 extracted characters, so low density reflects the image-led layout rather than lost text. |
| reinforcement-learning-finance | 386-page text PDF: PyMuPDF extracts 339,446 characters (879/page); Markdown retains 308,977 (91.0%). Five pages have under 100 extracted characters; source density is below the calibrated floor. |
| llm-security-playbook | 380-page text PDF: PyMuPDF extracts 424,249 characters (1,116/page); Markdown retains 386,000 (91.0%). The 1,016-character Markdown density is slightly below the 1,093 p05 floor; two pages are sparse. |
| ui-design-principles | 323-page highly visual text PDF: PyMuPDF extracts 221,294 characters (685/page); Markdown retains 203,782 (92.1%). Five pages have under 100 extracted characters, consistent with the visual layout. |

## Ingest and chunk rule changes

- `_is_chapter_heading` now recognizes numeric, Roman-numeral, and written-number chapter/part labels. This restores chapter structure for lowercase word-number headings such as “chapter one” in the affected source.
- `strip_front_back_matter` considers chapter openers after front-matter headings, supports a short plain-text Chapter 1 opener and embedded H3 chapter markers, and uses a bounded early search to avoid mistaking answer keys for the opening chapter.
- `_is_front_matter_heading` now matches anchored starts and exact labels rather than broad substrings. This removes praise, copyright, dedication, about-the-author, contents, and publisher pages without dropping ordinary headings that happen to contain generic words.
- `_is_back_matter_heading` and `_is_auxiliary_index_trailer` remove a terminal alphabetical index and its publisher/copyright trailer while retaining an “Index” section followed by real chapters or one appearing early in a technical book. A late index after 65% of the source is removed when no later chapter begins.
- EPUB TOC reconstruction reads nested NCX navigation, maps linked chapter labels back to extracted text, and supports flat numbered navigation lists after stripping front matter. Flat chapter outlines become H2 structure; all-H3 chapter outlines are retained at H2 when they contain enough chapters.
- PDF ingestion promotes flat chapter bookmarks to H2 and adds a PyMuPDF typography/numbered-section fallback when bookmarks or MarkItDown’s PDF conversion are unavailable. The first pass logged four missing optional MarkItDown PDF dependency errors; those files were re-ingested through the PyMuPDF fallback and pass the final audit. Applied-ML PDFs are no longer skipped by the batch ingest loop.
- Extraction repair removes the stray backspace glyph and joins known split drop-cap opening words only for `storytelling-with-data`. Unmatched code-fence closure is enabled only for `vector-databases-introduction`.
- `chunk.py` now measures candidate merged text instead of summing estimates, and hard-splits oversized paragraphs, code lines, long tokens, and overlap-expanded parents. Exact token recounts keep all child chunks at or below 250 and parents at or below 1,900 tokens.
- `scripts/eval_retrieval.py` already exposed `--golden`; its default remains the existing golden file. Adding the repository root to `sys.path` makes the script’s CLI import work when called directly. `--help` was checked; retrieval evaluation itself was not run because no index/model work was in scope.

## Regression guard

`.venv/bin/python scripts/regression_ingest.py` completed with 15/15 byte-identical comparisons and zero differences/errors: the ten v7.1 additions recorded in the regression script plus five earlier PDF books. Each conversion wrote to a temporary directory; source Markdown was read only.

## Sanity gate

`.venv/bin/python scripts/eval_retrieval.py --help` confirms the `--golden` path option. `data/golden/sanity_v8.jsonl` contains 60 sampled, paraphrased developer questions from 60 distinct new books. The question set spans all 15 ingest domains. Positive IDs were checked against chunk JSON files; no book titles are used in the query text, and no exact five-word phrase overlaps its sampled passage.

## Exceptions

Exception file: [`data/intake/audit-exceptions.json`](audit-exceptions.json). It lists 16 density-only exceptions with per-source reasons. No exception is used to waive a missing or empty chunk file.

## Remaining work

No ingest, chunk, audit, regression, or sanity-set acceptance item remains open. OCR for the scanned Tukey PDF is outside this ingest pass; its concrete exception is documented. No embeddings or retrieval index were created.
