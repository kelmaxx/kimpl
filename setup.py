# -*- coding: utf-8 -*-
"""
Created on Thu Aug 30 09:46:30 2018

@author: Kelly
"""

from setuptools import setup,find_packages

description="""
kimple is a package designed to extend the functionality of interactive tools in matplotlib.

"""


setup(name='kimpl',
      version='1.5.0',
      description=description,
      url="",
      author="Kelly Wilson",
      author_email="kelmaxx@gmail.com",
      license='University of Texas',
      classifiers=['Development Status :: 3 - Alpha',
                   'Intended Audience :: Developers',
                   'Topic :: Software Development :: Build Tools',
                   'License :: UTlicense',
                   'Programming Language :: Python :: 3'],
      keywords='kimpl matplotlib interactive',
      packages=find_packages(),
      install_requires=['PyQt5>=5.12','matplotlib>=3.6','dill>=0.2.8'],
      python_requires='>=3.8',
      package_data={'kimpl':['*.ico']},
      include_package_data=True,
      data_files=['LICENSE.txt','README.md'],
      zip_safe=False)