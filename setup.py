import setuptools

from bear import __version__ as version

with open('README.md') as file:
    long_description = file.read()

setuptools.setup(
    name='pybear',
    version=version,
    description='Trivial python library to access Bear Writer notes',
    long_description=long_description,
    long_description_content_type='text/markdown',
    author='Richard Clark',
    author_email='richard@redspider.co.nz',
    url='https://github.com/redspider/pybear',
    classifiers=[
        'Programming Language :: Python :: 3',
        'Operating System :: OS Independent',
    ],
    install_requires=[
        'Markdown',
    ],

    packages=setuptools.find_packages(),
    entry_points={
        'console_scripts': [
            'bear_to_html = bear.bear_to_html:main',
            'bear_to_jekyll = bear.bear_to_jekyll:main',
        ],
    },
)
