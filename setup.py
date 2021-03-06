import os
import codecs
import versioneer
from setuptools import setup, find_packages

HERE = os.path.abspath(os.path.dirname(__file__))


def read(*parts):
    with codecs.open(os.path.join(HERE, *parts), 'rb', 'utf-8') as f:
        return f.read()


setup(
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    name='txacme',
    description='ACME protocol implementation for Twisted',
    license='Expat',
    url='https://github.com/mithrandi/txacme',
    author='Tristan Seligmann',
    author_email='mithrandi@mithrandi.net',
    maintainer='Tristan Seligmann',
    maintainer_email='mithrandi@mithrandi.net',
    long_description=read('README.rst'),
    packages=find_packages(where='src') + ['twisted.plugins'],
    package_dir={'': 'src'},
    zip_safe=True,
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: Developers',
        'Natural Language :: English',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: Implementation :: CPython',
        'Programming Language :: Python :: Implementation :: PyPy',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    install_requires=[
        'Twisted[tls]>=15.5.0',
        'acme>=0.4.0',
        'attrs',
        'eliot>=0.8.0',
        'pem>=16.1.0',
        'treq>=15.1.0',
        'txsni',
        ],
    extras_require={
        'test': [
            'fixtures>=1.4.0',
            'hypothesis>=3.1.0,<4.0.0',
            'testrepository>=0.0.20',
            'testscenarios',
            'testtools>=2.0.0',
            ],
        },
    )
