import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="pywinupdate",
    version="0.0.1",
    author="Mathieu Tarral",
    author_email="mathieu.tarral@protonmail.com",
    description="Python controlled search and installation of Windows updates via WinRM and Ansible",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=setuptools.find_packages(),
    install_requires=requirements,
    entry_points={
        'console_scripts': [
            'pywinupdate = winupdate.__main__:main'
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires='>=3.7',
)
