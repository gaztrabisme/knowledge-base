### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.667 / 0.680 | A1/B0=11, A0/B1=13 | — | 0.8388 | n.s. |
| overall | cited | 150 | 0.660 / 0.653 | A1/B0=13, A0/B1=12 | — | 1.0000 | n.s. |
| overall | gave_up | 150 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 8117.8 / 7942.9 | -174.9 | [-1076.9, +849.5] | 0.0001 | n.s. |
| overall | tool_tokens_total | 150 | 2478.8 / 2923.6 | +444.8 | [+130.1, +806.4] | 0.0096 | worse |
| overall | max_prompt_tokens | 150 | 4019.4 / 4053.2 | +33.8 | [-303.2, +433.8] | 0.0151 | n.s. |
| overall | n_calls | 150 | 2.0 / 2.2 | +0.2 | [+0.1, +0.4] | 0.0032 | worse |
| overall | invalid_calls | 150 | 0.0 / 0.1 | +0.1 | [+0.1, +0.2] | 0.0007 | worse |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.3711 | n.s. |
| golden | found | 120 | 0.658 / 0.658 | A1/B0=9, A0/B1=9 | — | 1.0000 | n.s. |
| golden | cited | 120 | 0.650 / 0.625 | A1/B0=11, A0/B1=8 | — | 0.6476 | n.s. |
| golden | gave_up | 120 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 7972.6 / 7819.5 | -153.1 | [-1260.2, +1099.2] | 0.0001 | n.s. |
| golden | tool_tokens_total | 120 | 2400.0 / 2877.8 | +477.8 | [+102.4, +917.3] | 0.0241 | worse |
| golden | max_prompt_tokens | 120 | 3924.6 / 3999.2 | +74.6 | [-328.9, +561.5] | 0.0244 | n.s. |
| golden | n_calls | 120 | 2.0 / 2.2 | +0.2 | [+0.0, +0.3] | 0.0298 | worse |
| golden | invalid_calls | 120 | 0.0 / 0.1 | +0.1 | [+0.0, +0.2] | 0.0098 | worse |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.3711 | n.s. |
| new-books | found | 30 | 0.700 / 0.767 | A1/B0=2, A0/B1=4 | — | 0.6875 | n.s. |
| new-books | cited | 30 | 0.700 / 0.767 | A1/B0=2, A0/B1=4 | — | 0.6875 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 8698.5 / 8436.4 | -262.1 | [-1544.2, +1062.4] | 0.2249 | n.s. |
| new-books | tool_tokens_total | 30 | 2794.0 / 3106.8 | +312.8 | [-116.5, +755.1] | 0.2172 | n.s. |
| new-books | max_prompt_tokens | 30 | 4398.7 / 4269.1 | -129.6 | [-576.1, +327.5] | 0.3655 | n.s. |
| new-books | n_calls | 30 | 2.1 / 2.5 | +0.4 | [+0.1, +0.7] | 0.0464 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.2 | +0.2 | [+0.1, +0.4] | 0.0225 | worse |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.840 / 0.840 | A1/B0=12, A0/B1=12 | — | 1.0000 | n.s. |
| overall | cited | 150 | 0.780 / 0.773 | A1/B0=17, A0/B1=16 | — | 1.0000 | n.s. |
| overall | gave_up | 150 | 0.067 / 0.107 | A1/B0=6, A0/B1=12 | — | 0.2379 | n.s. |
| overall | prompt_tokens_total | 150 | 24854.8 / 30772.8 | +5918.0 | [+1505.0, +10811.4] | 0.0178 | worse |
| overall | tool_tokens_total | 150 | 6406.7 / 8140.1 | +1733.3 | [+858.3, +2685.5] | 0.0006 | worse |
| overall | max_prompt_tokens | 150 | 9092.3 / 10508.1 | +1415.8 | [+507.9, +2409.4] | 0.0254 | worse |
| overall | n_calls | 150 | 3.5 / 4.0 | +0.5 | [+0.2, +0.9] | 0.0050 | worse |
| overall | invalid_calls | 150 | 0.1 / 0.2 | +0.1 | [+0.0, +0.2] | 0.0774 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [+0.0, +0.1] | 0.1003 | n.s. |
| golden | found | 120 | 0.833 / 0.825 | A1/B0=11, A0/B1=10 | — | 1.0000 | n.s. |
| golden | cited | 120 | 0.767 / 0.758 | A1/B0=15, A0/B1=14 | — | 1.0000 | n.s. |
| golden | gave_up | 120 | 0.075 / 0.117 | A1/B0=5, A0/B1=10 | — | 0.3018 | n.s. |
| golden | prompt_tokens_total | 120 | 26178.0 / 30985.5 | +4807.5 | [+73.3, +10222.8] | 0.1110 | n.s. |
| golden | tool_tokens_total | 120 | 6657.6 / 8139.5 | +1481.9 | [+494.8, +2505.4] | 0.0100 | worse |
| golden | max_prompt_tokens | 120 | 9382.0 / 10539.7 | +1157.7 | [+109.5, +2237.2] | 0.1338 | n.s. |
| golden | n_calls | 120 | 3.6 / 4.1 | +0.4 | [+0.0, +0.8] | 0.0540 | n.s. |
| golden | invalid_calls | 120 | 0.1 / 0.2 | +0.1 | [+0.0, +0.3] | 0.1045 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [+0.0, +0.1] | 0.1003 | n.s. |
| new-books | found | 30 | 0.867 / 0.900 | A1/B0=1, A0/B1=2 | — | 1.0000 | n.s. |
| new-books | cited | 30 | 0.833 / 0.833 | A1/B0=2, A0/B1=2 | — | 1.0000 | n.s. |
| new-books | gave_up | 30 | 0.033 / 0.067 | A1/B0=1, A0/B1=2 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 19561.9 / 29922.3 | +10360.3 | [+40.6, +22297.1] | 0.0397 | worse |
| new-books | tool_tokens_total | 30 | 5403.4 / 8142.2 | +2738.8 | [+875.2, +4868.3] | 0.0101 | worse |
| new-books | max_prompt_tokens | 30 | 7933.5 / 10381.8 | +2448.3 | [+600.2, +4564.7] | 0.0417 | worse |
| new-books | n_calls | 30 | 2.9 / 3.9 | +1.0 | [+0.3, +1.8] | 0.0156 | worse |
| new-books | invalid_calls | 30 | 0.1 / 0.2 | +0.1 | [-0.1, +0.2] | 0.5896 | n.s. |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.753 / 0.760 | A1/B0=23, A0/B1=25 | — | 0.8854 | n.s. |
| overall | cited | 300 | 0.720 / 0.713 | A1/B0=30, A0/B1=28 | — | 0.8957 | n.s. |
| overall | gave_up | 300 | 0.033 / 0.053 | A1/B0=6, A0/B1=12 | — | 0.2379 | n.s. |
| overall | prompt_tokens_total | 300 | 16486.3 / 19357.8 | +2871.6 | [+566.8, +5409.7] | 0.9398 | n.s. |
| overall | tool_tokens_total | 300 | 4442.8 / 5531.8 | +1089.0 | [+611.0, +1590.9] | 0.0000 | worse |
| overall | max_prompt_tokens | 300 | 6555.9 / 7280.6 | +724.8 | [+224.8, +1252.0] | 0.5551 | n.s. |
| overall | n_calls | 300 | 2.8 / 3.1 | +0.4 | [+0.2, +0.6] | 0.0001 | worse |
| overall | invalid_calls | 300 | 0.1 / 0.2 | +0.1 | [+0.1, +0.2] | 0.0004 | worse |
| overall | empty_results | 300 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.5294 | n.s. |
| golden | found | 240 | 0.746 / 0.742 | A1/B0=20, A0/B1=19 | — | 1.0000 | n.s. |
| golden | cited | 240 | 0.708 / 0.692 | A1/B0=26, A0/B1=22 | — | 0.6655 | n.s. |
| golden | gave_up | 240 | 0.037 / 0.058 | A1/B0=5, A0/B1=10 | — | 0.3018 | n.s. |
| golden | prompt_tokens_total | 240 | 17075.3 / 19402.5 | +2327.2 | [-82.0, +5049.7] | 0.6268 | n.s. |
| golden | tool_tokens_total | 240 | 4528.8 / 5508.7 | +979.9 | [+445.8, +1539.1] | 0.0007 | worse |
| golden | max_prompt_tokens | 240 | 6653.3 / 7269.4 | +616.1 | [+51.4, +1210.8] | 0.9054 | n.s. |
| golden | n_calls | 240 | 2.8 / 3.1 | +0.3 | [+0.1, +0.5] | 0.0071 | worse |
| golden | invalid_calls | 240 | 0.1 / 0.2 | +0.1 | [+0.0, +0.2] | 0.0040 | worse |
| golden | empty_results | 240 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.5294 | n.s. |
| new-books | found | 60 | 0.783 / 0.833 | A1/B0=3, A0/B1=6 | — | 0.5078 | n.s. |
| new-books | cited | 60 | 0.767 / 0.800 | A1/B0=4, A0/B1=6 | — | 0.7539 | n.s. |
| new-books | gave_up | 60 | 0.017 / 0.033 | A1/B0=1, A0/B1=2 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 60 | 14130.2 / 19179.3 | +5049.1 | [-193.0, +11315.6] | 0.2942 | n.s. |
| new-books | tool_tokens_total | 60 | 4098.7 / 5624.5 | +1525.8 | [+542.8, +2670.8] | 0.0037 | worse |
| new-books | max_prompt_tokens | 60 | 6166.1 / 7325.5 | +1159.4 | [+169.1, +2296.2] | 0.2743 | n.s. |
| new-books | n_calls | 60 | 2.5 / 3.2 | +0.7 | [+0.3, +1.1] | 0.0019 | worse |
| new-books | invalid_calls | 60 | 0.1 / 0.2 | +0.1 | [+0.0, +0.3] | 0.0376 | worse |
| new-books | empty_results | 60 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A3b-vs-A2b.json
