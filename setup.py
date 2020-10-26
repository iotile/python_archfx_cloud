from setuptools import setup
import version

setup(name='archfx_cloud',
    version=version.version,
    description='Python client for https://archfx.io',
    url='https://github.com/iotile/python_archfx_cloud',
    author='Arch Systems Inc.',
    author_email="info@arch-iot.com",
    license='MIT',
    packages=[
        'archfx_cloud',
        'archfx_cloud.api',
        'archfx_cloud.utils'
    ],
    entry_points={
        'pytest11': ['mock_cloud = archfx_cloud.utils.mock_cloud']
    },
    install_requires=[
        'requests>=2.21.0',
        'python-dateutil'
    ],
    keywords=["iotile", "archfx", "arch", "iot", "automation"],
    classifiers=[
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules"
    ],
    zip_safe=False)
