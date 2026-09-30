"""Varied synthetic weather, not real climatology or a forecast provider."""
import hashlib,math,random
VERSION='regional-v4'

def weather_noise(ts,key,period):
    """Deterministic smooth random knots, with no repeating daily template."""
    x=ts/period; left=math.floor(x); f=x-left; f=f*f*(3-2*f)
    def knot(n):return random.Random(f'{key}:{n}').uniform(-1,1)
    return knot(left)*(1-f)+knot(left+1)*f

def regional_values(ts, station_id, meta, seed=26073):
    lat,lon=meta['latitude'],meta['longitude']
    identity=int(hashlib.sha256(f'{seed}:{station_id}'.encode()).hexdigest()[:12],16)
    profile=random.Random(identity)
    offset=profile.uniform(-1.8,1.8);pressure_bias=profile.uniform(-1.4,1.4)
    phase_shift=profile.uniform(-.3,.3)
    # Smooth spatial fields keep close sites related, with explicit desert/coastal/mountain regimes.
    aridity=math.exp(-((lat-27)/6)**2-((lon-72)/7)**2)
    humid=math.exp(-((lon-93)/7)**2)+.6*math.exp(-((lat-11)/5)**2)
    elevation=meta.get('elevation_m',0) or 0
    if not elevation and lat>30:elevation=max(0,(lat-30)*450)  # synthetic terrain proxy for generated sites only
    day=ts/86400;hour=(ts/3600+lon/15)%24
    phase=2*math.pi*(hour-9)/24+phase_shift
    synoptic=math.sin(day*2*math.pi/5+lon*.12-lat*.07)
    seasonal=2*math.sin(day*2*math.pi/365-1)
    mean=30-.27*(lat-12)-.005*elevation+aridity*4+offset+seasonal
    t=mean+(3+3.5*aridity-1.2*min(1,humid))*math.sin(phase)+1.8*synoptic
    vapour_base=mean-(7+12*aridity-3*min(1,humid))
    vapour=6.112*math.exp(17.67*vapour_base/(vapour_base+243.5))*(1+.07*synoptic)
    rng=random.Random(f'{identity}:{int(ts)}')
    # Independent site phases and non-harmonic periods avoid repeated curves across stations.
    local_phase=(identity%10000)/10000*2*math.pi
    mesoscale=.42*math.sin(ts/3600*1.73+local_phase)+.24*math.sin(ts/3600*3.17+local_phase*2)
    # Evolving cloud/air-mass variation changes each day's amplitude and local shape.
    cloud=weather_noise(ts,f'{identity}:cloud',5*3600)
    local=weather_noise(ts,f'{identity}:local',100*60)
    air=weather_noise(ts,f'{seed}:region:{round(lat/4)}:{round(lon/4)}',17*3600)
    t+=mesoscale+1.4*cloud+.55*local+1.1*air+rng.gauss(0,.16)
    vapour*=1+.045*weather_noise(ts,f'{identity}:moisture',3*3600)+.04*air
    vapour*=1+.025*math.sin(ts/3600*2.31+local_phase)
    rh=max(8,min(98,100*vapour/(6.112*math.exp(17.67*t/(t+243.5)))+rng.gauss(0,.45)))
    p=1.2*weather_noise(ts,f'{identity}:pressure',7*3600)+.5*air+1008+4.5*synoptic+2*math.sin(lat*.15)+pressure_bias+.65*math.sin(phase*2)+.32*math.sin(ts/3600*1.37+local_phase)+rng.gauss(0,.10)
    # Values here are MSL for our synthetic network; do not imitate real station pressure at altitude.
    return [round(t,3),round(p,3),round(rh,3)]
