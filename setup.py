from os.path import join, dirname
import os
from setuptools import setup, find_packages

__version__ = open(join(dirname(__file__), 'oncall_slackbot/VERSION')).read().strip()

install_requires = (
    'slackbot==0.5.5',
    'pygerduty>=0.38.2',
    'pytz>=2019.3',
    'humanize>=0.5.1',
    'spacy==2.2.3',
)  # yapf: disable

excludes = (
    '*test*',
    '*local_settings*',
) # yapf: disable

setup(name='oncall-slackbot',
      version=__version__,
      license='MIT',
      description='Extended slackbot made specifically to handle on-call requests',
      author='Brian Saville',
      author_email='bksaville@gmail.com',
      url='http://github.com/bluesliverx/oncall-slackbot',
      platforms=['Any'],
      packages=find_packages(exclude=excludes),
      install_requires=install_requires,
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 2',
                   'Programming Language :: Python :: 2.7',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6'])
