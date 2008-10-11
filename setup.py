#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 
# This script is inspired by the debian package python-chardet
import os
import glob
from distutils.core import setup
from distutils.command.build import build

data_files = []

class build_locales(build):
    os.system("cd po && make >/dev/null 2>&1")

for (path, dirs, files) in os.walk("po"):
    if "jclic_browser.mo" in files:
        target = path.replace("po", "share/locale", 1)
        data_files.append((target, [os.path.join(path, "jclic_browser.mo")]))

def get_files(ipath, filters="*"):
    files = []
    for afile in glob.glob('%s/%s'%(ipath, filters) ):
        if os.path.isfile(afile):
            files.append(afile)
    return files

# images
data_files.append(('share/jclic_browser', ['pixmaps/logo.png'] ))


# files
data_files.append(('share/jclic_browser', ['jclic_browser.glade', 
                                           'library.jclic', 
                                           'downloader/jclic.db'] ))

data_files.append(('share/jclic_browser/utils', get_files("utils", "*sh") ))
data_files.append(('share/jclic_browser/utils', get_files("utils", "urls*") ))
data_files.append(('share/jclic_browser/utils', ['utils/data.sql'] ))



setup(name='JclicBrowser',
      description = 'JClic activity browser and downloader',
      version='0.1.0',
      author = 'Mario Izquierdo',
      author_email = 'mariodebian@gmail.com',
      url = 'http://www.tcosproject.org',
      license = 'GPLv2',
      platforms = ['linux'],
      keywords = ['thin client', 'teacher tool', 'jclic', 'learning'],
      packages=['jclic'],
      package_dir = {'':''},
      scripts=['jclic-browser', 'utils/jclicbrowser-sudo'],
      cmdclass = {'build': build_locales},
      data_files=data_files
      )

