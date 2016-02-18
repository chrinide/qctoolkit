import qctoolkit as qtk
from qctoolkit.QM.gaussianbasis_io import GaussianBasisInput
from qctoolkit.QM.gaussianbasis_io import GaussianBasisOutput
import os, sys, copy, shutil, re
import numpy as np
import qctoolkit.QM.qmjob as qmjob
import periodictable as pt

class inp(GaussianBasisInput):
  def __init__(self, molecule, **kwargs):
    GaussianBasisInput.__init__(self, molecule, **kwargs)
    self.setting.update(kwargs)

  def run(self, name=None, **kwargs):
    # creat_folder routine check default name
    name = self.create_folder(name)
    cwd = os.getcwd()
    os.chdir(name)
    inp = name + '.inp'
    self.write(inp)
    try:
      out = qmjob.QMRun(inp, 'nwchem', **kwargs)
    except:
      qtk.warning("qmjob finished unexpectedly for '" + \
                  name + "'")
      out = GaussianBasisOutput(program='nwchem')
    finally:
      os.chdir(cwd)
    return out
    
  def write(self, name=None):
    inp, molecule = \
      super(GaussianBasisInput, self).write(name, **self.setting)

    # mode setup
    if self.setting['mode'] == 'single_point':
      operation = 'energy'
    elif self.setting['mode'] == 'geopt':
      operation = 'optimize'

    # Theory setupt
    dft = {
      'pbe': 'xpbe96 cpbe96',
      'pbe0': 'pbe0',
      'blyp': 'becke88 lyp',
      'b3lyp': 'b3lyp',
      'bp91': 'becke88 perdew91',
      'bp86': 'becke88 perdew86',
      'pw91': 'xperdew91 perdew91',
    }
    scf = {
      'rhf', 'rohf', 'uhf',
    }
    tce = {
      'mp2', 'ccsd', 'ccsd(t)',
    }
    if self.setting['theory'] in dft:
      module = 'dft'
      xc = dft[self.setting['theory']]
    elif self.setting['theory'] in scf:
      module = 'scf'
    elif self.setting['theory'] in tce:
      module = 'tce'

    # print file
    inp.write('title %s\n' % name)
    inp.write('start %s\n' % name)
    inp.write('echo\n')
    if self.setting['fix_molecule']\
    and self.setting['fix_molecule']:
      fix_mol = 'nocenter'
    else:
      fix_mol = ''
    inp.write('\ngeometry units angstrom %s\n' % fix_mol)
    if fix_mol:
      inp.write('symmetry group c1\n')
    if 'nuclear_charges' in self.setting:
      new_Z = self.setting['nuclear_charges']
    else:
      new_Z = []
    z_itr = 0
    for i in range(molecule.N):
      n_charge = ''
      e_str = molecule.type_list[i]
      if new_Z and z_itr < len(new_Z):
        if new_Z[z_itr][0] == i+1:
          n_charge = 'charge %.3f' % float(new_Z[z_itr][1])
          e_str = new_Z[z_itr][2]
          molecule.string[i] = e_str
          z_itr = z_itr + 1
      inp.write(' %-8s % 8.4f % 8.4f % 8.4f %s\n' % \
                (e_str,
                 molecule.R[i, 0],
                 molecule.R[i, 1],
                 molecule.R[i, 2],
                 n_charge
               ))
    inp.write('end\n\n')
    inp.write('basis\n')
    if self.setting['basis_set'] != 'gen':
      eStr = []
      for e in range(len(molecule.Z)):
        if molecule.string[e]:
          eString = molecule.string[e]
        else:
          eString = molecule.type_list[e]
        if eString not in set(eStr):
          eStr.append(eString)
          inp.write(' %-8s library %2s %s\n' % (\
            eString,
            molecule.type_list[e],
            self.setting['basis_set'].upper()),
          )
    inp.write('end\n\n')
    if module == 'dft':
      inp.write('dft\n')
      inp.write(' xc %s\n' % xc)
      inp.write('end\n\n')
    elif module == 'scf':
      pass
    if molecule.charge != 0:
      inp.write('charge % 5.2f\n' % molecule.charge)
    if molecule.multiplicity != 1:
      inp.write('multiplicity %d\n' % molecule.multiplicity)

    inp.write('\ntask %s %s\n' % (module, operation))

    inp.close()


class out(GaussianBasisOutput):
  """
  directly parse vasp xml output, 'vasprun.xml'
  converged energy, system info, and scf steps are extracted
  """
  def __init__(self, qmout=None, **kwargs):
    GaussianBasisOutput.__init__(self, qmout, **kwargs)
    if qmout:
      outfile = open(qmout, 'r')
      data = outfile.readlines()
      Et = filter(lambda x: 'Total' in x and 'energy' in x, data)
      try:
        self.Et = float(Et[-1].split( )[-1])
      except:
        self.Et = np.nan
      # necessary for opening *.movecs file
      n_basis = filter(lambda x: ' functions ' in x, data)
      try:
        self.n_basis = int(n_basis[-1].split('=')[1])
      except:
        self.n_basis = np.nan

      ######################################
      # extract basis function information #
      ######################################

      basis_dict = {"S":0, "P":1, "D":2, "F":3, "G":4, "H":5}

      basis_P = re.compile(r" *[0-9]+ [A-Z]  [0-9]\.[0-9]{8}")
      batom_P = re.compile(r"^  [0-9A-Za-z\-_\.]+ *\([A-Z][a-z]*\)")
      bname_P = re.compile(r"\((.*)\)")
      coord_P = re.compile(r"^ [0-9A-Za-z\.\-_]+ +[- ][0-9\.]{9,}")
      basisStr = filter(basis_P.match, data)
      batomStr = filter(batom_P.match, data)
      coordStr = filter(coord_P.match, data)

      # change 'Sulphur' to 'Sulfur' for NWChem format
      _sulphur = filter(lambda x: 'Sulphur' in x, batomStr)
      if _sulphur:
        _sulphur = _sulphur[0]
        _s = batomStr.index(_sulphur)
        batomStr[_s] = re.sub('Sulphur', 'Sulfur', batomStr[_s])
        _s = data.index(_sulphur)
        data[_s] = re.sub('Sulphur', 'Sulfur', data[_s])

      _exponents = [float(filter(None, s.split(' '))\
        [2]) for s in basisStr]
      _coefficients = [float(filter(None, s.split(' '))\
        [3]) for s in basisStr]
      _N = [int(filter(None, s.split(' '))[0])\
        for s in basisStr]
      _type = [filter(None, s.split(' '))[1]\
        for s in basisStr]
      _bfnInd = [data.index(batom) for batom in batomStr]
      _bfnEndPtn = re.compile(r" Summary of \"")
      _bfnEndStr = filter(_bfnEndPtn.match, data)[0]
      _bfnInd.append(data.index(_bfnEndStr))

      _ao_keys = [0]
      for ind in range(len(_bfnInd)-1):
        _key = _ao_keys[-1]
        for i in range(_bfnInd[ind]+4, _bfnInd[ind+1]):
          if len(data[i]) > 1:
            _key = _key + 1
        _ao_keys.append(_key)
      _atoms = [getattr(pt, bname_P.match(
        filter(None, s.split(' '))[1]).group(1).lower()).symbol\
        for s in batomStr]
      self.type_list = [re.split(r'[\._]',
        filter(None, s.split(' '))[0])[0].title()\
        for s in coordStr]
      self.R = np.array([filter(None, s.split(' '))[1:4]\
        for s in coordStr]).astype(float)
      self.N = len(self.R)
      self.Z = [qtk.n2Z(e) for e in self.type_list]
      self.R_bohr = 1.889725989 * self.R

      _N.append(0)
      self.basis = []
      for i in range(len(self.type_list)):
        e = self.type_list[i]
        center = self.R_bohr[i]
        ind = self.type_list.index(e)
        bfn_base = {}
        bfn_base['atom'] = e
        bfn_base['center'] = center
        bfn_base['index'] = i
        exp = []
        cef = []
        for g in range(_ao_keys[ind], _ao_keys[ind+1]):
          exp.append(_exponents[g])
          cef.append(_coefficients[g])
          if _N[g] != _N[g+1] or g+1 >= _ao_keys[ind+1]:
            bfn = copy.deepcopy(bfn_base)
            bfn['exponents'] = copy.deepcopy(exp)
            bfn['coefficients'] = copy.deepcopy(cef)
            if _type[g] in basis_dict:
              _bfnList = self.basisList(basis_dict[_type[g]])
              for bStr in _bfnList:
                bfn['type'] = _type[g].lower() + bStr
                self.basis.append(copy.deepcopy(bfn))
            exp = []
            cef = []
          

      movecs = os.path.join(self.path, self.stem) + '.modat'
      if os.path.exists(movecs):
        self.getMO(movecs)

  def getMO(self, mo_file):
    """
    setup self.n_ao
          self.n_mo
          self.occupation
          self.mo_eigenvalues
          self.mo_vectors
          self.nuclear_repulsion
    """
    if os.path.exists(mo_file):
      mo = open(mo_file, 'r')
      mo_out = mo.readlines()
      self.n_ao = int(mo_out[12].split( )[0])
      self.n_mo = int(mo_out[13].split( )[0])
      if self.n_ao % 3 != 0:
        lines = self.n_ao / 3 + 1
      else:
        lines = self.n_ao / 3
      self.occupation = \
        [float(j) for i in mo_out[14:14+lines]\
         for j in i.split( )]
      self.mo_eigenvalues = \
        [float(j) for i in mo_out[14+lines:14+(2*lines)]\
         for j in i.split( )]

      _mo = []
      for k in range(self.n_mo):
        start = 14+((2+k)*lines)
        end = 14+((3+k)*lines)
        vec = [float(j) for i in mo_out[start:end]\
               for j in i.split( )]
        _mo.append(vec)
      self.mo_vectors = np.array(_mo)
      self.nuclear_repulsion = float(mo_out[-1].split( )[1])

  def basisList(self, N):
    lm = ['x', 'y', 'z']
    outList = []
    outStr = []
    item = ['x' for s in range(N)]
  
    # recursive function that collects all the ids in `acc`
    def recurse(current, depth, N, count):
      if depth < N:
        for s in range(current, 3): 
          item[depth] = lm[s]
          if depth == N-1:
            count = depth
            outList.append(copy.deepcopy(item))
          recurse(s, depth+1, N, count)
  
    recurse(0, 0, N, 0) # starts the recursion
    if outList:
      for out in outList:
        outStr.append(''.join(out))
    else:
      outStr = ['']
    return outStr
