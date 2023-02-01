# -*- coding: utf-8 -*-
# @Author: Spencer H
# @Date:   2022-09-01
# @Last Modified by:   Spencer H
# @Last Modified date: 2022-09-01
# @Description:
"""

"""

from setuptools import setup


setup(name='rad',
      version=0.1,
      description='Library of radar utilities',
      url='',
      author='Spencer Hallyburton',
      author_email='spencer@shally.dev',
      packages=['rad'],
      install_requires=['numpy', 'pyserial', 'pyqtgraph', 'pyqt5'])