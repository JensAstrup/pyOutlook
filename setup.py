import setuptools

from pyOutlook import __release__

setuptools.setup(
    name='pyOutlook',
    version=__release__,
    packages=['pyOutlook', 'pyOutlook.internal', 'pyOutlook.core'],
    url='https://pypi.python.org/pypi/pyOutlook',
    license='MIT',
    author='Jens Astrup',
    author_email='jensaiden@gmail.com',
    description='A Python module for connecting to the Outlook REST API, without the hassle of dealing with the '
                'JSON formatting for requests/responses and the REST endpoints and their varying requirements',
    long_description='Documentation is available at `ReadTheDocs <http://pyoutlook.readthedocs.io/en/latest/>`_.',
    install_requires=['requests', 'python-dateutil'],
    tests_require=['coverage', 'pytest', 'pytest-cov'],
    keywords='outlook office365 microsoft email',
    classifiers=[
        'Development Status :: 5 - Production/Stable',

        'Intended Audience :: Developers',

        'Topic :: Communications :: Email :: Email Clients (MUA)',
        'Topic :: Office/Business',

        'License :: OSI Approved :: MIT License',

        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 2.7',
        'Natural Language :: English'
    ]
)
