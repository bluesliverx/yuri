from os.path import join, dirname
from setuptools import setup, find_packages

__version__ = open(join(dirname(__file__), 'yuri/VERSION')).read().strip()

install_requires = (
    'inquirer>=2.6.3',
)  # yapf: disable

excludes = (
    '*test*',
) # yapf: disable

setup(name='yuri',
      version=__version__,
      license='MIT',
      description='Yuri the trainer who trains for slackbot ML',
      author='Brian Saville',
      author_email='bksaville@gmail.com',
      url='http://github.com/bluesliverx/yuri',
      platforms=['Any'],
      packages=find_packages(exclude=excludes),
      install_requires=install_requires,
      classifiers=['Development Status :: 4 - Beta',
                   'License :: OSI Approved :: MIT License',
                   'Operating System :: OS Independent',
                   'Programming Language :: Python',
                   'Programming Language :: Python :: 3',
                   'Programming Language :: Python :: 3.4',
                   'Programming Language :: Python :: 3.5',
                   'Programming Language :: Python :: 3.6',
                   'Programming Language :: Python :: 3.7'])
