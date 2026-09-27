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

### LFM2.5-2.6B-MLX-8bit vs LFM2.5-2.6B-MLX-8bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 128 | 0.906 / 0.938 | A1/B0=4, A0/B1=8 | — | 0.3877 | n.s. |
| overall | cited | 128 | 0.727 / 0.820 | A1/B0=12, A0/B1=24 | — | 0.0652 | n.s. |
| overall | gave_up | 128 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 128 | 30259.6 / 22876.7 | -7382.9 | [-12612.8, -1388.6] | 0.0000 | better |
| overall | tool_tokens_total | 128 | 31288.1 / 7189.6 | -24098.5 | [-31295.4, -17622.4] | 0.0000 | better |
| overall | max_prompt_tokens | 128 | 17571.8 / 9635.2 | -7936.6 | [-9290.8, -6586.5] | 0.0000 | better |
| overall | n_calls | 128 | 3.8 / 4.5 | +0.8 | [+0.1, +1.4] | 0.0001 | worse |
| overall | invalid_calls | 128 | 0.9 / 0.4 | -0.5 | [-0.8, -0.3] | 0.0002 | better |
| overall | empty_results | 128 | 0.5 / 0.6 | +0.1 | [-0.1, +0.3] | 0.2613 | n.s. |
| golden | found | 99 | 0.879 / 0.919 | A1/B0=4, A0/B1=8 | — | 0.3877 | n.s. |
| golden | cited | 99 | 0.697 / 0.818 | A1/B0=8, A0/B1=20 | — | 0.0357 | better |
| golden | gave_up | 99 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 99 | 32207.7 / 25833.7 | -6374.1 | [-12947.5, +1035.6] | 0.0000 | n.s. |
| golden | tool_tokens_total | 99 | 36207.0 / 7728.8 | -28478.2 | [-37700.5, -20227.5] | 0.0000 | better |
| golden | max_prompt_tokens | 99 | 17906.7 / 10314.0 | -7592.7 | [-9123.4, -6001.2] | 0.0000 | better |
| golden | n_calls | 99 | 4.0 / 4.9 | +0.9 | [+0.1, +1.7] | 0.0003 | worse |
| golden | invalid_calls | 99 | 1.1 / 0.4 | -0.6 | [-1.0, -0.3] | 0.0007 | better |
| golden | empty_results | 99 | 0.6 / 0.7 | +0.1 | [-0.2, +0.4] | 0.3498 | n.s. |
| new-books | found | 29 | 1.000 / 1.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | cited | 29 | 0.828 / 0.828 | A1/B0=4, A0/B1=4 | — | 1.0000 | n.s. |
| new-books | gave_up | 29 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 29 | 23609.2 / 12782.1 | -10827.1 | [-15074.8, -6616.7] | 0.0002 | better |
| new-books | tool_tokens_total | 29 | 14496.2 / 5349.0 | -9147.2 | [-11828.1, -6712.6] | 0.0000 | better |
| new-books | max_prompt_tokens | 29 | 16428.3 / 7317.9 | -9110.4 | [-11909.3, -6569.5] | 0.0000 | better |
| new-books | n_calls | 29 | 2.9 / 3.2 | +0.3 | [-0.2, +0.8] | 0.2322 | n.s. |
| new-books | invalid_calls | 29 | 0.3 / 0.1 | -0.2 | [-0.3, +0.0] | 0.1083 | n.s. |
| new-books | empty_results | 29 | 0.3 / 0.3 | +0.1 | [-0.1, +0.2] | 0.4652 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 256 | 0.891 / 0.895 | A1/B0=17, A0/B1=18 | — | 1.0000 | n.s. |
| overall | cited | 256 | 0.609 / 0.684 | A1/B0=35, A0/B1=54 | — | 0.0558 | n.s. |
| overall | gave_up | 256 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 256 | 23416.3 / 15346.5 | -8069.8 | [-11123.4, -4834.3] | 0.0000 | better |
| overall | tool_tokens_total | 256 | 21287.8 / 4918.1 | -16369.6 | [-20161.8, -12839.8] | 0.0000 | better |
| overall | max_prompt_tokens | 256 | 14791.7 / 6922.3 | -7869.3 | [-8749.6, -6983.6] | 0.0000 | better |
| overall | n_calls | 256 | 2.5 / 2.9 | +0.5 | [+0.1, +0.8] | 0.0000 | worse |
| overall | invalid_calls | 256 | 0.5 / 0.2 | -0.3 | [-0.4, -0.1] | 0.0001 | better |
| overall | empty_results | 256 | 0.3 / 0.3 | +0.0 | [-0.1, +0.2] | 0.3083 | n.s. |
| golden | found | 198 | 0.864 / 0.884 | A1/B0=14, A0/B1=18 | — | 0.5966 | n.s. |
| golden | cited | 198 | 0.611 / 0.702 | A1/B0=27, A0/B1=45 | — | 0.0444 | better |
| golden | gave_up | 198 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 198 | 24882.6 / 17222.9 | -7659.7 | [-11465.9, -3544.0] | 0.0000 | better |
| golden | tool_tokens_total | 198 | 23933.3 / 5306.0 | -18627.3 | [-23650.8, -14193.0] | 0.0000 | better |
| golden | max_prompt_tokens | 198 | 15029.0 / 7385.1 | -7643.9 | [-8701.6, -6598.3] | 0.0000 | better |
| golden | n_calls | 198 | 2.6 / 3.2 | +0.6 | [+0.2, +1.0] | 0.0000 | worse |
| golden | invalid_calls | 198 | 0.6 / 0.2 | -0.3 | [-0.5, -0.2] | 0.0003 | better |
| golden | empty_results | 198 | 0.3 / 0.4 | +0.0 | [-0.1, +0.2] | 0.4675 | n.s. |
| new-books | found | 58 | 0.983 / 0.931 | A1/B0=3, A0/B1=0 | — | 0.2500 | n.s. |
| new-books | cited | 58 | 0.603 / 0.621 | A1/B0=8, A0/B1=9 | — | 1.0000 | n.s. |
| new-books | gave_up | 58 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 58 | 18410.8 / 8941.1 | -9469.7 | [-11905.6, -7136.3] | 0.0000 | better |
| new-books | tool_tokens_total | 58 | 12256.5 / 3594.0 | -8662.5 | [-10219.6, -7247.7] | 0.0000 | better |
| new-books | max_prompt_tokens | 58 | 13981.5 / 5342.4 | -8639.0 | [-10262.4, -7179.1] | 0.0000 | better |
| new-books | n_calls | 58 | 2.0 / 2.1 | +0.2 | [-0.1, +0.4] | 0.2949 | n.s. |
| new-books | invalid_calls | 58 | 0.1 / 0.1 | -0.1 | [-0.2, +0.0] | 0.1083 | n.s. |
| new-books | empty_results | 58 | 0.1 / 0.2 | +0.1 | [-0.0, +0.1] | 0.2807 | n.s. |

Wrote JSON metrics to ../data/bench/compare-A1r-vs-A0r-LFM-v2.json
