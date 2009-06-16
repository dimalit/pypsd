from paver.setuputils import setup

setup(
    name="Python PSD Parser",
    packages=['pypsd'],
    package_data={'pypsd': ['conf/*.conf', 'psd_files/*.psd']},
    version="0.1",
    url="http://code.google.com/p/pypsd",
    author="Aleksandr Motsjonov",
    author_email="soswow@gmail.com"
)
