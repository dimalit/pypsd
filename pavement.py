from paver.setuputils import setup
from paver.easy import *

setup(
    name="pypsd",
    packages=['pypsd'],
    package_data={'pypsd': ['/pypsd/conf/*.conf', 'samples/*.psd', 'docs/*.pdf']},
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
