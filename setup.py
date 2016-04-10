from distutils.core import setup

setup(
    name='pyOutlook',
    version='1.1b0',
    packages=['pyOutlook'],
    py_modules=['main.py'],
    url='https://pypi.python.org/pypi/pyOutlook',
    license='',
    author='Jens Astrup',
    author_email='jensaiden@gmail.com',
    description='A Python module for connecting to the Outlook REST API, without the hassle of dealing with the JSON '
                'formatting for requests/responses and the REST endpoints and their varying requirements'
)
