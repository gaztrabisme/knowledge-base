### LFM2.5-8B-A1B-MLX-8bit vs LFM2.5-8B-A1B-MLX-8bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.875 / 0.852 | A1/B0=13, A0/B1=10 | — | 0.6776 | n.s. |
| overall | cited | 128 | 0.492 / 0.547 | A1/B0=23, A0/B1=30 | — | 0.4101 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 16573.0 / 7816.4 | -8756.6 | [-11816.6, -6270.4] | 0.0000 | better |
| overall | tool_tokens_total | 128 | 11287.4 / 2646.6 | -8640.8 | [-10978.0, -6967.4] | 0.0000 | better |
| overall | max_prompt_tokens | 128 | 12011.6 / 4209.5 | -7802.1 | [-8971.4, -6733.3] | 0.0000 | better |
| overall | n_calls | 128 | 1.2 / 1.4 | +0.2 | [-0.0, +0.4] | 0.0367 | n.s. |
| overall | invalid_calls | 128 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 0.2249 | n.s. |
| overall | empty_results | 128 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 0.7893 | n.s. |
| golden | found | 99 | 0.848 / 0.848 | A1/B0=10, A0/B1=10 | — | 1.0000 | n.s. |
| golden | cited | 99 | 0.525 / 0.586 | A1/B0=19, A0/B1=25 | — | 0.4514 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 17557.4 / 8612.0 | -8945.4 | [-12681.1, -5776.8] | 0.0000 | better |
| golden | tool_tokens_total | 99 | 11659.6 / 2883.2 | -8776.4 | [-11836.1, -6618.6] | 0.0000 | better |
| golden | max_prompt_tokens | 99 | 12151.3 / 4456.2 | -7695.0 | [-9114.1, -6374.3] | 0.0000 | better |
| golden | n_calls | 99 | 1.2 / 1.5 | +0.3 | [-0.0, +0.5] | 0.0285 | n.s. |
| golden | invalid_calls | 99 | 0.1 / 0.0 | -0.0 | [-0.1, +0.0] | 0.2249 | n.s. |
| golden | empty_results | 99 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 1.0000 | n.s. |
| new-books | found | 29 | 0.966 / 0.862 | A1/B0=3, A0/B1=0 | — | 0.2500 | n.s. |
| new-books | cited | 29 | 0.379 / 0.414 | A1/B0=4, A0/B1=5 | — | 1.0000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 13212.4 / 5100.1 | -8112.3 | [-10252.0, -6294.0] | 0.0000 | better |
| new-books | tool_tokens_total | 29 | 10016.8 / 1839.0 | -8177.9 | [-9610.9, -6728.3] | 0.0000 | better |
| new-books | max_prompt_tokens | 29 | 11534.7 / 3367.0 | -8167.6 | [-9629.9, -6684.2] | 0.0000 | better |
| new-books | n_calls | 29 | 1.0 / 1.0 | +0.0 | [-0.2, +0.2] | 0.9442 | n.s. |
| new-books | invalid_calls | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.1] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.875 / 0.852 | A1/B0=13, A0/B1=10 | — | 0.6776 | n.s. |
| overall | cited | 128 | 0.492 / 0.547 | A1/B0=23, A0/B1=30 | — | 0.4101 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 16573.0 / 7816.4 | -8756.6 | [-11816.6, -6270.4] | 0.0000 | better |
| overall | tool_tokens_total | 128 | 11287.4 / 2646.6 | -8640.8 | [-10978.0, -6967.4] | 0.0000 | better |
| overall | max_prompt_tokens | 128 | 12011.6 / 4209.5 | -7802.1 | [-8971.4, -6733.3] | 0.0000 | better |
| overall | n_calls | 128 | 1.2 / 1.4 | +0.2 | [-0.0, +0.4] | 0.0367 | n.s. |
| overall | invalid_calls | 128 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 0.2249 | n.s. |
| overall | empty_results | 128 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 0.7893 | n.s. |
| golden | found | 99 | 0.848 / 0.848 | A1/B0=10, A0/B1=10 | — | 1.0000 | n.s. |
| golden | cited | 99 | 0.525 / 0.586 | A1/B0=19, A0/B1=25 | — | 0.4514 | n.s. |
| golden | gave_up | 99 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 17557.4 / 8612.0 | -8945.4 | [-12681.1, -5776.8] | 0.0000 | better |
| golden | tool_tokens_total | 99 | 11659.6 / 2883.2 | -8776.4 | [-11836.1, -6618.6] | 0.0000 | better |
| golden | max_prompt_tokens | 99 | 12151.3 / 4456.2 | -7695.0 | [-9114.1, -6374.3] | 0.0000 | better |
| golden | n_calls | 99 | 1.2 / 1.5 | +0.3 | [-0.0, +0.5] | 0.0285 | n.s. |
| golden | invalid_calls | 99 | 0.1 / 0.0 | -0.0 | [-0.1, +0.0] | 0.2249 | n.s. |
| golden | empty_results | 99 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 1.0000 | n.s. |
| new-books | found | 29 | 0.966 / 0.862 | A1/B0=3, A0/B1=0 | — | 0.2500 | n.s. |
| new-books | cited | 29 | 0.379 / 0.414 | A1/B0=4, A0/B1=5 | — | 1.0000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 13212.4 / 5100.1 | -8112.3 | [-10252.0, -6294.0] | 0.0000 | better |
| new-books | tool_tokens_total | 29 | 10016.8 / 1839.0 | -8177.9 | [-9610.9, -6728.3] | 0.0000 | better |
| new-books | max_prompt_tokens | 29 | 11534.7 / 3367.0 | -8167.6 | [-9629.9, -6684.2] | 0.0000 | better |
| new-books | n_calls | 29 | 1.0 / 1.0 | +0.0 | [-0.2, +0.2] | 0.9442 | n.s. |
| new-books | invalid_calls | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 29 | 0.0 / 0.0 | +0.0 | [+0.0, +0.1] | 1.0000 | n.s. |

Wrote JSON metrics to ../data/bench/compare-A1r-vs-A0r-LFM8B-v2.json
