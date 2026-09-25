### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.867 / 0.700 | A1/B0=37, A0/B1=12 | — | 0.0005 | worse |
| overall | cited | 150 | 0.840 / 0.667 | A1/B0=38, A0/B1=12 | — | 0.0003 | worse |
| overall | gave_up | 150 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 9925.0 / 7124.9 | -2800.0 | [-3857.0, -1766.7] | 0.0000 | better |
| overall | tool_tokens_total | 150 | 4385.1 / 2653.5 | -1731.6 | [-2194.5, -1275.4] | 0.0000 | better |
| overall | max_prompt_tokens | 150 | 5595.7 / 3744.7 | -1851.0 | [-2331.1, -1368.6] | 0.0000 | better |
| overall | n_calls | 150 | 1.5 / 2.2 | +0.6 | [+0.5, +0.8] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.0 / 0.1 | +0.1 | [+0.1, +0.2] | 0.0001 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.6547 | n.s. |
| golden | found | 120 | 0.858 / 0.692 | A1/B0=31, A0/B1=11 | — | 0.0029 | worse |
| golden | cited | 120 | 0.825 / 0.650 | A1/B0=32, A0/B1=11 | — | 0.0019 | worse |
| golden | gave_up | 120 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 10352.3 / 6928.2 | -3424.1 | [-4632.9, -2221.3] | 0.0000 | better |
| golden | tool_tokens_total | 120 | 4554.4 / 2640.8 | -1913.5 | [-2456.6, -1366.9] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 5758.4 / 3715.7 | -2042.8 | [-2608.9, -1468.9] | 0.0000 | better |
| golden | n_calls | 120 | 1.6 / 2.1 | +0.5 | [+0.3, +0.7] | 0.0000 | worse |
| golden | invalid_calls | 120 | 0.0 / 0.1 | +0.1 | [+0.0, +0.1] | 0.0059 | worse |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.6547 | n.s. |
| new-books | found | 30 | 0.900 / 0.733 | A1/B0=6, A0/B1=1 | — | 0.1250 | n.s. |
| new-books | cited | 30 | 0.900 / 0.733 | A1/B0=6, A0/B1=1 | — | 0.1250 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8215.7 / 7911.9 | -303.9 | [-2266.0, +1535.5] | 0.5928 | n.s. |
| new-books | tool_tokens_total | 30 | 3708.2 / 2704.3 | -1003.9 | [-1853.0, -211.2] | 0.2410 | n.s. |
| new-books | max_prompt_tokens | 30 | 4944.6 / 3860.9 | -1083.7 | [-1952.5, -263.3] | 0.2096 | n.s. |
| new-books | n_calls | 30 | 1.3 / 2.5 | +1.2 | [+0.9, +1.5] | 0.0000 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.4 | +0.4 | [+0.2, +0.6] | 0.0059 | worse |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.893 / 0.673 | A1/B0=37, A0/B1=4 | — | 0.0000 | worse |
| overall | cited | 150 | 0.840 / 0.613 | A1/B0=41, A0/B1=7 | — | 0.0000 | worse |
| overall | gave_up | 150 | 0.047 / 0.053 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 20774.1 / 18746.8 | -2027.3 | [-6518.5, +2145.2] | 0.0800 | n.s. |
| overall | tool_tokens_total | 150 | 6509.3 / 5165.4 | -1343.9 | [-2317.7, -389.6] | 0.0007 | better |
| overall | max_prompt_tokens | 150 | 8755.2 / 7370.5 | -1384.8 | [-2416.0, -354.7] | 0.0011 | better |
| overall | n_calls | 150 | 3.0 / 2.6 | -0.4 | [-0.7, -0.0] | 0.0457 | better |
| overall | invalid_calls | 150 | 0.1 / 0.1 | -0.0 | [-0.1, +0.1] | 0.8424 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.5930 | n.s. |
| golden | found | 120 | 0.875 / 0.642 | A1/B0=32, A0/B1=4 | — | 0.0000 | worse |
| golden | cited | 120 | 0.833 / 0.583 | A1/B0=36, A0/B1=6 | — | 0.0000 | worse |
| golden | gave_up | 120 | 0.058 / 0.067 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 22987.7 / 20477.7 | -2510.0 | [-7810.4, +2477.7] | 0.1258 | n.s. |
| golden | tool_tokens_total | 120 | 7041.0 / 5467.2 | -1573.8 | [-2690.2, -473.1] | 0.0021 | better |
| golden | max_prompt_tokens | 120 | 9353.4 / 7713.7 | -1639.7 | [-2825.2, -457.0] | 0.0031 | better |
| golden | n_calls | 120 | 3.2 / 2.8 | -0.5 | [-0.9, -0.0] | 0.0415 | better |
| golden | invalid_calls | 120 | 0.1 / 0.1 | -0.0 | [-0.1, +0.1] | 0.6832 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.5930 | n.s. |
| new-books | found | 30 | 0.967 / 0.800 | A1/B0=5, A0/B1=0 | — | 0.0625 | n.s. |
| new-books | cited | 30 | 0.867 / 0.733 | A1/B0=5, A0/B1=1 | — | 0.2188 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 11919.5 / 11823.1 | -96.4 | [-4688.5, +5679.3] | 0.3991 | n.s. |
| new-books | tool_tokens_total | 30 | 4382.4 / 3958.1 | -424.3 | [-1939.0, +1327.0] | 0.0999 | n.s. |
| new-books | max_prompt_tokens | 30 | 6362.6 / 5997.6 | -365.0 | [-1971.3, +1509.4] | 0.1442 | n.s. |
| new-books | n_calls | 30 | 2.2 / 2.1 | -0.1 | [-0.6, +0.5] | 0.9165 | n.s. |
| new-books | invalid_calls | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.1] | 1.0000 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.880 / 0.687 | A1/B0=74, A0/B1=16 | — | 0.0000 | worse |
| overall | cited | 300 | 0.840 / 0.640 | A1/B0=79, A0/B1=19 | — | 0.0000 | worse |
| overall | gave_up | 300 | 0.023 / 0.027 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 300 | 15349.5 / 12935.8 | -2413.7 | [-4700.0, -251.0] | 0.0001 | better |
| overall | tool_tokens_total | 300 | 5447.2 / 3909.4 | -1537.8 | [-2077.1, -993.5] | 0.0000 | better |
| overall | max_prompt_tokens | 300 | 7175.4 / 5557.6 | -1617.9 | [-2183.1, -1035.4] | 0.0000 | better |
| overall | n_calls | 300 | 2.3 / 2.4 | +0.1 | [-0.1, +0.3] | 0.1136 | n.s. |
| overall | invalid_calls | 300 | 0.0 / 0.1 | +0.1 | [+0.0, +0.1] | 0.0061 | worse |
| overall | empty_results | 300 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.5896 | n.s. |
| golden | found | 240 | 0.867 / 0.667 | A1/B0=63, A0/B1=15 | — | 0.0000 | worse |
| golden | cited | 240 | 0.829 / 0.617 | A1/B0=68, A0/B1=17 | — | 0.0000 | worse |
| golden | gave_up | 240 | 0.029 / 0.033 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 240 | 16670.0 / 13702.9 | -2967.1 | [-5665.2, -412.4] | 0.0001 | better |
| golden | tool_tokens_total | 240 | 5797.7 / 4054.0 | -1743.7 | [-2362.0, -1128.0] | 0.0000 | better |
| golden | max_prompt_tokens | 240 | 7555.9 / 5714.7 | -1841.2 | [-2502.6, -1186.0] | 0.0000 | better |
| golden | n_calls | 240 | 2.4 / 2.4 | +0.0 | [-0.2, +0.3] | 0.6760 | n.s. |
| golden | invalid_calls | 240 | 0.1 / 0.1 | +0.0 | [-0.0, +0.1] | 0.1985 | n.s. |
| golden | empty_results | 240 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.5896 | n.s. |
| new-books | found | 60 | 0.933 / 0.767 | A1/B0=11, A0/B1=1 | — | 0.0063 | worse |
| new-books | cited | 60 | 0.883 / 0.733 | A1/B0=11, A0/B1=2 | — | 0.0225 | worse |
| new-books | gave_up | 60 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 60 | 10067.6 / 9867.5 | -200.1 | [-2768.7, +2841.3] | 0.6245 | n.s. |
| new-books | tool_tokens_total | 60 | 4045.3 / 3331.2 | -714.1 | [-1590.3, +241.1] | 0.0425 | n.s. |
| new-books | max_prompt_tokens | 60 | 5653.6 / 4929.2 | -724.4 | [-1652.5, +292.0] | 0.0506 | n.s. |
| new-books | n_calls | 60 | 1.8 / 2.3 | +0.6 | [+0.2, +0.9] | 0.0027 | worse |
| new-books | invalid_calls | 60 | 0.0 / 0.2 | +0.2 | [+0.1, +0.3] | 0.0039 | worse |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A3hb-vs-A1.json
