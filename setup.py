import setuptools

with open('requirements.txt') as reqf:
    requirements = reqf.read().split()


setuptools.setup(
    name='installSynApps',
    version='R2-0',
    cmdclass='',
    author='jakubwlodek',
    author_email=None,
    license='BSD (3-clause)',
    url='https://github.com/epicsNSLS2-deploy/installSynApps',
    packages=setuptools.find_packages(),
    python_requires='>=3.2',
    install_requirements=requirements,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python :: 3.6.8",
    ]
)