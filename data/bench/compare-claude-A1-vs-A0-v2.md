### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| overall | cited | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| overall | gave_up | 20 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 20 | 37491.2 / 29499.4 | -7991.8 | [-19223.2, +287.1] | 0.0894 | n.s. |
| overall | tool_tokens_total | 20 | 12922.2 / 12195.4 | -726.8 | [-2655.9, +994.5] | 0.6026 | n.s. |
| overall | n_calls | 20 | 5.7 / 5.0 | -0.8 | [-1.8, +0.2] | 0.1961 | n.s. |
| overall | invalid_calls | 20 | 0.1 / 0.0 | -0.1 | [-0.3, +0.0] | 1.0000 | n.s. |
| overall | empty_results | 20 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| golden | cited | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| golden | gave_up | 20 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 20 | 37491.2 / 29499.4 | -7991.8 | [-19223.2, +287.1] | 0.0894 | n.s. |
| golden | tool_tokens_total | 20 | 12922.2 / 12195.4 | -726.8 | [-2655.9, +994.5] | 0.6026 | n.s. |
| golden | n_calls | 20 | 5.7 / 5.0 | -0.8 | [-1.8, +0.2] | 0.1961 | n.s. |
| golden | invalid_calls | 20 | 0.1 / 0.0 | -0.1 | [-0.3, +0.0] | 1.0000 | n.s. |
| golden | empty_results | 20 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| overall | cited | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| overall | gave_up | 20 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 20 | 37491.2 / 29499.4 | -7991.8 | [-19223.2, +287.1] | 0.0894 | n.s. |
| overall | tool_tokens_total | 20 | 12922.2 / 12195.4 | -726.8 | [-2655.9, +994.5] | 0.6026 | n.s. |
| overall | n_calls | 20 | 5.7 / 5.0 | -0.8 | [-1.8, +0.2] | 0.1961 | n.s. |
| overall | invalid_calls | 20 | 0.1 / 0.0 | -0.1 | [-0.3, +0.0] | 1.0000 | n.s. |
| overall | empty_results | 20 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| golden | cited | 20 | 0.950 / 0.900 | A1/B0=1, A0/B1=0 | — | 1.0000 | n.s. |
| golden | gave_up | 20 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 20 | 37491.2 / 29499.4 | -7991.8 | [-19223.2, +287.1] | 0.0894 | n.s. |
| golden | tool_tokens_total | 20 | 12922.2 / 12195.4 | -726.8 | [-2655.9, +994.5] | 0.6026 | n.s. |
| golden | n_calls | 20 | 5.7 / 5.0 | -0.8 | [-1.8, +0.2] | 0.1961 | n.s. |
| golden | invalid_calls | 20 | 0.1 / 0.0 | -0.1 | [-0.3, +0.0] | 1.0000 | n.s. |
| golden | empty_results | 20 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to ../data/bench/compare-claude-A1-vs-A0-v2.json
