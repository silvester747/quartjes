#!/usr/bin/env python

from distutils.core import setup

setup(name='Quartjesavond',
      version='2014.1',
      description='QuartjesAvond application',
      author='Rob van der Most',
      author_email='Rob@RMSoft.nl',
      package_dir={'': 'src'},
      packages=['quartjes',
                'quartjes.connector',
                'quartjes.controllers',
                'quartjes.gui',
                'quartjes.gui.cocos',
                'quartjes.models',
                'quartjes.resources',
                'quartjes.util'],
      requires=['axel', 
                'pyglet(>=1.2)', 
                'cocos2d(>=0.5.5)'],
      scripts=['src/quartjes_server.py',
               'src/quartjes_client.py',
               'src/quartjes_cocos_gui.py'],
      package_data={'quartjes.resources': ['*.png']},
     )