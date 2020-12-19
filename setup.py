from setuptools import setup

setup(name='owmeta_modeldb',
      install_requires=[
          'owmeta_core',
          'beautifulsoup4',
          'requests',
          'cachecontrol[filecache]'],
      packages=['owmeta_modeldb'])
