import sys
from setuptools import find_packages, setup

#
py_ver_range_min = 8
py_ver_range_max = max(sys.version_info[1], 9) + 1

VALID_PY_VERSIONS = [
    f"Programming Language :: Python :: 3.{v}"
    for v in range(py_ver_range_min, py_ver_range_max)
]

setup(
    name="typed_cap",
    setup_requires=['setuptools_scm'],
    use_scm_version={
        "write_to": "typed_cap/_version.py",
        "write_to_template": 'version = "{version}"\n',
    },
    author="MamoruDS",
    author_email="mamoruds.io@gmail.com",
    description="typed command line argument parser",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/MamoruDS/typed-cap",
    packages=find_packages(),
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        *VALID_PY_VERSIONS,
    ],
    python_requires=">=3.8",
)
