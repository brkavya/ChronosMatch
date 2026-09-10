from setuptools import setup
from Cython.Build import cythonize

setup(
    ext_modules=cythonize("src/matching_engine.pyx", language_level="3")
)