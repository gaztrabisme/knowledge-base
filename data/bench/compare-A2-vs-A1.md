### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.867 / 0.580 | A1/B0=52, A0/B1=9 | — | 0.0000 | worse |
| overall | cited | 150 | 0.840 / 0.553 | A1/B0=53, A0/B1=10 | — | 0.0000 | worse |
| overall | gave_up | 150 | 0.000 / 0.007 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 9925.0 / 7712.8 | -2212.2 | [-3250.2, -1169.7] | 0.0001 | better |
| overall | tool_tokens_total | 150 | 4385.1 / 2393.1 | -1992.0 | [-2429.8, -1559.4] | 0.0000 | better |
| overall | max_prompt_tokens | 150 | 5595.7 / 3913.9 | -1681.7 | [-2124.0, -1245.0] | 0.0000 | better |
| overall | n_calls | 150 | 1.5 / 1.9 | +0.4 | [+0.3, +0.6] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.4652 | n.s. |
| golden | found | 120 | 0.858 / 0.583 | A1/B0=41, A0/B1=8 | — | 0.0000 | worse |
| golden | cited | 120 | 0.825 / 0.550 | A1/B0=42, A0/B1=9 | — | 0.0000 | worse |
| golden | gave_up | 120 | 0.000 / 0.008 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 10352.3 / 7587.1 | -2765.2 | [-3959.6, -1570.2] | 0.0000 | better |
| golden | tool_tokens_total | 120 | 4554.4 / 2313.5 | -2240.8 | [-2733.3, -1748.5] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 5758.4 / 3812.0 | -1946.4 | [-2442.5, -1446.3] | 0.0000 | better |
| golden | n_calls | 120 | 1.6 / 1.9 | +0.4 | [+0.2, +0.5] | 0.0005 | worse |
| golden | invalid_calls | 120 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.4652 | n.s. |
| new-books | found | 30 | 0.900 / 0.567 | A1/B0=11, A0/B1=1 | — | 0.0063 | worse |
| new-books | cited | 30 | 0.900 / 0.567 | A1/B0=11, A0/B1=1 | — | 0.0063 | worse |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8215.7 / 8215.2 | -0.5 | [-1976.2, +1897.9] | 0.5237 | n.s. |
| new-books | tool_tokens_total | 30 | 3708.2 / 2711.6 | -996.6 | [-1883.6, -159.0] | 0.1872 | n.s. |
| new-books | max_prompt_tokens | 30 | 4944.6 / 4321.6 | -623.0 | [-1533.8, +237.9] | 0.3441 | n.s. |
| new-books | n_calls | 30 | 1.3 / 2.0 | +0.6 | [+0.4, +0.8] | 0.0002 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.893 / 0.867 | A1/B0=10, A0/B1=6 | — | 0.4545 | n.s. |
| overall | cited | 150 | 0.840 / 0.787 | A1/B0=17, A0/B1=9 | — | 0.1686 | n.s. |
| overall | gave_up | 150 | 0.047 / 0.133 | A1/B0=4, A0/B1=17 | — | 0.0072 | worse |
| overall | prompt_tokens_total | 150 | 20774.1 / 28266.1 | +7492.0 | [+2762.7, +11694.4] | 0.0000 | worse |
| overall | tool_tokens_total | 150 | 6509.3 / 6862.0 | +352.7 | [-551.4, +1211.2] | 0.0277 | n.s. |
| overall | max_prompt_tokens | 150 | 8755.2 / 9545.1 | +789.9 | [-163.6, +1696.0] | 0.0004 | n.s. |
| overall | n_calls | 150 | 3.0 / 4.2 | +1.2 | [+0.8, +1.5] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.1 / 0.6 | +0.5 | [+0.3, +0.7] | 0.0000 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.5896 | n.s. |
| golden | found | 120 | 0.875 / 0.858 | A1/B0=8, A0/B1=6 | — | 0.7905 | n.s. |
| golden | cited | 120 | 0.833 / 0.783 | A1/B0=14, A0/B1=8 | — | 0.2863 | n.s. |
| golden | gave_up | 120 | 0.058 / 0.142 | A1/B0=4, A0/B1=14 | — | 0.0309 | worse |
| golden | prompt_tokens_total | 120 | 22987.7 / 29634.6 | +6646.9 | [+885.3, +11783.7] | 0.0000 | worse |
| golden | tool_tokens_total | 120 | 7041.0 / 7070.3 | +29.2 | [-1037.9, +1014.9] | 0.1786 | n.s. |
| golden | max_prompt_tokens | 120 | 9353.4 / 9799.5 | +446.2 | [-666.0, +1485.4] | 0.0120 | n.s. |
| golden | n_calls | 120 | 3.2 / 4.2 | +1.0 | [+0.6, +1.4] | 0.0000 | worse |
| golden | invalid_calls | 120 | 0.1 / 0.6 | +0.5 | [+0.3, +0.6] | 0.0000 | worse |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.5896 | n.s. |
| new-books | found | 30 | 0.967 / 0.900 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | cited | 30 | 0.867 / 0.800 | A1/B0=3, A0/B1=1 | — | 0.6250 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.100 | A1/B0=0, A0/B1=3 | — | 0.2500 | n.s. |
| new-books | prompt_tokens_total | 30 | 11919.5 / 22792.1 | +10872.6 | [+6190.4, +15875.5] | 0.0001 | worse |
| new-books | tool_tokens_total | 30 | 4382.4 / 6029.1 | +1646.7 | [+76.4, +3387.9] | 0.0135 | worse |
| new-books | max_prompt_tokens | 30 | 6362.6 / 8527.3 | +2164.7 | [+497.1, +3956.6] | 0.0020 | worse |
| new-books | n_calls | 30 | 2.2 / 4.0 | +1.8 | [+1.1, +2.6] | 0.0002 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.7 | +0.7 | [+0.3, +1.2] | 0.0059 | worse |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.880 / 0.723 | A1/B0=62, A0/B1=15 | — | 0.0000 | worse |
| overall | cited | 300 | 0.840 / 0.670 | A1/B0=70, A0/B1=19 | — | 0.0000 | worse |
| overall | gave_up | 300 | 0.023 / 0.070 | A1/B0=4, A0/B1=18 | — | 0.0043 | worse |
| overall | prompt_tokens_total | 300 | 15349.5 / 17989.4 | +2639.9 | [+155.7, +4886.6] | 0.0259 | worse |
| overall | tool_tokens_total | 300 | 5447.2 / 4627.6 | -819.6 | [-1342.6, -315.1] | 0.0035 | better |
| overall | max_prompt_tokens | 300 | 7175.4 / 6729.5 | -445.9 | [-992.1, +80.5] | 0.3283 | n.s. |
| overall | n_calls | 300 | 2.3 / 3.0 | +0.8 | [+0.6, +1.0] | 0.0000 | worse |
| overall | invalid_calls | 300 | 0.0 / 0.3 | +0.3 | [+0.2, +0.3] | 0.0000 | worse |
| overall | empty_results | 300 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.3139 | n.s. |
| golden | found | 240 | 0.867 / 0.721 | A1/B0=49, A0/B1=14 | — | 0.0000 | worse |
| golden | cited | 240 | 0.829 / 0.667 | A1/B0=56, A0/B1=17 | — | 0.0000 | worse |
| golden | gave_up | 240 | 0.029 / 0.075 | A1/B0=4, A0/B1=15 | — | 0.0192 | worse |
| golden | prompt_tokens_total | 240 | 16670.0 / 18610.9 | +1940.8 | [-1103.8, +4676.5] | 0.3149 | n.s. |
| golden | tool_tokens_total | 240 | 5797.7 / 4691.9 | -1105.8 | [-1703.5, -538.1] | 0.0004 | better |
| golden | max_prompt_tokens | 240 | 7555.9 / 6805.8 | -750.1 | [-1381.6, -155.2] | 0.0656 | n.s. |
| golden | n_calls | 240 | 2.4 / 3.1 | +0.7 | [+0.5, +0.9] | 0.0000 | worse |
| golden | invalid_calls | 240 | 0.1 / 0.3 | +0.2 | [+0.1, +0.3] | 0.0000 | worse |
| golden | empty_results | 240 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.3139 | n.s. |
| new-books | found | 60 | 0.933 / 0.733 | A1/B0=13, A0/B1=1 | — | 0.0018 | worse |
| new-books | cited | 60 | 0.883 / 0.683 | A1/B0=14, A0/B1=2 | — | 0.0042 | worse |
| new-books | gave_up | 60 | 0.000 / 0.050 | A1/B0=0, A0/B1=3 | — | 0.2500 | n.s. |
| new-books | prompt_tokens_total | 60 | 10067.6 / 15503.6 | +5436.1 | [+2598.4, +8584.1] | 0.0017 | worse |
| new-books | tool_tokens_total | 60 | 4045.3 / 4370.4 | +325.1 | [-617.6, +1343.6] | 0.3997 | n.s. |
| new-books | max_prompt_tokens | 60 | 5653.6 / 6424.5 | +770.9 | [-214.9, +1829.3] | 0.0856 | n.s. |
| new-books | n_calls | 60 | 1.8 / 3.0 | +1.2 | [+0.8, +1.6] | 0.0000 | worse |
| new-books | invalid_calls | 60 | 0.0 / 0.3 | +0.3 | [+0.1, +0.6] | 0.0059 | worse |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A2-vs-A1.json
