import json
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests

class exoMAST_API(object):
    # Default exoMAS API website
    default_url = 'https://exo.mast.stsci.edu/api'
    
    # set of default placeholders:
    _spectra_filelist = None
    planetary_spectra_table = None
    spectra_bokeh_plot = None
    _planet_ident_dict = None
    _planet_property_dict = None
    tce = None
    planet_metadata = None
    _planet_table = None
    planet_phaseplot = None
    
    def __init__(self, planet_name, 
                    exomast_version=0.1, 
                    api_url=default_url, 
                    verbose=False,
                    quickstart=False):
        
        self.verbose = verbose
        
        if self.verbose: 
            print('Allocating Planetary Information from ', end=' ')
            print('{} version {} for {}.'.format(api_url,
                                                 exomast_version,
                                                 planet_name))
        
        self.api_url = '{}/v{}'.format(api_url, exomast_version)
        
        self.planet_name = planet_name
        self.exomast_version = exomast_version
        self.verbose = verbose
        
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
        
        if not quickstart:
            # Default behaviour to grab the planetary identifiers
            self.get_identifiers()
        if not quickstart:
            # Default behaviour to grab the planetary identifiers 
            self.get_properties()
        
    def get_spectra_filelist(self):
        
        planet_spec_fname_url = '{}/spectra/{}/filelist/'.format(self.api_url, 
                                                            self._planet_name)
        
        if self.verbose: 
            print('Acquiring Planetary Spectral File List from {}'.format(
                                                            planet_spec_fname_url))
        
        spec_fname_request = requests.get(planet_spec_fname_url)
        spec_fname_request = spec_fname_request.content.decode('utf-8')
        
        self._spectra_filelist = json.loads(spec_fname_request)
    
    def get_spectra(self, idx_spec=0, header=None):
        if header is None: header = self.header
        
        if self._spectra_filelist is None:self.get_spectra_filelist()
        
        spec_fname = self._spectra_filelist['filenames'][idx_spec]
        
        spectrum_request_url = "{}/spectra/{}/file/{}".format(self.api_url, 
                                                              self._planet_name, 
                                                              spec_fname)
        
        if self.verbose: 
            print('Acquiring Planetary Spectral File List from {}'.format(
                                                            spectrum_request_url))
        
        spectra_request = requests.get(spectrum_request_url)
        spectra_request = spectra_request.content.decode('utf-8')
        
        spectra_table = [list(filter(lambda a: a != '', line.split(' '))) 
                                        for line in spectra_request.split('\n') 
                                            if len(line) > 0 and line[0] != '#']
        
        self.planetary_spectra_table = pd.DataFrame(spectra_table, 
                                                    columns=header, 
                                                    dtype=float)
    
    def get_spectra_bokeh_plot(self, idx_tce=1):
        spectra_bokehplot_url = '{}/spectra/{}/plot/'.format(self.api_url, 
                                                             self._planet_name)
        
        if self.verbose: 
            print('Acquiring Planetary Bokeh Spectral Plot from {}'.format(
                                                            spectra_bokehplot_url))
        
        bokehplot_request = requests.get(spectra_bokehplot_url)
        spectra_bokehplot_request = bokehplot_request.content.decode('utf-8')
        
        # to be injected into Bokeh somehow (FINDME??)
        self.spectra_bokeh_plot = json.loads(spectra_bokehplot_request) 
    
    def get_identifiers(self, idx_list=0):
        planet_identifier_url = '{}/exoplanets/identifiers/?name={}'.format(
                                    self.api_url, self._planet_name)
        
        if self.verbose: print('Acquiring Planetary Identifiers from {}'.format(
                                                           planet_identifier_url))
        
        planet_ident_request = requests.get(planet_identifier_url)
        planet_ident_request = planet_ident_request.content.decode('utf-8')
        
        # Store dictionary of planetary identification parameters
        self._planet_ident_dict = json.loads(planet_ident_request)
        
        if isinstance(self._planet_ident_dict, list): 
            self._planet_ident_dict = self._planet_ident_dict[idx_list]
        
        for key in self._planet_ident_dict.keys():
            exec("self." + key + " = self._planet_ident_dict['" + key + "']")        
    
    def get_properties(self, idx_list=0):
        planet_properties_url = '{}/exoplanets/{}/properties'.format(
                                                                self.api_url, 
                                                                self._planet_name)
        
        if self.verbose: 
            print('Acquiring Planetary Properties from {}'.format(
                                                           planet_properties_url))
        
        planet_prop_request = requests.get(planet_properties_url)
        planet_properties_request = planet_prop_request.content.decode('utf-8')
        
        # Store dictionary of planetary properties
        self._planet_property_dict = json.loads(planet_properties_request)
        
        if isinstance(self._planet_property_dict, list): 
            self._planet_property_dict = self._planet_property_dict[idx_list]
        
        for key in self._planet_property_dict.keys():
            # print("self." + key + " = self._planet_property_dict['" + key + "']")
            exec("self." + key.replace('/', '_') + " = self._planet_property_dict['" + key + "']")
    
    def get_tce(self):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful \
                                for Kepler and TESS objects')
        
        tce_url = '{}/dvdata/{}/{}/tces/'.format(self.api_url, 
                                                 self._collection, 
                                                 self.planet_id)
        
        if self.verbose: 
            print('Acquiring Planetary Threshold Crossing Database from {}'.format(
                                                                        tce_url))
        
        tce_request = requests.get(tce_url).content.decode('utf-8')
        
        # theshold_crossing_event
        self.tce = json.loads(tce_request)
    
    def get_planet_metadata(self, idx_tce=1):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful for \
                                Kepler and TESS objects')
        
        if self.planet_id is None:
            planet_metadata_url = '{}/dvdata/{}/info'.format(self.api_url, 
                                                             self._collection)
        else:
            planet_metadata_url = '{}/dvdata/{}/{}/info/?tce={}'.format(
                                                                self.api_url, 
                                                                self._collection, 
                                                                self.planet_id, 
                                                                idx_tce)
        
        if self.verbose: print('Accessing Meta Data from {}'.format(
                                                            planet_metadata_url))
        
        planet_metadata_request = requests.get(planet_metadata_url)
        planet_metadata_request = planet_metadata_request.content.decode('utf-8')
        
        # Plantary metadata
        self._planet_metadata_dict = json.loads(planet_metadata_request)
        
        for key in self._planet_metadata_dict.keys():
            exec("self." + key + " = self._planet_metadata_dict['" + key + "']")
    
    def get_planet_table(self, idx_tce=1):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful for \
                                Kepler and TESS objects')
        
        planet_table_url = '{}/dvdata/{}/{}/table/?tce={}'.format(self.api_url, 
                                                                self._collection, 
                                                                self.planet_id, 
                                                                idx_tce)
        
        if self.verbose: print('Acquiring Planetary Table from {}'.format(
                                                                planet_table_url))
        
        planet_table_request = requests.get(planet_table_url)
        planet_table_request = planet_table_request.content.decode('utf-8')
        
        self._planet_table = json.loads(planet_table_request)
    
    def get_planet_phaseplot(self, idx_tce=1, embed=False):
        if self._collection not in ['kepler', 'tess']: 
            raise ValueError('This method is only useful for \
                                    Kepler and TESS objects')
        
        if embed:
            planet_phaseplot_url = '{}/dvdata/{}/{}/phaseplot/?tce={}&embed'.format(
                                                                self._api_url, 
                                                                self._collection,
                                                                self.planet_id, 
                                                                idx_tce)
        else:
            planet_phaseplot_url = '{}/dvdata/{}/{}/phaseplot/?tce={}'.format(
                                                                self.api_url, 
                                                                self._collection, 
                                                                self.planet_id, 
                                                                idx_tce)
        
        if self.verbose: print('Acquiring Planetary Phase Plot from {}'.format(
                                                            planet_phaseplot_url))
        
        planet_phplot_request = requests.get(planet_phaseplot_url)
        planet_phaseplot_request = planet_phplot_request.content.decode('utf-8')
        
        self.planet_phaseplot = json.loads(planet_phaseplot_request)
        # planet_phaseplot_request
        # json.loads(planet_phaseplot_request) 
        # to be injected into Bokeh somehow (FINDME??)
    
    def make_spectra_plot(self, ax=None, add_current_fig=False, 
                            header=None, no_return=False, 
                            xscale='log', show_now = False):
        
        if self.verbose: print('Creating Planetary Spectral Plot for {}'.format(
                                                                self.planet_name))
        
        if ax is None: ax = plt.gcf().get_axes()[0] \
                        if add_current_fig else plt.figure().add_subplot(111)
        
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
    planet_name0 = 'HAT-P-26 b'
    planet_name1 = 'HD 189733 b'
    planet_name2 = 'HD 209458 b'
    planet_name3 = 'KIC 12557548 b'
    
    hat26 = exoMAST_API(planet_name0, verbose=True)    
    hd189 = exoMAST_API(planet_name1, verbose=True)
    hd209 = exoMAST_API(planet_name2, verbose=True)
    kic1255 = exoMAST_API(planet_name3, verbose=True)
    
    hat26.get_spectra_filelist()
    hat26.get_spectra()
    # hat26.get_spectra_bokeh_plot()
    hat26.make_spectra_plot()
    
    kic1255.get_identifiers()
    kic1255.get_properties()
    kic1255.get_tce()
    kic1255.get_planet_metadata()
    kic1255.get_planet_table()
    kic1255.get_planet_phaseplot()
    
    fig = plt.figure()
    ax = fig.add_subplot(111)
    
    hat26.make_spectra_plot(ax)
    hd189.make_spectra_plot(ax)
    hd209.make_spectra_plot(ax)
    
    plt.show()