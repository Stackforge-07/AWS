# ML methodology

`ml/train.py` trains Isolation Forest on six synthetic station streams. Inputs are only T/P/RH-derived rates and temporal residuals. For each station the first 70% of the generated time range trains the model, the next 15% determines novelty-score normalization and edge thresholds, and the final 15% is reserved. No random row split is used. The separate stress benchmark uses later dates, different seeds and station indices excluded from fitting.

The novelty model supplies evidence, not a final weather-versus-fault probability. Deterministic guards and explicit temporal/spatial policy make the baseline decision. The current classifier is **not learned fusion**, and its displayed evidence strength is **not calibrated**. Long-history seasonal climatology, calibrated logistic/XGBoost fusion, conformal prediction sets, SHAP, sequence models and TinyTimeMixer selection remain unimplemented.

The edge autoencoder uses 12 past timestamps × 3 variables flattened oldest first. Means and standard deviations are fit on training windows only. Network: 36→32→8→32→36, ReLU hidden layers. The model is trained on synthetic normal sequences, then quantized using a representative training subset. Input and output are verified INT8. The anomaly threshold is the 99.5th percentile of the INT8 reconstruction error on the chronological normal validation set.

Artifacts record feature order, seed, data provenance, split details, model version, thresholds and SHA-256. Hashes identify artifacts; they are not signatures. No real AWS generalization is claimed. Synthetic development regressions are not a blinded final test because implementation was reviewed against their failures.
