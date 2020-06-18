from setuptools import setup, find_packages

setup(
    name = 'exomast_api',
    version = '0.1',
    url = 'https://github.com/exowanderer/exomast_api',
    author = 'Jonathan Fraine',
    author_email = 'jfraine @ spacescience.org',
    description = 'exoMAST API Python Wrapper',
    packages = find_packages(),    
    install_requires = ['numpy >= 1.11.1', 'matplotlib >= 1.5.1'],
)
