# Physics engine

Implemented in `backend/app/physics.py` and calculated from the supplied T/P/RH values. The formulation is a liquid-water Magnus approximation, with guardrails on the domain. It is not an independent humidity or dew-point sensor and does not independently prove a fault.

- Saturation vapour pressure: `es = 6.112 exp(17.67 T / (T + 243.5))` in hPa.
- Vapour pressure: `e = RH/100 × es` in hPa.
- Dew point: invert the same Magnus relation. At zero RH return unavailable rather than evaluate log(0).
- Dew-point depression: `T - Td`, °C.
- Vapour pressure deficit: `es - e`, hPa.
- Mixing ratio: `.622 e/(P-e)` in kg/kg, displayed in g/kg.
- Specific humidity: `.622 e/(P-.378 e)` in kg/kg, displayed in g/kg.
- Virtual temperature: `(T+273.15)(1+.61 q)`, K.
- Air density: `P×100/(287.05 Tv)`, kg/m³; the factor 100 converts hPa to Pa.
- Potential temperature: `(T+273.15)(1000/P)^(287.05/1004)`, K.
- T/P/RH rates use elapsed minutes, not a presumed row interval.

Moisture evidence measures a rapid change in implied vapour pressure and is explicitly soft evidence. It is not summed repeatedly with every correlated transform. No arbitrary transform is described as an independent sensor. The current moisture baseline is simplified and needs station-specific validation, especially freezing conditions, sensor uncertainty and pressure-reference conversion.

General observational context: [WMO Instruments and Methods of Observation Programme](https://wmo.int/activities/instruments-and-methods-of-observation-programme-imop/instruments-and-methods-of-observation). This project does not claim WMO certification or compliance validation.
