### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.867 / 0.680 | A1/B0=39, A0/B1=11 | — | 0.0001 | worse |
| overall | cited | 150 | 0.840 / 0.653 | A1/B0=40, A0/B1=12 | — | 0.0001 | worse |
| overall | gave_up | 150 | 0.000 / 0.013 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| overall | prompt_tokens_total | 150 | 9925.0 / 7871.5 | -2053.5 | [-3248.1, -860.9] | 0.0011 | better |
| overall | tool_tokens_total | 150 | 4385.1 / 3395.3 | -989.8 | [-1532.0, -441.8] | 0.0001 | better |
| overall | max_prompt_tokens | 150 | 5595.7 / 4353.9 | -1241.7 | [-1813.8, -656.6] | 0.0000 | better |
| overall | n_calls | 150 | 1.5 / 2.3 | +0.8 | [+0.6, +1.0] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.0 / 0.3 | +0.3 | [+0.2, +0.4] | 0.0000 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 120 | 0.858 / 0.683 | A1/B0=30, A0/B1=9 | — | 0.0011 | worse |
| golden | cited | 120 | 0.825 / 0.658 | A1/B0=30, A0/B1=10 | — | 0.0022 | worse |
| golden | gave_up | 120 | 0.000 / 0.017 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| golden | prompt_tokens_total | 120 | 10352.3 / 7465.6 | -2886.7 | [-4183.0, -1553.1] | 0.0001 | better |
| golden | tool_tokens_total | 120 | 4554.4 / 3082.6 | -1471.8 | [-2001.6, -927.7] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 5758.4 / 3997.0 | -1761.4 | [-2316.8, -1185.6] | 0.0000 | better |
| golden | n_calls | 120 | 1.6 / 2.3 | +0.7 | [+0.5, +1.0] | 0.0000 | worse |
| golden | invalid_calls | 120 | 0.0 / 0.2 | +0.2 | [+0.1, +0.3] | 0.0001 | worse |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 1.0000 | n.s. |
| new-books | found | 30 | 0.900 / 0.667 | A1/B0=9, A0/B1=2 | — | 0.0654 | n.s. |
| new-books | cited | 30 | 0.900 / 0.633 | A1/B0=10, A0/B1=2 | — | 0.0386 | worse |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8215.7 / 9495.0 | +1279.3 | [-1249.3, +3811.4] | 0.4716 | n.s. |
| new-books | tool_tokens_total | 30 | 3708.2 / 4646.1 | +937.9 | [-496.7, +2470.9] | 0.4345 | n.s. |
| new-books | max_prompt_tokens | 30 | 4944.6 / 5781.7 | +837.1 | [-709.6, +2507.8] | 0.4590 | n.s. |
| new-books | n_calls | 30 | 1.3 / 2.5 | +1.2 | [+0.8, +1.5] | 0.0000 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.4 | +0.4 | [+0.2, +0.7] | 0.0092 | worse |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.893 / 0.807 | A1/B0=19, A0/B1=6 | — | 0.0146 | worse |
| overall | cited | 150 | 0.840 / 0.753 | A1/B0=23, A0/B1=10 | — | 0.0351 | worse |
| overall | gave_up | 150 | 0.047 / 0.120 | A1/B0=4, A0/B1=15 | — | 0.0192 | worse |
| overall | prompt_tokens_total | 150 | 20774.1 / 26263.3 | +5489.2 | [+1266.6, +9367.0] | 0.0002 | worse |
| overall | tool_tokens_total | 150 | 6509.3 / 7290.2 | +780.9 | [-96.1, +1670.2] | 0.0506 | n.s. |
| overall | max_prompt_tokens | 150 | 8755.2 / 9409.8 | +654.6 | [-271.4, +1595.9] | 0.1702 | n.s. |
| overall | n_calls | 150 | 3.0 / 3.7 | +0.7 | [+0.3, +1.0] | 0.0004 | worse |
| overall | invalid_calls | 150 | 0.1 / 0.3 | +0.2 | [+0.1, +0.4] | 0.0002 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.3711 | n.s. |
| golden | found | 120 | 0.875 / 0.800 | A1/B0=14, A0/B1=5 | — | 0.0636 | n.s. |
| golden | cited | 120 | 0.833 / 0.750 | A1/B0=18, A0/B1=8 | — | 0.0755 | n.s. |
| golden | gave_up | 120 | 0.058 / 0.108 | A1/B0=4, A0/B1=10 | — | 0.1796 | n.s. |
| golden | prompt_tokens_total | 120 | 22987.7 / 26142.7 | +3155.0 | [-1508.6, +7488.5] | 0.0175 | n.s. |
| golden | tool_tokens_total | 120 | 7041.0 / 7380.5 | +339.4 | [-614.9, +1276.9] | 0.3399 | n.s. |
| golden | max_prompt_tokens | 120 | 9353.4 / 9548.3 | +195.0 | [-822.5, +1216.5] | 0.6877 | n.s. |
| golden | n_calls | 120 | 3.2 / 3.6 | +0.4 | [+0.1, +0.8] | 0.0310 | worse |
| golden | invalid_calls | 120 | 0.1 / 0.3 | +0.2 | [+0.1, +0.3] | 0.0085 | worse |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.3711 | n.s. |
| new-books | found | 30 | 0.967 / 0.833 | A1/B0=5, A0/B1=1 | — | 0.2188 | n.s. |
| new-books | cited | 30 | 0.867 / 0.767 | A1/B0=5, A0/B1=2 | — | 0.4531 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.167 | A1/B0=0, A0/B1=5 | — | 0.0625 | n.s. |
| new-books | prompt_tokens_total | 30 | 11919.5 / 26745.6 | +14826.2 | [+7661.1, +22584.9] | 0.0007 | worse |
| new-books | tool_tokens_total | 30 | 4382.4 / 6929.0 | +2546.6 | [+738.0, +4927.4] | 0.0108 | worse |
| new-books | max_prompt_tokens | 30 | 6362.6 / 8855.7 | +2493.1 | [+620.8, +4915.0] | 0.0144 | worse |
| new-books | n_calls | 30 | 2.2 / 3.9 | +1.7 | [+0.9, +2.5] | 0.0007 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.5 | +0.5 | [+0.2, +0.8] | 0.0059 | worse |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.880 / 0.743 | A1/B0=58, A0/B1=17 | — | 0.0000 | worse |
| overall | cited | 300 | 0.840 / 0.703 | A1/B0=63, A0/B1=22 | — | 0.0000 | worse |
| overall | gave_up | 300 | 0.023 / 0.067 | A1/B0=4, A0/B1=17 | — | 0.0072 | worse |
| overall | prompt_tokens_total | 300 | 15349.5 / 17067.4 | +1717.9 | [-477.8, +3796.9] | 0.2948 | n.s. |
| overall | tool_tokens_total | 300 | 5447.2 / 5342.7 | -104.5 | [-628.8, +435.2] | 0.2281 | n.s. |
| overall | max_prompt_tokens | 300 | 7175.4 / 6881.9 | -293.6 | [-849.9, +278.9] | 0.0412 | n.s. |
| overall | n_calls | 300 | 2.3 / 3.0 | +0.7 | [+0.6, +0.9] | 0.0000 | worse |
| overall | invalid_calls | 300 | 0.0 / 0.3 | +0.2 | [+0.2, +0.3] | 0.0000 | worse |
| overall | empty_results | 300 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.1814 | n.s. |
| golden | found | 240 | 0.867 / 0.742 | A1/B0=44, A0/B1=14 | — | 0.0001 | worse |
| golden | cited | 240 | 0.829 / 0.704 | A1/B0=48, A0/B1=18 | — | 0.0003 | worse |
| golden | gave_up | 240 | 0.029 / 0.062 | A1/B0=4, A0/B1=12 | — | 0.0768 | n.s. |
| golden | prompt_tokens_total | 240 | 16670.0 / 16804.2 | +134.2 | [-2295.8, +2487.5] | 0.6085 | n.s. |
| golden | tool_tokens_total | 240 | 5797.7 / 5231.5 | -566.2 | [-1131.3, -18.7] | 0.0098 | better |
| golden | max_prompt_tokens | 240 | 7555.9 / 6772.7 | -783.2 | [-1384.8, -193.2] | 0.0007 | better |
| golden | n_calls | 240 | 2.4 / 3.0 | +0.6 | [+0.4, +0.8] | 0.0000 | worse |
| golden | invalid_calls | 240 | 0.1 / 0.3 | +0.2 | [+0.1, +0.3] | 0.0000 | worse |
| golden | empty_results | 240 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.1814 | n.s. |
| new-books | found | 60 | 0.933 / 0.750 | A1/B0=14, A0/B1=3 | — | 0.0127 | worse |
| new-books | cited | 60 | 0.883 / 0.700 | A1/B0=15, A0/B1=4 | — | 0.0192 | worse |
| new-books | gave_up | 60 | 0.000 / 0.083 | A1/B0=0, A0/B1=5 | — | 0.0625 | n.s. |
| new-books | prompt_tokens_total | 60 | 10067.6 / 18120.3 | +8052.7 | [+4072.7, +12576.1] | 0.0007 | worse |
| new-books | tool_tokens_total | 60 | 4045.3 / 5787.6 | +1742.2 | [+565.6, +3148.9] | 0.0124 | worse |
| new-books | max_prompt_tokens | 60 | 5653.6 / 7318.7 | +1665.1 | [+420.5, +3126.6] | 0.0223 | worse |
| new-books | n_calls | 60 | 1.8 / 3.2 | +1.4 | [+1.0, +1.9] | 0.0000 | worse |
| new-books | invalid_calls | 60 | 0.0 / 0.4 | +0.4 | [+0.2, +0.6] | 0.0001 | worse |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A4b-vs-A1.json
