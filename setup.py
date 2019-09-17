from setuptools import setup
import versioneer

if __name__ == "__main__":
    setup(
        name="etserver",
        version=versioneer.get_version(),
        cmdclass=versioneer.get_cmdclass(),
        entry_points={
            'console_scripts': ['et=etserver.serve:main']
        },
    )
