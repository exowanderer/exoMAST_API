# exoMAST_API
Python wrapper for exo.mast.stsci.edu/api

Object oriented python wrapper based on the API provided by exo.mast.stsci.edu/api with stellar documentation provided here: https://exo.mast.stsci.edu/docs/


This python wrapper accesses the exo.mast.stsci.edu api (v0.1) in order to access both the currated planet information and any other data access (e.g. spectra, file listings, time series) that are provided by mast, now via a python wrapper.

I use the code primarily to access exoplanet system parameters as inputs to any transit light curve fitting tools. I would imagine that RV curve fitting models would also benefit from the background database access.

I owe great thanks for helping to develop this API to documentation and conversations with the exo.MAST team and, especially, [Dr. Susan Mullally](https://github.com/mustaric)!

---
Here is a nominal layout for usage:

# Resolving Exoplanets

```python
import exomast_api
planet_name = 'HD 189733 b'
exoplanet = exomast_api.exoMAST_API(planet_name, quickstart=False)

```
`quickstart == True` does not automatically run self.get_identifiers() or self.get_properties()
These are the default because the base operation is to "get the identifiers and properties". This is useful if the user has already downloaded the json file from `exo.mast.stsci.edu` and stored it locally.

For example:
```bash
wget -c -O hd187733b_identifiers.json https://exo.mast.stsci.edu/api/v0.1/exoplanets/identifiers/?name=HD189733b
wget -c -O hd187733b_properties.json https://exo.mast.stsci.edu/api/v0.1/exoplanets/HD%20189733%20b/properties

# After the downloads are complete:
ipython
```

Followed in `ipython` by 
```python
from exomast_api import exoMAST_API
hd189733b = exoMAST_API('HD 189733 b', quickstart=False)
hd189733b.get_identifiers(jsonfile='hd187733b_identifiers.json')
hd189733b.get_properties(jsonfile='hd187733b_properties.json')
```


Either which way, we can now look at what data is available
```python
print('Planet Name: {}'.format(exoplanet.planet_name), end=" ")
print('Rp/Rs: {}'.format(exoplanet.Rp_Rs), end=" ")
print('a/Rs: {}'.format(exoplanet.a_Rs), end=" ")
print('Orbital Period: {}'.format(exoplanet.orbital_period), end=" ")
print('Transit Center Time: {}'.format(exoplanet.transit_time), end=" ")
print('Eccentricity: {}'.format(exoplanet.eccentricity), end=" ")
print('Argument of Periastron: {}'.format(exoplanet.omega), end=" ")
```

There are also dictionaries containing *all* of the information accessed from the STScI exo.MAST API.

```python
for key,val in exoplanet._planet_ident_dict.items():
    print('{:15}{}'.format(key,val))

for key,val in exoplanet._planet_property_dict.items():
    print('{:25}{}'.format(key,val))
```

# Detrended Flux Time Series Data Queries

If the target has a KIC (Kepler) or (soon-to-be) TIC (TESS) id, then the api can access the more specific information; such as

### Listing TCEs
*List all of the available TCEs for this star: considerations apply for multiple transiting system*

These can be accesses from exomast_api (here) as

```python
exoplanet.get_tce()
print('TCEs Available: {}'.format(exoplanet.tce))
```

### Metatdata queries
*Provide extensive information about this KIC/TIC system*
This operation will acquire 'DV Primary Header' and 'DV Data Header' information

```python
exoplanet.get_planet_metadata()
for key0 in exoplanet._planet_metadata_dict.keys():
    print('\n\n{}\n'.format(key0))
    for key,val in exoplanet._planet_metadata_dict[key0].items():
        print('{:12}{}'.format(key,val))
```

### Data queries
*Acquire the detrended light curves for either a KIC or a TIC*
This provides 2 entries in the dictionary `exoplanet._planet_table`, which can be viewed as:
```python
exoplanet.get_planet_table()
print('\n\nFields:\n'.format(key0))
for val in exoplanet._planet_table['fields']:
    print('{:12}{:13}{}'.format(val['colname'], val['datatype'], val['description']))

print(type(exoplanet._planet_table['data']))
for key,val in exoplanet._planet_table['data'][0].items():
    print('{:12}{}'.format(key,val))
```
