### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.867 / 0.680 | A1/B0=37, A0/B1=9 | — | 0.0000 | worse |
| overall | cited | 150 | 0.840 / 0.653 | A1/B0=37, A0/B1=9 | — | 0.0000 | worse |
| overall | gave_up | 150 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 9925.0 / 7942.9 | -1982.1 | [-3181.8, -700.9] | 0.0017 | better |
| overall | tool_tokens_total | 150 | 4385.1 / 2923.6 | -1461.5 | [-1951.2, -971.7] | 0.0000 | better |
| overall | max_prompt_tokens | 150 | 5595.7 / 4053.2 | -1542.5 | [-2049.1, -1026.4] | 0.0000 | better |
| overall | n_calls | 150 | 1.5 / 2.2 | +0.7 | [+0.6, +0.9] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.0 / 0.1 | +0.1 | [+0.1, +0.2] | 0.0001 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.7893 | n.s. |
| golden | found | 120 | 0.858 / 0.658 | A1/B0=32, A0/B1=8 | — | 0.0002 | worse |
| golden | cited | 120 | 0.825 / 0.625 | A1/B0=32, A0/B1=8 | — | 0.0002 | worse |
| golden | gave_up | 120 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 10352.3 / 7819.5 | -2532.8 | [-3930.4, -1087.4] | 0.0006 | better |
| golden | tool_tokens_total | 120 | 4554.4 / 2877.8 | -1676.6 | [-2224.4, -1114.6] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 5758.4 / 3999.2 | -1759.2 | [-2338.8, -1164.3] | 0.0000 | better |
| golden | n_calls | 120 | 1.6 / 2.2 | +0.6 | [+0.4, +0.8] | 0.0000 | worse |
| golden | invalid_calls | 120 | 0.0 / 0.1 | +0.1 | [+0.1, +0.2] | 0.0017 | worse |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.7893 | n.s. |
| new-books | found | 30 | 0.900 / 0.767 | A1/B0=5, A0/B1=1 | — | 0.2188 | n.s. |
| new-books | cited | 30 | 0.900 / 0.767 | A1/B0=5, A0/B1=1 | — | 0.2188 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8215.7 / 8436.4 | +220.7 | [-2158.9, +2524.1] | 0.9918 | n.s. |
| new-books | tool_tokens_total | 30 | 3708.2 / 3106.8 | -601.4 | [-1555.0, +321.1] | 0.3820 | n.s. |
| new-books | max_prompt_tokens | 30 | 4944.6 / 4269.1 | -675.5 | [-1652.3, +270.6] | 0.3441 | n.s. |
| new-books | n_calls | 30 | 1.3 / 2.5 | +1.1 | [+0.8, +1.5] | 0.0001 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.2 | +0.2 | [+0.1, +0.4] | 0.0225 | worse |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.893 / 0.840 | A1/B0=15, A0/B1=7 | — | 0.1338 | n.s. |
| overall | cited | 150 | 0.840 / 0.773 | A1/B0=21, A0/B1=11 | — | 0.1102 | n.s. |
| overall | gave_up | 150 | 0.047 / 0.107 | A1/B0=4, A0/B1=13 | — | 0.0490 | worse |
| overall | prompt_tokens_total | 150 | 20774.1 / 30772.8 | +9998.7 | [+4551.9, +15291.6] | 0.0000 | worse |
| overall | tool_tokens_total | 150 | 6509.3 / 8140.1 | +1630.7 | [+610.4, +2685.1] | 0.0002 | worse |
| overall | max_prompt_tokens | 150 | 8755.2 / 10508.1 | +1752.9 | [+681.2, +2849.5] | 0.0002 | worse |
| overall | n_calls | 150 | 3.0 / 4.0 | +1.0 | [+0.7, +1.4] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.1 / 0.2 | +0.1 | [+0.0, +0.3] | 0.0280 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.3525 | n.s. |
| golden | found | 120 | 0.875 / 0.825 | A1/B0=13, A0/B1=7 | — | 0.2632 | n.s. |
| golden | cited | 120 | 0.833 / 0.758 | A1/B0=19, A0/B1=10 | — | 0.1360 | n.s. |
| golden | gave_up | 120 | 0.058 / 0.117 | A1/B0=4, A0/B1=11 | — | 0.1185 | n.s. |
| golden | prompt_tokens_total | 120 | 22987.7 / 30985.5 | +7997.7 | [+1904.1, +14079.8] | 0.0000 | worse |
| golden | tool_tokens_total | 120 | 7041.0 / 8139.5 | +1098.5 | [-62.4, +2296.4] | 0.0235 | n.s. |
| golden | max_prompt_tokens | 120 | 9353.4 / 10539.7 | +1186.3 | [-36.3, +2458.7] | 0.0228 | n.s. |
| golden | n_calls | 120 | 3.2 / 4.1 | +0.8 | [+0.5, +1.2] | 0.0000 | worse |
| golden | invalid_calls | 120 | 0.1 / 0.2 | +0.1 | [-0.0, +0.3] | 0.1005 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.3525 | n.s. |
| new-books | found | 30 | 0.967 / 0.900 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | cited | 30 | 0.867 / 0.833 | A1/B0=2, A0/B1=1 | — | 1.0000 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.067 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| new-books | prompt_tokens_total | 30 | 11919.5 / 29922.3 | +18002.8 | [+10029.9, +28407.6] | 0.0000 | worse |
| new-books | tool_tokens_total | 30 | 4382.4 / 8142.2 | +3759.8 | [+2036.3, +5801.7] | 0.0001 | worse |
| new-books | max_prompt_tokens | 30 | 6362.6 / 10381.8 | +4019.2 | [+2261.2, +6097.3] | 0.0001 | worse |
| new-books | n_calls | 30 | 2.2 / 3.9 | +1.8 | [+1.2, +2.3] | 0.0000 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.2 | +0.2 | [+0.0, +0.3] | 0.0591 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.880 / 0.760 | A1/B0=52, A0/B1=16 | — | 0.0000 | worse |
| overall | cited | 300 | 0.840 / 0.713 | A1/B0=58, A0/B1=20 | — | 0.0000 | worse |
| overall | gave_up | 300 | 0.023 / 0.053 | A1/B0=4, A0/B1=13 | — | 0.0490 | worse |
| overall | prompt_tokens_total | 300 | 15349.5 / 19357.8 | +4008.3 | [+1172.3, +6767.5] | 0.0007 | worse |
| overall | tool_tokens_total | 300 | 5447.2 / 5531.8 | +84.6 | [-521.1, +687.7] | 0.5616 | n.s. |
| overall | max_prompt_tokens | 300 | 7175.4 / 7280.6 | +105.2 | [-525.4, +739.1] | 0.5548 | n.s. |
| overall | n_calls | 300 | 2.3 / 3.1 | +0.9 | [+0.7, +1.1] | 0.0000 | worse |
| overall | invalid_calls | 300 | 0.0 / 0.2 | +0.1 | [+0.1, +0.2] | 0.0000 | worse |
| overall | empty_results | 300 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.2845 | n.s. |
| golden | found | 240 | 0.867 / 0.742 | A1/B0=45, A0/B1=15 | — | 0.0001 | worse |
| golden | cited | 240 | 0.829 / 0.692 | A1/B0=51, A0/B1=18 | — | 0.0001 | worse |
| golden | gave_up | 240 | 0.029 / 0.058 | A1/B0=4, A0/B1=11 | — | 0.1185 | n.s. |
| golden | prompt_tokens_total | 240 | 16670.0 / 19402.5 | +2732.5 | [-520.4, +5910.8] | 0.0642 | n.s. |
| golden | tool_tokens_total | 240 | 5797.7 / 5508.7 | -289.0 | [-963.0, +393.6] | 0.0831 | n.s. |
| golden | max_prompt_tokens | 240 | 7555.9 / 7269.4 | -286.5 | [-993.0, +429.1] | 0.0709 | n.s. |
| golden | n_calls | 240 | 2.4 / 3.1 | +0.7 | [+0.5, +0.9] | 0.0000 | worse |
| golden | invalid_calls | 240 | 0.1 / 0.2 | +0.1 | [+0.1, +0.2] | 0.0019 | worse |
| golden | empty_results | 240 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.2845 | n.s. |
| new-books | found | 60 | 0.933 / 0.833 | A1/B0=7, A0/B1=1 | — | 0.0703 | n.s. |
| new-books | cited | 60 | 0.883 / 0.800 | A1/B0=7, A0/B1=2 | — | 0.1797 | n.s. |
| new-books | gave_up | 60 | 0.000 / 0.033 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| new-books | prompt_tokens_total | 60 | 10067.6 / 19179.3 | +9111.7 | [+4445.5, +14981.1] | 0.0001 | worse |
| new-books | tool_tokens_total | 60 | 4045.3 / 5624.5 | +1579.2 | [+462.0, +2822.8] | 0.0226 | worse |
| new-books | max_prompt_tokens | 60 | 5653.6 / 7325.5 | +1671.9 | [+514.9, +2932.8] | 0.0178 | worse |
| new-books | n_calls | 60 | 1.8 / 3.2 | +1.4 | [+1.1, +1.8] | 0.0000 | worse |
| new-books | invalid_calls | 60 | 0.0 / 0.2 | +0.2 | [+0.1, +0.3] | 0.0025 | worse |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A3b-vs-A1.json
