# EO Land-Cover Segmentation & the SAM Lineage for Edge

Synthesis for an on-orbit land-cover segmentation system (landmass / ocean / forest / cloud) targeting Jetson-class hardware, where energy is the dominant constraint. Hardware envelope spans the original Jetson Nano (Maxwell, ~0.5 TFLOPS FP16, 4 GB shared LPDDR4, ~5–10 W) up to the Orin Nano (~40 TOPS INT8, 8 GB, ~7–15 W). The central question: adapt a SAM-family foundation model in orbit, or train a small task-specific net and use SAM only on the ground? The evidence points firmly to the latter.

## The SAM lineage: SAM, SAM2, SAM3 (and 3.1)

**SAM (Segment Anything, Meta, April 2023)** established the promptable-segmentation paradigm: an image encoder produces an embedding once, then a lightweight prompt encoder + mask decoder turn points/boxes into masks cheaply. Three encoder scales: ViT-B (91M), ViT-L (308M), ViT-H (~632–636M); the mask decoder is only ~3.9M. Input 1024×1024. License Apache 2.0. Critically, SAM is **class-agnostic** — it segments *things*, not *land-cover classes*. It will happily carve an image into regions but cannot tell you "ocean" vs "forest" without an added classification head or post-hoc labeling. ([SAM RS survey, arXiv:2306.16623](https://arxiv.org/pdf/2306.16623); [Roboflow SAM guide](https://blog.roboflow.com/how-to-use-segment-anything-model-sam/))

**SAM2 (Aug 2024)** swapped the single-scale ViT for a multi-scale hierarchical **Hiera** encoder and added video/memory. Four sizes with real published params and A100 speeds: Tiny 38.9M (~47 FPS), Small 46M, Base+ 80M (~43.8 FPS), Large 224.4M (~30 FPS). Trained on 11M images / 11B masks. Apache 2.0. The Tiny variant is the only SAM-lineage model whose parameter count is even in Jetson territory, but those FPS are A100 numbers — not edge. ([SAM2 paper, arXiv:2408.00714](https://arxiv.org/html/2408.00714v2); [facebookresearch/sam2](https://github.com/facebookresearch/sam2))

**SAM3 (Meta, November 19, 2025)** is real and its key novelty is **Promptable Concept Segmentation (PCS)**: give it a short noun phrase ("red baseball cap") or an image exemplar and it detects, segments, and tracks *all* instances — open-vocabulary, no per-object clicking. Architecture fuses a **Meta Perception Encoder** (text+image), a **DETR-based detector** with a decoupled presence head, and a SAM2-style memory tracker. It reports a 2× gain over prior systems on image/video PCS. Weights, fine-tuning code, and the **SA-Co** benchmark released under an open license; a "Segment Anything Playground" and companion **SAM 3D** also shipped. ([Ultralytics SAM3](https://docs.ultralytics.com/models/sam-3); [Meta research page](https://ai.meta.com/research/publications/sam-3-segment-anything-with-concepts/); [Roboflow](https://blog.roboflow.com/what-is-sam3/))

**SAM3.1 (March 27, 2026)** is a drop-in upgrade adding "object multiplexing" (track up to 16 objects per forward pass) and global reasoning, doubling video throughput from 16→32 FPS on a single H100. ([Meta blog](https://ai.meta.com/blog/segment-anything-model-3/))

**The decisive edge fact about SAM3:** Meta benchmarks it at **30 ms for a single image with 100+ objects on an H200 GPU**, and SAM3.1's "more accessible hardware" language explicitly means smaller *GPUs (H100)*, not phones or Jetsons. Meta publishes **no parameter count, no model size, and zero edge/mobile deployment claim** for SAM3. The Perception-Encoder + DETR + tracker stack is heavy. **SAM3 cannot run on any Jetson** and is not designed to — it is a datacenter/cloud model. For EO land-cover it is attractive as a ground-side *labeler* (its text-prompt PCS can auto-mask "forest", "water", "cloud"), but not as an in-orbit segmenter.

## Efficient SAM variants for the edge

These distill or redesign SAM's encoder for real-time use. Params and benchmarks below are from the efficient-SAM survey ([arXiv:2410.04960](https://arxiv.org/html/2410.04960v2)) and primary repos.

- **MobileSAM** — replaces ViT-H encoder with a TinyViT via decoupled distillation. ~9.7M total params, **≈66× smaller than SAM**, mIoU ≈0.74 (only ~2–4 pts below full SAM). The de-facto baseline for "SAM on a small device." ([Ultralytics MobileSAM](https://docs.ultralytics.com/models/mobile-sam/))
- **NanoSAM (NVIDIA)** — distilled from MobileSAM, encoder swapped to a pure-CNN **ResNet18**, built end-to-end in **TensorRT FP16**. This is the *only* SAM variant purpose-built and benchmarked on Jetson. On **Jetson AGX Orin**: image encoder **27 ms** (vs MobileSAM 146 ms — a 5× speedup), full pipeline real-time, throughput ~27.9 img/s, mIoU 0.706 (vs 0.728 MobileSAM) on COCO with GT-box prompts. ([NVIDIA-AI-IOT/nanosam](https://github.com/NVIDIA-AI-IOT/nanosam))
- **EdgeSAM** — fully-CNN encoder distilled from ViT-H with prompt-in-the-loop distillation. ~259 ms CPU, 713 ms on edge device; >37× faster than SAM on a 2080 Ti, >7× faster than MobileSAM on iPhone. ([arXiv:2312.06660](https://arxiv.org/pdf/2312.06660))
- **TinySAM** — TinyViT-5M encoder + hierarchical "everything" acceleration + **8-bit PTQ**. Footprint **60 MB FP32 / 30 MB INT8**, ~2× faster than EfficientSAM, beats MobileSAM by ~1–2 AP. The INT8 story makes it the most quantization-friendly. ([arXiv:2312.13789](https://arxiv.org/html/2312.13789v3))
- **EfficientViT-SAM-L0** — fastest in the survey: ~30× GPU / ~50× CPU acceleration vs SAM-H with little accuracy loss. ([arXiv:2402.05008](https://arxiv.org/html/2402.05008v2))
- **EfficientSAM (Ti/S)** — SAMI masked-pretraining; strong accuracy but very expensive to train (400 ep ImageNet + 5 ep SA-1B) and not well-optimized on mobile accelerators. ([arXiv:2312.00863](https://arxiv.org/pdf/2312.00863))
- **FastSAM** — YOLOv8-seg instance segmentation trained on 2% of SA-1B; ~7× larger and ~5× slower than MobileSAM. Convenient but not the smallest.

**Edge-fit read:** NanoSAM and TinySAM are the only two with a credible orbit-class footprint. NanoSAM is TensorRT-native on Orin (proven 27 ms encoder); TinySAM is the INT8/30 MB champion. Even these remain **promptable, class-agnostic** segmenters — they still need a prompt source and a classification step to produce land-cover maps. None matches the energy-per-frame of a purpose-built 4-class net.

## Purpose-built land-cover segmentation nets

For a fixed ~4-class problem (landmass/ocean/forest/cloud), a small task-specific semantic-segmentation net is far more efficient than adapting SAM, because it outputs class maps directly with no prompt loop.

- **U-Net** — encoder-decoder with skip connections; the workhorse of RS segmentation, precise pixel labels, trains well on modest data. ([Nature Sci. Rep. land-cover U-Net](https://www.nature.com/articles/s41598-024-84795-1))
- **DeepLabv3+** — atrous spatial pyramid pooling for multi-scale context. With an Xception backbone it is 208.7 MB; **swapping in MobileNetV2 drops it to 22.19 MB** (~10× smaller) at a ~4.4-point mIoU cost — recoverable with attention/HDC modules. ([Improved lightweight DeepLabv3+, Springer](https://link.springer.com/article/10.1007/s40747-023-01304-z))
- **SegFormer (incl. B0)** — hierarchical transformer + lightweight all-MLP decoder; B0 is a strong small model, though one head-to-head Five-Billion-Pixels study found SegFormer struggled with edge sharpness vs CNNs. ([Five-Billion-Pixels benchmark, Nature Sci. Rep.](https://www.nature.com/articles/s41598-024-84795-1))
- **PSPNet** — pyramid pooling for global context; heavier, less edge-friendly.
- **Lightweight backbones (MobileNetV2/V3)** — depthwise-separable convolutions factorize standard conv into depthwise + 1×1 pointwise, the core efficiency lever; ideal for a small EO net and trivially INT8-quantizable.

**The case for a small net over SAM:** For 4 classes, a MobileNetV2-DeepLabv3+ or a small U-Net is a few million params, ~20 MB, INT8-quantizable, runs at video rate on Orin Nano in well under the SAM-variant energy budget, and emits class maps in one pass. SAM's promptable generality is wasted on a closed 4-class set and adds an unnecessary prompt-generation stage.

## SAM as ground-side teacher → small distilled net in orbit

This pattern is **validated in the 2025–2026 RS literature**, and one paper targets exactly our scenario:

- **Mask-CDKD** — "a source-free and label-free cross-domain knowledge distillation framework from SAM for **satellite onboard** VHR land-cover mapping." It distills SAM's representations into a lightweight student explicitly because foundation models are "prohibitively expensive for direct deployment" on satellites constrained by "computation, memory, and power." Uses gated dynamic multi-scale fusion to fight the natural-image→RS domain shift, plus single-stage bidirectional distillation. This is precisely the "SAM teacher on the ground, compact student in orbit" architecture. ([ISPRS J., ScienceDirect S0924271626001486](https://www.sciencedirect.com/science/article/abs/pii/S0924271626001486))
- **RS-MTDF** — multi-teacher distillation/fusion from vision foundation models guiding semi-supervised RS segmentation; tops LoveDA across label ratios.
- **Baltimore Atlas / UAMT** — uses **SAM2** for pseudo-labeling ultra-high-res land cover with an entropy-based Uncertainty-Aware Mean Teacher to filter noisy pseudo-labels. ([arXiv:2506.15565](https://arxiv.org/pdf/2506.15565))
- General precedent: EMA mean-teacher + pseudo-label distillation is a mature RS technique (Yuan et al. 2023 mutual KD; Chen et al. semi-supervised urban mapping).

**Read:** Auto-labeling with SAM/SAM3 on the ground + distilling into a tiny onboard student is not speculative — it is an active, published paradigm with a satellite-onboard exemplar. SAM3's text-prompt PCS strengthens the labeling side: you can auto-generate "ocean"/"forest"/"cloud" masks at scale without manual clicking, then distill.

## EO datasets for land-cover

- **LoveDA** — 3,338 aerial images (0.3 m), 7 classes, 86,516 objects, urban+rural domains for domain-adaptation. ([NeurIPS 2021](https://datasets-benchmarks-proceedings.neurips.cc/paper/2021/file/4e732ced3463d06de0ca9a15b6153677-Paper-round2.pdf))
- **OpenEarthMap** — 97 global regions, 8 classes; best pre-training transfer of the three (>20% initial-IoU lift fine-tuning to LoveDA). ([arXiv:2210.10732](https://ar5iv.labs.arxiv.org/html/2210.10732))
- **DeepGlobe Land Cover** — 2448×2448 tiles, 7 classes; classic FCN-era benchmark.
- **Five-Billion-Pixels** — 150 Gaofen-2 images (4 m), **24 classes**, 5B+ labeled pixels; ships with a UDA method generalizing to Sentinel-2/PlanetScope. ([project page](https://x-ytong.github.io/project/Five-Billion-Pixels.html))
- **SEN12MS** — 180,662 SAR+optical+MODIS triplets, 10 m, ~10 coarse classes; global, multi-sensor, but weak MODIS labels. ([arXiv:1906.07789](https://arxiv.org/pdf/1906.07789))
- **EuroSAT** — 27,000 Sentinel-2 patches, 13 bands, 10 classes; **scene classification** (not pixel segmentation), useful for pretraining/sanity checks. ([study set, arXiv:2502.10669](https://arxiv.org/pdf/2502.10669))

For a coarse ocean/land/forest/cloud task, **OpenEarthMap** (clean transfer, global) and **LoveDA** (domain robustness) are the best fine-tuning sources; SEN12MS adds ocean/water + SAR fusion at the cost of label precision; Five-Billion-Pixels gives the richest natural-class taxonomy to collapse down to 4.

## Energy & Jetson-fit summary

| Model class | Params / size | Fits 4 GB? | INT8? | Edge speed (best evidence) | Verdict for orbit |
|---|---|---|---|---|---|
| SAM3 / 3.1 | unpublished, large | No | N/A | 30 ms @ H200 (datacenter) | Ground only |
| SAM2-Tiny | 38.9M | Tight | partial | 47 FPS @ A100 (not edge) | No |
| MobileSAM | ~9.7M | Yes | partial | 146 ms encoder @ AGX Orin | Marginal |
| **NanoSAM** | ResNet18 enc | Yes | FP16 (TRT) | **27 ms encoder @ AGX Orin, ~28 img/s** | Possible (if prompts needed) |
| **TinySAM** | 5M / 30 MB INT8 | Yes | **Yes (8-bit)** | ~2× EfficientSAM | Possible |
| **MobileNetV2-DeepLabv3+ / small U-Net** | few M / ~20 MB | **Yes** | **Yes** | video-rate @ Orin, 1-pass class maps | **Best fit** |

Key energy facts: SAM3 is a datacenter model with no edge path. Among SAM variants only NanoSAM (TensorRT FP16, 27 ms on AGX Orin) and TinySAM (30 MB INT8) are orbit-plausible — but both are promptable, class-agnostic, and still need a prompt + classification stage, inflating energy-per-map. A purpose-built 4-class CNN with a MobileNet backbone is smaller, fully INT8-quantizable, emits class maps in a single forward pass, and therefore wins decisively on joules-per-frame — the metric that matters in orbit. Note the original Jetson **Nano** (Maxwell, no INT8 tensor cores, 4 GB) is much tighter than **Orin Nano** (40 TOPS INT8); even NanoSAM's headline numbers are AGX Orin, so on a Nano-class part the small dedicated net is effectively the only viable option.

## Recommended approach for our seg task

**In orbit:** deploy a small, task-specific semantic-segmentation net — **MobileNetV2/V3-backbone DeepLabv3+ or a compact U-Net**, trained for the fixed ~4 classes (landmass / ocean / forest / cloud), exported to **TensorRT INT8**. This maximizes joules-per-inference efficiency, fits the 4 GB Nano envelope, and produces class maps directly with no prompt loop. Do **not** run any SAM-family model in orbit — SAM3 is impossible there, and even NanoSAM/TinySAM are less energy-efficient than a dedicated 4-class net while adding a prompt stage.

**On the ground (teacher):** use **SAM3's text-prompt Promptable Concept Segmentation** to auto-label large volumes of EO imagery (prompt "ocean", "forest", "cloud", "land") — optionally refined with exemplar prompts — building a pseudo-labeled corpus cheaply and at open-vocabulary scale. Then apply **cross-domain knowledge distillation in the Mask-CDKD style** (source-free, label-free, multi-scale, EMA mean-teacher with uncertainty-filtered pseudo-labels à la Baltimore Atlas/UAMT) to compress that knowledge into the onboard student. Fine-tune/validate on **OpenEarthMap + LoveDA** (and SEN12MS for ocean/SAR robustness), harmonizing their 7–8 class taxonomies down to the 4 target classes.

This split — **heavy promptable foundation model as a ground-side label factory + a distilled, INT8, single-pass CNN in orbit** — is the only configuration in the literature that simultaneously satisfies the open-vocabulary labeling need and the hard on-orbit energy budget, and it has a published satellite-onboard precedent (Mask-CDKD).
