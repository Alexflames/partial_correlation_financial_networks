from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension
import numpy

ext_modules=[
    Extension("louvain_cython", ["louvain_cython.pyx"], extra_compile_args = ["-ffast-math"], include_dirs=[numpy.get_include()]),
]


setup(
  ext_modules = cythonize(["*.pyx"]),
  include_dirs=[numpy.get_include()]
  )
