"""Liquid-water Magnus approximation. Derived representations, not independent sensors."""
import math

def derive(t: float, p: float, rh: float) -> dict:
    if not (-80 <= t <= 60 and 100 <= p <= 1200 and 0 <= rh <= 100):
        return {'available': False, 'reason': 'Outside validated approximation domain', 'label': 'DERIVED FROM T/P/RH'}
    es = 6.112 * math.exp(17.67 * t / (t + 243.5))
    e = rh / 100 * es
    if p <= e:
        return {'available': False, 'reason': 'Vapour pressure exceeds total pressure', 'label': 'DERIVED FROM T/P/RH'}
    gamma = math.log(e / 6.112) if e > 0 else None
    td = 243.5 * gamma / (17.67 - gamma) if gamma is not None else None
    q = .622 * e / (p - .378 * e)
    tv = (t + 273.15) * (1 + .61 * q)
    values = {'saturation_vapour_pressure_hpa': es, 'vapour_pressure_hpa': e, 'dew_point_c': td,
              'dew_point_depression_c': t - td if td is not None else None,
              'vpd_hpa': es-e, 'mixing_ratio_g_kg': 1000*.622*e/(p-e), 'specific_humidity_g_kg': q*1000,
              'virtual_temperature_k': tv, 'air_density_kg_m3': p*100/(287.05*tv),
              'potential_temperature_k': (t+273.15)*(1000/p)**(287.05/1004)}
    return {'available': True, 'label': 'DERIVED FROM T/P/RH', **{k: round(v, 4) if v is not None else None for k,v in values.items()}}
