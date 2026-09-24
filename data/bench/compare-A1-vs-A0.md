### Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B vs Qwen3.6-35B-A3B-OptiQ-4bit-REAP-19B

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.880 / 0.893 | A1/B0=7, A0/B1=9 | — | 0.8036 | n.s. |
| overall | cited | 150 | 0.800 / 0.840 | A1/B0=12, A0/B1=18 | — | 0.3616 | n.s. |
| overall | gave_up | 150 | 0.040 / 0.047 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 39802.1 / 20774.1 | -19028.0 | [-26094.5, -12342.4] | 0.0000 | better |
| overall | tool_tokens_total | 150 | 19172.5 / 6509.3 | -12663.2 | [-18912.2, -8177.5] | 0.0000 | better |
| overall | max_prompt_tokens | 150 | 17715.9 / 8755.2 | -8960.7 | [-10578.4, -7415.1] | 0.0000 | better |
| overall | n_calls | 150 | 2.3 / 3.0 | +0.7 | [+0.4, +1.0] | 0.0000 | worse |
| overall | invalid_calls | 150 | 0.1 / 0.1 | -0.0 | [-0.1, +0.0] | 0.3670 | n.s. |
| overall | empty_results | 150 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 0.2719 | n.s. |
| golden | found | 120 | 0.867 / 0.875 | A1/B0=7, A0/B1=8 | — | 1.0000 | n.s. |
| golden | cited | 120 | 0.792 / 0.833 | A1/B0=10, A0/B1=15 | — | 0.4244 | n.s. |
| golden | gave_up | 120 | 0.050 / 0.058 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 44343.4 / 22987.7 | -21355.7 | [-30229.5, -12964.5] | 0.0000 | better |
| golden | tool_tokens_total | 120 | 21195.3 / 7041.0 | -14154.3 | [-21814.5, -8683.4] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 18849.2 / 9353.4 | -9495.8 | [-11437.3, -7656.3] | 0.0000 | better |
| golden | n_calls | 120 | 2.5 / 3.2 | +0.7 | [+0.3, +1.1] | 0.0003 | worse |
| golden | invalid_calls | 120 | 0.1 / 0.1 | -0.1 | [-0.2, +0.1] | 0.3670 | n.s. |
| golden | empty_results | 120 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 0.5294 | n.s. |
| new-books | found | 30 | 0.933 / 0.967 | A1/B0=0, A0/B1=1 | — | 1.0000 | n.s. |
| new-books | cited | 30 | 0.833 / 0.867 | A1/B0=2, A0/B1=3 | — | 1.0000 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 21636.9 / 11919.5 | -9717.4 | [-13355.6, -6170.1] | 0.0000 | better |
| new-books | tool_tokens_total | 30 | 11081.3 / 4382.4 | -6698.9 | [-8533.3, -4679.9] | 0.0000 | better |
| new-books | max_prompt_tokens | 30 | 13182.7 / 6362.6 | -6820.1 | [-8768.3, -4696.7] | 0.0000 | better |
| new-books | n_calls | 30 | 1.6 / 2.2 | +0.6 | [+0.1, +1.0] | 0.0113 | worse |
| new-books | invalid_calls | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | empty_results | 30 | 0.1 / 0.0 | -0.1 | [-0.2, +0.0] | 1.0000 | n.s. |

### gemma-4-12B-it-qat-OptiQ-4bit vs gemma-4-12B-it-qat-OptiQ-4bit

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 150 | 0.787 / 0.867 | A1/B0=7, A0/B1=19 | — | 0.0290 | better |
| overall | cited | 150 | 0.760 / 0.840 | A1/B0=8, A0/B1=20 | — | 0.0357 | better |
| overall | gave_up | 150 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 150 | 12485.5 / 9925.0 | -2560.6 | [-3785.9, -1308.4] | 0.0001 | better |
| overall | tool_tokens_total | 150 | 77846.7 / 4385.1 | -73461.6 | [-81697.8, -65230.8] | 0.0000 | better |
| overall | max_prompt_tokens | 150 | 10933.0 / 5595.7 | -5337.3 | [-6198.4, -4445.9] | 0.0000 | better |
| overall | n_calls | 150 | 1.5 / 1.5 | -0.0 | [-0.2, +0.1] | 0.7399 | n.s. |
| overall | invalid_calls | 150 | 0.7 / 0.0 | -0.7 | [-0.7, -0.6] | 0.0000 | better |
| overall | empty_results | 150 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| golden | found | 120 | 0.775 / 0.858 | A1/B0=6, A0/B1=16 | — | 0.0525 | n.s. |
| golden | cited | 120 | 0.742 / 0.825 | A1/B0=7, A0/B1=17 | — | 0.0639 | n.s. |
| golden | gave_up | 120 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 120 | 12712.1 / 10352.3 | -2359.8 | [-3761.9, -891.6] | 0.0016 | better |
| golden | tool_tokens_total | 120 | 85271.2 / 4554.4 | -80716.9 | [-89370.2, -71640.3] | 0.0000 | better |
| golden | max_prompt_tokens | 120 | 11095.2 / 5758.4 | -5336.8 | [-6307.0, -4312.9] | 0.0000 | better |
| golden | n_calls | 120 | 1.6 / 1.6 | -0.0 | [-0.2, +0.1] | 0.6419 | n.s. |
| golden | invalid_calls | 120 | 0.7 / 0.0 | -0.7 | [-0.8, -0.6] | 0.0000 | better |
| golden | empty_results | 120 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |
| new-books | found | 30 | 0.833 / 0.900 | A1/B0=1, A0/B1=3 | — | 0.6250 | n.s. |
| new-books | cited | 30 | 0.833 / 0.900 | A1/B0=1, A0/B1=3 | — | 0.6250 | n.s. |
| new-books | gave_up | 30 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 30 | 11579.3 / 8215.7 | -3363.5 | [-5733.9, -965.2] | 0.0170 | better |
| new-books | tool_tokens_total | 30 | 48148.4 / 3708.2 | -44440.2 | [-62600.2, -27502.5] | 0.0000 | better |
| new-books | max_prompt_tokens | 30 | 10283.8 / 4944.6 | -5339.2 | [-7104.1, -3565.3] | 0.0001 | better |
| new-books | n_calls | 30 | 1.3 / 1.3 | +0.0 | [-0.2, +0.3] | 0.8336 | n.s. |
| new-books | invalid_calls | 30 | 0.4 / 0.0 | -0.4 | [-0.6, -0.2] | 0.0025 | better |
| new-books | empty_results | 30 | 0.0 / 0.0 | +0.0 | [+0.0, +0.0] | 1.0000 | n.s. |

### Pooled across model pairs

| Stratum | Metric | n | A / B | Δ B−A or discordants | 95% CI | p | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| overall | found | 300 | 0.833 / 0.880 | A1/B0=14, A0/B1=28 | — | 0.0436 | better |
| overall | cited | 300 | 0.780 / 0.840 | A1/B0=20, A0/B1=38 | — | 0.0247 | better |
| overall | gave_up | 300 | 0.020 / 0.023 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| overall | prompt_tokens_total | 300 | 26143.8 / 15349.5 | -10794.3 | [-14523.2, -7332.4] | 0.0000 | better |
| overall | tool_tokens_total | 300 | 48509.6 / 5447.2 | -43062.4 | [-49207.5, -36984.2] | 0.0000 | better |
| overall | max_prompt_tokens | 300 | 14324.4 / 7175.4 | -7149.0 | [-8080.2, -6234.4] | 0.0000 | better |
| overall | n_calls | 300 | 1.9 / 2.3 | +0.3 | [+0.2, +0.5] | 0.0002 | worse |
| overall | invalid_calls | 300 | 0.4 / 0.0 | -0.3 | [-0.4, -0.3] | 0.0000 | better |
| overall | empty_results | 300 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.4412 | n.s. |
| golden | found | 240 | 0.821 / 0.867 | A1/B0=13, A0/B1=24 | — | 0.0989 | n.s. |
| golden | cited | 240 | 0.767 / 0.829 | A1/B0=17, A0/B1=32 | — | 0.0444 | better |
| golden | gave_up | 240 | 0.025 / 0.029 | A1/B0=5, A0/B1=6 | — | 1.0000 | n.s. |
| golden | prompt_tokens_total | 240 | 28527.8 / 16670.0 | -11857.7 | [-16423.2, -7577.1] | 0.0000 | better |
| golden | tool_tokens_total | 240 | 53233.3 / 5797.7 | -47435.6 | [-54561.8, -40567.8] | 0.0000 | better |
| golden | max_prompt_tokens | 240 | 14972.2 / 7555.9 | -7416.3 | [-8528.4, -6344.6] | 0.0000 | better |
| golden | n_calls | 240 | 2.1 / 2.4 | +0.3 | [+0.1, +0.5] | 0.0018 | worse |
| golden | invalid_calls | 240 | 0.4 / 0.1 | -0.4 | [-0.5, -0.3] | 0.0000 | better |
| golden | empty_results | 240 | 0.0 / 0.0 | -0.0 | [-0.0, +0.0] | 0.7998 | n.s. |
| new-books | found | 60 | 0.883 / 0.933 | A1/B0=1, A0/B1=4 | — | 0.3750 | n.s. |
| new-books | cited | 60 | 0.833 / 0.883 | A1/B0=3, A0/B1=6 | — | 0.5078 | n.s. |
| new-books | gave_up | 60 | 0.000 / 0.000 | A1/B0=0, A0/B1=0 | — | 1.0000 | n.s. |
| new-books | prompt_tokens_total | 60 | 16608.1 / 10067.6 | -6540.5 | [-8877.2, -4213.1] | 0.0000 | better |
| new-books | tool_tokens_total | 60 | 29614.9 / 4045.3 | -25569.6 | [-35960.8, -16003.3] | 0.0000 | better |
| new-books | max_prompt_tokens | 60 | 11733.3 / 5653.6 | -6079.7 | [-7423.8, -4666.1] | 0.0000 | better |
| new-books | n_calls | 60 | 1.4 / 1.8 | +0.3 | [+0.0, +0.6] | 0.0155 | worse |
| new-books | invalid_calls | 60 | 0.2 / 0.0 | -0.2 | [-0.3, -0.1] | 0.0025 | better |
| new-books | empty_results | 60 | 0.0 / 0.0 | -0.0 | [-0.1, +0.0] | 1.0000 | n.s. |

Wrote JSON metrics to data/bench/compare-A1-vs-A0.json
