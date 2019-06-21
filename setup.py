from setuptools import setup, find_packages


setup(
    name='cariban_morphemes',
    version='0.0',
    description='cariban_morphemes',
    classifiers=[
        "Programming Language :: Python",
        "Framework :: Pyramid",
        "Topic :: Internet :: WWW/HTTP",
        "Topic :: Internet :: WWW/HTTP :: WSGI :: Application",
    ],
    author='',
    author_email='',
    url='',
    keywords='web pyramid pylons',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'clld',
    ],
    extras_require={
        'dev': ['flake8', 'waitress'],
        'test': [
            'mock',
            'pytest>=3.1',
            'pytest-clld',
            'pytest-mock',
            'pytest-cov',
            'clld_phylogeny_plugin',
            'coverage>=4.2',
            'selenium',
            'zope.component>=3.11.0',
        ],
    },
    test_suite="cariban_morphemes",
    entry_points="""\
    [paste.app_factory]
    main = cariban_morphemes:main
""")
