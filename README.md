# exoMAST_API
Python wrapper for exo.mast.stsci.edu/api

Object oriented python wrapper based on the API provided by exo.mast.stsci.edu/api with stellar documentation provided here: https://exo.mast.stsci.edu/docs/


This python wrapper accesses the exo.mast.stsci.edu api (v0.1) in order to access both the currated planet information and any other data access (e.g. spectra, file listings, time series) that are provided by mast, now via a python wrapper.

I use the code primarily to access exoplanet system parameters as inputs to any transit light curve fitting tools. I would imagine that RV curve fitting models would also benefit from the background databse access.

Here is a nominal layout for usage:

# Resolving Exoplanets

```python
import exomast_api
planet_name = 'HD 189733 b'
exoplanet = exomast_api.exoMAST_API(planet_name, quickstart=False)

'''
quickstart == True does not automatically run self.get_identifiers() or self.get_properties()
These are the default because the base operation is to "get the identifiers and properties"
'''
```
And then look at what data is available
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

# 
