import qctoolkit as qtk
from qctoolkit.QM.planewave_io import PlanewaveInput
from qctoolkit.QM.planewave_io import PlanewaveOutput
import os, copy, glob, re
import qctoolkit.QM.qmjob as qmjob
import numpy as np
import universal as univ
from bigdft import PPCheck

class inp(PlanewaveInput):
  """
  abinit input class.
  """
  __doc__ = PlanewaveInput.__doc__ + __doc__
  def __init__(self, molecule, **kwargs):
    PlanewaveInput.__init__(self, molecule, **kwargs)
    self.setting.update(**kwargs)
    self.backup()
    self.content = ['']

  def run(self, name=None, **kwargs):
    self.setting.update(kwargs)
    return univ.runCode(self, PlanewaveInput, name, **self.setting)

  def write(self, name=None, **kwargs):
    self.setting.update(kwargs)
    self.setting['no_molecule'] = False
    inp, molecule = \
      super(PlanewaveInput, self).write(name, **self.setting)

    molecule.sort()
    type_index = molecule.index
    type_list = molecule.type_list

    self.pp_path = qtk.setting.bigdft_pp
    if 'pp_path' in self.setting:
      self.pp_path = self.setting['pp_path']

    if 'pp_theory' not in self.setting:
      self.setting['pp_theory'] = self.setting['theory']

    pp_files = []
    inp.write('# abinit input generated by qctoolkit\n')

    # restart section
    if 'restart' in self.setting and self.setting['restart']:
      inp.write('\n# restart, reading wavefunction from file\n')
      inp.write('irdwfk 1\n')
      inp.write('getwfk -1\n')
 
    # cell definition
    inp.write('\n# cell definition\n')
    # cell specified by Bohr
    if not molecule.symmetry:
      inp.write('# NOTE: cell defined by lattice vector, ')
      inp.write('NOT supported by abinit spacegroup detector!\n')
      inp.write('acell 3*1.889726124993\n')
      if 'lattice' not in self.setting:
        self.celldm2lattice()
      lattice_vec = self.setting['lattice']
      inp.write('chkprim 0\n')
    elif molecule.symmetry.lower() == 'fcc':
      inp.write("# fcc primitive cell\n")
      a0 = molecule.celldm[0] * 1.889726124993
      inp.write('acell 1 1 1\n')
      lattice_vec = 0.5 * a0 * np.array([
        [0, 1, 1],
        [1, 0, 1],
        [1, 1, 0],
      ])
    elif molecule.symmetry.lower() == 'bcc':
      inp.write("# bcc primitive cell\n")
      inp.write('acell 1 1 1\n')
      a0 = molecule.celldm[0] * 1.889726124993
      lattice_vec = 0.5 * a0 * np.array([
        [-1, 1, 1],
        [ 1,-1, 1],
        [ 1, 1,-1],
      ])
    strList = ['rprim', '', '']
    for i in range(3):
      vec = lattice_vec[i]
      inp.write('%5s % 11.6f % 11.6f % 11.6f\n' % (
        strList[i], vec[0], vec[1], vec[2],
      ))

    # atom definition
    inp.write("\n# atom definition\n")
    inp.write('ntypat %d\n' % (len(type_index) - 1))
    inp.write('znucl')
    for a in range(len(type_index)-1):
      symb = type_list[type_index[a]]
      Z = qtk.n2Z(symb)
      inp.write(' %d' % Z)
    inp.write('\n')

    # atom position
    inp.write("\n# atom position\n")
    inp.write("natom %d\n" % molecule.N)
    inp.write('typat')
    for a in range(len(type_index)-1):
      start = type_index[a]
      end = type_index[a+1]
      for i in range(end - start):
        inp.write(' %d' % (a+1))
    inp.write('\nxangst\n\n')
    for i in range(molecule.N):
      inp.write('  ')
      for j in range(3):
        inp.write(' % 11.6f' % molecule.R[i][j])
      inp.write('\n')

      # construct pp files depandency
      pp_file = 'psppar.' + molecule.type_list[i]
      pp_list = set([pp[1] for pp in pp_files])
      if pp_file not in pp_list:
        pp_src = PPCheck(self.setting['theory'],
                         self.setting['pp_theory'],
                         self.pp_path,
                         molecule.type_list[i])
        pp_files.append([pp_src, pp_file])

    inp.write('\n')

    # system setting
    inp.write("\n# system settings\n")
    # cutoff in Hartree
    inp.write('ecut %.2f\n' % float(self.setting['cutoff']/2.))
    if 'kmesh' not in self.setting:
      self.setting['kmesh'] = [1,1,1]
    if self.setting['full_kmesh']:
      inp.write('kptopt 3\n')
    inp.write('ngkpt')
    for k in self.setting['kmesh']:
      inp.write(' %d' % k)
    if 'kshift' not in self.setting:
      inp.write('\nshiftk 0.0 0.0 0.0')
    if 'ks_states' in self.setting and self.setting['ks_states']:
      vs = int(round(molecule.getValenceElectrons() / 2.0))
      nbnd = self.setting['ks_states'] + vs
      if 'd_shell' in self.setting:
        for a in molecule.type_list:
          if a in self.setting['d_shell'] and qtk.n2ve(a) < 10:
            nbnd += 5
      inp.write('\nnband %d' % nbnd)
    inp.write('\nnstep %d\n' % self.setting['scf_step']) 
    if 'wf_convergence' in self.setting:
      inp.write('toldfe %.2E\n' % self.setting['wf_convergence'])
    if molecule.charge != 0:
      inp.write('charge=%d\n' % molecule.charge)
    if molecule.multiplicity != 1:
      inp.write('nsppol 2 # for spin polarized\n')
      inp.write('occopt 7 # for relaxed occupation\n')

    if 'save_restart' in self.setting and self.setting['save_restart']:
      pass
    else:
      inp.write('prtwf 0\n')

    for item in self.content:
      inp.write(item)

    inp.close(dependent_files=pp_files)

    if hasattr(inp, 'final_name'):
      self.setting['no_molecule'] = True
      self.setting['root_dir'] = name
      files = \
        super(PlanewaveInput, self).write(name, **self.setting)
      files.extension = 'files'
      files.write(inp.final_name + '\n')
      root = os.path.splitext(inp.final_name)[0]
      files.write(root + '.out\n')
      files.write(root + 'i\n')
      files.write(root + 'o\n')
      files.write(root + 'x\n')
      for pp in pp_files:
        files.write(pp[1] + '\n')
      files.close(no_cleanup = True)

    return inp

class out(PlanewaveOutput):
  def __init__(self, qmout, **kwargs):
    PlanewaveOutput.__init__(self, qmout, **kwargs)
    out_file = open(qmout)
    data = out_file.readlines()
    out_file.close()

    EStrList = filter(lambda x: 'Etotal' in x, data)
    EList = filter(lambda x: 'ETOT' in x, data)
    self.scf_step = len(EList)
    if self.scf_step > 0:
      Et_list = [float(filter(None, s.split(' '))[2]) for s in EList]
      self.Et = Et_list[-1]
    elif len(EStrList) > 0:
      EStr = EStrList[-1]
      self.Et = float(EStr.split(' ')[-1])

    if len(EStrList) > 0:
      EStr = EStrList[-1]
      detailInd = data.index(EStr)
      self.detail = data[detailInd-7:detailInd]
  
    xangst = filter(lambda x: 'xangst' in x, data)[-1]
    angst_n = len(data) - data[::-1].index(xangst) - 1
    xcart = filter(lambda x: 'xcart' in x, data)[-1]
    cart_n = len(data) - data[::-1].index(xcart) - 1
    Rstr = copy.deepcopy(data[angst_n:cart_n])
    Rstr[0] = Rstr[0].replace('xangst', '')
    R = [[float(r) for r in filter(None, s.split(' '))] for s in Rstr]
    N = len(R)
    ZstrOriginal = filter(lambda x: ' typat' in x, data)[-1]
    Zstr = ZstrOriginal.replace('typat', '')
    Zind = [int(z) for z in filter(None, Zstr.split(' '))]
    ZindItr = data.index(ZstrOriginal)
    while len(Zind) != N:
      ZindItr += 1
      ZindNewStr = filter(None, data[ZindItr].split(' '))
      ZindNew = [int(z) for z in ZindNewStr]
      Zind.extend(ZindNew)
    Znuc = filter(lambda x: 'znucl ' in x, data)[-1]
    Znuc = filter(None, Znuc.replace('znucl', '').split(' '))
    Znuc = [float(z) for z in Znuc]
    build = []
    for i in range(N):
      Z = [Znuc[Zind[i]-1]]
      Z.extend(R[i])
      build.append(Z)
    self.molecule = qtk.Molecule()
    self.molecule.build(build)

    if self.scf_step > 0:
      fStr = filter(lambda x: 'tesian forces (hartree/b' in x, data)[-1]
      fInd = data.index(fStr)
      fData = data[fInd+1:fInd+1+N]
      force = []
      for f in fData:
        fStr = filter(None, f.split(' '))[1:]
        force.append([float(fs) for fs in fStr])
      self.force = np.array(force)

    self.occupation = []
    try:
      r1p = re.compile(r'^[ a-z]{17} +[ 0-9.E+-]+$')
      r2p = re.compile(r'^ +[a-z]+ +.*$')
      report = filter(r2p.match, filter(r1p.match, data))
      occ_pattern = filter(lambda x: ' occ ' in x, report)[-1]
      occ_pattern_ind = len(report) - report[::-1].index(occ_pattern)
      occ_pattern_end = report[occ_pattern_ind]
      occ_ind_start = len(data) - data[::-1].index(occ_pattern) - 1
      occ_ind_end = len(data) - data[::-1].index(occ_pattern_end) - 1
      for i in range(occ_ind_start, occ_ind_end):
        for occ in filter(None, data[i].split(' ')):
          try:
            self.occupation.append(float(occ))
          except:
            pass
    except Exception as err:
      qtk.warning("error when extracting occupation number with" +\
        " error message: %s" % str(err))

    eigStr = os.path.join(os.path.split(qmout)[0], '*_EIG')
    eigFileList = glob.glob(eigStr)
    if len(eigFileList) != 0:
      if len(eigFileList) > 1:
        qtk.warning("more than one o_EIG files found")
      eigFile = open(eigFileList[0])
      eigData = eigFile.readlines()
      eigFile.close()
      spinList = filter(lambda x: 'SPIN' in x, eigData)
      if len(spinList) != 0:
        spinFactor = 2
        maxInd = eigData.index(spinList[-1])
      else:
        spinFactor = 1
        maxInd = len(eigData)
      ind = []
      for kStr in filter(lambda x: 'kpt#' in x, eigData):
        ind.append(eigData.index(kStr))
      band = []
      kpoints = []
      if spinFactor == 1:
        for i in range(len(ind)):
          wcoord = eigData[ind[i]].split('wtk=')[-1].split(', kpt=')
          weight = float(wcoord[0])
          cStr = filter(None, wcoord[1].split('(')[0].split(' '))
          coord = [float(c) for c in cStr]
          coord.append(weight)
          kpoints.append(coord)
          s = ind[i] + 1
          if i < len(ind) - 1:
            e = ind[i+1]
          else:
            e = len(eigData)
          eig_i = filter(None, ''.join(eigData[s:e]).split(' '))
          band.append([qtk.convE(float(ew), 'Eh-eV')[0]
                       for ew in eig_i])
  
        self.band = np.array(band)
        self.kpoints = np.array(kpoints)
        self.mo_eigenvalues = np.array(band[0]).copy()
        if len(self.occupation) > 0:
          diff = np.diff(self.occupation)
          ind = np.array(range(len(diff)))
          pos = diff[np.where(abs(diff) > 0.5)]
          mask = np.in1d(diff, pos)
          if len(ind[mask]) > 0:
            N_state = ind[mask][0]
            vb = max(self.band[:, N_state])
            cb = min(self.band[:, N_state + 1])
            vb_pos = np.argmax(self.band[:, N_state])
            cb_pos = np.argmin(self.band[:, N_state + 1])
            self.Eg = cb - vb
            if vb_pos == cb_pos:
              self.Eg_direct = True
            else:
              self.Eg_direct = False
  
      else:
        qtk.warning("spin polarized band data " +\
                    "extraction is not yet implemented")
    else:
      qtk.warning('no k-point information (o_EIG file) found')
