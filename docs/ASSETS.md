# Assets and references

The six user-provided screenshots guided the light blue/white palette, navy type, compact cards and operations layout. They are design references rather than live metrics or embedded screenshots. The user's original 3D map source is pending and can replace `frontend/src/Map.tsx`.

Temporary geographic polygons: [geohacker/india](https://github.com/geohacker/india), `state/india_state.geojson`, sourced upstream from GADM. Coordinates were simplified with a 0.025-degree Douglas–Peucker tolerance for rendering performance; retained coordinates are rounded to four decimals. These are historical boundaries (35 features) and do not reflect all current administrative divisions. The UI labels the map as a geographic preview. Replace with an approved authoritative dataset before government-facing deployment. Repository code licensing does not override upstream geographic-data terms; [GADM terms](https://gadm.org/license.html) apply to the data.

UI icons: lucide-react. Typography: DM Sans and Manrope via Google Fonts CSS; system sans-serif fallback works offline. Geographic polygons and model artifacts are bundled locally; no forecast, radar or satellite observation is supplied to the detector. The map currently uses colored extrusions, not satellite terrain.

## Northern boundary revision, 22 September 2026

Jammu and Kashmir and Ladakh now use the corresponding polygons from [AbhinavSwami28/india-official-geojson](https://github.com/AbhinavSwami28/india-official-geojson), `india-states-simplified.geojson`, whose northern source is [india-in-data/kashmir](https://github.com/india-in-data/kashmir). This uses India's claimed territorial extent, including disputed areas; it is not a statement about de facto administration. The source repository's MIT notice is preserved in NORTHERN_GEOGRAPHY_LICENSE.txt; upstream geographic-data terms remain relevant. Lakshadweep geometry was also restored from that file because the previous simplification had removed all its islands.

These are community-maintained polygons, not newly certified Survey of India data. Other polygons retain the earlier historical base (including the older Andhra Pradesh/Telangana and Dadra/Daman administrative organization). The northern correction does not certify every internal boundary as current. UI attribution identifies the boundary convention. The user-supplied original 3D map remains pending.

### Neighbor country context outlines
`frontend/public/neighbor-countries.geojson` contains Pakistan, China, Nepal, Bhutan, Bangladesh, Myanmar, Sri Lanka and Afghanistan from Natural Earth's public-domain 1:110m admin-0 countries dataset. Source: https://github.com/nvkelso/natural-earth-vector/blob/master/geojson/ne_110m_admin_0_countries.geojson . Only names and geometry are retained. Low-opacity lines provide generalized context behind the existing India map; they do not replace its boundary geometry.
