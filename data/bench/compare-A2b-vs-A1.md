### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.867 / 0.667 | A1/B0=40, A0/B1=10 | — | 0.0000 | worse |
| overall | cited | 150 | 0.840 / 0.660 | A1/B0=37, A0/B1=10 | — | 0.0001 | worse |
| overall | gave_up | 150 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 9925.0 / 8117.8 | -1807.2 | [-2875.2, -748.5] | 0.0001 | better |
| overall | tool_tokens_total | 150 | 4385.1 / 2478.8 | -1906.3 | [-2335.8, -1484.0] | 0.0000 | better |
| overall | max_prompt_tokens | 150 | 5595.7 / 4019.4 | -1576.3 | [-2019.2, -1148.3] | 0.0000 | better |
| overall | n_calls | 150 | 1.5 / 2.0 | +0.5 | [+0.4, +0.6] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 0.3711 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.3613 | n.s. |
| golden | found | 120 | 0.858 / 0.658 | A1/B0=32, A0/B1=8 | — | 0.0002 | worse |
| golden | cited | 120 | 0.825 / 0.650 | A1/B0=29, A0/B1=8 | — | 0.0008 | worse |
| golden | gave_up | 120 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 10352.3 / 7972.6 | -2379.7 | [-3592.6, -1141.1] | 0.0000 | better |
| golden | tool_tokens_total | 120 | 4554.4 / 2400.0 | -2154.3 | [-2635.8, -1667.4] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 5758.4 / 3924.6 | -1833.9 | [-2322.8, -1338.8] | 0.0000 | better |
| golden | n_calls | 120 | 1.6 / 2.0 | +0.4 | [+0.3, +0.6] | 0.0000 | worse |
| golden | invalid_calls | 120 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 0.3711 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.3613 | n.s. |
| new-books | found | 30 | 0.900 / 0.700 | A1/B0=8, A0/B1=2 | — | 0.1094 | n.s. |
| new-books | cited | 30 | 0.900 / 0.700 | A1/B0=8, A0/B1=2 | — | 0.1094 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8215.7 / 8698.5 | +482.8 | [-1461.9, +2339.5] | 0.9672 | n.s. |
| new-books | tool_tokens_total | 30 | 3708.2 / 2794.0 | -914.2 | [-1808.7, -65.5] | 0.2848 | n.s. |
| new-books | max_prompt_tokens | 30 | 4944.6 / 4398.7 | -545.9 | [-1466.4, +331.3] | 0.5237 | n.s. |
| new-books | n_calls | 30 | 1.3 / 2.1 | +0.8 | [+0.6, +1.0] | 0.0001 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.893 / 0.840 | A1/B0=13, A0/B1=5 | — | 0.0963 | n.s. |
| overall | cited | 150 | 0.840 / 0.780 | A1/B0=16, A0/B1=7 | — | 0.0931 | n.s. |
| overall | gave_up | 150 | 0.047 / 0.067 | A1/B0=6, A0/B1=9 | — | 0.6072 | n.s. |
| overall | prompt_tokens_total | 150 | 20774.1 / 24854.8 | +4080.7 | [-330.7, +7929.9] | 0.0001 | n.s. |
| overall | tool_tokens_total | 150 | 6509.3 / 6406.7 | -102.6 | [-929.8, +666.5] | 0.5839 | n.s. |
| overall | max_prompt_tokens | 150 | 8755.2 / 9092.3 | +337.1 | [-526.2, +1137.5] | 0.0284 | n.s. |
| overall | n_calls | 150 | 3.0 / 3.5 | +0.5 | [+0.2, +0.8] | 0.0024 | worse |
| overall | invalid_calls | 150 | 0.1 / 0.1 | +0.0 | [-0.0, +0.1] | 0.3684 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.7893 | n.s. |
| golden | found | 120 | 0.875 / 0.833 | A1/B0=10, A0/B1=5 | — | 0.3018 | n.s. |
| golden | cited | 120 | 0.833 / 0.767 | A1/B0=14, A0/B1=6 | — | 0.1153 | n.s. |
| golden | gave_up | 120 | 0.058 / 0.075 | A1/B0=6, A0/B1=8 | — | 0.7905 | n.s. |
| golden | prompt_tokens_total | 120 | 22987.7 / 26178.0 | +3190.3 | [-2032.9, +7751.8] | 0.0051 | n.s. |
| golden | tool_tokens_total | 120 | 7041.0 / 6657.6 | -383.4 | [-1375.8, +523.3] | 0.9027 | n.s. |
| golden | max_prompt_tokens | 120 | 9353.4 / 9382.0 | +28.7 | [-994.9, +974.1] | 0.2471 | n.s. |
| golden | n_calls | 120 | 3.2 / 3.6 | +0.4 | [+0.1, +0.8] | 0.0208 | worse |
| golden | invalid_calls | 120 | 0.1 / 0.1 | +0.0 | [-0.1, +0.1] | 0.6909 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.7893 | n.s. |
| new-books | found | 30 | 0.967 / 0.867 | A1/B0=3, A0/B1=0 | — | 0.2500 | n.s. |
| new-books | cited | 30 | 0.867 / 0.833 | A1/B0=2, A0/B1=1 | — | 1.0000 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.033 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 11919.5 / 19561.9 | +7642.5 | [+2942.4, +13722.4] | 0.0016 | worse |
| new-books | tool_tokens_total | 30 | 4382.4 / 5403.4 | +1021.0 | [+18.2, +2136.2] | 0.1003 | n.s. |
| new-books | max_prompt_tokens | 30 | 6362.6 / 7933.5 | +1570.9 | [+533.7, +2702.3] | 0.0058 | worse |
| new-books | n_calls | 30 | 2.2 / 2.9 | +0.7 | [+0.2, +1.3] | 0.0217 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.1 | +0.1 | [+0.0, +0.3] | 0.3711 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.880 / 0.753 | A1/B0=53, A0/B1=15 | — | 0.0000 | worse |
| overall | cited | 300 | 0.840 / 0.720 | A1/B0=53, A0/B1=17 | — | 0.0000 | worse |
| overall | gave_up | 300 | 0.023 / 0.033 | A1/B0=6, A0/B1=9 | — | 0.6072 | n.s. |
| overall | prompt_tokens_total | 300 | 15349.5 / 16486.3 | +1136.8 | [-1101.2, +3223.9] | 0.3704 | n.s. |
| overall | tool_tokens_total | 300 | 5447.2 / 4442.8 | -1004.4 | [-1488.2, -558.9] | 0.0000 | better |
| overall | max_prompt_tokens | 300 | 7175.4 / 6555.9 | -619.6 | [-1117.9, -154.5] | 0.0349 | better |
| overall | n_calls | 300 | 2.3 / 2.8 | +0.5 | [+0.3, +0.7] | 0.0000 | worse |
| overall | invalid_calls | 300 | 0.0 / 0.1 | +0.0 | [-0.0, +0.1] | 0.2197 | n.s. |
| overall | empty_results | 300 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.6121 | n.s. |
| golden | found | 240 | 0.867 / 0.746 | A1/B0=42, A0/B1=13 | — | 0.0001 | worse |
| golden | cited | 240 | 0.829 / 0.708 | A1/B0=43, A0/B1=14 | — | 0.0002 | worse |
| golden | gave_up | 240 | 0.029 / 0.037 | A1/B0=6, A0/B1=8 | — | 0.7905 | n.s. |
| golden | prompt_tokens_total | 240 | 16670.0 / 17075.3 | +405.3 | [-2310.5, +2808.1] | 0.9493 | n.s. |
| golden | tool_tokens_total | 240 | 5797.7 / 4528.8 | -1268.9 | [-1825.9, -746.1] | 0.0000 | better |
| golden | max_prompt_tokens | 240 | 7555.9 / 6653.3 | -902.6 | [-1479.6, -357.4] | 0.0030 | better |
| golden | n_calls | 240 | 2.4 / 2.8 | +0.4 | [+0.2, +0.6] | 0.0000 | worse |
| golden | invalid_calls | 240 | 0.1 / 0.1 | +0.0 | [-0.0, +0.1] | 0.4348 | n.s. |
| golden | empty_results | 240 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.6121 | n.s. |
| new-books | found | 60 | 0.933 / 0.783 | A1/B0=11, A0/B1=2 | — | 0.0225 | worse |
| new-books | cited | 60 | 0.883 / 0.767 | A1/B0=10, A0/B1=3 | — | 0.0923 | n.s. |
| new-books | gave_up | 60 | 0.000 / 0.017 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 60 | 10067.6 / 14130.2 | +4062.6 | [+1341.7, +7461.4] | 0.0153 | worse |
| new-books | tool_tokens_total | 60 | 4045.3 / 4098.7 | +53.4 | [-681.2, +808.7] | 0.6975 | n.s. |
| new-books | max_prompt_tokens | 60 | 5653.6 / 6166.1 | +512.5 | [-246.1, +1290.2] | 0.1322 | n.s. |
| new-books | n_calls | 60 | 1.8 / 2.5 | +0.8 | [+0.5, +1.1] | 0.0000 | worse |
| new-books | invalid_calls | 60 | 0.0 / 0.1 | +0.1 | [+0.0, +0.1] | 0.3711 | n.s. |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A2b-vs-A1.json
