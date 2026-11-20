# Provenance and release preparation

Prepared 20 November 2026 from a dedicated, pre-existing publication copy of the experiment project. The original research workspace and its saved results were not modified.

## Preserved evidence

Historical plan texts and saved experiment results retain their original bytes from the reviewed publication copy. Plan texts were additionally compared with the corresponding original research files. No experimental result was edited to improve the narrative. Fingerprint logs may record intermediate plan snapshots plus later addenda; a hash for an initial snapshot is not automatically the hash of the final amended file.

Some source plans or reports refer to internal review notes absent from this code release. Those references document the working history; the private dialogue, application answers, funding statements and personal documents are not part of the repository.

## Packaging changes

- Aligned the README with the accepted research title and repository URL. The software citation names the preparatory code; future classifier-versus-simple-calibration work is explicitly distinguished from implemented experiments.
- Rewrote README/data/reproduction documentation to match the current interpretation and actual included inputs.
- Added a complete core runner; the previous runner started at Study 2 despite instructions calling it an all-study runner.
- Made camera setup conditional and added on-demand annotation and 25-video acquisition helpers. No motion data were downloaded during packaging.
- Removed dependency on a nonexistent GitHub Release/keypoint asset.
- Corrected the Python requirement to 3.11+ because the commands use `-P`.
- Improved comparison handling of non-finite values, Boolean types and failing exit status; no model fitting code was changed.
- Validated and quoted frame-decoder paths, excluded an obsolete parallel-download resumer, and made the optional keypoint plot conditional on locally acquired inputs.
- Kept source annotations and keypoint plots/arrays outside this initial source-only release, along with redundant session-launch jobs and a backup script.
- Replaced an outdated partial author-rerun status with the author's later completion statement; did not fabricate a new machine-generated comparison.

The private release audit records syntax, JSON parsing, link checks, content screening, source-result integrity and the explicit inclusion/exclusion inventory. These checks do not establish scientific novelty, clinical validity or universal reproducibility. Original data acquisition and full model reruns were not repeated for packaging.
