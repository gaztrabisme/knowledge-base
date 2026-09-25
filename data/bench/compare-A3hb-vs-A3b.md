### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.680 / 0.700 | A1/B0=7, A0/B1=10 | — | 0.6291 | n.s. |
| overall | cited | 150 | 0.653 / 0.667 | A1/B0=9, A0/B1=11 | — | 0.8238 | n.s. |
| overall | gave_up | 150 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 7942.9 / 7124.9 | -817.9 | [-1720.2, -97.8] | 0.1163 | n.s. |
| overall | tool_tokens_total | 150 | 2923.6 / 2653.5 | -270.1 | [-544.9, -30.9] | 0.2610 | n.s. |
| overall | max_prompt_tokens | 150 | 4053.2 / 3744.7 | -308.5 | [-602.7, -58.3] | 0.1243 | n.s. |
| overall | n_calls | 150 | 2.2 / 2.2 | -0.1 | [-0.2, +0.1] | 0.3881 | n.s. |
| overall | invalid_calls | 150 | 0.1 / 0.1 | +0.0 | [-0.1, +0.1] | 1.0000 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 120 | 0.658 / 0.692 | A1/B0=5, A0/B1=9 | — | 0.4240 | n.s. |
| golden | cited | 120 | 0.625 / 0.650 | A1/B0=7, A0/B1=10 | — | 0.6291 | n.s. |
| golden | gave_up | 120 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 7819.5 / 6928.2 | -891.3 | [-1984.0, -12.4] | 0.1808 | n.s. |
| golden | tool_tokens_total | 120 | 2877.8 / 2640.8 | -237.0 | [-569.3, +54.1] | 0.6730 | n.s. |
| golden | max_prompt_tokens | 120 | 3999.2 / 3715.7 | -283.5 | [-641.9, +20.8] | 0.4594 | n.s. |
| golden | n_calls | 120 | 2.2 / 2.1 | -0.1 | [-0.2, +0.1] | 0.2348 | n.s. |
| golden | invalid_calls | 120 | 0.1 / 0.1 | -0.0 | [-0.1, +0.0] | 0.3133 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 1.0000 | n.s. |
| new-books | found | 30 | 0.767 / 0.733 | A1/B0=2, A0/B1=1 | — | 1.0000 | n.s. |
| new-books | cited | 30 | 0.767 / 0.733 | A1/B0=2, A0/B1=1 | — | 1.0000 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8436.4 / 7911.9 | -524.5 | [-1511.6, +424.7] | 0.4048 | n.s. |
| new-books | tool_tokens_total | 30 | 3106.8 / 2704.3 | -402.5 | [-719.2, -122.6] | 0.0776 | n.s. |
| new-books | max_prompt_tokens | 30 | 4269.1 / 3860.9 | -408.2 | [-727.5, -129.0] | 0.0316 | better |
| new-books | n_calls | 30 | 2.5 / 2.5 | +0.0 | [-0.3, +0.3] | 0.7837 | n.s. |
| new-books | invalid_calls | 30 | 0.2 / 0.4 | +0.2 | [-0.0, +0.4] | 0.2049 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.840 / 0.673 | A1/B0=35, A0/B1=10 | — | 0.0002 | worse |
| overall | cited | 150 | 0.773 / 0.613 | A1/B0=38, A0/B1=14 | — | 0.0012 | worse |
| overall | gave_up | 150 | 0.107 / 0.053 | A1/B0=11, A0/B1=3 | — | 0.0574 | n.s. |
| overall | prompt_tokens_total | 150 | 30772.8 / 18746.8 | -12026.1 | [-16821.3, -7505.6] | 0.0000 | better |
| overall | tool_tokens_total | 150 | 8140.1 / 5165.4 | -2974.7 | [-4005.3, -1986.0] | 0.0000 | better |
| overall | max_prompt_tokens | 150 | 10508.1 / 7370.5 | -3137.7 | [-4254.4, -2049.8] | 0.0000 | better |
| overall | n_calls | 150 | 4.0 / 2.6 | -1.4 | [-1.8, -1.0] | 0.0000 | better |
| overall | invalid_calls | 150 | 0.2 / 0.1 | -0.2 | [-0.3, -0.1] | 0.0086 | better |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.8339 | n.s. |
| golden | found | 120 | 0.825 / 0.642 | A1/B0=30, A0/B1=8 | — | 0.0005 | worse |
| golden | cited | 120 | 0.758 / 0.583 | A1/B0=33, A0/B1=12 | — | 0.0025 | worse |
| golden | gave_up | 120 | 0.117 / 0.067 | A1/B0=9, A0/B1=3 | — | 0.1460 | n.s. |
| golden | prompt_tokens_total | 120 | 30985.5 / 20477.7 | -10507.8 | [-15905.1, -5614.7] | 0.0000 | better |
| golden | tool_tokens_total | 120 | 8139.5 / 5467.2 | -2672.3 | [-3798.7, -1555.1] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 10539.7 / 7713.7 | -2826.0 | [-4064.5, -1597.9] | 0.0000 | better |
| golden | n_calls | 120 | 4.1 / 2.8 | -1.3 | [-1.7, -0.9] | 0.0000 | better |
| golden | invalid_calls | 120 | 0.2 / 0.1 | -0.2 | [-0.3, -0.0] | 0.0235 | better |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [-0.1, +0.1] | 0.8339 | n.s. |
| new-books | found | 30 | 0.900 / 0.800 | A1/B0=5, A0/B1=2 | — | 0.4531 | n.s. |
| new-books | cited | 30 | 0.833 / 0.733 | A1/B0=5, A0/B1=2 | — | 0.4531 | n.s. |
| new-books | gave_up | 30 | 0.067 / 0.000 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | prompt_tokens_total | 30 | 29922.3 / 11823.1 | -18099.2 | [-29754.7, -8671.1] | 0.0001 | better |
| new-books | tool_tokens_total | 30 | 8142.2 / 3958.1 | -4184.0 | [-6583.4, -2183.5] | 0.0002 | better |
| new-books | max_prompt_tokens | 30 | 10381.8 / 5997.6 | -4384.3 | [-6857.8, -2332.0] | 0.0002 | better |
| new-books | n_calls | 30 | 3.9 / 2.1 | -1.8 | [-2.5, -1.1] | 0.0002 | better |
| new-books | invalid_calls | 30 | 0.2 / 0.0 | -0.1 | [-0.3, +0.0] | 0.1730 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.760 / 0.687 | A1/B0=42, A0/B1=20 | — | 0.0071 | worse |
| overall | cited | 300 | 0.713 / 0.640 | A1/B0=47, A0/B1=25 | — | 0.0128 | worse |
| overall | gave_up | 300 | 0.053 / 0.027 | A1/B0=11, A0/B1=3 | — | 0.0574 | n.s. |
| overall | prompt_tokens_total | 300 | 19357.8 / 12935.8 | -6422.0 | [-8921.9, -3968.8] | 0.0000 | better |
| overall | tool_tokens_total | 300 | 5531.8 / 3909.4 | -1622.4 | [-2163.9, -1083.6] | 0.0000 | better |
| overall | max_prompt_tokens | 300 | 7280.6 / 5557.6 | -1723.1 | [-2307.6, -1139.8] | 0.0000 | better |
| overall | n_calls | 300 | 3.1 / 2.4 | -0.7 | [-0.9, -0.5] | 0.0000 | better |
| overall | invalid_calls | 300 | 0.2 / 0.1 | -0.1 | [-0.1, -0.0] | 0.0478 | better |
| overall | empty_results | 300 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.6121 | n.s. |
| golden | found | 240 | 0.742 / 0.667 | A1/B0=35, A0/B1=17 | — | 0.0175 | worse |
| golden | cited | 240 | 0.692 / 0.617 | A1/B0=40, A0/B1=22 | — | 0.0300 | worse |
| golden | gave_up | 240 | 0.058 / 0.033 | A1/B0=9, A0/B1=3 | — | 0.1460 | n.s. |
| golden | prompt_tokens_total | 240 | 19402.5 / 13702.9 | -5699.5 | [-8471.1, -3147.9] | 0.0000 | better |
| golden | tool_tokens_total | 240 | 5508.7 / 4054.0 | -1454.7 | [-2061.4, -881.7] | 0.0000 | better |
| golden | max_prompt_tokens | 240 | 7269.4 / 5714.7 | -1554.8 | [-2207.4, -929.3] | 0.0000 | better |
| golden | n_calls | 240 | 3.1 / 2.4 | -0.7 | [-0.9, -0.5] | 0.0000 | better |
| golden | invalid_calls | 240 | 0.2 / 0.1 | -0.1 | [-0.2, -0.0] | 0.0152 | better |
| golden | empty_results | 240 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.6121 | n.s. |
| new-books | found | 60 | 0.833 / 0.767 | A1/B0=7, A0/B1=3 | — | 0.3438 | n.s. |
| new-books | cited | 60 | 0.800 / 0.733 | A1/B0=7, A0/B1=3 | — | 0.3438 | n.s. |
| new-books | gave_up | 60 | 0.033 / 0.000 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | prompt_tokens_total | 60 | 19179.3 / 9867.5 | -9311.9 | [-15469.1, -4129.9] | 0.0000 | better |
| new-books | tool_tokens_total | 60 | 5624.5 / 3331.2 | -2293.3 | [-3553.9, -1180.7] | 0.0000 | better |
| new-books | max_prompt_tokens | 60 | 7325.5 / 4929.2 | -2396.2 | [-3689.6, -1244.4] | 0.0000 | better |
| new-books | n_calls | 60 | 3.2 / 2.3 | -0.9 | [-1.4, -0.5] | 0.0007 | better |
| new-books | invalid_calls | 60 | 0.2 / 0.2 | +0.0 | [-0.1, +0.2] | 0.8339 | n.s. |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A3hb-vs-A3b.json
