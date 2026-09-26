### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.938 / 0.922 | A1/B0=8, A0/B1=6 | — | 0.7905 | n.s. |
| overall | cited | 128 | 0.938 / 0.922 | A1/B0=8, A0/B1=6 | — | 0.7905 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 6256.9 / 4948.5 | -1308.5 | [-2104.5, -569.4] | 0.0087 | better |
| overall | tool_tokens_total | 128 | 2874.4 / 2112.0 | -762.3 | [-1134.4, -417.8] | 0.0051 | better |
| overall | max_prompt_tokens | 128 | 4045.5 / 3476.9 | -568.6 | [-944.8, -222.7] | 0.2114 | n.s. |
| overall | n_calls | 128 | 1.2 / 1.0 | -0.2 | [-0.3, -0.1] | 0.0016 | better |
| overall | invalid_calls | 128 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| overall | empty_results | 128 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 99 | 0.919 / 0.899 | A1/B0=8, A0/B1=6 | — | 0.7905 | n.s. |
| golden | cited | 99 | 0.919 / 0.899 | A1/B0=8, A0/B1=6 | — | 0.7905 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 6461.8 / 4980.9 | -1480.9 | [-2426.5, -603.6] | 0.0748 | n.s. |
| golden | tool_tokens_total | 99 | 2951.1 / 2123.1 | -828.0 | [-1273.7, -411.6] | 0.0196 | better |
| golden | max_prompt_tokens | 99 | 4113.5 / 3473.7 | -639.8 | [-1087.8, -219.3] | 0.4743 | n.s. |
| golden | n_calls | 99 | 1.2 / 1.0 | -0.2 | [-0.3, -0.1] | 0.0045 | better |
| golden | invalid_calls | 99 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | empty_results | 99 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | found | 29 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | cited | 29 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 5557.6 / 4837.6 | -720.0 | [-2149.3, +385.4] | 0.0232 | n.s. |
| new-books | tool_tokens_total | 29 | 2612.3 / 2074.2 | -538.1 | [-1143.4, -56.1] | 0.0979 | n.s. |
| new-books | max_prompt_tokens | 29 | 3813.5 / 3487.8 | -325.7 | [-953.7, +171.1] | 0.1945 | n.s. |
| new-books | n_calls | 29 | 1.1 / 1.0 | -0.1 | [-0.2, +0.0] | 0.1814 | n.s. |
| new-books | invalid_calls | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.992 / 0.992 | A1/B0=1, A0/B1=1 | — | 1.0000 | n.s. |
| overall | cited | 128 | 0.953 / 0.930 | A1/B0=8, A0/B1=5 | — | 0.5811 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.008 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 30780.4 / 33294.2 | +2513.8 | [-13215.5, +15339.0] | 0.0075 | n.s. |
| overall | tool_tokens_total | 128 | 9030.2 / 9251.3 | +221.1 | [-930.8, +1147.4] | 0.0564 | n.s. |
| overall | max_prompt_tokens | 128 | 11781.8 / 12431.6 | +649.7 | [-663.0, +1705.4] | 0.0028 | n.s. |
| overall | n_calls | 128 | 4.0 / 4.5 | +0.4 | [-0.1, +0.9] | 0.0147 | n.s. |
| overall | invalid_calls | 128 | 0.0 / 0.1 | +0.0 | [-0.0, +0.1] | 0.4412 | n.s. |
| overall | empty_results | 128 | 0.0 / 0.1 | +0.1 | [+0.0, +0.2] | 0.1029 | n.s. |
| golden | found | 99 | 0.990 / 0.990 | A1/B0=1, A0/B1=1 | — | 1.0000 | n.s. |
| golden | cited | 99 | 0.939 / 0.929 | A1/B0=6, A0/B1=5 | — | 1.0000 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.010 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 35443.5 / 37785.4 | +2341.9 | [-16917.4, +19132.7] | 0.0410 | n.s. |
| golden | tool_tokens_total | 99 | 9945.8 / 10103.2 | +157.4 | [-1239.1, +1300.7] | 0.1249 | n.s. |
| golden | max_prompt_tokens | 99 | 12816.0 / 13420.7 | +604.7 | [-992.8, +1916.8] | 0.0155 | n.s. |
| golden | n_calls | 99 | 4.3 / 4.8 | +0.5 | [-0.2, +1.0] | 0.0335 | n.s. |
| golden | invalid_calls | 99 | 0.1 / 0.1 | +0.0 | [-0.0, +0.1] | 0.4412 | n.s. |
| golden | empty_results | 99 | 0.0 / 0.2 | +0.1 | [+0.0, +0.3] | 0.1029 | n.s. |
| new-books | found | 29 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | cited | 29 | 1.000 / 0.931 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 14861.5 / 17962.1 | +3100.7 | [-493.8, +6683.4] | 0.0421 | n.s. |
| new-books | tool_tokens_total | 29 | 5904.7 / 6343.1 | +438.4 | [-637.4, +1437.7] | 0.1731 | n.s. |
| new-books | max_prompt_tokens | 29 | 8251.6 / 9055.1 | +803.6 | [-378.3, +1889.6] | 0.0400 | n.s. |
| new-books | n_calls | 29 | 3.1 / 3.4 | +0.3 | [-0.2, +0.9] | 0.2273 | n.s. |
| new-books | invalid_calls | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 256 | 0.965 / 0.957 | A1/B0=9, A0/B1=7 | — | 0.8036 | n.s. |
| overall | cited | 256 | 0.945 / 0.926 | A1/B0=16, A0/B1=11 | — | 0.4421 | n.s. |
| overall | gave_up | 256 | 0.000 / 0.004 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 256 | 18518.6 / 19121.3 | +602.7 | [-6975.2, +7144.7] | 0.0007 | n.s. |
| overall | tool_tokens_total | 256 | 5952.3 / 5681.7 | -270.6 | [-849.0, +247.2] | 0.8792 | n.s. |
| overall | max_prompt_tokens | 256 | 7913.7 / 7954.2 | +40.6 | [-606.8, +622.0] | 0.0063 | n.s. |
| overall | n_calls | 256 | 2.6 / 2.7 | +0.1 | [-0.1, +0.4] | 0.1582 | n.s. |
| overall | invalid_calls | 256 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.3139 | n.s. |
| overall | empty_results | 256 | 0.0 / 0.1 | +0.1 | [+0.0, +0.1] | 0.1029 | n.s. |
| golden | found | 198 | 0.955 / 0.944 | A1/B0=9, A0/B1=7 | — | 0.8036 | n.s. |
| golden | cited | 198 | 0.929 / 0.914 | A1/B0=14, A0/B1=11 | — | 0.6900 | n.s. |
| golden | gave_up | 198 | 0.000 / 0.005 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 198 | 20952.6 / 21383.1 | +430.5 | [-9452.2, +8848.2] | 0.0157 | n.s. |
| golden | tool_tokens_total | 198 | 6448.5 / 6113.1 | -335.3 | [-1068.0, +279.1] | 0.7850 | n.s. |
| golden | max_prompt_tokens | 198 | 8464.7 / 8447.2 | -17.6 | [-842.1, +674.1] | 0.0596 | n.s. |
| golden | n_calls | 198 | 2.8 / 2.9 | +0.1 | [-0.2, +0.4] | 0.2786 | n.s. |
| golden | invalid_calls | 198 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.3139 | n.s. |
| golden | empty_results | 198 | 0.0 / 0.1 | +0.1 | [+0.0, +0.1] | 0.1029 | n.s. |
| new-books | found | 58 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | cited | 58 | 1.000 / 0.966 | A1/B0=2, A0/B1=0 | — | 0.5000 | n.s. |
| new-books | gave_up | 58 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 58 | 10209.5 / 11399.9 | +1190.3 | [-754.1, +3152.3] | 0.0041 | n.s. |
| new-books | tool_tokens_total | 58 | 4258.5 / 4208.7 | -49.8 | [-669.7, +540.7] | 0.8036 | n.s. |
| new-books | max_prompt_tokens | 58 | 6032.5 / 6271.5 | +238.9 | [-430.0, +873.6] | 0.0124 | n.s. |
| new-books | n_calls | 58 | 2.1 / 2.2 | +0.1 | [-0.2, +0.4] | 0.3301 | n.s. |
| new-books | invalid_calls | 58 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 58 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to ../data/bench/compare-A5r-vs-A1r-v2.json
