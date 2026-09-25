### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.680 / 0.680 | A1/B0=16, A0/B1=16 | — | 1.0000 | n.s. |
| overall | cited | 150 | 0.653 / 0.653 | A1/B0=17, A0/B1=17 | — | 1.0000 | n.s. |
| overall | gave_up | 150 | 0.000 / 0.013 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| overall | prompt_tokens_total | 150 | 7942.9 / 7871.5 | -71.4 | [-1090.5, +847.3] | 0.3320 | n.s. |
| overall | tool_tokens_total | 150 | 2923.6 / 3395.3 | +471.7 | [+6.3, +936.6] | 0.0000 | worse |
| overall | max_prompt_tokens | 150 | 4053.2 / 4353.9 | +300.8 | [-222.5, +826.7] | 0.0083 | n.s. |
| overall | n_calls | 150 | 2.2 / 2.3 | +0.1 | [-0.1, +0.3] | 0.3022 | n.s. |
| overall | invalid_calls | 150 | 0.1 / 0.3 | +0.1 | [+0.0, +0.2] | 0.0411 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.3711 | n.s. |
| golden | found | 120 | 0.658 / 0.683 | A1/B0=11, A0/B1=14 | — | 0.6900 | n.s. |
| golden | cited | 120 | 0.625 / 0.658 | A1/B0=11, A0/B1=15 | — | 0.5572 | n.s. |
| golden | gave_up | 120 | 0.000 / 0.017 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| golden | prompt_tokens_total | 120 | 7819.5 / 7465.6 | -353.9 | [-1564.4, +756.1] | 0.3319 | n.s. |
| golden | tool_tokens_total | 120 | 2877.8 / 3082.6 | +204.8 | [-291.8, +686.1] | 0.0001 | n.s. |
| golden | max_prompt_tokens | 120 | 3999.2 / 3997.0 | -2.2 | [-552.6, +542.0] | 0.0299 | n.s. |
| golden | n_calls | 120 | 2.2 / 2.3 | +0.1 | [-0.1, +0.3] | 0.3021 | n.s. |
| golden | invalid_calls | 120 | 0.1 / 0.2 | +0.1 | [+0.0, +0.2] | 0.1071 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.3711 | n.s. |
| new-books | found | 30 | 0.767 / 0.667 | A1/B0=5, A0/B1=2 | — | 0.4531 | n.s. |
| new-books | cited | 30 | 0.767 / 0.633 | A1/B0=6, A0/B1=2 | — | 0.2891 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8436.4 / 9495.0 | +1058.6 | [-280.3, +2604.2] | 0.8531 | n.s. |
| new-books | tool_tokens_total | 30 | 3106.8 / 4646.1 | +1539.3 | [+479.6, +2826.3] | 0.0098 | worse |
| new-books | max_prompt_tokens | 30 | 4269.1 / 5781.7 | +1512.6 | [+340.2, +2948.9] | 0.1086 | n.s. |
| new-books | n_calls | 30 | 2.5 / 2.5 | +0.0 | [-0.3, +0.3] | 0.8445 | n.s. |
| new-books | invalid_calls | 30 | 0.2 / 0.4 | +0.2 | [-0.1, +0.4] | 0.2361 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.840 / 0.807 | A1/B0=18, A0/B1=13 | — | 0.4731 | n.s. |
| overall | cited | 150 | 0.773 / 0.753 | A1/B0=21, A0/B1=18 | — | 0.7493 | n.s. |
| overall | gave_up | 150 | 0.107 / 0.120 | A1/B0=9, A0/B1=11 | — | 0.8238 | n.s. |
| overall | prompt_tokens_total | 150 | 30772.8 / 26263.3 | -4509.5 | [-9175.8, -355.2] | 0.0412 | better |
| overall | tool_tokens_total | 150 | 8140.1 / 7290.2 | -849.9 | [-1865.0, +149.9] | 0.0854 | n.s. |
| overall | max_prompt_tokens | 150 | 10508.1 / 9409.8 | -1098.3 | [-2178.0, -20.6] | 0.0237 | better |
| overall | n_calls | 150 | 4.0 / 3.7 | -0.4 | [-0.7, -0.0] | 0.0755 | n.s. |
| overall | invalid_calls | 150 | 0.2 / 0.3 | +0.1 | [-0.0, +0.3] | 0.1574 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.1, -0.0] | 0.0591 | n.s. |
| golden | found | 120 | 0.825 / 0.800 | A1/B0=13, A0/B1=10 | — | 0.6776 | n.s. |
| golden | cited | 120 | 0.758 / 0.750 | A1/B0=16, A0/B1=15 | — | 1.0000 | n.s. |
| golden | gave_up | 120 | 0.117 / 0.108 | A1/B0=7, A0/B1=6 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 30985.5 / 26142.7 | -4842.7 | [-9992.8, -300.3] | 0.0327 | better |
| golden | tool_tokens_total | 120 | 8139.5 / 7380.5 | -759.1 | [-1842.1, +299.1] | 0.2448 | n.s. |
| golden | max_prompt_tokens | 120 | 10539.7 / 9548.3 | -991.4 | [-2160.0, +153.4] | 0.0930 | n.s. |
| golden | n_calls | 120 | 4.1 / 3.6 | -0.4 | [-0.8, -0.1] | 0.0517 | n.s. |
| golden | invalid_calls | 120 | 0.2 / 0.3 | +0.1 | [-0.1, +0.2] | 0.4755 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.1, -0.0] | 0.0591 | n.s. |
| new-books | found | 30 | 0.900 / 0.833 | A1/B0=5, A0/B1=3 | — | 0.7266 | n.s. |
| new-books | cited | 30 | 0.833 / 0.767 | A1/B0=5, A0/B1=3 | — | 0.7266 | n.s. |
| new-books | gave_up | 30 | 0.067 / 0.167 | A1/B0=2, A0/B1=5 | — | 0.4531 | n.s. |
| new-books | prompt_tokens_total | 30 | 29922.3 / 26745.6 | -3176.6 | [-14692.3, +7106.1] | 0.6658 | n.s. |
| new-books | tool_tokens_total | 30 | 8142.2 / 6929.0 | -1213.2 | [-3835.5, +1615.1] | 0.1442 | n.s. |
| new-books | max_prompt_tokens | 30 | 10381.8 / 8855.7 | -1526.2 | [-4207.9, +1373.2] | 0.1132 | n.s. |
| new-books | n_calls | 30 | 3.9 / 3.9 | -0.1 | [-0.9, +0.8] | 0.8664 | n.s. |
| new-books | invalid_calls | 30 | 0.2 / 0.5 | +0.3 | [+0.0, +0.6] | 0.0972 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.760 / 0.743 | A1/B0=34, A0/B1=29 | — | 0.6147 | n.s. |
| overall | cited | 300 | 0.713 / 0.703 | A1/B0=38, A0/B1=35 | — | 0.8151 | n.s. |
| overall | gave_up | 300 | 0.053 / 0.067 | A1/B0=9, A0/B1=13 | — | 0.5235 | n.s. |
| overall | prompt_tokens_total | 300 | 19357.8 / 17067.4 | -2290.5 | [-4626.9, -56.5] | 0.0223 | better |
| overall | tool_tokens_total | 300 | 5531.8 / 5342.7 | -189.1 | [-734.6, +376.6] | 0.3456 | n.s. |
| overall | max_prompt_tokens | 300 | 7280.6 / 6881.9 | -398.8 | [-986.9, +210.6] | 0.5789 | n.s. |
| overall | n_calls | 300 | 3.1 / 3.0 | -0.1 | [-0.3, +0.1] | 0.3178 | n.s. |
| overall | invalid_calls | 300 | 0.2 / 0.3 | +0.1 | [+0.0, +0.2] | 0.0183 | worse |
| overall | empty_results | 300 | 0.0 / 0.0 | -0.0 | [-0.0, -0.0] | 0.0225 | better |
| golden | found | 240 | 0.742 / 0.742 | A1/B0=24, A0/B1=24 | — | 1.0000 | n.s. |
| golden | cited | 240 | 0.692 / 0.704 | A1/B0=27, A0/B1=30 | — | 0.7914 | n.s. |
| golden | gave_up | 240 | 0.058 / 0.062 | A1/B0=7, A0/B1=8 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 240 | 19402.5 / 16804.2 | -2598.3 | [-5144.1, -249.9] | 0.0173 | better |
| golden | tool_tokens_total | 240 | 5508.7 / 5231.5 | -277.1 | [-878.0, +308.5] | 0.3262 | n.s. |
| golden | max_prompt_tokens | 240 | 7269.4 / 6772.7 | -496.8 | [-1145.2, +144.4] | 0.7220 | n.s. |
| golden | n_calls | 240 | 3.1 / 3.0 | -0.2 | [-0.4, +0.0] | 0.2651 | n.s. |
| golden | invalid_calls | 240 | 0.2 / 0.3 | +0.1 | [-0.0, +0.2] | 0.1289 | n.s. |
| golden | empty_results | 240 | 0.0 / 0.0 | -0.0 | [-0.1, -0.0] | 0.0225 | better |
| new-books | found | 60 | 0.833 / 0.750 | A1/B0=10, A0/B1=5 | — | 0.3018 | n.s. |
| new-books | cited | 60 | 0.800 / 0.700 | A1/B0=11, A0/B1=5 | — | 0.2101 | n.s. |
| new-books | gave_up | 60 | 0.033 / 0.083 | A1/B0=2, A0/B1=5 | — | 0.4531 | n.s. |
| new-books | prompt_tokens_total | 60 | 19179.3 / 18120.3 | -1059.0 | [-6706.7, +4117.8] | 0.7046 | n.s. |
| new-books | tool_tokens_total | 60 | 5624.5 / 5787.6 | +163.1 | [-1293.6, +1691.5] | 0.8830 | n.s. |
| new-books | max_prompt_tokens | 60 | 7325.5 / 7318.7 | -6.8 | [-1527.3, +1579.1] | 0.6883 | n.s. |
| new-books | n_calls | 60 | 3.2 / 3.2 | -0.0 | [-0.5, +0.4] | 0.9610 | n.s. |
| new-books | invalid_calls | 60 | 0.2 / 0.4 | +0.2 | [+0.1, +0.5] | 0.0386 | worse |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A4b-vs-A3b.json
