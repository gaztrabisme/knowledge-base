### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.938 / 0.875 | A1/B0=11, A0/B1=3 | — | 0.0574 | n.s. |
| overall | cited | 128 | 0.938 / 0.875 | A1/B0=11, A0/B1=3 | — | 0.0574 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 6256.9 / 5723.5 | -533.4 | [-1446.5, +320.9] | 0.2444 | n.s. |
| overall | tool_tokens_total | 128 | 2874.4 / 2537.8 | -336.6 | [-756.6, +53.7] | 0.1689 | n.s. |
| overall | max_prompt_tokens | 128 | 4045.5 / 3595.3 | -450.2 | [-881.1, -39.1] | 0.9147 | n.s. |
| overall | n_calls | 128 | 1.2 / 1.6 | +0.4 | [+0.3, +0.6] | 0.0000 | worse |
| overall | invalid_calls | 128 | 0.0 / 0.0 | +0.0 | [+0.0, +0.1] | 0.1003 | n.s. |
| overall | empty_results | 128 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 99 | 0.919 / 0.859 | A1/B0=9, A0/B1=3 | — | 0.1460 | n.s. |
| golden | cited | 99 | 0.919 / 0.859 | A1/B0=9, A0/B1=3 | — | 0.1460 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 6461.8 / 5654.2 | -807.6 | [-1832.2, +187.6] | 0.5541 | n.s. |
| golden | tool_tokens_total | 99 | 2951.1 / 2536.2 | -414.9 | [-895.3, +64.4] | 0.6067 | n.s. |
| golden | max_prompt_tokens | 99 | 4113.5 / 3585.7 | -527.8 | [-1026.1, -26.8] | 0.6273 | n.s. |
| golden | n_calls | 99 | 1.2 / 1.6 | +0.4 | [+0.2, +0.5] | 0.0002 | worse |
| golden | invalid_calls | 99 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | empty_results | 99 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | found | 29 | 1.000 / 0.931 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | cited | 29 | 1.000 / 0.931 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 5557.6 / 5960.2 | +402.7 | [-1460.1, +2138.9] | 0.2098 | n.s. |
| new-books | tool_tokens_total | 29 | 2612.3 / 2543.1 | -69.2 | [-771.7, +503.4] | 0.0379 | n.s. |
| new-books | max_prompt_tokens | 29 | 3813.5 / 3628.3 | -185.2 | [-918.1, +415.4] | 0.1945 | n.s. |
| new-books | n_calls | 29 | 1.1 / 1.7 | +0.6 | [+0.2, +1.0] | 0.0162 | worse |
| new-books | invalid_calls | 29 | 0.0 / 0.2 | +0.2 | [+0.0, +0.4] | 0.1814 | n.s. |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.992 / 0.953 | A1/B0=5, A0/B1=0 | — | 0.0625 | n.s. |
| overall | cited | 128 | 0.953 / 0.914 | A1/B0=9, A0/B1=4 | — | 0.2668 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.008 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 30780.4 / 26079.3 | -4701.0 | [-18959.8, +4785.5] | 0.8538 | n.s. |
| overall | tool_tokens_total | 128 | 9030.2 / 7309.6 | -1720.6 | [-2975.0, -591.4] | 0.0074 | better |
| overall | max_prompt_tokens | 128 | 11781.8 / 10112.3 | -1669.5 | [-3073.5, -415.3] | 0.0369 | better |
| overall | n_calls | 128 | 4.0 / 3.8 | -0.3 | [-0.8, +0.2] | 0.1196 | n.s. |
| overall | invalid_calls | 128 | 0.0 / 0.1 | +0.0 | [-0.0, +0.1] | 0.3270 | n.s. |
| overall | empty_results | 128 | 0.0 / 0.1 | +0.0 | [-0.0, +0.1] | 0.3525 | n.s. |
| golden | found | 99 | 0.990 / 0.960 | A1/B0=3, A0/B1=0 | — | 0.2500 | n.s. |
| golden | cited | 99 | 0.939 / 0.919 | A1/B0=6, A0/B1=4 | — | 0.7539 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.010 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 35443.5 / 28975.3 | -6468.2 | [-24255.5, +5780.3] | 0.8382 | n.s. |
| golden | tool_tokens_total | 99 | 9945.8 / 7965.1 | -1980.7 | [-3541.2, -600.5] | 0.0209 | better |
| golden | max_prompt_tokens | 99 | 12816.0 / 10864.4 | -1951.6 | [-3701.2, -419.1] | 0.0825 | n.s. |
| golden | n_calls | 99 | 4.3 / 4.0 | -0.3 | [-0.9, +0.3] | 0.2075 | n.s. |
| golden | invalid_calls | 99 | 0.1 / 0.1 | +0.0 | [-0.0, +0.1] | 0.6121 | n.s. |
| golden | empty_results | 99 | 0.0 / 0.1 | +0.1 | [-0.0, +0.2] | 0.3525 | n.s. |
| new-books | found | 29 | 1.000 / 0.931 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | cited | 29 | 1.000 / 0.897 | A1/B0=3, A0/B1=0 | — | 0.2500 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 14861.5 / 16193.1 | +1331.7 | [-3271.9, +6534.2] | 0.8120 | n.s. |
| new-books | tool_tokens_total | 29 | 5904.7 / 5071.9 | -832.9 | [-2218.4, +606.0] | 0.1599 | n.s. |
| new-books | max_prompt_tokens | 29 | 8251.6 / 7545.0 | -706.6 | [-2233.4, +840.2] | 0.2518 | n.s. |
| new-books | n_calls | 29 | 3.1 / 2.8 | -0.2 | [-0.9, +0.5] | 0.3317 | n.s. |
| new-books | invalid_calls | 29 | 0.0 / 0.1 | +0.1 | [+0.0, +0.2] | 1.0000 | n.s. |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 256 | 0.965 / 0.914 | A1/B0=16, A0/B1=3 | — | 0.0044 | worse |
| overall | cited | 256 | 0.945 / 0.895 | A1/B0=20, A0/B1=7 | — | 0.0192 | worse |
| overall | gave_up | 256 | 0.000 / 0.004 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 256 | 18518.6 / 15901.4 | -2617.2 | [-9591.3, +2196.5] | 0.7270 | n.s. |
| overall | tool_tokens_total | 256 | 5952.3 / 4923.7 | -1028.6 | [-1684.0, -411.3] | 0.0971 | n.s. |
| overall | max_prompt_tokens | 256 | 7913.7 / 6853.8 | -1059.9 | [-1790.0, -378.0] | 0.0894 | n.s. |
| overall | n_calls | 256 | 2.6 / 2.7 | +0.1 | [-0.2, +0.3] | 0.4266 | n.s. |
| overall | invalid_calls | 256 | 0.0 / 0.1 | +0.0 | [+0.0, +0.1] | 0.0653 | n.s. |
| overall | empty_results | 256 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.3525 | n.s. |
| golden | found | 198 | 0.955 / 0.909 | A1/B0=12, A0/B1=3 | — | 0.0352 | worse |
| golden | cited | 198 | 0.929 / 0.889 | A1/B0=15, A0/B1=7 | — | 0.1338 | n.s. |
| golden | gave_up | 198 | 0.000 / 0.005 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 198 | 20952.6 / 17314.7 | -3637.9 | [-12583.5, +2515.4] | 0.8809 | n.s. |
| golden | tool_tokens_total | 198 | 6448.5 / 5250.7 | -1197.8 | [-2029.4, -451.6] | 0.0962 | n.s. |
| golden | max_prompt_tokens | 198 | 8464.7 / 7225.0 | -1239.7 | [-2163.0, -416.6] | 0.1060 | n.s. |
| golden | n_calls | 198 | 2.8 / 2.8 | +0.0 | [-0.3, +0.3] | 0.4926 | n.s. |
| golden | invalid_calls | 198 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.4412 | n.s. |
| golden | empty_results | 198 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.3525 | n.s. |
| new-books | found | 58 | 1.000 / 0.931 | A1/B0=4, A0/B1=0 | — | 0.1250 | n.s. |
| new-books | cited | 58 | 1.000 / 0.914 | A1/B0=5, A0/B1=0 | — | 0.0625 | n.s. |
| new-books | gave_up | 58 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 58 | 10209.5 / 11076.7 | +867.2 | [-1596.7, +3528.1] | 0.7421 | n.s. |
| new-books | tool_tokens_total | 58 | 4258.5 / 3807.5 | -451.0 | [-1216.2, +309.9] | 0.6646 | n.s. |
| new-books | max_prompt_tokens | 58 | 6032.5 / 5586.6 | -445.9 | [-1269.2, +374.7] | 0.5667 | n.s. |
| new-books | n_calls | 58 | 2.1 / 2.2 | +0.2 | [-0.3, +0.6] | 0.6657 | n.s. |
| new-books | invalid_calls | 58 | 0.0 / 0.1 | +0.1 | [+0.0, +0.3] | 0.1003 | n.s. |
| new-books | empty_results | 58 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to ../data/bench/compare-A3hbr-vs-A1r-v2.json
