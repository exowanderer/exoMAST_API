import os

from astropy import units
from json import loads as jsonloads
from numpy import copy as npcopy
from pandas import DataFrame
from requests import get as requests_get, HTTPError
from sklearn.externals import joblib

class exoMAST_API(object):
	"""The summary line for a class docstring should fit on one line.
		If the class has public attributes, they may be documented here
		in an ``Attributes`` section and follow the same formatting as a
		function's ``Args`` section. Alternatively, attributes may be documented
		inline with the attribute's declaration (see __init__ method below).
		Properties created with the ``@property`` decorator should be documented
		in the property's getter method.
		Attributes:
			attr1 (str): Description of `attr1`.
			attr2 (:obj:`int`, optional): Description of `attr2`.
	"""
	
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
	canonical_name = None
	_collection = None

	def __init__(self, planet_name, exomast_version=0.1, 
						api_url=default_url, verbose=False, quickstart=False):
		"""Example of docstring on the __init__ method.

		The __init__ method may be documented in either the class level
		docstring, or as a docstring on the __init__ method itself.
		Either form is acceptable, but the two should not be mixed. Choose one
		convention to document the __init__ method and be consistent with it.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1 (str): Description of `param1`.
			param2 (:obj:`int`, optional): Description of `param2`. Multiple
				lines are supported.
			param3 (:obj:`list` of :obj:`str`): Description of `param3`.
		"""
		self.verbose = verbose
		
		if self.verbose: 
			print('Allocating Planetary Information from '
				  '{} version {} for {}.'.format(api_url,
												 exomast_version,
												 planet_name))
		
		self.api_url = '{}/v{}'.format(api_url, exomast_version)
		
		# this is static
		self.input_planet_name = planet_name 

		# this *may* be updated in `get_identifiers`
		self.planet_name = planet_name
		self._planet_url_name = self.planet_name.replace(' ', '%20')
		
		self.exomast_version = exomast_version
		self.verbose = verbose
		
		# self.get_canonical_name()

		# For use with `self.get_spectra`
		self.header = ['Wavelength (microns)', 
						'Delta Wavelength (microns)',
						'(Rp/Rs)^2',
						'(Rp/Rs)^2 +/-uncertainty']
		
		if 'kic' in planet_name.lower(): 
			self._collection= 'kepler'
			self.planet_name.replace('KIC ', 'KIC') # delete space
			self.planet_id = self.planet_name.lower().replace('kic', '')

		if 'tic' in planet_name.lower(): 
			self._collection = 'tess'
			self.planet_name.replace('TIC ', 'TIC') # delete space
			self.planet_id = self.planet_name.lower().replace('tic', '')

		if not quickstart:
			# Default behaviour to grab the planetary identifiers
			self.get_identifiers()

			planet_name_ = self.planet_name.replace(' ', '_')
			default_load_dir = os.environ['HOME'] + '/.exomast_api/'
			load_filename = '{}.exomast.joblib.save'
			load_filename = load_filename.format(planet_name_)
			load_filename = '{}/{}'.format(default_load_dir, load_filename)
			print(load_filename)

			if os.path.exists(load_filename):
				self.load_instance()
			else:
				# Default behaviour to grab the planetary identifiers 
				self.get_properties()
				self.save_instance()
	
	def check_request(self, request_url, request_return):
		api_example_url = "https://exo.mast.stsci.edu/api/v0.1/exoplanets/"\
						  "identifiers/?name=kepler%201b"

		if 'Internal Server Error' in request_return:
			print("Cannot access exo.mast.stsci.edu via API.\n"
				  " Confirm that the URL "
				  "{} exits in your browser.\n".format(
											request_url.replace(' ', '%20')))

			print("\nIf that site does not load, then confirm that the URL"
				  " {} loads instead."
				  " The second URL is the API example URL."
				  " If it does not load, then the API server is likely"
				  " unavailable".format(api_example_url))

			raise HTTPError('{} generated the error:\n{}'.format(request_url, 
															request_return))

	def get_identifiers(self, idx_list=0):
		""" Class methods are similar to regular functions.
			
			Note:
				Do not include the `self` parameter in the ``Args`` section.
			Args:
				param1: The first parameter.
				param2: The second parameter.
			Returns:
				True if successful, False otherwise.
		"""

		planet_identifier_url = '{}/exoplanets/identifiers/?name={}'.format(
									self.api_url, self._planet_url_name)
		
		if self.verbose: print('Acquiring Planetary Identifiers '
								'from {}'.format(planet_identifier_url))
		
		planet_ident_request = requests_get(planet_identifier_url)
		planet_ident_request = planet_ident_request.content.decode('utf-8')
		
		if len(planet_ident_request) == 0:
			raise HTTPError('Could not find identifier in table.'
							' It is possible that the target is not '
							' included in the database as named; or it may not'
							' exist.')

		self.check_request(planet_identifier_url, planet_ident_request)

		# Store dictionary of planetary identification parameters
		self._planet_ident_dict = jsonloads(planet_ident_request)
		
		if isinstance(self._planet_ident_dict, list): 
			self._planet_ident_dict = self._planet_ident_dict[idx_list]
		
		for key in self._planet_ident_dict.keys():
			exec("self." + key + " = self._planet_ident_dict['" + key + "']")

		if 'canonicalName' in self._planet_ident_dict.keys():
			self.planet_name = self._planet_ident_dict['canonicalName']
			self._planet_url_name = self.planet_name.replace(' ', '%20')
	
	def get_properties(self, idx_list=0):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		planet_properties_url = '{}/exoplanets/{}/properties'.format(
														self.api_url, 
														self._planet_url_name)
		
		if self.verbose: 
			print('Acquiring Planetary Properties from {}'.format(
														planet_properties_url))
		
		planet_prop_request = requests_get(planet_properties_url)
		planet_properties_request = planet_prop_request.content.decode('utf-8')
		
		self.check_request(planet_properties_url, planet_properties_request)

		# Store dictionary of planetary properties
		self._planet_property_dict = jsonloads(planet_properties_request)
		
		if isinstance(self._planet_property_dict, list) \
			and len(self._planet_property_dict) > 0: 
			
			if idx_list >= len(self._planet_property_dict):
				raise IndexError('{} does not exist in range {}'.format(
						idx_list, len(self._planet_property_dict)))

			self._planet_property_dict = self._planet_property_dict[idx_list]
		else:
			self._planet_property_dict = {}

		for key in self._planet_property_dict.keys():
			# print("self." + key + " = self._planet_property_dict['" + key + "']")
			exec("self." + key.replace('/', '_') + 
				" = self._planet_property_dict['" + key + "']")

		if not hasattr(self,'Rp_Rs') and \
			hasattr(self,'Rp') and hasattr(self,'Rs'):
				# This might differ from `self.transit_depth`
				Rp_sun = (self.Rp * units.R_jup).to(units.R_sun).value
				self.Rp_Rs = Rp_sun / self.Rs

	def get_spectra_filelist(self):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		planet_spec_fname_url = '{}/spectra/{}/filelist/'.format(self.api_url, 
														self._planet_url_name)
		
		if self.verbose: 
			print('Acquiring Planetary Spectral File List from {}'.format(
														planet_spec_fname_url))
		
		spec_fname_request = requests_get(planet_spec_fname_url)
		spec_fname_request = spec_fname_request.content.decode('utf-8')
		
		self.check_request(planet_spec_fname_url, spec_fname_request)

		self._spectra_filelist = jsonloads(spec_fname_request)
	
	def get_spectra(self, idx_spec=0, header=None, caption=None):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		if header is None: header = self.header
		
		if self._spectra_filelist is None:self.get_spectra_filelist()
		
		spec_fname = self._spectra_filelist['filenames'][idx_spec]
		
		spectrum_request_url = "{}/spectra/{}/file/{}".format(
														self.api_url, 
														self._planet_url_name, 
														spec_fname)
		
		if self.verbose: 
			print('Acquiring Planetary Spectral File List from {}'.format(
														spectrum_request_url))
		
		spectra_request = requests_get(spectrum_request_url)
		spectra_request = spectra_request.content.decode('utf-8')
		
		spectra_table = [list(filter(lambda a: a != '', line.split(' '))) 
									for line in spectra_request.split('\n') 
										if len(line) > 0 and line[0] != '#']
		
		self.planetary_spectra_table = DataFrame(spectra_table, 
													columns=header, 
													dtype=float)
	
	def get_spectra_bokeh_plot(self, idx_tce=1):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		spectra_bokehplot_url = '{}/spectra/{}/plot/'.format(self.api_url, 
														self._planet_url_name)
		
		if self.verbose: 
			print('Acquiring Planetary Bokeh Spectral Plot from {}'.format(
														spectra_bokehplot_url))
		
		bokehplot_request = requests_get(spectra_bokehplot_url)
		spectra_bokehplot_request = bokehplot_request.content.decode('utf-8')
		
		self.check_request(spectra_bokehplot_url, spectra_bokehplot_request)

		# to be injected into Bokeh somehow (FINDME??)
		self.spectra_bokeh_plot = jsonloads(spectra_bokehplot_request) 
	
	def get_tce(self):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		if self._collection not in ['kepler', 'tess']: 
			raise ValueError('This method is only useful'
							 ' for Kepler and TESS objects')
		
		tce_url = '{}/dvdata/{}/{}/tces/'.format(self.api_url, 
												 self._collection, 
												 self.planet_id)
		
		if self.verbose: 
			print('Acquiring Planetary Threshold Crossing Database from {}'.format(
																		tce_url))
		
		tce_request = requests_get(tce_url).content.decode('utf-8')
		
		self.check_request(tce_url, tce_request)

		# theshold_crossing_event
		self.tce = jsonloads(tce_request)
	
	def get_planet_metadata(self, idx_tce=1):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		if self._collection not in ['kepler', 'tess']: 
			raise ValueError('This method is only useful for '
							 'Kepler and TESS objects')
		
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
		
		planet_metadata_request = requests_get(planet_metadata_url)
		planet_metadata_request = planet_metadata_request.content
		planet_metadata_request = planet_metadata_request.decode('utf-8')
		
		self.check_request(planet_metadata_url, planet_metadata_request)

		# Plantary metadata
		self._planet_metadata_dict = jsonloads(planet_metadata_request)
		
		for key in self._planet_metadata_dict.keys():
			att_name = key.replace(' ', '_')
			exec("self." + att_name + \
				 " = self._planet_metadata_dict['" + key + "']")
	
	def get_planet_table(self, idx_tce=1):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		if self._collection not in ['kepler', 'tess']: 
			raise ValueError('This method is only useful for'
							 ' Kepler and TESS objects')
		
		planet_table_url = '{}/dvdata/{}/{}/table/?tce={}'.format(self.api_url, 
																self._collection, 
																self.planet_id, 
																idx_tce)
		
		if self.verbose: print('Acquiring Planetary Table from {}'.format(
																planet_table_url))
		
		planet_table_request = requests_get(planet_table_url)
		planet_table_request = planet_table_request.content.decode('utf-8')
		
		self.check_request(planet_table_url, planet_table_request)

		self._planet_table = jsonloads(planet_table_request)
	
	def get_planet_phaseplot(self, idx_tce=1, embed=False):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		if self._collection not in ['kepler', 'tess']: 
			raise ValueError('This method is only useful for'
							 ' Kepler and TESS objects')
		
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
		
		planet_phplot_request = requests_get(planet_phaseplot_url)
		planet_phaseplot_request = planet_phplot_request.content
		planet_phplot_request = planet_phplot_request.decode('utf-8')
		
		self.check_request(planet_phaseplot_url, planet_phplot_request)

		self.planet_phaseplot = jsonloads(planet_phaseplot_request)
		# planet_phaseplot_request
		# jsonloads(planet_phaseplot_request) 
		# to be injected into Bokeh somehow (FINDME??)
	
	def make_spectra_plot(self, ax=None, add_current_fig=False, 
							header=None, no_return=False, 
							xscale='log', show_now = False):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		import matplotlib.pyplot as plt
		
		if self.verbose: 
			print('Creating Planetary Spectral Plot for {}'.format(
					self.input_planet_name))
		
		if ax is None: ax = plt.gcf().get_axes()[0] \
						if add_current_fig else plt.figure().add_subplot(111)
		
		if header is None: header = list(npcopy(self.header))
		
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
	
	def print_table(self, table_name=None, flt_fmt=None, def_fmt=None, 
							print_none=False, latex_style=False, header=None, 
							caption=None, print_to_file=None, overwrite=False):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		
		# For latex, output to a .tex file and then use \input{filename.tex}
		# https://tex.stackexchange.com/questions/133021/table-input-from-separate-tex-file
		"""
		
		if table_name not in ['ident','property']: raise ValueError("table_name must be either 'ident' or 'property'")
		
		if 'ident' in table_name.lower(): table_name = 'ident'
		if 'prop' in table_name.lower(): table_name = 'property'
		
		if caption is None: caption = 'INSERT CAPTION HERE'
		
		exec("table_to_print = self._planet_"+table_name+"_dict", locals(), globals())
		
		max_key_len = 0
		for key in table_to_print.keys():
			if len(key) > max_key_len: 
				max_key_len = len(key)
		
		if flt_fmt is None: 
			if latex_style:
				flt_fmt = '\t\t{:<' + str(max_key_len) + '} & {:.2f}\\\\'
			else:
				flt_fmt = '{:<' + str(max_key_len) + '}\t{:.2f}'
		if def_fmt is None: 
			if latex_style:
				def_fmt = '\t\t{:<' + str(max_key_len) + '} & {}\\\\'
			else:
				def_fmt = '{:<' + str(max_key_len) + '}\t{}'
		
		if isinstance(print_to_file, str):
			if os.path.exists(print_to_file) and not overwrite:
				print('[WARNING] This will overwrite existing {}'.format(print_to_file))
				print_to_file = print_to_file + '.new'
				
				print('[INFO] Added `.new` to end as {}'.format(print_to_file))
				
				# while os.path.exists(print_to_file):
				#	 print_to_file = print_to_file[:-1] + str(int(print_to_file[-1])+1)
			
			# Add '.tex' in case the above `if` adds ".new"
			if latex_style and print_to_file[-4:] != '.tex':
				print_to_file = print_to_file + '.tex'
			
			print('[INFO] Storing table in {}'.format(print_to_file))
			
			fileout = open(print_to_file, 'w')
		else:
			import sys
			fileout = sys.stdout
		
		if latex_style:
			print('\\begin{table}[h]', file=fileout)
			print('\t\\begin{tabular}{cc}', file=fileout)
			print('\t\t\\hline\\\\', file=fileout)
			
			# Header: Epoch &  $T_c-2450000$  & $i$  & $a/{R_*}$ & ${R_p}/{R_*}$ & $c_0$ \\
			if header is not None: print('\t\t{}\\\\'.format(header), file=fileout)
		
		for key,val in table_to_print.items(): 
			# if val is none; but 
			if val is not None or print_none:
				
				key = key.replace('_', ' ')
				if isinstance(val, str): val = val.replace('_', '\_')
				
				fmt = flt_fmt if isinstance(val, float) else def_fmt
				
				print(fmt.format(key,val), file=fileout)
		
		if latex_style:
			print('\t\\end{tabular}', file=fileout)
			print('\t\\caption{'+caption+'}', file=fileout)
			print('\t\\label{tbl:planet_'+table_name+'}', file=fileout)
			print('\\end{table}', file=fileout)
		
		if isinstance(print_to_file, str): fileout.close()
	
	def print_ident_table(self, flt_fmt=None, def_fmt=None, print_none=False, latex_style=False, header=None, caption=None, print_to_file=None):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		self.print_table(table_name='ident', 
			flt_fmt=flt_fmt, def_fmt=def_fmt, print_none=print_none, latex_style=latex_style, header=header, caption=caption, print_to_file=print_to_file)
	
	def print_properties_table(self, flt_fmt=None, def_fmt=None, print_none=False, latex_style=False, header=None, caption=None, print_to_file=None):
		"""Class methods are similar to regular functions.
		Note:
			Do not include the `self` parameter in the ``Args`` section.
		Args:
			param1: The first parameter.
			param2: The second parameter.
		Returns:
			True if successful, False otherwise.
		"""
		self.print_table(table_name='property', 
			flt_fmt=flt_fmt, def_fmt=def_fmt, print_none=print_none, latex_style=latex_style, header=header, caption=caption, print_to_file=print_to_file)

	def save_instance(self, save_dir=None, verbose=False):
		default_save_dir = os.environ['HOME'] + '/.exomast_api'
		save_dir = save_dir or default_save_dir
		if not os.path.exists(save_dir): os.mkdir(save_dir)

		planet_name_ = self.planet_name.replace(' ', '_')
		save_filename = '{}.exomast.joblib.save'.format(planet_name_)
		save_filename = '{}/{}'.format(save_dir, save_filename)

		if self.verbose or verbose:
			print('[INFO]: Saving Results to {}'.format(save_filename))
		
		joblib.dump(self.__dict__ , save_filename)

	def load_instance(self, load_dir=None):
		default_load_dir = os.environ['HOME'] + '/.exomast_api/'
		load_dir = load_dir or default_load_dir
		if not os.path.exists(load_dir): os.mkdir(load_dir)

		planet_name_ = self.planet_name.replace(' ', '_')
		load_filename = '{}.exomast.joblib.save'.format(planet_name_)
		load_filename = '{}/{}'.format(load_dir, load_filename)
		
		if self.verbose or verbose:
			print('[INFO]: Loading Results from {}'.format(load_filename))

		self.__dict__ = joblib.load(load_filename)

if __name__ == '__main__':
	from exomast_api import exoMAST_API
	input_planet_name0 = 'HAT-P-26 b'
	input_planet_name1 = 'HD 189733 b'
	input_planet_name2 = 'HD 209458 b'
	input_planet_name3 = 'KIC 12557548 b'
	
	hat26 = exoMAST_API(input_planet_name0, verbose=True)
	hd189 = exoMAST_API(input_planet_name1, verbose=True)
	hd209 = exoMAST_API(input_planet_name2, verbose=True)
	kic1255 = exoMAST_API(input_planet_name3, verbose=True)
	
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
	
	## Plotting Spectra
	import matplotlib.pyplot as plt
	fig = plt.figure()
	ax = fig.add_subplot(111)
	
	hat26.make_spectra_plot(ax)
	hd189.make_spectra_plot(ax)
	hd209.make_spectra_plot(ax)
	
	plt.show()