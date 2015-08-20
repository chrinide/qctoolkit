import numpy as np
import utilities as ut
import re, os, sys, copy

class Molecule(object):
  def __init__(self):
    # number of atoms
    self.N = 0
    # atom coordinates
    self.R = np.atleast_2d(np.array([]))
    # atom symbols
    self.type_list = 'None'
    # nuclear charges
    self.Z = 0
    # moelcule charge
    self.charge = 0
    self.multiplicity = 1
    # index of different atoms
    self.index = 0
    self.bonds = {}
    self.bond_types = {}
    self.scale = False
    self.celldm = False

  def __add__(self, other):
    out = Molecule()
    out.N = self.N + other.N
    out.R = np.vstack([self.R, other.R])
    out.Z = np.hstack([self.Z, other.Z])
    return out

  def cyl2xyz(self):
    try:
      for i in range(3):
        self.R[:,i] = self.R[:,i] * self.celldm[i]\
                     / float(self.scale[i])
      self.scale = []
    except AttributeError:
      pass

  def view(self):
    import pymol
    tmp = copy.deepcopy(self)
    if self.celldm and self.scale:
      try:
        for i in range(3):
          tmp.R[:,i] = tmp.R[:,i] * tmp.celldm[i]\
                       / float(tmp.scale[i])
      except AttributeError:
        pass
    pymol.finish_launching()
    tmp_file = 'pymol_tmp_'+str(os.getpid())+'.xyz'
    tmp.write_xyz(tmp_file)
    pymol.cmd.load(tmp_file, 'structure')
    os.remove(tmp_file)

  def find_bonds(self):
    itr = 0
    for i in xrange(self.N):
      for j in xrange(i+1, self.N):
        d_ij = np.linalg.norm(self.R[i,:] - self.R[j,:])
        if d_ij < 1.75:
          if self.Z[i] < self.Z[j]:
            atom_begin = self.Z[i]
            atom_end = self.Z[j]
            index_begin = i
            index_end = j
          else:
            atom_begin = self.Z[j]
            atom_end = self.Z[i]
            index_begin = j
            index_end = i
          self.bonds[itr] = {'atom_begin'  : atom_begin,
                             'index_begin' : index_begin,
                             'atom_end'    : atom_end,
                             'index_end'   : index_end,
                             'length'      : d_ij}
          type_begin = ut.Z2n(atom_begin)
          type_end   = ut.Z2n(atom_end)
          bond_type  = type_begin + "-" + type_end
          if bond_type in self.bond_types:
            self.bond_types[bond_type] += 1
          else:
            self.bond_types[bond_type] = 1
          itr += 1

  def flip_atom(self, index, element):
    index -= 1
    if index <= self.N:
      self.type_list[index] = ut.qAtomName(element)
      self.Z[index] = ut.qAtomicNumber(element)
    else:
      print "index:%d out of range, nothing has happend"\
            % int(index+1)

  def remove_atom(self, index):
    index -= 1
    if index <= self.N - 1:
      self.N -= 1
      self.R = np.delete(self.R, index, 0)
      self.Z = np.delete(self.Z, index)
      self.type_list = list(np.delete(self.type_list, index))
    else:
      print "index:%d out of range, nothing has happend"\
            % index+1

  def isolate_atoms(self, index_list):
    if type(index_list) != list:
      index_list = [index_list]
    index_list = map(lambda a: a-1, index_list)
    self.N = len(index_list)
    self.R = np.array([coord for coord in self.R[index_list]])
    self.Z = np.array([coord for coord in self.Z[index_list]])
    self.type_list = \
      np.array([coord for coord in self.type_list[index_list]])

  def have_bond(self, type_a, type_b):
    result = False
    if '0' not in self.bonds:
      self.find_bonds()
    if ut.n2Z(type_a) > ut.n2Z(type_b):
      atom_begin = ut.n2Z(type_b)
      atom_end = ut.n2Z(type_a)
    else:
      atom_begin = ut.n2Z(type_a)
      atom_end = ut.n2Z(type_b)
    for key in self.bonds:
      if self.bonds[key]['atom_begin'] == atom_begin and \
         self.bonds[key]['atom_end'] == atom_end:
        print self.bonds[key]['atom_begin'],
        print self.bonds[key]['atom_end']
        result = True
    return result

  def center(self, center_coord):
    center_matrix = np.kron(
      np.transpose(np.atleast_2d(np.ones(self.N))),
      center_coord
    )
    self.R = self.R - center_coord

  def shift(self, shift_vector):
    shift_matrix = np.kron(
      np.transpose(np.atleast_2d(np.ones(self.N))),
      shift_vector
    )
    self.R = self.R + shift_matrix

  def getValenceElectrons(self):
    ve = np.vectorize(ut.n2ve)
    nve = sum(ve(self.type_list)) - self.charge
    return nve

  def setChargeMultiplicity(self, c, m, **kwargs):
    if type(c) == int or type(c) == float:
      self.charge = c
    if type(m) == int:
      self.multiplicity = m

    if type(self.multiplicity)==int and\
       type(self.charge)==(int or float):
      if not (self.multiplicity % 2 != \
              (np.sum(self.Z) + self.charge) % 2):
        ve = np.vectorize(ut.n2ve)
        nve = sum(ve(self.type_list)) - self.charge
        msg = "Multiplicity %d " % self.multiplicity + \
              "and %d valence electrons " % nve +\
              "\n(with charge %3.1f) " % float(self.charge) +\
              "are not compatible"
        if not ('no_warning' in kwargs and kwargs['no_warning']):
          ut.prompt(msg + "\nsuppress warning py no_warning=True,"\
                    + " continue?")

  def rotate(self, u, angle):
    print "not yet implemented"	

  def align(self, i,j,k):
    print "not yet implemented"

  def stretch(self):
    print "not yet implemented"

  def twist(self):
    print "not yet implemented"

  def sort(self):
    data = np.hstack([np.transpose(np.atleast_2d(self.Z)), self.R])
    data = data[data[:,0].argsort()]
    Z2n_vec = np.vectorize(ut.Z2n)
    self.Z = data[:,0].astype(int)
    self.type_list = Z2n_vec(self.Z)
    self.R = data[:,1:4]

    index_a = np.insert(self.Z, 0, 0)
    index_b = np.insert(self.Z, len(self.Z), 0)
    self.index = np.where((index_a != index_b))[0]

  def sort_coord(self, **kwargs):
    if 'order' in kwargs:
      order = kwargs['order']
    else:
      order = [0,1,2]
    ind = np.lexsort((self.R[:,order[2]],\
                      self.R[:,order[1]],\
                      self.R[:,order[0]]))
    self.R = self.R[ind]

  # general interface to dertermine file type
  def read(self, name, **kwargs):
    stem, extension = os.path.splitext(name)
    if re.match('\.xyz', extension):
      self.read_xyz(name, **kwargs)
    elif re.match('\.cyl', extension):
      self.read_cyl(name, **kwargs)
    elif name == 'VOID':
      pass
    elif 'type' in kwargs and kwargs['type']=='cpmdinp':
      self.read_cpmdinp(name)
    else:
      ut.exit("suffix " + extension + " is not reconized")
      
  # read structrue from xyz
  def read_xyz(self, name, **kwargs):

    # caution! no format check. 
    # correct xyz format is assumed

    # local array varaible for easy append function
    coord = []
    type_list = []
    Z = []

    # open xyz file
    xyz_in = open(name, 'r')
    self.N = int(xyz_in.readline())
    xyz_in.readline()

    # loop through every line in xyz file
    for i in xrange(0, self.N):
      data = re.sub("[\n\t]", "",xyz_in.readline()).split(' ')
      # remove empty elements
      data = filter(None, data)
      type_list.append(data[0])
      Z.append(ut.n2Z(data[0]))
      crd = [float(data[1]),float(data[2]),float(data[3])]
      coord.append(crd)
    self.R = np.vstack(coord)
    self.type_list = type_list
    self.Z = np.array(Z)

    if np.sum(self.Z) % 2 == 1:
      self.charge = -1

    xyz_in.close()

  # read structrue from cyl crystal format
  def read_cyl(self, name, **kwargs):

    # local array varaible for easy append function
    coord = []
    type_list = []
    Z = []

    # open xyz file
    xyz_in = open(name, 'r')
    self.N = int(xyz_in.readline())
    self.celldm = map(float,re.sub("[\n\t]", "",xyz_in.readline())\
                  .split(' '))
    self.scale = map(int,re.sub("[\n\t]", "",xyz_in.readline())\
                         .split(' '))

    # loop through every line in xyz file
    for i in xrange(0, self.N):
      data = re.sub("[\n\t]", "",xyz_in.readline()).split(' ')
      # remove empty elements
      data = filter(None, data)
      type_list.append(data[0])
      Z.append(ut.n2Z(data[0]))
      crd = [float(data[1]),float(data[2]),float(data[3])]
      coord.append(crd)
    self.R = np.vstack(coord)
    self.type_list = np.array(type_list)
    self.Z = np.array(Z)

    if np.sum(self.Z) % 2 == 1:
      self.charge = -1

    xyz_in.close()

  # write xyz format to file
  def write_xyz(self, *args):
    if len(args) == 1:
      name = args[0]
    else: name = ''
    out = sys.stdout if not name else open(name,"w")

    #if len(self.type_list) != self.N:
    tlist = np.vectorize(ut.Z2n)
    self.type_list = tlist(self.Z)

    print >>out, str(self.N)+"\n"
    for I in xrange(0, self.N):
      print >>out, "%-2s " % self.type_list[I],
      print >>out, " ".join("% 8.4f" % i for i in self.R[I][:])

    if not re.match("",name):
      out.close()

  # read structure from CPMD input
  def read_cpmdinp(self, name):
 
    self.N = 0
    #self.NType = 0
    #NTypeName = []
    coord = []
    Z = []
    type_list = []

    element_p = re.compile('\*([A-Za-z])*_')
    pp_p = re.compile('^\*')
    inp = open(name, 'r')
    while True:
      line = inp.readline()
      if not line: break
      if(re.match("&ATOMS",line)):
        while not (re.match("&END",line)):
          line = inp.readline()
          if(re.match(pp_p,line)):
            #self.NType += 1
            element = element_p.match(line).group(1)
            #NTypeName.append(element)
            inp.readline()
            N = int(inp.readline())
            for i in xrange(0, N):
              self.N += 1
              line = inp.readline()
              coord.append([float(x) for x in line.split()])
              type_list.append(element)
              Z.append(ut.n2Z(element))
    self.R = np.vstack(coord)
    #self.NTypeName = np.array(NTypeName)
    self.type_list = np.array(type_list)
    self.Z = np.array(Z)

    inp.close()

