-Data Queries
exoplanet.get_planet_table()
print('\n\nFields:\n'.format(key0))
for val in exoplanet._planet_table['fields']:
    print('{:12}{:13}{}'.format(val['colname'], val['datatype'], val['description']))

print(type(exoplanet._planet_table['data']))
for key,val in exoplanet._planet_table['data'][0].items():
    print('{:12}{}'.format(key,val))
