# On-Board & In-Orbit AI for Earth Observation: Prior Art & Constraints

<!-- knowledge-base doc: space-edge-ai/onboard-space-ai -->

On-board AI moves the first stage of analysis from the ground station into the spacecraft: instead of downlinking everything and sorting later, the satellite runs inference at the sensor and transmits only what matters. For an energy-constrained Jetson-class EO payload, this reframes the central trade — every watt spent on inference is justified only if it saves more watts (and bandwidth, and storage) downstream by discarding data that would otherwise be transmitted. The prior art below is read through that lens.

## ESA Φ-sat-1 / CloudScout — the first DNN in orbit for EO

Launched 3 September 2020 on a 6U CubeSat, Φ-sat-1 was the first European (and first operational) demonstration of a deep neural network running on an EO satellite. It paired the HyperScout-2 hyperspectral/TIR imager with an **Intel Movidius Myriad 2 VPU** (integrated by Ubotica). The flight model, **CloudScout**, is a ConvNet that detects cloud cover per frame and discards images exceeding a cloudiness threshold (~70%) before downlink.

Energy/efficiency figures are directly relevant to us: CloudScout ran at **~325 ms inference, ~1.8 W, 2.1 MB footprint, ~92% accuracy** on Sentinel-2-derived hyperspectral data, saving roughly **30% of downlink bandwidth**. GPU-trained FP32 weights were converted to FP16 (the Myriad 2's native precision). Crucially for COTS-in-LEO confidence: ground radiation testing showed **no SEL up to 8.8 MeV·cm²/mg and no measurable TID degradation up to 49 krad (Co-60)**.

Why it matters: this is the canonical proof that a sub-2 W accelerator can do cloud-gating in orbit and pay for itself in bandwidth — the exact value proposition of our cloud-gating stage. ([Φ-sat-1 mission paper, IEEE TGRS 2022](https://ui.adsabs.harvard.edu/abs/2022ITGRS..6025567G); [CloudScout, ResearchGate](https://www.researchgate.net/publication/342855283_CloudScout_A_Deep_Neural_Network_for_On-Board_Cloud_Detection_on_Hyperspectral_Images); [eoPortal](https://www.eoportal.org/satellite-missions/phisat-1))

## ESA Φ-sat-2 — a reconfigurable on-board AI app platform

Launched 16 August 2024 (22×10×33 cm CubeSat, Open Cosmos prime, Ubotica + KP Labs + CGI + others), Φ-sat-2 carries a 7-band-plus-pan multispectral imager and again an **Intel Movidius Myriad 2**, but the key advance is architectural: it runs **multiple swappable AI apps** that can be developed, uploaded, and operated **in orbit** via the open-source NanoSat MO Framework. Demonstrated apps include cloud detection/classification (KP Labs), vessel detection, marine-anomaly and wildfire detection, on-board image compression with ground reconstruction, and Sat2Map street-map generation (CGI).

Why it matters: it shows the operational model we'd want long-term — a fixed compute payload that hosts a *fleet* of models updated post-launch, not a single frozen network. The compression-on-board + reconstruct-on-ground app is a second bandwidth lever beyond cloud-gating. ([ESA Φsat-2](https://www.esa.int/Applications/Observing_the_Earth/Phsat-2/Introducing_Phsat-2); [eoPortal](https://www.eoportal.org/satellite-missions/phisat-1))

## ESA OPS-SAT — the in-orbit ML flying laboratory

OPS-SAT (launched 18 December 2019, deorbited May 2024) was a 3U "flying laboratory" built to let experimenters safely run risky software in orbit on a processor ~10× more powerful than contemporary ESA spacecraft (Altera **Cyclone V SoC with FPGA**, plus camera and SDR). It hosted **thousands of experiments from 134 teams**, and racked up several ML firsts: first on-board FPGA deep-learning image processing, **first in-flight re-training of an on-board model with live data**, first on-board ANN update in an institutional mission, and first on-board generative AI (WGANs). ML experiments spanned telemetry anomaly detection (KP Labs), on-board change detection / deforestation, and image-feature recognition challenges.

Why it matters: OPS-SAT is the reference for *on-orbit learning and model updates* and for the FPGA path as an alternative/complement to a GPU. Its anomaly-detection work is directly transferable to FDIR on our own payload. ([ESA OPS-SAT](https://www.esa.int/Enabling_Support/Operations/OPS-SAT_your_flying_laboratory); [eoPortal](https://www.eoportal.org/satellite-missions/ops-sat); [Discovery Campaign](https://www.esa.int/Enabling_Support/Preparing_for_the_Future/Discovery_and_Preparation/The_Discovery_Campaign_on_OPS-SAT_experiments))

## Commercial on-board AI — Ubotica CogniSAT-6 and the VPU lineage

Ubotica's **CogniSAT-6** (6U, with Open Cosmos, launched March 2024) is the first *commercial* "Live Earth Intelligence" service. Its **CogniSAT-XE2** board (PC/104, 0.15U, 65 g) runs an **Intel Movidius Myriad X VPU**. Power numbers are excellent and directly comparable to a Jetson budget: **~3.5 W peak during inference, 15 mW standby**. Operational results: over its first year it flew **5,576 orbits and ran >100,000 inferences**; in one pass it detected **142 ships near Khor Fakkan at 21.3 km²/s**, and it relays insights over inter-satellite links — including identifying "dark ships" by fusing on-board detections with AIS. Models are developed in TF/PyTorch/Caffe and compiled to Myriad via Intel **OpenVINO**; the **CVAI Toolkit** exposes the VPU through a host-side API.

Why it matters: CogniSAT is the strongest evidence that a few-watt accelerator delivers a *commercial-grade* detection pipeline. The 15 mW standby figure underscores how aggressively duty-cycled these payloads are — the accelerator is "off" most of the orbit. ([CogniSAT-6 overview, TechRxiv](https://www.techrxiv.org/doi/pdf/10.36227/techrxiv.170862166.69578112/v4); [Ubotica, one year](https://ubotica.com/one-year-of-cognisat-6-pioneering-live-earth-intelligence/); [Electronics Weekly](https://www.electronicsweekly.com/news/cognisat-6-satellite-mission-achieves-ai-detection-of-earth-objects-2024-08/))

## Jetson in space — SpIRIT/Loris and the commercial Jetson-Orin wave

The most directly relevant flight to our mission is **SpIRIT** (6U, University of Melbourne + Italian Space Agency, launched December 2023, 510 km SSO). Its **Loris** payload pairs six visible + three IR COTS cameras with an **NVIDIA Jetson Nano GPU module** — a true Jetson-class onboard-AI flight. Loris runs AI models with **on-orbit fine-tuning** plus a progressive-coding compression algorithm for downlink. Notable engineering details for us: the Nano sits at **−14 to −21 °C in cold rest** (above its −25 °C operational and −40 °C survival limits), and the team explicitly considered **duty-cycling the Jetson** to manage heat but found the thermal design tuned to the orbit avoided it. COTS-sensor failure risk is mitigated by **sensor multiplexing/redundancy**, and AI errors are handled with software error detection/correction. ([SpIRIT/Loris, arXiv:2404.08399](https://arxiv.org/abs/2404.08399); [CVPR 2024 AI4Space paper](https://openaccess.thecvf.com/content/CVPR2024W/AI4Space/papers/Del_Castillo_Mitigating_Challenges_of_the_Space_Environment_for_Onboard_Artificial_Intelligence_CVPRW_2024_paper.pdf))

The broader commercial Jetson-in-space wave is now real: NVIDIA formally launched a **Space Computing** program (Jetson Orin / IGX Thor / Space-1 Vera Rubin) with Planet, Kepler, Axiom and others. Space-rated Jetson products include **AICube** (Jetson Orin NX 16 GB, ~150 TOPS), **EDGX Sterna** (Orin NX, marketed on compute-per-watt-hour for 5-year LEO SSO), **Aitech S-A2300** (Orin, LEO), and **Aethero NxA** (Orin/Thor). Earlier TX1/TX2 feasibility studies (2017–2019) showed a Jetson fits a 1U power/mass budget. ([NVIDIA Space Computing](https://www.nvidia.com/en-us/edge-computing/space-computing/); [NVIDIA newsroom](https://nvidianews.nvidia.com/news/space-computing); [AICube/satsearch](https://satsearch.co/products/tm2s-aicube))

## FPGA-based on-board inference — the radiation-tolerant alternative

Beyond VPUs and GPUs, FPGAs are a recurring on-board AI accelerator: OPS-SAT's Cyclone V did the first on-board FPGA deep-learning, and recent work demonstrates **FPGA-accelerated CNNs for cloud detection on CubeSats**. FPGAs offer fine-grained power/throughput control and easier hardware-level fault mitigation (TMR, scrubbing) than a monolithic GPU, at the cost of harder model deployment. Surveys on enabling onboard AI via FPGA/ASIP acceleration map this trade space. ([FPGA CNN cloud detection, arXiv:2504.03891](https://arxiv.org/pdf/2504.03891); [FPGA/ASIP onboard AI, arXiv:2506.12970](https://arxiv.org/pdf/2506.12970))

Why it matters: if our Jetson's radiation posture proves marginal, an FPGA co-processor for the most safety-critical gating function is a known fallback.

## Surveys and reviews — the field's reference points

Several syntheses anchor the literature. The foundational review is **Furano, Meoni, Dunne et al., "Towards the use of AI on the edge in space systems: Challenges and opportunities," IEEE A&E Systems Magazine, 2020**. More recent: **"Advancing Earth Observation: A Survey on AI-Powered Image Processing in Satellites" (2025)** (taxonomy of on-board image processing); **MDPI Remote Sensing (2024) "Review on Hardware Devices and Software Techniques Enabling Neural Network Inference Onboard Satellites"** (the best hardware-focused review — VPUs vs GPUs vs FPGAs); the **JPL/NASA LEO-SatS workshop report "Towards Space Edge Computing and Onboard AI"**; and **"Edge Computing in Low-Earth Orbit — What Could Possibly Go Wrong?" (arXiv:2302.08952)**, which is the key reference on what radiation actually does to COTS edge compute. ([Advancing EO survey](https://www.tandfonline.com/doi/full/10.1080/22797254.2025.2567921); [MDPI hardware review](https://www.mdpi.com/2072-4292/16/21/3957); [JPL report](https://ai.jpl.nasa.gov/public/documents/papers/ieee-leo-sats-report.pdf); [Edge in LEO, arXiv:2302.08952](https://arxiv.org/pdf/2302.08952))

## Space-environment constraints on COTS compute (SEU / SEL / TID)

COTS compute is attractive because rad-hard parts cost far more and lag commercial performance by generations — but LEO radiation (trapped protons in the inner Van Allen belt and the **South Atlantic Anomaly**, down to ~200 km) imposes three failure modes:

- **SEU (single-event upset):** a particle flips a bit — corrupting weights, activations, sensor data, or program state; can escalate to SEFI (functional interrupt). Mitigation: **ECC memory, memory scrubbing, TMR/voting, watchdog-triggered restarts**, and re-running inference.
- **SEL (single-event latch-up):** the most dangerous — a parasitic SCR latches a high-current state that can **permanently destroy the chip** unless power is cut. Mitigation: **current-limiting + fast power-cycling (LCL latch-up protection)** is mandatory for COTS compute. Φ-sat-1 specifically demonstrated Myriad 2 was SEL-free to 8.8 MeV·cm²/mg.
- **TID (total ionizing dose):** cumulative degradation over the mission; managed by **shielding, part selection, and dose budgeting** against expected orbit/duration. Myriad 2 showed no TID effect to 49 krad.

The practical COTS-in-LEO posture: accept that faults *will* occur and design **FDIR** — watchdog timers, current limiters (often as stacked 3D modules to save mass), circumvention/safe-state logic, and recoverable software. SpIRIT's answer was sensor redundancy/multiplexing plus software error correction; OPS-SAT's whole premise was a robust bus that can always recover a misbehaving experiment. ([COTS in LEO, arXiv:2302.08952](https://arxiv.org/pdf/2302.08952); [COTS Devices for Space Missions in LEO](https://www.academia.edu/123602900/COTS_Devices_for_Space_Missions_in_LEO))

## Thermal and power budgets on CubeSats/smallsats in LEO

Power is the hard ceiling. A **3U platform typically lives within ~5–20 W total**, shared across ADCS, comms, OBC and payload; batteries are ~10 Wh-class. LEO SSO sees **~30% eclipse per orbit**, so the payload must duty-cycle against the orbit and battery depth-of-discharge / cycle life become limiting. This is why flown accelerators report a high peak / near-zero standby split (CogniSAT-XE2: 3.5 W peak vs 15 mW idle) — the compute is *bursty*, gated to imaging passes.

In **vacuum, radiation is the only heat-rejection path** (no convection), so high-dissipation compute must sit adjacent to an external radiator; designs are validated against worst-case-hot (peak dissipation all-orbit) and worst-case-cold transients, and coupled electrical-thermal models are used because junction temperature affects both efficiency and lifetime. SpIRIT confirms the cold side bites first for a Jetson (Nano resting at −14 to −21 °C, near its −25 °C operational floor) — heater power and thermal tuning, not just heat removal, matter. Duty-cycling is the lever of last resort for both power *and* thermal limits. ([SPEQTRE thermal design](https://ttu-ir.tdl.org/server/api/core/bitstreams/6b3a5d50-0483-427d-afad-63e1433bc0c9/content); [LEO power budgeting](https://www.researchgate.net/publication/353831997_Power_Budgeting_of_LEO_Satellites_An_Electrical_Power_System_Design_for_5G_Missions); [SpIRIT thermal, arXiv:2404.08399](https://arxiv.org/abs/2404.08399))

## The downlink-bandwidth argument — the core energy win

This is the crux of the energy case. EO missions collect **hundreds of GB/day**, and **up to ~90% of raw data is low-value "noise"** (cloud, empty terrain, irrelevant frames). Quantified savings from on-board filtering:

- **30–40%** of optical data is discarded *after* downlink anyway (AIKO) — pure wasted transmission energy that on-board gating recovers.
- **~30%** bandwidth saved by Φ-sat-1's CloudScout in practice.
- **up to 80%** downlink reduction with a full on-board disaster-analytics suite (cloud + flood + wildfire + fusion).
- **orders of magnitude** with advanced AI compression/semantic-communication approaches.

The energy linkage is explicit and quantitative: **required transmit power scales roughly linearly with data volume** at fixed transfer time, so discarding a cloudy frame avoids its entire transmit-energy cost — plus storage and processing-pipeline energy. On-board filtering is therefore not just a bandwidth optimization; it is the primary *energy* optimization for a downlink-bound EO satellite. ([AIKO cloudy_CHARLES](https://blog.satsearch.co/2023-05-02-sifting-out-low-quality-earth-observation-data-with-aiko); [Advancing EO survey](https://www.tandfonline.com/doi/full/10.1080/22797254.2025.2567921); [SKAISEN](https://incubed.esa.int/portfolio/skaisen/); [eoPortal onboard data processing](https://www.eoportal.org/other-space-activities/onboard-data-processing))

## Implications for our mission (energy-first)

1. **Cloud-gating is the energy engine, not a feature.** Every cloudy/empty frame the Jetson rejects avoids its full transmit energy (transmit power ∝ data volume). Budget the inference cost (CloudScout proved ~1.8 W, ~325 ms for this exact job) against ~30–80% downlink-volume savings — the gating model must be the cheapest, most reliable thing on the payload, run first in the pipeline.

2. **Design for bursty, duty-cycled compute, not continuous inference.** The flown norm is high peak / near-zero idle (CogniSAT 3.5 W / 15 mW). Gate the Jetson to imaging passes and sun phases; assume ~30% eclipse and size battery DoD/cycle-life accordingly. Keep an aggressive low-power/standby state between passes.

3. **Cold, not hot, is the Jetson's first thermal problem** (SpIRIT: Nano at −14 to −21 °C near its −25 °C floor). Plan heater power and radiator placement together; tune the thermal design to the orbit so duty-cycling stays a fallback, not a requirement.

4. **Treat radiation as "when," not "if."** Mandatory: current-limiting + power-cycling for SEL (potentially destructive), ECC + scrubbing + watchdog restarts + inference re-runs for SEU, and a TID dose budget for the mission lifetime. Φ-sat-1's Myriad 2 SEL/TID results are encouraging precedent but must be re-established for our specific Jetson SKU.

5. **Borrow the proven software model:** OpenVINO/TensorRT-style compile-to-target + FP16, a swappable multi-app framework (Φ-sat-2 / NanoSat MO) so models update post-launch, and on-orbit fine-tuning (OPS-SAT, SpIRIT) to handle distribution shift without a hardware change.

6. **Keep FPGA as the safety-critical fallback.** If the Jetson's rad posture is marginal, move the gating CNN to a radiation-tolerant FPGA co-processor (OPS-SAT / CubeSat FPGA-CNN precedent) while the GPU handles the heavier land-cover segmentation.

7. **Stack the bandwidth levers:** cloud-gating *then* on-board compression/semantic encoding (Φ-sat-2, SpIRIT Loris progressive coding) compounds the energy savings toward the "orders-of-magnitude" regime.
