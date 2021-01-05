from setuptools import setup

setup(name='owmeta_modeldb',
      install_requires=[
          'owmeta_core>=0.14.0.dev0',
          'beautifulsoup4',
          'requests',
          'cachecontrol[filecache]'],
      packages=['owmeta_modeldb'])
