import sys
import machines as machs
from os import system as sh_command

class MARBL_testcase(object):

  def __init__(self):
    from os import path

    # supported_compilers is public, needed by the build tests
    self.supported_compilers = []

    # all other variables are private
    self._compiler = None
    self._machine = None
    self._namelistfile = 'marbl_in'
    self._GPTLroot = None
    self._marbl_dir = path.abspath('%s/../..' % path.dirname(__file__))

  # -----------------------------------------------

  # Parse the arguments to the MARBL test script
  # Some tests will let you specify a compiler and / or namelist
  # Some tests will require you to specify a machine
  def parse_args(self, desc, HaveCompiler=True, HaveNamelist=True,
                 CleanLibOnly=False, UseGPTL=False):

    import argparse

    parser = argparse.ArgumentParser(description=desc)
    if HaveCompiler:
      parser.add_argument('-c', '--compiler', action='store',
                          dest='compiler', help='compiler to build with')

    if HaveNamelist:
      parser.add_argument('-n', '--namelist', action='store', dest='namelistfile',
                          help='namelist file to read', default='marbl_in')

    if CleanLibOnly:
      parser.add_argument('--clean', action='store_true',
             help='remove object, module, and library files for MARBL lib')
    else:
      parser.add_argument('--clean', action='store_true',
             help='remove object, module, and library files for MARBL driver')

    parser.add_argument('-m', '--mach', action='store', dest='mach',
           help='machine to build on', choices=machs.supported_machines)

    parser.add_argument('--gptl_loc', action='store', dest='gptl',
                        default=None, help='location of GPTL library')

    args = parser.parse_args()

    # Run make clean if option is specified
    if args.clean:
      if CleanLibOnly:
        self._clean_lib()
      else:
        self._clean_exe()
      sys.exit(0)

    if args.mach == None:
      # If --mach is not specified, guess at machine name from hostname
      from socket import gethostname
      hostname = gethostname()
      found = True
      if any(host in hostname for host in ['geyser', 'caldera', 'prong', 'yslogin']):
        self._machine = 'yellowstone'
      elif 'hobart' in hostname:
        self._machine = 'hobart'
      elif 'edison' in hostname:
        self._machine = 'edison'
      else:
        found = False
        print 'No machine specified and %s is not recognized' % hostname
        print 'This test will assume you are not running on a supported cluster'
        self._machine = 'local-gnu'

      if found:
        print 'No machine specified, but it looks like you are running on %s' % self._machine

      print 'Override with the --mach option if this is not correct'
    else:
      self._machine = args.mach
      print 'Running test on %s' % self._machine

    machs.machine_specific(self._machine, self.supported_compilers)
    
    if HaveCompiler:
      self._compiler = args.compiler
      if self._compiler == None:
        self._compiler = self.supported_compilers[0]
        print 'No compiler specified, using %s by default' % self._compiler
      else:
        print 'Testing with %s' % self._compiler

    if HaveNamelist:
      self._namelistfile = args.namelistfile

    if args.gptl is not None:
      self._GPTLroot = args.gptl
      print "Loading GPTL library from %s" % self._GPTLroot
    print '----'
    sys.stdout.flush()

    # ERROR CHECKING
    if HaveCompiler:
      if not self._compiler in self.supported_compilers:
        print("%s is not supported on %s, please use one of following:" % (self._compiler, self._machine))
        print self.supported_compilers
        sys.exit(1)

    if (UseGPTL) and (args.gptl is None):
      print "ERROR: GPTL is required for this test. Run with --gptl_loc option."
      sys.exit(1)

  # -----------------------------------------------

  # Build libmarbl.a
  def build_lib(self, loc_compiler=None):

    if loc_compiler == None:
      loc_compiler = self._compiler

    src_dir = '%s/src' % self._marbl_dir

    if self._machine != 'local-gnu':
      machs.load_module(self._machine, loc_compiler)

    makecmd = 'make %s' % loc_compiler
    if self._GPTLroot is not None:
      makecmd = '%s GPTL_DIR=%s' % (makecmd, self._GPTLroot)
    sh_command('cd %s; %s' % (src_dir, makecmd))

  # -----------------------------------------------

  # Build marbl.exe
  def build_exe(self, loc_compiler=None):

    if loc_compiler == None:
      loc_compiler = self._compiler

    drv_dir = '%s/tests/driver_src' % self._marbl_dir

    if self._machine != 'local-gnu':
      machs.load_module(self._machine, loc_compiler)

    makecmd = 'make %s' % loc_compiler
    if self._GPTLroot is not None:
      makecmd = '%s GPTL_DIR=%s' % (makecmd, self._GPTLroot)
    sh_command('cd %s; %s' % (drv_dir, makecmd))

  # -----------------------------------------------

  # Execute marbl.exe
  def run_exe(self):

    exe_dir = '%s/tests/driver_exe' % self._marbl_dir

    execmd = '%s/marbl.exe < %s' % (exe_dir, self._namelistfile)
    if self._GPTLroot is not None:
      execmd = 'mpirun -n 1 %s' % execmd
    print "Running following command:"
    print execmd
    print ''
    sh_command(execmd)

  # -----------------------------------------------
  # PRIVATE ROUTINES
  # -----------------------------------------------

  # clean libmarbl.a
  def _clean_lib(self):

    src_dir = '%s/src' % self._marbl_dir
    sh_command('cd %s; make clean' % src_dir)

  # -----------------------------------------------

  # Clean marbl.exe
  def _clean_exe(self):

    drv_dir = '%s/tests/driver_src' % self._marbl_dir
    sh_command('cd %s; make clean' % drv_dir)

