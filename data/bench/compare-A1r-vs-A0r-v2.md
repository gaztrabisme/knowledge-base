### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.930 / 0.938 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| overall | cited | 128 | 0.922 / 0.938 | A1/B0=5, A0/B1=7 | — | 0.7744 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 13043.4 / 6256.9 | -6786.5 | [-7763.0, -5775.9] | 0.0000 | better |
| overall | tool_tokens_total | 128 | 51027.2 / 2874.4 | -48152.8 | [-56965.6, -39445.0] | 0.0000 | better |
| overall | max_prompt_tokens | 128 | 11658.9 / 4045.5 | -7613.4 | [-8375.3, -6867.7] | 0.0000 | better |
| overall | n_calls | 128 | 1.4 / 1.2 | -0.2 | [-0.3, -0.1] | 0.0021 | better |
| overall | invalid_calls | 128 | 0.4 / 0.0 | -0.4 | [-0.5, -0.3] | 0.0000 | better |
| overall | empty_results | 128 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 99 | 0.909 / 0.919 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| golden | cited | 99 | 0.899 / 0.919 | A1/B0=5, A0/B1=7 | — | 0.7744 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 13110.5 / 6461.8 | -6648.7 | [-7851.5, -5389.2] | 0.0000 | better |
| golden | tool_tokens_total | 99 | 56538.2 / 2951.1 | -53587.1 | [-64211.0, -43216.1] | 0.0000 | better |
| golden | max_prompt_tokens | 99 | 11670.2 / 4113.5 | -7556.8 | [-8450.9, -6653.5] | 0.0000 | better |
| golden | n_calls | 99 | 1.4 / 1.2 | -0.2 | [-0.4, -0.1] | 0.0030 | better |
| golden | invalid_calls | 99 | 0.4 / 0.0 | -0.4 | [-0.5, -0.3] | 0.0000 | better |
| golden | empty_results | 99 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | found | 29 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | cited | 29 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 12814.3 / 5557.6 | -7256.7 | [-8856.2, -5661.3] | 0.0000 | better |
| new-books | tool_tokens_total | 29 | 32213.9 / 2612.3 | -29601.6 | [-46828.1, -15060.2] | 0.0000 | better |
| new-books | max_prompt_tokens | 29 | 11620.1 / 3813.5 | -7806.6 | [-9143.9, -6558.7] | 0.0000 | better |
| new-books | n_calls | 29 | 1.2 / 1.1 | -0.1 | [-0.3, +0.1] | 0.4069 | n.s. |
| new-books | invalid_calls | 29 | 0.2 / 0.0 | -0.2 | [-0.4, -0.1] | 0.0360 | better |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.984 / 0.992 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| overall | cited | 128 | 0.938 / 0.953 | A1/B0=5, A0/B1=7 | — | 0.7744 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 43139.8 / 30780.4 | -12359.4 | [-27603.1, +4183.9] | 0.0000 | n.s. |
| overall | tool_tokens_total | 128 | 34837.8 / 9030.2 | -25807.6 | [-32640.8, -19642.9] | 0.0000 | better |
| overall | max_prompt_tokens | 128 | 23198.5 / 11781.8 | -11416.6 | [-13981.5, -8971.5] | 0.0000 | better |
| overall | n_calls | 128 | 2.6 / 4.0 | +1.4 | [+1.0, +1.9] | 0.0000 | worse |
| overall | invalid_calls | 128 | 0.2 / 0.0 | -0.2 | [-0.3, -0.1] | 0.0028 | better |
| overall | empty_results | 128 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.8551 | n.s. |
| golden | found | 99 | 0.980 / 0.990 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| golden | cited | 99 | 0.939 / 0.939 | A1/B0=5, A0/B1=5 | — | 1.0000 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 47503.4 / 35443.5 | -12060.0 | [-32231.7, +7974.2] | 0.0001 | n.s. |
| golden | tool_tokens_total | 99 | 38884.9 / 9945.8 | -28939.1 | [-37291.0, -21252.6] | 0.0000 | better |
| golden | max_prompt_tokens | 99 | 24412.0 / 12816.0 | -11596.0 | [-14885.6, -8639.9] | 0.0000 | better |
| golden | n_calls | 99 | 2.7 / 4.3 | +1.6 | [+1.1, +2.2] | 0.0000 | worse |
| golden | invalid_calls | 99 | 0.2 / 0.1 | -0.2 | [-0.3, -0.1] | 0.0069 | better |
| golden | empty_results | 99 | 0.0 / 0.0 | +0.0 | [-0.0, +0.1] | 0.8551 | n.s. |
| new-books | found | 29 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | cited | 29 | 0.931 / 1.000 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 28243.1 / 14861.5 | -13381.6 | [-18740.3, -8556.2] | 0.0000 | better |
| new-books | tool_tokens_total | 29 | 21022.0 / 5904.7 | -15117.3 | [-25023.7, -9304.1] | 0.0000 | better |
| new-books | max_prompt_tokens | 29 | 19055.8 / 8251.6 | -10804.2 | [-12999.9, -8596.7] | 0.0000 | better |
| new-books | n_calls | 29 | 2.5 / 3.1 | +0.6 | [+0.1, +1.1] | 0.0328 | worse |
| new-books | invalid_calls | 29 | 0.1 / 0.0 | -0.1 | [-0.3, +0.0] | 0.3711 | n.s. |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 256 | 0.957 / 0.965 | A1/B0=5, A0/B1=7 | — | 0.7744 | n.s. |
| overall | cited | 256 | 0.930 / 0.945 | A1/B0=10, A0/B1=14 | — | 0.5413 | n.s. |
| overall | gave_up | 256 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 256 | 28091.6 / 18518.6 | -9572.9 | [-17408.5, -1505.5] | 0.0000 | better |
| overall | tool_tokens_total | 256 | 42932.5 / 5952.3 | -36980.2 | [-42705.6, -31355.9] | 0.0000 | better |
| overall | max_prompt_tokens | 256 | 17428.7 / 7913.7 | -9515.0 | [-10922.3, -8244.0] | 0.0000 | better |
| overall | n_calls | 256 | 2.0 / 2.6 | +0.6 | [+0.4, +0.8] | 0.0000 | worse |
| overall | invalid_calls | 256 | 0.3 / 0.0 | -0.3 | [-0.3, -0.2] | 0.0000 | better |
| overall | empty_results | 256 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.8551 | n.s. |
| golden | found | 198 | 0.944 / 0.955 | A1/B0=5, A0/B1=7 | — | 0.7744 | n.s. |
| golden | cited | 198 | 0.919 / 0.929 | A1/B0=10, A0/B1=12 | — | 0.8318 | n.s. |
| golden | gave_up | 198 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 198 | 30307.0 / 20952.6 | -9354.4 | [-19499.1, +1118.2] | 0.0000 | n.s. |
| golden | tool_tokens_total | 198 | 47711.5 / 6448.5 | -41263.1 | [-47938.6, -34555.4] | 0.0000 | better |
| golden | max_prompt_tokens | 198 | 18041.1 / 8464.7 | -9576.4 | [-11318.3, -7953.1] | 0.0000 | better |
| golden | n_calls | 198 | 2.1 / 2.8 | +0.7 | [+0.4, +1.0] | 0.0000 | worse |
| golden | invalid_calls | 198 | 0.3 / 0.0 | -0.3 | [-0.4, -0.2] | 0.0000 | better |
| golden | empty_results | 198 | 0.0 / 0.0 | +0.0 | [-0.0, +0.0] | 0.8551 | n.s. |
| new-books | found | 58 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | cited | 58 | 0.966 / 1.000 | A1/B0=0, A0/B1=2 | — | 0.5000 | n.s. |
| new-books | gave_up | 58 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 58 | 20528.7 / 10209.5 | -10319.1 | [-13243.5, -7678.5] | 0.0000 | better |
| new-books | tool_tokens_total | 58 | 26617.9 / 4258.5 | -22359.4 | [-32031.9, -14006.2] | 0.0000 | better |
| new-books | max_prompt_tokens | 58 | 15337.9 / 6032.5 | -9305.4 | [-10636.8, -8004.4] | 0.0000 | better |
| new-books | n_calls | 58 | 1.8 / 2.1 | +0.2 | [-0.0, +0.5] | 0.0926 | n.s. |
| new-books | invalid_calls | 58 | 0.2 / 0.0 | -0.2 | [-0.3, -0.1] | 0.0143 | better |
| new-books | empty_results | 58 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to ../data/bench/compare-A1r-vs-A0r-v2.json
