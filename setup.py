import pathlib
from setuptools import find_packages, setup, Command
import version

# The directory containing this file
HERE = pathlib.Path(__file__).parent

# The text of the README file
README = (HERE / "README.md").read_text()


setup(name='archfx_cloud',
    version=version.version,
    description='Python client for https://archfx.io',
    long_description=README,
    long_description_content_type="text/markdown",
    url='https://github.com/iotile/python_archfx_cloud',
    author='Arch Systems Inc.',
    author_email="info@archsys.io",
    license='MIT',
    packages=find_packages(exclude=("tests",)),
    entry_points={},
    python_requires=">=3.7,<4",
    install_requires=[
        'requests>=2.21.0',
        'python-dateutil',
        'msgpack>=1.0.2,<1.1',
        'typedargs>=1.1.2,<2',
    ],
    keywords=["iotile", "archfx", "arch", "iiot", "automation"],
    classifiers=[
        "Programming Language :: Python",
        'Programming Language :: Python :: 3',
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: Implementation :: PyPy",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    zip_safe=False
)
