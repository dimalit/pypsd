from paver.setuputils import setup
from paver.setuputils import find_package_data
from paver.easy import *

setup(
	name="pypsd",
	packages=['pypsd'],
	package_data=find_package_data('pypsd', 'pypsd', only_in_packages=False),
	version="0.1",
	url="http://code.google.com/p/pypsd",
	author="Aleksandr Motsjonov",
	author_email="soswow@gmail.com",
	sphinx=Bunch(
		builddir="_build"
	)
)

@task
@needs('setuptools.command.sdist')
def sdist():
	"""Overrides sdist to make sure that our setup.py is generated."""
	pass
