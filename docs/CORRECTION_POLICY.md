# Correction policy

Only confirmed sensor-fault classifications with enough history and at least three fresh trusted peers are eligible. Temperature and humidity candidates require agreement between the temporal estimate and the peer median within a conservative tolerance. Pressure correction is withheld because absolute station pressures may have different reference/elevation. No correction is proposed for genuine weather, ambiguous review cases, integrity errors or strongly disagreeing estimators.

A proposal preserves raw_value, expected_value, corrected_candidate, lower and upper bounds, method, null probability/confidence, and state. The range is heuristic, not conformal. PROPOSED records may transition to MANUALLY_APPROVED or REJECTED through an audited endpoint. A reviewed proposal cannot be reviewed a second time. Raw rows remain unchanged even after approval. No downstream operational product is automatically published.

Quarantine is not currently a separate product-publication policy. Human review is a database workflow; stronger RBAC, dual approval and external product publication require deployment-specific work.
