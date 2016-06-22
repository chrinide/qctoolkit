from setuptools import setup
from distutils.core import Extension
#from Cython.Build import cythonize
import numpy as np
import glob, os

version = '0.0.10'

required = [
  #'cython',
  'numpy>=1.11.0',
  'scipy>=0.16.0',
  'pandas>=0.17.1',
  'matplotlib>=1.5.1',
  'pyyaml>=3.11',
  'psutil',
  'networkx',
  'periodictable',
  'mdtraj',
  'paramiko',
]

# to enable openmp, use:
#  extra_compile_args=['-fopenmp', '-fpic']
#  and extra_link_args=['-lgomp', '-shared']
# Cython extension:
#  Extension(name = 'qctoolkit.path.to.extension.name',
#    sources = ['qctoolkit/path/to/extension/name.pyx'])

#            Extension(name = "qctoolkit.read_cube", 
#              extra_compile_args=['-O3'],
#              sources = ['qctoolkit/src/readcubemodule.c']),
c_module = [Extension(name = "qctoolkit.ML.kernel_matrix", 
              sources = ['qctoolkit/ML/c_extension/'+\
                         'kernelmatrixmodule.c',
                         'qctoolkit/ML/c_extension/kernels.c'],
              extra_compile_args=['-fopenmp', '-fpic',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.ML.kernel_vectors", 
              sources = ['qctoolkit/ML/c_extension/'+\
                         'kernelvectorsmodule.c',
                         'qctoolkit/ML/c_extension/kernels.c'],
              extra_compile_args=['-fopenmp', '-fpic',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.analysis.read_cube", 
              extra_compile_args=['-O3'],
              sources = ['qctoolkit/analysis/c_extension/'+\
                         'readcubemodule.c']),
            Extension(name = "qctoolkit.analysis.write_cube", 
              extra_compile_args=['-O3'],
              sources = ['qctoolkit/analysis/c_extension/'+\
                         'writecubemodule.c']),
            Extension(name = "qctoolkit.ML.coulomb_matrix", 
              extra_compile_args=['-O3'],
              sources = ['qctoolkit/ML/c_extension/'+\
                         'coulombmatrixmodule.c',
                         'qctoolkit/ML/c_extension/utilities.c']),
            Extension(name = "qctoolkit.MD.dlist_1", 
              sources = ['qctoolkit/MD/c_extension/'+\
                         'dlist1.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.MD.dlist_2", 
              sources = ['qctoolkit/MD/c_extension/'+\
                         'dlist2.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.MD.vacf", 
              sources = ['qctoolkit/MD/c_extension/'+\
                         'vacf.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.QM.veint", 
              sources = ['qctoolkit/QM/c_extension/veint.c',
                         'qctoolkit/QM/c_extension/gaussian.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared',
                               '-lgsl', '-lgslcblas', '-llapack'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.QM.eeint", 
              sources = ['qctoolkit/QM/c_extension/eeint.c',
                         'qctoolkit/QM/c_extension/gaussian.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared',
                               '-lgsl', '-lgslcblas', '-llapack'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.QM.neint", 
              sources = ['qctoolkit/QM/c_extension/neint.c',
                         'qctoolkit/QM/c_extension/gaussian.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared',
                               '-lgsl', '-lgslcblas', '-llapack'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.QM.nnint", 
              sources = ['qctoolkit/QM/c_extension/nnint.c',
                         'qctoolkit/QM/c_extension/gaussian.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared',
                               '-lgsl', '-lgslcblas', '-llapack'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.QM.vnint", 
              sources = ['qctoolkit/QM/c_extension/vnint.c',
                         'qctoolkit/QM/c_extension/gaussian.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared',
                               '-lgsl', '-lgslcblas', '-llapack'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.QM.keint", 
              sources = ['qctoolkit/QM/c_extension/keint.c',
                         'qctoolkit/QM/c_extension/gaussian.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared',
                               '-lgsl', '-lgslcblas', '-llapack'],
              include_dirs = [np.get_include()]),
            Extension(name = "qctoolkit.QM.knint", 
              sources = ['qctoolkit/QM/c_extension/knint.c',
                         'qctoolkit/QM/c_extension/gaussian.c'],
              extra_compile_args=['-fopenmp', '-fpic', '-lm',
                                  '-Wno-write-strings'],
              extra_link_args=['-lgomp', '-shared',
                               '-lgsl', '-lgslcblas', '-llapack'],
              include_dirs = [np.get_include()]),
           ]

data_inc=[]
for root, sub_dir, files in os.walk('qctoolkit/data/unittest'):
  file_list = [root + '/' + data_file for data_file in files]
  data_inc.append((root, file_list))

setup(name='qctoolkit',
  version=version,
  description='quantum chemistry tool kit',
  url='https://github.com/SamKChang/qctoolkit.git',
  author='K. Y. S. Chang',
  author_email='ky.sam.chang@gmail.com',
  keywords = ['quantum', 'chemistry', 'wrapper', 'tools', 'alchemy',
              'cpmd', 'quantumespresso', 'nwchem', 'bigdft'],
  headers = [
    'qctoolkit/ML/c_extension/kernels.h',
    'qctoolkit/ML/c_extension/kernels_capi.h',
    'qctoolkit/ML/c_extension/utilities.h',
    'qctoolkit/QM/c_extension/gaussian.h',
    'qctoolkit/utilities/c_extension/utilities.h',
  ],
  packages = [
    'qctoolkit',
    'qctoolkit.QM',
    'qctoolkit.QM.qmcode',
    'qctoolkit.QM.pseudo',
    'qctoolkit.utilities',
    'qctoolkit.projects',
    'qctoolkit.projects.Basel',
    'qctoolkit.projects.Basel.p01_AlGaAs',
    'qctoolkit.data',
    'qctoolkit.data.elements',
    'qctoolkit.data.PP',
    'qctoolkit.data.PP.cpmd',
    'qctoolkit.data.PP.espresso',
    'qctoolkit.data.PP.bigdft',
    'qctoolkit.ccs',
    'qctoolkit.optimization',
    'qctoolkit.ML',
    'qctoolkit.MD',
    'qctoolkit.MD.mdcode',
    'qctoolkit.MD.trajectory',
    'qctoolkit.alchemy',
    'qctoolkit.analysis',
  ],
  package_data={'': ['elements/elements.yml', 
                     'data/PP/cpmd/*.psp',
                    ]},
  install_requires = required,
  data_files = data_inc,
  include_package_data=True,
  #ext_modules = cythonize(c_module),
  ext_modules = c_module,
  include_dirs=[np.get_include()],
)
