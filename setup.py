from setuptools import setup, find_packages

_REQUIRES = [
    "sanic",
    "aiohttp",
    "motor",
]

setup(
    name="etelemetry",
    author="Mathias Goncalves",
    version="0.0.1dev0",
    packages=find_packages(),
    entry_points={'console_scripts': [
     'et=etelemetry.app:main'
     ]},
     install_requires=_REQUIRES,
)
