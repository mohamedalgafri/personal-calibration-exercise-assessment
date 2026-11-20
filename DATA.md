# Data sources and acquisition

This source release contains code, plans, reports and saved evaluation metrics. It does not contain raw recordings, videos, frame images, source repetition annotations or extracted keypoint arrays.

| Dataset | Original source | Licence | Inputs |
|---|---|---|---|
| PHYTMO (García-de-Villa et al., 2022) | [V0](https://zenodo.org/records/5052756), [V0.1](https://zenodo.org/records/6319979) | CC BY 4.0 | Wearable measurements and optical rigid-body measurements |
| GAITEX (Spilz and colleagues) | [Zenodo 15729056](https://zenodo.org/records/15729056), [paper](https://doi.org/10.1038/s41597-025-06439-x) | CC BY 4.0 | Published sensor-orientation files for RD and RGS |
| REHAB24-6 (Černek, Sedmidubský and Budíková, 2024) | [Zenodo 13305826](https://zenodo.org/records/13305826) | CC BY-NC 4.0 | Camera-17 video, projected optical reference and repetition annotations |

The PHYTMO downloader retains the V0 URL used in the original scripts. The two official records were checked during release preparation and list the same `PHYTMO.zip` byte size and MD5 (`3c21da9abac392c9f998df379d4b7f42`). V0.1 adds equipment datasheets. No full archive was downloaded again for this packaging check.

## Main sensor studies

```bash
bash get_data.sh phytmo
bash get_data.sh gaitex
```

These fetch only the selected archive members. Original access terms and attribution still apply.

## Optional camera reproduction

```bash
bash get_data.sh camera
bash tools/download_camera_videos.sh
bash camera_plan7/code/decode_frames.sh
python3 -P camera_plan7/code/serve.py 8765
```

`get_data.sh camera` downloads the reference measurements and the three small annotation/name files from the original Zenodo record; the latter are checked against recorded source MD5s. The video helper includes all 25 recordings, including PM_013 used in the initial feasibility check. It requires ffmpeg and prepares intra-frame videos locally. Decoded frames can occupy substantially more disk than the compressed videos.

Open `http://127.0.0.1:8765/code/extract_frames.html` in Chrome and follow the extraction interface and PLAN7 Addendum C. Check the results using `camera_plan7/code/check_extraction.py`. Extracted files belong in `camera_plan7/results/PM_*_jpg1.json`. The included `extraction_log.jsonl` documents the original run selection; any repeat extraction with different filenames must have its own matching log and quality audit before it can reproduce or change the comparison. Do not silently substitute extraction runs.

The local server binds to the loopback interface and is a research utility, not a deployed patient service. There is no uploaded keypoint archive or promised Release asset to download.

## Other studies

- KIMORE: download instructions in [the feature-selection study](preliminary_experiment/README.md). Person groups were inferred, not supplied as documented participant IDs.
- Parkinson's telemonitoring: see [the real-ID plan](preliminary_experiment/realid_confirm_2026-11-15/PLAN.md).
- UCI HAR: see [the quantification plan](quantification_pilot/PLAN.md).

The automated core runner does not cover these secondary studies or repeat browser extraction. Run them separately according to their recorded commands and input requirements. These different tasks are methodological preparation, not independent confirmations of exercise-assessment performance.

MIT applies to the original software, not to source data or third-party-derived data. Do not add locally downloaded or extracted movement data to a public commit without checking their own terms and intended scope. This release deliberately keeps those files separate.
