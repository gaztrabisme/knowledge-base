# Cloud Detection & Cloud-Cover Gating for On-Orbit EO

On-board cloud screening is the single most-proven AI application in orbit today: roughly two-thirds of Earth is cloud-covered at any moment ([NASA/ESA via eoPortal](https://www.eoportal.org/satellite-missions/phisat-1)), and every cloud-corrupted frame that gets downlinked wastes the scarcest resource on a satellite — power-hungry RF downlink bandwidth. For a Jetson-class gating processor whose top constraint is energy, the relevant prior art is dominated by ESA's CloudScout/Φ-sat-1, with a supporting literature of Sentinel-2 cloud-masking algorithms and lightweight CNNs. The key framing: you need a *yes/no retake* decision, not a science-grade pixel mask — and that distinction buys you orders of magnitude in compute.

## ESA CloudScout & Φ-sat-1 — the canonical prior art

Φ-sat-1 (PhiSat-1) is a 6U CubeSat ("about the size of a cereal box"), the first of the two-satellite FSSCat mission, launched on a Vega rocket from Kourou on 3 September 2020. It carried the **HyperScout-2** imager (hyperspectral VNIR 400–1000 nm at 12 nm resolution, plus 4 TIR bands) and was the first satellite to run a deep CNN in orbit for EO triage ([eoPortal](https://www.eoportal.org/satellite-missions/phisat-1); [Giuffrida et al., *IEEE TGRS* 2022](https://ui.adsabs.harvard.edu/abs/2022ITGRS..6025567G)).

**CloudScout** is the CNN. Architecture: a two-stage design — a feature-extraction stack of ten bias-free convolutional layers with squared filters, followed by a decision stage. The original model was a simple **image-wise binary classifier** (cloudy vs. not-cloudy) — exactly the gating decision our mission needs; a later variant (UNet-CloudScout) added pixel segmentation ([CloudScout, *Remote Sensing* 2020, MDPI](https://www.researchgate.net/publication/342855283_CloudScout_A_Deep_Neural_Network_for_On-Board_Cloud_Detection_on_Hyperspectral_Images)).

Hard numbers on the flight hardware (Intel Movidius Myriad 2 VPU, 28 nm, 12 vector cores, ~2 TOPS at <1 W):
- **Accuracy: 92%**, false-positive rate **1%** (deliberately tuned low — a false "cloudy" wrongly discards a *good* science image)
- **Inference time: 325 ms** on 512×512×3 datacubes
- **Power: ~1.8 W per inference**
- **Memory footprint: 2.1 MB**
- **Outcome: ~30% downlink bandwidth saved** by discarding cloudy frames on-board

Sources: [CloudScout / *Remote Sensing* 2020](https://www.researchgate.net/publication/342855283_CloudScout_A_Deep_Neural_Network_for_On-Board_Cloud_Detection_on_Hyperspectral_Images); [Φ-sat-1 mission paper, *IEEE TGRS* 2022](https://ui.adsabs.harvard.edu/abs/2022ITGRS..6025567G).

Two engineering lessons transfer directly to a Jetson build. First, **precision conversion is a real risk**: the GPU-trained FP32 weights had to be cast to FP16 for Myriad 2 via the Movidius NCSDK, and quantization/pruning can shift behavior unpredictably — budget for accuracy re-validation after any INT8 quantization on Orin. Second, **training data had to be synthesized** from a proxy archive (Sentinel-2) because the novel sensor had no pre-flight data — the same problem any new RGB payload faces.

A follow-up FPGA port (Rapuano et al.) re-implemented a CloudScout variant with custom fixed-point arithmetic: 48% memory reduction (204→107 Mbit) at only 0.3% accuracy loss, faster inference (141.68 ms) but *higher* power than the VPU ([Rapuano et al.; see also FPGA CubeSat survey, arXiv:2504.03891](https://arxiv.org/html/2504.03891)). The takeaway for us: fixed-point/INT8 buys memory and latency cheaply, but the VPU/SoC still wins on raw energy-per-inference.

## Sentinel-2 cloud masking — threshold/physical vs. learned

These are the ground-segment reference algorithms. They matter to us as (a) the source of training labels and (b) a "why not just use thresholds" baseline.

- **Fmask** — USGS physical/threshold algorithm (object-based cloud probability + thresholds), strong over tropical forest (90% in an Amazon study), but classically leans on thermal bands that Sentinel-2/an RGB payload lacks ([Skakun et al., *Remote Sensing of Environment* 2020](https://www.sciencedirect.com/science/article/pii/S2666017220300092)).
- **Sen2Cor** — ESA's operational L2A processor; threshold-based Scene Classification Layer, ~79–84% overall accuracy in comparisons ([benchmark, *Remote Sensing* 2021](https://www.mdpi.com/2072-4292/13/5/992)).
- **MAJA** (CNES) — multi-temporal, conservative, uses dilation to protect clear-sky accuracy; needs an image time-series, so it's unusable for a single-shot on-board gate ([Amazon comparison, *Remote Sensing* 2020](https://www.mdpi.com/2072-4292/12/8/1284)).

These rely heavily on spectral bands (cirrus B10, SWIR, sometimes thermal) that an RGB-only camera does not have — which is precisely why a *learned* RGB classifier is the right path for us rather than porting a threshold cascade.

## s2cloudless — the lightweight learned baseline

**s2cloudless** (Sentinel Hub) is the most relevant *cheap* learned model: a **LightGBM gradient-boosted tree** single-scene, per-pixel classifier — not a CNN. It uses 10 raw Sentinel-2 bands (B01, B02, B04, B05, B08, B8A, B09, B10, B11, B12), with tuned params (n_estimators=170, num_leaves=770) ([Zupanc, Sentinel Hub / Medium](https://medium.com/sentinel-hub/improving-cloud-detection-with-machine-learning-c09dc5d7cf13)). It significantly cut omission error vs. threshold methods in one benchmark ([*Remote Sensing* 2021](https://www.mdpi.com/2072-4292/13/5/992)) but was "erratic" over the Amazon (52% accuracy) in another ([*Remote Sensing* 2020](https://www.mdpi.com/2072-4292/12/8/1284)). **Edge-fit read:** a GBDT is featherweight on a CPU and trivially cheap energy-wise, but its accuracy leans on 10 *multispectral* bands. Strip it to RGB and the spectral separability that makes it work largely evaporates — so s2cloudless is a strong CPU baseline only if our payload has NIR/SWIR, which it may not.

## Cloud-detection CNNs — Cloud-Net, RS-Net, KappaMask, CloudS2Mask

The segmentation-CNN family (heavier, pixel-level, ground-oriented — useful as accuracy ceilings and label sources):

- **Cloud-Net / Cloud-Net+** — end-to-end FCN for Landsat-8, trained on 192×192×4 (RGB+NIR) patches with a soft/Filtered-Jaccard loss; Cloud-Net+ beats SOTA on 38-Cloud, 95-Cloud, Biome-8, SPARCS ([Mohajerani & Saeedi, IGARSS 2019, doi:10.1109/IGARSS.2019.8898776](https://github.com/SorourMo/Cloud-Net-A-semantic-segmentation-CNN-for-cloud-detection); [Cloud-Net+, arXiv:2001.08768](https://arxiv.org/abs/2001.08768)).
- **RS-Net** — U-Net-style; notably strong over snow/ice and shows you can train on *noisy Fmask-generated labels* and beat Fmask itself — relevant because we'll likely auto-label training data ([Jeppesen et al., *RSE* 2019](https://www.sciencedirect.com/science/article/pii/S0034425719301294)).
- **KappaMask** — U-Net deep-learning processor for S2, ~17% higher Dice than s2cloudless on its test set ([*Remote Sensing* 2021](https://www.mdpi.com/2072-4292/13/20/4100)).
- **CloudS2Mask / Swin-Unet** — current SOTA transformer-based maskers on CloudSEN12+ (~91% OA) ([CloudSEN12+ / *Data in Brief* 2024](https://www.sciencedirect.com/science/article/pii/S2352340924008163)).

**Edge-fit read:** all are pixel-level segmenters built for ground GPUs — overkill and over-budget for a yes/no gate. Their value to us is as *teachers* (knowledge distillation) and *label generators*, not as flight models.

## Recent on-board / energy-targeted work (2023–2025)

This is the most directly applicable newer literature for a Jetson energy budget:

- **Knowledge distillation of nnU-Nets** for on-board cloud detection — compresses heavy segmentation nets into deployable students with minimal accuracy loss ([Grycel et al., arXiv:2306.09886](https://arxiv.org/pdf/2306.09886)). Directly applicable: distill a CloudS2Mask/Cloud-Net teacher into a tiny RGB student.
- **Lightweight cloud-masking for on-board hyperspectral inference** (2025) — explicitly profiles models for on-board deployment; flags **MobileNetV4** as an excellent candidate at ~306 M FLOPs / 87% accuracy with very low latency ([arXiv:2507.08052](https://arxiv.org/pdf/2507.08052)).
- **FPGA-accelerated CNNs for CubeSat cloud detection** (2025) — quantifies the VPU-vs-FPGA energy/latency/dev-time tradeoff for exactly this task ([arXiv:2504.03891](https://arxiv.org/pdf/2504.03891)).
- **2025 comprehensive review** of optical cloud-detection explicitly calls out *lightweight architectures for on-board deployment* and self-/semi-supervised domain adaptation as the open frontier — and notes the energy crux: in some cases the *transmission energy saved by discarding cloudy frames exceeds the energy spent detecting them*, but this trade is under-quantified ([*Geomatics* 2025, MDPI](https://www.mdpi.com/2673-7418/5/3/27); [survey, *Eur. J. Remote Sensing* 2025](https://www.tandfonline.com/doi/full/10.1080/22797254.2025.2567921)).

## RGB-only cloud detection (no NIR/SWIR)

Critical for us if the payload camera is RGB-only. Cloud detection without thermal/NIR is harder (no cirrus/SWIR discrimination) but demonstrably feasible:

- A multi-modal CNN study found RGB-only performance "significantly improved" and "promising… for smaller satellites with limited multi-spectral capabilities" ([Mateo-García et al., *RSE* 2019/2020](https://www.sciencedirect.com/science/article/pii/S0034425719304651)).
- A **ZiYuan-3 GAP-CNN** used only 3 visible bands + global-average-pooling (instead of FC layers) to cut parameters — a directly reusable lightweight trick for an RGB gate ([cloud-detection review, MDPI 2025](https://www.mdpi.com/2673-7418/5/3/27)).
- Transfer-learning a pretrained ResNet on RGB hit 96% accuracy in 3 epochs in a practitioner walkthrough — pretrained ImageNet RGB backbones port cleanly since they expect 3 channels ([Cordeiro, Analytics Vidhya](https://medium.com/analytics-vidhya/a-simple-cloud-detection-walk-through-using-convolutional-neural-network-cnn-and-u-net-and-bc745dda4b04)).
- The **OpenSICDR** repo hosts RGB(+NIR) block-labeled S2/PlanetScope subscenes useful for RGB training ([OpenSICDR, GitHub](https://github.com/dr-lizhiwei/OpenSICDR)).

**Read:** RGB-only loses the cirrus/thin-cloud edge cases that need B10/SWIR, but for a *coarse "too cloudy → retake"* threshold (e.g., >X% scene cloud cover), RGB texture+brightness is sufficient, and pretrained RGB backbones make it the most transferable path.

## Image-level gate vs. pixel-level mask — the key tradeoff for us

Our decision is binary (retake or keep), which means we should prefer an **image-level binary classifier**, not a segmenter:

- **Image-level classifier** (CloudScout-original, MobileNet, small ResNet): one forward pass → scalar cloud-probability → threshold. Smallest compute, smallest memory, lowest energy, no per-pixel decoder. Tune the decision threshold to encode "too cloudy" (e.g., discard if cloud-prob > 0.5, or train directly on a >30% cloud-cover label). This is the natural energy-optimal choice ([CloudScout binary classifier design](https://www.researchgate.net/publication/342855283_CloudScout_A_Deep_Neural_Network_for_On-Board_Cloud_Detection_on_Hyperspectral_Images)).
- **Pixel-level mask** (U-Net family): gives exact cloud fraction and *which* regions are clouded — useful if you later want partial-scene salvage or quality metadata, but the decoder roughly doubles compute/energy and you'd just threshold the cloud fraction anyway. Overkill for pure gating.

Asymmetric error cost matters: CloudScout tuned FPR to 1% because a false "cloudy" throws away good data. For a *retake* gate, also weigh the opposite — a false "clear" downlinks a wasted cloudy frame. Set the threshold from the relative cost of wasted downlink vs. lost imaging opportunity.

## Datasets

- **38-Cloud / 95-Cloud** — Landsat-8, RGB+NIR, pixel ground truth; 38-Cloud = 8,400 train / 9,201 test 384×384 patches; 95-Cloud extends to 34,701 train patches (75 scenes). Best fit for an RGB(+NIR) segmentation/label pipeline ([95-Cloud, GitHub](https://github.com/SorourMo/95-Cloud-An-Extension-to-38-Cloud-Dataset); [38-Cloud, GitHub](https://github.com/SorourMo/38-Cloud-A-Cloud-Segmentation-Dataset)).
- **CloudSEN12 / CloudSEN12+** — global, multi-modal S2 (L1C+L2A+SAR+aux), 49,400 patches with thick/thin-cloud + shadow labels *and* outputs of 8 reference algorithms baked in for fair benchmarking; CloudSEN12+ is the largest expert-labeled set. Best for global generalization + distillation teachers ([CloudSEN12, *Scientific Data* 2022](https://www.nature.com/articles/s41597-022-01878-2); [CloudSEN12+, 2024](https://www.sciencedirect.com/science/article/pii/S2352340924008163)).
- **SPARCS** — Landsat-8, multi-class (cloud/shadow/snow/water), good hard-negative source (snow≠cloud) ([referenced in Cloud-Net+, arXiv:2001.08768](https://arxiv.org/abs/2001.08768)).
- **OpenSICDR** — aggregator of RGB(+NIR) cloud datasets/tools ([GitHub](https://github.com/dr-lizhiwei/OpenSICDR)).

## Energy & Jetson-fit summary

The hard reference point is CloudScout: **~1.8 W/inference, 325 ms, 2.1 MB, 92% acc** on a ~2 TOPS / <1 W VPU ([CloudScout 2020](https://www.researchgate.net/publication/342855283_CloudScout_A_Deep_Neural_Network_for_On-Board_Cloud_Detection_on_Hyperspectral_Images)). Mapping to our envelope:

- **Jetson Orin Nano (~40 TOPS INT8, 8 GB)** is ~20× the VPU's compute and can run an INT8 MobileNetV4/small-ResNet image classifier in single-digit ms, well under 1 W of *compute* energy if clocked down — the bottleneck becomes capture+I/O, not inference. Use the 7 W power mode and INT8 via TensorRT.
- **Jetson Nano (Maxwell, ~0.5 TFLOPS FP16, 4 GB)** is far tighter — comparable order to the Myriad 2. A CloudScout-sized 10-layer CNN or a distilled MobileNet (≤2–3 MB INT8) is the realistic ceiling; segmentation U-Nets will blow the latency/energy budget. FP16, batch-1, fixed input size.
- **Energy logic that justifies the whole system:** discarding a cloudy frame avoids its downlink RF cost, which on small platforms can *exceed* the inference cost — the core CloudScout result (30% bandwidth saved) and the 2025 review's "savings may exceed processing cost" both support this, though the exact break-even is mission-specific and under-quantified ([*Geomatics* review 2025](https://www.mdpi.com/2673-7418/5/3/27)).
- **Quantization is the main energy lever and the main risk:** INT8 (Orin) / FP16 (Nano) cut energy and memory sharply, but CloudScout's FP32→FP16 experience shows you must re-validate accuracy and especially the false-positive rate after quantization.

## Recommended approach for our gating task

1. **Use an image-level binary classifier, not a segmenter.** Train directly on a "too-cloudy" label (e.g., scene cloud cover > a mission-set threshold). One forward pass, scalar output, threshold → retake. This is the energy-optimal architecture and matches CloudScout's original, flight-proven design.
2. **Backbone: a small/quantized MobileNetV4 (or distilled CloudScout-class 10-layer CNN).** MobileNetV4 is explicitly flagged as an on-board candidate (~306 M FLOPs, 87% acc, low latency) ([arXiv:2507.08052](https://arxiv.org/pdf/2507.08052)); on Orin run INT8/TensorRT, on Nano run FP16 and keep the model ≤3 MB.
3. **If RGB-only:** lean on a pretrained-RGB backbone + transfer learning (3-channel native, proven ~96% feasible) and a GAP head to shrink params; accept reduced thin-cirrus sensitivity since the gate is coarse.
4. **Labels via distillation:** generate training labels by running a heavy teacher (CloudS2Mask / Cloud-Net+ / s2cloudless) on RGB(+NIR) data, then distill into the tiny student — RS-Net showed training on noisy auto-labels can match or beat the labeler ([Jeppesen 2019](https://www.sciencedirect.com/science/article/pii/S0034425719301294); KD precedent: [arXiv:2306.09886](https://arxiv.org/pdf/2306.09886)).
5. **Data:** train/validate on 95-Cloud (RGB+NIR) + CloudSEN12+ (global generalization) + SPARCS (snow hard-negatives); synthesize your sensor's spectral response from S2/Landsat as ESA did for Φ-sat-1.
6. **Tune the threshold by asymmetric cost** (wasted downlink vs. lost imaging opportunity), and **re-measure FPR after quantization** — that's where CloudScout-style deployments break.

Net: this is mature, flight-proven territory. A quantized image-level RGB classifier on Orin Nano sits comfortably inside the energy budget with large margin; on the original Nano it's feasible but demands a CloudScout-sized distilled model and FP16.
