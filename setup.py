from setuptools import setup, find_packages


setup(
    name='cariban',
    version='0.0',
    description='cariban',
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
            'pytest>=5',
            'pytest-clld',
            'pytest-mock',
            'pytest-cov',
            'clld-phylogeny-plugin',
            'coverage>=4.2',
            'selenium',
            'zope.component>=3.11.0',
        ],
    },
    test_suite="tests",
    entry_points="""\
    [paste.app_factory]
    main = cariban:main
""")
