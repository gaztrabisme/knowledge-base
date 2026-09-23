# Repository Analyses — On-Orbit EO AI Stack

This document analyzes the most relevant open-source repositories for a Jetson-class on-orbit Earth-observation payload doing cloud-cover gating + land/ocean/forest segmentation, energy-first. **Ranked shortlist for our use case:** (1) **NanoSAM** — the only SAM variant with a verified Jetson Orin Nano TensorRT path (27 ms full pipeline) and the cleanest INT8/FP16 design to mine; (2) **jetson-inference** — the reference deployment runtime, `segNet` + FCN-ResNet18 runs on the *original 4GB Nano*, the closest match to our low-power segmentation gate; (3) **segmentation_models.pytorch** — our training backbone, MobileNet/MobileOne encoders + ONNX export, MIT; (4) **omnicloudmask** — modern 4-class cloud segmentation, MIT, design + weights minable; (5) **MobileSAM** — 9.66M-param Apache-2.0 SAM, the architecture NanoSAM distills from; (6) **torch2trt** — the PyTorch→TensorRT bridge we'll use regardless; (7) **TorchGeo** — multispectral pretrained weights + RS data pipeline, MIT; (8) **s2cloudless** — the lightest cloud detector (LightGBM, runs on a microcontroller-class core), great low-power baseline; (9) **FastSAM** — fast but heavy (68M) and license-ambiguous; (10) **EfficientSAM** — strong accuracy, Apache-2.0, but no edge path yet. License traps to watch: **EdgeSAM (NTU S-Lab, non-commercial)**, **Cloud-Net (GPL-3.0)**, **s2cloudless (CC-BY-SA, copyleft-ish)**, **LoveDA (CC-BY-NC, non-commercial data)**.

## NanoSAM

- **Repo & URL**: NVIDIA-AI-IOT/nanosam — https://github.com/NVIDIA-AI-IOT/nanosam
- **Maturity**: ~891 stars, 303 commits. Maintained by NVIDIA's IOT team but commit cadence has slowed; treat as a stable reference rather than an actively-evolving project. Built on SAM + MobileSAM.
- **What it does**: A SAM variant purpose-built to run real-time on Jetson. It distills the MobileSAM image encoder into a ResNet18 backbone and pairs it with the MobileSAM mask decoder, then ships TensorRT engines for both.
- **Model / architecture & size**: Image encoder = ResNet18, built in FP16; mask decoder = MobileSAM decoder in FP32. Distilled on unlabeled images (no SAM ground-truth needed). Framework: **TensorRT** engines, with PyTorch + torch2trt for the build step.
- **License**: **Apache-2.0** — permissive, commercial-safe.
- **Jetson / edge-fit verdict**: This is the standout. Full-pipeline latency **27 ms on Jetson Orin Nano**, 8.1 ms on AGX Orin (vs MobileSAM 146 ms / 39 ms). mIoU 0.706 vs MobileSAM 0.728 — small accuracy cost for ~5x speedup. Targets Orin Nano (8GB) explicitly; the original 4GB Nano is not a documented target (TensorRT version + memory may need work).
- **Reuse value for us**: **High — mine the design and the recipe.** The ResNet18-distill-then-TensorRT pattern is exactly our energy-first playbook. We likely don't want SAM-style promptable segmentation for land/ocean/forest (that's a fixed-class job), but the distillation-to-CNN-then-TRT pipeline and the FP16-encoder/FP32-decoder split are directly transferable. Take the build scripts and torch2trt usage, not necessarily the weights.

## jetson-inference

- **Repo & URL**: dusty-nv/jetson-inference — https://github.com/dusty-nv/jetson-inference
- **Maturity**: ~8.9k stars, 2,241 commits, MIT. The canonical NVIDIA Jetson inference library; actively kept current through JetPack 6. Very mature, large community.
- **What it does**: A TensorRT-based inference + vision library exposing `imageNet`, `detectNet`, `segNet`, `poseNet` etc. from C++ or Python. `segNet` does real-time semantic segmentation on-device; PyTorch is used for the training/transfer-learning side.
- **Model / architecture & size**: Bundled segmentation uses **FCN-ResNet18** at multiple resolutions (Cityscapes 512x256→2048x1024, DeepScene, Pascal VOC, SUN RGB-D). FCN-ResNet18 is small (~tens of MB) and INT8/FP16-friendly via TensorRT. Legacy FCN-AlexNet models included (incl. an **Aerial-FPV** segmentation set).
- **License**: **MIT** — fully permissive.
- **Jetson / edge-fit verdict**: Best 4GB fit in this list. **Explicitly supports the original Jetson Nano Developer Kit (4GB, JetPack 4.2+)** through to Orin Nano. FCN-ResNet18 segmentation is the reference real-time-on-Nano workload. TensorRT INT8/FP16 paths are first-class.
- **Reuse value for us**: **High — adopt the runtime + mine the segmentation recipe.** This is the most defensible base for our land/ocean/forest gate: FCN-ResNet18 is cheap, proven on 4GB, and the transfer-learning tooling lets us retrain on EO classes. We'd take the segNet TensorRT inference path and the training scripts; swap their datasets for our 3-class EO labels. The Aerial-FPV precedent shows the pipeline already handles overhead imagery.

## segmentation_models.pytorch

- **Repo & URL**: qubvel-org/segmentation_models.pytorch (SMP) — https://github.com/qubvel-org/segmentation_models.pytorch
- **Maturity**: ~11.6k stars, v0.5.0 (Apr 2025), 737 commits. Actively maintained, the de-facto PyTorch segmentation library.
- **What it does**: Provides 12 segmentation architectures (Unet, Unet++, FPN, PSPNet, DeepLabV3/V3+, UPerNet, Segformer, DPT…) on top of 800+ pretrained encoders (incl. all of `timm`). You pick architecture + backbone and get a standard `nn.Module`.
- **Model / architecture & size**: Fully configurable — pair Unet/FPN with **MobileNet / MobileOne** encoders for edge, or shrink via `encoder_depth`. Framework: PyTorch; **ONNX export + torchscript/trace/compile friendly** with a dedicated export notebook.
- **License**: **MIT** (note: a few files carry other licenses — check per-file before shipping weights, but the core library is clean).
- **Jetson / edge-fit verdict**: Indirect — it doesn't ship TensorRT, but its MobileNet/MobileOne encoders are explicitly positioned for "real-time inference on edge devices," and ONNX export feeds straight into torch2trt / TensorRT for the Jetson leg. A Unet-MobileNet exported to INT8 is a realistic 4GB-Nano segmentation model.
- **Reuse value for us**: **High — adopt as the training backbone.** This is almost certainly where we build and train our land/ocean/forest segmenter: Unet or FPN + a MobileOne/MobileNetV3 encoder, trained on EO data, exported to ONNX, then TensorRT'd. We take the library wholesale (MIT permits it) and the export workflow.

## omnicloudmask

- **Repo & URL**: DPIRD-DMA/OmniCloudMask — https://github.com/DPIRD-DMA/OmniCloudMask
- **Maturity**: ~176 stars, 221 commits, MIT, published paper (ScienceDirect). Smaller but actively developed; pip + conda-forge distributed.
- **What it does**: Fast, sensor-agnostic cloud + cloud-shadow segmentation needing only Red/Green/NIR bands at 10-50m (down to 5m). Validated on Sentinel-2, Landsat 8, PlanetScope, Maxar. Outputs the **CloudSEN12 4-class scheme** (0=Clear, 1=Thick Cloud, 2=Thin Cloud, 3=Cloud Shadow).
- **Model / architecture & size**: PyTorch segmentation model (architecture not stated on the repo front page — needs a dive into the `omnicloudmask`/benchmarking dirs; trained on CloudSEN12+). Patch-based multi-threaded inference; CUDA/MPS/CPU. Param count not published front-and-center.
- **License**: **MIT** — permissive, weights reusable.
- **Jetson / edge-fit verdict**: No Jetson benchmarks published, but the design (RGB+NIR only, patch-based, CPU-capable) is edge-friendly and the MIT weights are directly portable. Would need our own ONNX→TensorRT pass + an fps measurement on Orin Nano.
- **Reuse value for us**: **High for the cloud-gate — mine design + weights + class scheme.** This is the most modern, permissively-licensed cloud detector here. The 3-band (R/G/NIR) input requirement is attractive for a low-power sensor. We'd take the 4-class CloudSEN12 labeling convention, potentially the weights as a teacher for distillation, and the patch-tiling inference approach. Strong candidate to seed our cloud-cover gating stage.

## MobileSAM

- **Repo & URL**: ChaoningZhang/MobileSAM — https://github.com/ChaoningZhang/MobileSAM
- **Maturity**: ~5.8k stars, 185 commits, Apache-2.0. Well-known, widely forked; the lineage parent of NanoSAM and several edge SAMs.
- **What it does**: Makes SAM lightweight by replacing the ViT-H image encoder with a Tiny-ViT, keeping the original mask decoder. Promptable segment-anything at a fraction of the cost.
- **Model / architecture & size**: Image encoder **Tiny-ViT, 5M params** (vs ViT-H 611M); mask decoder 3.876M; **whole pipeline 9.66M params**. Encoder ~8ms / decoder ~4ms → **12ms** on a GPU. PyTorch + **ONNX export** script; no native TensorRT (NanoSAM provides that).
- **License**: **Apache-2.0** — clean.
- **Jetson / edge-fit verdict**: Not directly benchmarked on Jetson here, but NanoSAM's table shows MobileSAM at 146ms on Orin Nano (full pipeline) — usable but ~5x slower than NanoSAM. It's the FP32/ONNX reference; for our hardware you'd go NanoSAM's distilled route instead.
- **Reuse value for us**: **Medium — mine the architecture, use as a distillation teacher.** We probably don't ship promptable SAM on-orbit, but MobileSAM is the clean Apache-2.0 source that NanoSAM distills. If we ever want lightweight promptable segmentation (e.g., operator-in-the-loop ground tooling), this is the base. For the fixed-class on-orbit job, its value is as a design reference and teacher network.

## torch2trt

- **Repo & URL**: NVIDIA-AI-IOT/torch2trt — https://github.com/NVIDIA-AI-IOT/torch2trt
- **Maturity**: ~4.9k stars, v0.5.0 (May 2024), 1,203 commits, MIT. Maintained by NVIDIA but with an acknowledged ~300-issue backlog and "limited coverage of TensorRT/PyTorch" caveat.
- **What it does**: Converts PyTorch modules to TensorRT engines with a single `torch2trt(model, [x])` call, using the TensorRT Python API. Extensible via custom Python-registered layer converters.
- **Model / architecture & size**: N/A — it's tooling, not a model. Outputs TensorRT engines (INT8/FP16/FP32).
- **License**: **MIT** — permissive.
- **Jetson / edge-fit verdict**: Built for Jetson (Nano/TX2/Xavier topic tags; Nano + Xavier benchmarks). It's the conversion glue NanoSAM already depends on. Caveat: coverage gaps mean exotic layers may need a hand-written converter or an ONNX→trtexec fallback.
- **Reuse value for us**: **Medium-high — adopt as a tool.** We'll need *some* PyTorch→TensorRT bridge for the segmentation gate; torch2trt is the lightest and NanoSAM already uses it. Expect to fall back to the ONNX→`trtexec` path for layers it doesn't cover. Take it as infrastructure, not as design.

## TorchGeo

- **Repo & URL**: microsoft/torchgeo — https://github.com/microsoft/torchgeo
- **Maturity**: ~4.1k stars, **v0.9.0 (Feb 2026)** — very actively maintained, 3,179 commits, MIT. Microsoft-backed.
- **What it does**: A PyTorch domain library for geospatial ML: datasets, samplers, transforms, and pretrained models, with CRS/resolution auto-matching. Covers classification, segmentation, detection, change detection. Lightning integration for trainers.
- **Model / architecture & size**: `SemanticSegmentationTask` (e.g. U-Net + ResNet-50). Notably the **first library with weights pretrained on multispectral sensors** — e.g. `ResNet18_Weights.SENTINEL2_ALL_MOCO` (Sentinel-2 self-supervised), usable through timm. Framework: PyTorch + Lightning.
- **License**: **MIT** — clean.
- **Jetson / edge-fit verdict**: A training/data-pipeline library, not an edge runtime — no on-device deployment notes. Its value is upstream: multispectral pretrained backbones that transfer better to EO than ImageNet, which you'd then export and TensorRT yourself.
- **Reuse value for us**: **Medium-high — mine the data pipeline + multispectral weights.** The Sentinel-2-pretrained ResNet encoders are a meaningfully better init for land/ocean/forest than ImageNet, and the geospatial dataset/sampler tooling saves us building tiling/CRS handling from scratch. We take the pretrained backbone + data loaders, then train in SMP and deploy via jetson-inference/TensorRT.

## s2cloudless

- **Repo & URL**: sentinel-hub/sentinel2-cloud-detector — https://github.com/sentinel-hub/sentinel2-cloud-detector
- **Maturity**: ~488 stars, v1.7.3 (Sep 2024), 150 commits. Maintained by Sentinel Hub; stable and widely used as a baseline.
- **What it does**: Single-scene, pixel-based cloud detector for Sentinel-2. Validated against 9 other algorithms across 4 datasets and found on the Pareto front each time. Masks are precomputed as a Sentinel Hub layer.
- **Model / architecture & size**: **LightGBM gradient-boosted decision trees** — not a neural net. Inputs 10 S2 bands (B01,B02,B04,B05,B08,B8A,B09,B10,B11,B12). Model file is tiny (a serialized GBDT, on the order of MBs or less). Framework: Python + LightGBM.
- **License**: **CC-BY-SA-4.0** — ⚠️ a copyleft-flavored license unusual for code; ShareAlike could obligate us to license derivatives alike. Verify with legal before embedding the model in a closed payload.
- **Jetson / edge-fit verdict**: Extraordinarily light — a GBDT runs on a microcontroller-class core with near-zero power, no GPU needed. The cheapest possible cloud-gate energy-wise. The constraint is it needs 10 specific spectral bands, which assumes a multispectral sensor.
- **Reuse value for us**: **Medium — mine the design/approach for an ultra-low-power gate.** If our payload has the multispectral bands and we want the absolute minimum-energy cloud gate, a GBDT-over-bands beats any CNN on power. We'd take the *approach* (feature-per-band → tree classifier) and likely retrain our own to dodge the CC-BY-SA ShareAlike obligation rather than ship their model.

## FastSAM

- **Repo & URL**: CASIA-IVA-Lab/FastSAM — https://github.com/CASIA-IVA-Lab/FastSAM
- **Maturity**: ~8.4k stars; last meaningful update mid-2024, training/val code release Sep 2023. Popular but cadence has slowed.
- **What it does**: Reframes segment-anything as YOLOv8-seg instance segmentation trained on 2% of SA-1B. Two sizes: FastSAM (YOLOv8x) and FastSAM-s (YOLOv8s).
- **Model / architecture & size**: **68M params** (YOLOv8x variant) — ~7x heavier than MobileSAM. 40ms constant inference on an RTX 3090; 2608 MB GPU memory. PyTorch; a community FastSAM_Awesome_TensorRT exists.
- **License**: ⚠️ **Ambiguous** — the repo metadata says **AGPL-3.0** (inherited from Ultralytics YOLOv8) while the README claims Apache-2.0. AGPL is a serious trap for an embedded/served product. Treat as AGPL until proven otherwise.
- **Jetson / edge-fit verdict**: Marginal. 68M params + 2.6GB GPU is heavy for a 4GB Nano; no official Jetson benchmarks. The YOLOv8-seg base means it *could* be TensorRT'd, but it's the wrong weight class for our energy budget.
- **Reuse value for us**: **Low.** Too heavy and license-encumbered. The only minable idea is "instance segmentation as a fast CNN" — but MobileSAM/NanoSAM dominate it on both size and license. Skip unless we specifically want YOLOv8-seg, in which case go to Ultralytics directly and resolve the AGPL question.

## EfficientSAM

- **Repo & URL**: yformer/EfficientSAM — https://github.com/yformer/EfficientSAM
- **Maturity**: ~2.5k stars, 96 commits, Apache-2.0. Meta-affiliated research release; moderately active.
- **What it does**: Uses SAM-leveraged masked image pretraining (SAMI) to train efficient SAM backbones, recovering more accuracy than naive lightweight encoders. Variants: EfficientSAM-S (ViT-S) and EfficientSAM-Ti (ViT-Ti).
- **Model / architecture & size**: ViT-S and ViT-Tiny backbones (param counts not stated on the repo front page; Ti is the smaller, ships as `efficient_sam_vitt.pt`). PyTorch with **TorchScript + ONNX** export (separate encoder/decoder ONNX on HF).
- **License**: **Apache-2.0** — clean.
- **Jetson / edge-fit verdict**: No edge or latency benchmarks published. ViT-Ti is small enough in principle, but without a TensorRT path or fps numbers it's unproven on Jetson; ViT backbones are generally less TensorRT-friendly than CNNs on Nano-class hardware.
- **Reuse value for us**: **Low-medium.** Strong accuracy-per-param and a clean license, but no demonstrated edge deployment and a ViT (vs the CNN encoders that TensorRT best on Nano). The minable idea is SAMI pretraining for sample-efficient backbones; for actual deployment, NanoSAM's CNN-distillation route is the safer engineering bet.

## Reuse shortlist & licensing watch-outs

**What we'd actually take, concretely:**

- **Cloud-cover gate** → seed from **omnicloudmask** (MIT weights + 4-class CloudSEN12 scheme, distill into a tiny CNN), or for absolute-minimum power, mine the **s2cloudless** GBDT-over-bands design and *retrain our own* (to avoid CC-BY-SA). Both assume multispectral bands.
- **Land/ocean/forest segmenter** → train in **segmentation_models.pytorch** (Unet/FPN + MobileOne/MobileNetV3, MIT), initialized from **TorchGeo's** Sentinel-2 multispectral pretrained backbone (MIT), exported to ONNX.
- **Deployment runtime** → **jetson-inference** `segNet`/FCN-ResNet18 path (MIT, proven on the original 4GB Nano) is our reference; **torch2trt** (MIT) + ONNX→`trtexec` for the PyTorch→TensorRT leg.
- **Distillation pattern** → copy **NanoSAM's** ResNet18-encoder + FP16/INT8 TensorRT recipe (Apache-2.0) as the template for shrinking whichever model we train, even though we likely don't ship promptable SAM itself.

**Ethos note:** every adopt-the-runtime decision above (jetson-inference, torch2trt, SMP) is permissively licensed and battle-tested, so adopting is justified; everywhere else we mine the *design* (NanoSAM's distillation, omnicloudmask's class scheme, s2cloudless's tree-over-bands) and rebuild, which also sidesteps the license traps.

**License traps — do NOT ship these as-is:**
- **EdgeSAM** — **NTU S-Lab License 1.0, non-commercial.** Fast on iPhone (38 fps) and tempting, but unusable in a commercial/operational payload. Design reference only.
- **LoveDA** — dataset is **CC-BY-NC-SA 4.0, academic-only.** Fine for benchmarking/research, cannot train shippable weights on it for a commercial mission.
- **Cloud-Net** — **GPL-3.0.** Copyleft; avoid linking its code into our payload. 38-Cloud dataset and the architecture idea are still informative.
- **s2cloudless** — **CC-BY-SA-4.0** ShareAlike; retrain our own GBDT rather than embed theirs.
- **FastSAM** — **AGPL-3.0 vs Apache-2.0 conflict** in the repo itself; assume AGPL (network-copyleft) until legal clears it. Avoid.
- Clean / commercial-safe (MIT or Apache-2.0): **NanoSAM, jetson-inference, segmentation_models.pytorch (per-file check), omnicloudmask, MobileSAM, torch2trt, TorchGeo, EfficientSAM, Raster Vision.**

**Honorable mentions not given full sections:** **CloudSEN12 / cloudsen12/models** (https://github.com/cloudsen12 — the dataset + 8 baseline detectors incl. `unet_mobilenetv2`; no license stated on the models repo, so treat weights cautiously — but the *dataset* is the gold-standard cloud-shadow training source); **Raster Vision** (azavea/raster-vision, Apache-2.0 — full geospatial training/predict framework, cloud-execution oriented, no edge story); **RSP / ViTAE-Transformer** (MillionAID-pretrained RS backbones, useful as alternative pretraining to TorchGeo's).

**Verified fact corrections worth flagging to the team:** CloudScout itself has **no canonical public GitHub repo** — it's an ESA Φ-Sat-1 / University of Pisa research artifact reimplemented across papers (Myriad 2 VPU original; FPGA ports by Rapuano/Pacini). If we want its design we mine the papers, not a repo.
