from setuptools import setup, find_packages
import versioneer

_REQUIRES = [
    "sanic",
    "aiohttp",
    "aiofiles",
    "requests",
    "motor",
]

setup(
    name="etserver",
    author="Mathias Goncalves",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    entry_points={
        'console_scripts': ['et=etserver.app:main']
    },
    install_requires=_REQUIRES,
)
