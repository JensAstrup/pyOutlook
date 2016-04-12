import setuptools

setuptools.setup(
    name='pyOutlook',
    version='2.2b0',
    packages=['pyOutlook', 'pyOutlook.internal'],
    url='https://pypi.python.org/pypi/pyOutlook',
    license='',
    author='Jens Astrup',
    author_email='jensaiden@gmail.com',
    description='A Python module for connecting to the Outlook REST API, without the hassle of dealing with the '
                'JSON formatting for requests/responses and the REST endpoints and their varying requirements',
    requires=['requests']
)
