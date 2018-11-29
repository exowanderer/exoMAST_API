import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

class exoMAST_API(object):
    def __init__(self, planet_name, exomast_version=0.1, api_url='https://exo.mast.stsci.edu/api', verbose=False):
        
        self.api_url = api_url
        
        self.planet_name = planet_name
        self.exomast_version = exomast_version
        self.verbose = verbose
        
        if self.verbose: print('Allocating Planetary Information from {} version {} for {}.'.format(
                                                                                        self.api_url,
                                                                                        self.exomast_version,
                                                                                        self.planet_name))
        
        self._planet_name = self.planet_name.lower().replace(' ', '%20')
        
        # For use with `self.get_spectra`
        self.header = ['Wavelength (microns)', 
                       'Delta Wavelength (microns)',
                       '(Rp/Rs)^2',
                       '(Rp/Rs)^2 +/-uncertainty']
        
        if 'planet' in self.planet_name.lower() \
            or 'kic' in self.planet_name.lower() \
            or 'koi' in self.planet_name.lower():
            self._collection = 'kepler'
        elif 'tess' in self.planet_name.lower() \
            or 'tic' in self.planet_name.lower() \
            or 'toi' in self.planet_name.lower():
            self._collection = 'tess'
        else:
            self._collection = None
        
        if self._collection is not None:
            if self.planet_name[:3] in ['kic', 'koi', 'tic', 'toi']:
                self.planet_id = int(self.planet_name[3:])
        
        # set of default placeholders:
        self._spectra_filelist = None
        self.planetary_spectra_table = None
        self.spectra_bokeh_plot = None
        self._planet_ident = None
        self._planet_property_dict = None
        self.tce = None
        self.planet_metadata = None
        self._planet_table = None
        self.planet_phaseplot = None
    
    def get_spectra_filelist(self):
        
        planet_spec_fname_url = '{}/v{}/spectra/{}/filelist/'.format(self.api_url, self.exomast_version, self._planet_name)
        
        if self.verbose: print('Acquiring Planetary Spectral File List from {}'.format(planet_spec_fname_url))
        
        spec_fname_request = requests.get(planet_spec_fname_url).content.decode('utf-8')
        
        self._spectra_filelist = json.loads(spec_fname_request)
    
    def get_spectra(self, idx_spec=0, header=None):
        if header is None: header = self.header
        
        if self._spectra_filelist is None:self.get_spectra_filelist()
        
        spec_fname = self._spectra_filelist['filenames'][idx_spec]
        
        spectrum_request_url = "{}/v{}/spectra/{}/file/{}".format(self.api_url, self.exomast_version, 
                                                                self._planet_name, spec_fname)
        
        if self.verbose: print('Acquiring Planetary Spectral File List from {}'.format(spectrum_request_url))
        
        spectra_request = requests.get(spectrum_request_url).content.decode('utf-8')
        
        spectra_table = [list(filter(lambda a: a != '', line.split(' '))) for line in spectra_request.split('\n') \
                                                                            if len(line) > 0 and line[0] != '#']
        
        self.planetary_spectra_table = pd.DataFrame(spectra_table, columns=header, dtype=float)
    
    def get_spectra_bokeh_plot(self, idx_tce=1):
        spectra_bokehplot_url = '{}/v{}/spectra/{}/plot/'.format(self.api_url, self.exomast_version, self._planet_name)
        
        if self.verbose: print('Acquiring Planetary Bokeh Spectral Plot from {}'.format(spectra_bokehplot_url))
        
        spectra_bokehplot_request = requests.get(spectra_bokehplot_url).content.decode('utf-8')
        self.spectra_bokeh_plot = json.loads(spectra_bokehplot_request) # to be injected into Bokeh (FINDME??)
    
    def get_identifiers(self):
        planet_identifier_url = '{}/v{}/exoplanets/identifiers/?name={}'.format(self.api_url, self.exomast_version, self._planet_name)
        
        if self.verbose: print('Acquiring Planetary Identifiers from {}'.format(planet_identifier_url))
        
        planet_ident_request = requests.get(planet_identifier_url).content.decode('utf-8')
        
        # Store dictionary of planetary identification parameters
        self._planet_ident = json.loads(planet_ident_request)

    def get_properties(self):
        planet_properties_url = '{}/v{}/exoplanets/{}/properties'.format(self.api_url, self.exomast_version, self._planet_name)
        
        if self.verbose: print('Acquiring Planetary Properties from {}'.format(planet_properties_url))
        
        planet_properties_request = requests.get(planet_properties_url).content.decode('utf-8')
        
        # Store dictionary of planetary properties
        self._planet_property_dict = json.loads(planet_properties_request)
    
    def get_tce(self):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful for Kepler and TESS objects')
        
        tce_url = '{}/v{}/dvdata/{}/{}/tces/'.format(self.api_url, self.exomast_version, 
                                                                self._collection, self.planet_id)
        
        if self.verbose: print('Acquiring Planetary Threshold Crossing Database from {}'.format(tce_url))
        
        tce_request = requests.get(tce_url).content.decode('utf-8')
        
        # theshold_crossing_event
        self.tce = json.loads(tce_request)
    
    def get_planet_metadata(self, idx_tce=1):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful for Kepler and TESS objects')
        
        if self.planet_id is None:
            planet_metadata_url = '{}/v{}/dvdata/{}/info'.format(self.api_url, self.exomast_version, self._collection)
        else:
            planet_metadata_url = '{}/v{}/dvdata/{}/{}/info/?tce={}'.format(self.api_url, self.exomast_version, 
                                                                            self._collection, self.planet_id, 
                                                                            idx_tce)
        
        if self.verbose: print('Accessing Meta Data from {}'.format(planet_metadata_url))
        
        planet_metadata_request = requests.get(planet_metadata_url).content.decode('utf-8')
        
        # Plantary metadata
        self.planet_metadata = json.loads(planet_metadata_request)
    
    def get_planet_table(self, idx_tce=1):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful for Kepler and TESS objects')
        
        planet_table_url = '{}/v{}/dvdata/{}/{}/table/?tce={}'.format(self.api_url, self.exomast_version, 
                                                                    self._collection, self.planet_id, idx_tce)
        
        if self.verbose: print('Acquiring Planetary Table from {}'.format(planet_table_url))
        
        planet_table_request = requests.get(planet_table_url).content.decode('utf-8')
        
        self._planet_table = json.loads(planet_table_request)
    
    def get_planet_phaseplot(self, idx_tce=1, embed=False):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful for Kepler and TESS objects')
        
        if embed:
            planet_phaseplot_url = '{}/v{}/dvdata/{}/{}/phaseplot/?tce={}&embed'.format(self._api_url, 
                                                                                        self._exomast_version, 
                                                                                        self._collection,
                                                                                        self.planet_id, idx_tce)
        else:
            planet_phaseplot_url = '{}/v{}/dvdata/{}/{}/phaseplot/?tce={}'.format(self.api_url, self.exomast_version, 
                                                                                self._collection, self.planet_id, idx_tce)
        
        if self.verbose: print('Acquiring Planetary Phase Plot from {}'.format(planet_phaseplot_url))
        
        planet_phaseplot_request = requests.get(planet_phaseplot_url).content.decode('utf-8')
        
        self.planet_phaseplot = planet_phaseplot_request
        # json.loads(planet_phaseplot_request) # to be injected into Bokeh (FINDME??)
    
    def make_spectra_plot(self, ax=None, add_current_fig=False, 
                            header=None, no_return=False, 
                            xscale='log', show_now = False):
        
        if self.verbose: print('Creating Planetary Spectral Plot for {}'.format(self.planet_name))
        
        if ax is None: ax = plt.gcf().get_axes()[0] if add_current_fig else plt.figure().add_subplot(111)
        
        if header is None: header = list(np.copy(self.header))
        
        if len(header) == 4:
            # assume same order as self.header:
            header.remove(header[1])
        
        if self.planetary_spectra_table is None: self.get_spectra()
        
        ax.errorbar(self.planetary_spectra_table[header[0]].values, 
                    self.planetary_spectra_table[header[1]].values, 
                    self.planetary_spectra_table[header[2]].values, fmt='o')
        
        ax.set_xscale(xscale)
        
        if show_now: plt.show()
        
        if not no_return: return ax

if __name__ == '__main__':
    planet_name0 = 'HAT-P-11 b'
    # planet_name1 = 'HD 189733 b'
    # planet_name2 = 'HD 209458 b'
    planet_name3 = 'kic12557548'
    
    hat11 = exoMAST_API(planet_name0, verbose=True)
    hd189 = exoMAST_API(planet_name1, verbose=True)
    hd209 = exoMAST_API(planet_name2, verbose=True)
    kic1255 = exoMAST_API(planet_name3, verbose=True)
    
    hat11.get_spectra_filelist()
    hat11.get_spectra()
    # hat11.get_spectra_bokeh_plot()
    hat11.make_spectra_plot()
    
    kic1255.get_identifiers()
    kic1255.get_properties()
    kic1255.get_tce()
    kic1255.get_planet_metadata()
    kic1255.get_planet_table()
    kic1255.get_planet_phaseplot()
    
    # fig = plt.figure()
    # ax = fig.add_subplot(111)
    #
    # hat11.make_spectra_plot(ax)
    # hd189.make_spectra_plot(ax)
    # hd209.make_spectra_plot(ax)
    #
    # plt.show()