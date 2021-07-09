{
  <bash wget -c -O hd187733b_identifiers.json'https://exo.mast.stsci.edu/api/v0.1/exoplanets/identifiers/?name=HD189733b`>
"HD 189733 b",
  "starName":
  "HD 189733",
    "ra":
    300.1821249961853,
      "dec":22.71146111064487,
        "planetNames":
        [
          "PPM 110211 b",
          "LSPM J2000+2242 b",
          "GSC 02141-00972 b",
          "GEN# +1.00189733 b",
          "ASCC 807144 b",
          "GC 27741 b",
          "YZ 22 7419 b",
          "Gaia DR1 1827242811876888960 b",
          "HD 189733 b",
          "1RXS J200043.3+224240 b",
          "2MASS J20004370+2242391 b",
          "TYC 2141-972-1 b",
          "HIP 98505 b",
          "AG+22 2072 b",
          "USNO-B1.0 1127-00538857 b",
          "EXO 195834+2234.6 b",
          "BD+22 3887 b",
          "GJ 4130 b",
          "SAO 88060 b",
          "LTT 15851 b",
          "NLTT 48568 b",
          "HIC 98505 b",
          "Wolf 864 b",
          "uvby98 100189733 b",
          "V452 Vul b",
          "SKY# 37530 b"
        ],
          "keplerID":null,
            "keplerTCE":null,
              "tessID":256364928,
                "tessTCE":null}
---
After the downloads are complete, open `ipython` and continue this example
python
from exomast_api import exoMAST_API
exoplanet = exoMAST_API('HD 189733 b', quickstart=False)
exoplanet.get_identifiers(jsonfile='hd187733b_identifiers.json')
exoplanet.get_properties(jsonfile='hd187733b_properties.json')

---

Either which way, we can now look at what data is available
python
print(f'Planet Name: {exoplanet.planet_name}')
print(f'Rp/Rs: {exoplanet.Rp_Rs}')
print(f'a/Rs: {exoplanet.a_Rs}'.format())
print(f'Orbital Period: {exoplanet.orbital_period}')
print(f'Transit Center Time: {exoplanet.transit_time}')
print(f'Eccentricity: {exoplanet.eccentricity}')
print(f'Argument of Periastron: {exoplanet.omega}')

---
There are also dictionaries containing *all* of the information accessed from the STScI exo.MAST API.
---
python
for key,val in exoplanet._planet_ident_dict.items():
  print('{:15}{}'.format(key,val))

for key,val in exoplanet._planet_property_dict.items():
  print('{:25}{}'.format(key,val))

---
# Detrended Flux Time Series Data Queries

If the target has a KIC (Kepler) or (soon-to-be) TIC (TESS) id, then the api can access the more specific information; such as

### Listing TCEs
*List all of the available TCEs for this star: considerations apply for multiple transiting system*
---
These can be accesses from exomast_api (here) as
---
python
exoplanet.get_tce()
print('TCEs Available: {}'.format(exoplanet.tce))
---

### Metatdata queries
*Provide extensive information about this KIC/TIC system*
This operation will acquire 'DV Primary Header' and 'DV Data Header' information
---
python
exoplanet.get_planet_metadata()
for key0 in exoplanet._planet_metadata_dict.keys():
  print('\n\n{}\n'.format(key0))
  for key,val in exoplanet._planet_metadata_dict[key0].items():
      print('{:12}{}'.format(key,val))
---

### Data queries
*Acquire the detrended light curves for either a KIC or a TIC*
This provides 2 entries in the dictionary `exoplanet._planet_table`, which can be viewed as:
python
exoplanet.get_planet_table()
print('\n\nFields:\n'.format(key0))
for val in exoplanet._planet_table['fields']:
  print('{:12}{:13}{}'.format(val['colname'], val['datatype'], val['description']))
---
print(type(exoplanet._planet_table['data']))
for key,val in exoplanet._planet_table['data'][0].items():
  print('{:12}{}'.format(key,val))

