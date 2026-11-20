# POST HOC: uninvolved-sensor diagnostic on RD (4-class, B = 16, fixed settings)

> POST HOC diagnostic (16 Nov 2026, after seeing PLAN6 results; NOT in PLAN6).
> 
> Why: ADAPT16 reached BA = 1.0 for 16/19 RD and 14/15 RGS persons. Calibration (first 4 reps per variant) and
> evaluation (last 5) come from the same set, and the variants were recorded in a fixed order. A within-session
> signature (stance, sensor drift) could therefore let a person-specific model separate the variants without
> learning the right-foot movement itself.
> 
> Diagnostic: repeat the primary RD analysis (4-class, B = 16, fixed settings, same folds/seeds) using ONLY sensors on
> the LEFT leg (Foot_Left, LowerLeg_Left), which do not perform RD (right-foot dorsiflexion while standing).
> A second subset uses the Sternum only.
> 
> Interpretation rule, written before running this script:
> - If ADAPT16 or PERS16 on the left-leg subset reaches mean BA >= 0.80 while GEN on that subset stays <= 0.50,
>   a within-session signature is a plausible contributor to the near-perfect personal results, and the PLAN6 gains
>   must not be attributed to learning the target movement alone.
> - If ADAPT16/PERS16 on the left-leg subset stay <= 0.50, this specific confound is not supported by this check
>   (it does not rule out other session effects).
> - In between: inconclusive, reported as such.
> Usage: python3 -P posthoc_uninvolved_sensors.py <raw_dir> <out_md>

Persons: 19. Person score = mean over 2 repeats (same folds and seeds as PLAN6).

| Feature subset | GEN | ADAPT16 | PERS16 | CTRL-NEW16 | ADAPT16 = 1.0 (persons) |
|---|---|---|---|---|---|
| left leg (Foot_Left + LowerLeg_Left) | 0.413 | 0.714 | 0.784 | 0.412 | 0/19 |
| sternum only | 0.450 | 0.630 | 0.655 | 0.409 | 0/19 |
| all 9 sensors (reproduces PLAN6) | 0.922 | 0.993 | 0.962 | 0.925 | 16/19 |

Chance level for 4 balanced classes = 0.25.
