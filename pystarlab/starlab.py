"""Python wrapper for starlab.

This wrapper provides data structures, serialization, and execution.
"""

import re
import uuid
from enum import Enum
from subprocess import Popen, PIPE
from tempfile import SpooledTemporaryFile as tempfile
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, Text, Float, String

Base = declarative_base()
class ArchivedStory(Base):
    """Class for archiving stories via SQLAlchemy."""
    __tablename__ = "stories"

    story_id = Column(Integer, primary_key=True)
    story_text = Column(Text)

    def __repr__(self):
        return self.story_text

class Story(object):
    """Generic container class for starlab data."""
    def __init__(self):
        """Create an empty story."""
        self.story_lines = []
        self.story_vals = dict()
        self.story_subobjects = []
        self.kind = None
        return

    def __repr__(self):
        """A unique representation of the story object."""
        return ("[Story] %s, %d lines, %d values, %d subobjects" %
                (self.kind,
                 len(self.story_lines),
                 len(self.story_vals.keys()),
                 len(self.story_subobjects)))

    def __str__(self):
        """A string matching starlab's native format."""
        selfstr = "(%s\n" % self.kind
        for line in self.story_lines:
            selfstr += "%s\n" % line
        for key, val in sorted(self.story_vals.items()):
            selfstr += "  %s = %s\n" % (key, val)
        for substory in self.story_subobjects:
            selfstr += str(substory)
        return selfstr + ")%s\n" % self.kind

    @classmethod
    def from_buf(cls, buffered_result):
        """Generate a story from a buffer.

        This could either be a stream or a string that has
        been split into lines. It's supposed to add flexibility for
        running long kira integrations in which we don't want to hold
        the whole string in memory when converting it to stories.

        We use a little bit of state to avoid using recursion here. The
        reason for that is twofold:

        1. We want to treat lines in Log-type stories a little differently, and
        2. This will be more efficient, especially for large buffers.

        :param buffered_result: Results of a starlab command in an buffer
        :type buffered_result: iterable

        :returns: results parsed into a story
        :rtype: story instance
        """
        stories_to_return = []
        story_stack = []

        # shouldn't be necessary
        thestory = None

        for line in buffered_result:
            if isinstance(line, bytes):
                line = line.decode()
            # check to see if we need to start a new story
            storystart = re.match(r"^\((\w+)", line)
            if storystart:
                thestory = cls()
                thestory.kind = storystart.group(1)
                story_stack.append(thestory)
            else:
                storyend = re.match(r"\)%s" % story_stack[-1].kind, line)
                if storyend:
                    thestory = story_stack.pop()
                    if len(story_stack) > 0:
                        story_stack[-1].story_subobjects.append(thestory)
                    else:
                        stories_to_return.append(thestory)
                else:
                    chunks = re.split('=', line)
                    if (len(chunks) == 2) and story_stack[-1].kind != "Log":
                        story_stack[-1].story_vals[chunks[0].strip()] = chunks[1].strip()
                    else:
                        story_stack[-1].story_lines.append(line)

        if len(stories_to_return) == 0:
            raise ValueError("No stories found in buffer!")
        elif len(stories_to_return) == 1:
            return stories_to_return[0]
        else:
            return stories_to_return

    @classmethod
    def from_string(cls, result_string):
        """Generate a story from a string.

        Assumes the string contains a single story (possibly with story
        subobjects). If there's more than one story in the string (e.g.,
        output from kira), this will grab the last and discard the rest.

        :param result_string: The string to parse
        :type result_string: bytestring or unicode string

        :returns: string parsed into a story
        :rtype: Story instance
        """
        if isinstance(result_string, bytes):
            lines = result_string.decode('utf-8').splitlines()
        elif isinstance(result_string, str):
            lines = result_string.splitlines()
        else:
            raise TypeError('result_string should be a string or bytestring')

        newstory = cls.from_buf(lines)

        return newstory

    @classmethod
    def from_single_command(cls, command):
        """Generate a story from a single command.

        The command should be a creation command (e.g., makeking,
        makeplummer, etc.). It should also include all of the necessary
        command line options.

        :param command: The starlab command to run
        :type command: a string as it would appear on the command line
                       or a list suitable for subprocess.Popen()

        :returns: the output of command
        :rtype: Story instance
        """
        if isinstance(command, str):
            command = command.split(" ")
        elif isinstance(command, list):
            pass
        else:
            raise TypeError('command should be a string or list')
        thestory = None
        story_lines = []

        with Popen(command,
                   stdout=PIPE,
                   bufsize=1,
                   universal_newlines=True) as process:
            for line in process.stdout:
                story_lines.append(line.rstrip())

        thestory = cls.from_buf(story_lines)

        return thestory

    @classmethod
    def from_command_list(cls, command_list):
        """Generate a story from a list of commands.

        This makes use of the from_single_command() and apply_command()
        methods. The output of each command serves as the input of the
        next; only the output of the last command is returned.

        :param command_list: the list of commands.
        :type command_list: an iterable of strings containing the commands.

        :returns: the output of the last command in the list
        :rtype: Story instance
        """
        current_story = cls.from_single_command(command_list.pop(0))
        for command in command_list:
            current_story = current_story.apply_command(command)
        return current_story

    def apply_command(self, command):
        """Apply a starlab command to this story and return the result.

        Uses the current story as input to the given command.
        :param command: The starlab command to run
        :type command: a string as it would appear on the command line
                       or a list suitable for subprocess.Popen()

        :returns: the output of command
        :rtype: Story instance
        """
        if isinstance(command, str):
            command = command.split(" ")
        elif isinstance(command, list):
            pass
        else:
            raise TypeError('command should be a string or list')

        story_lines = []
        with tempfile() as f:
            f.write(str(self).encode())
            f.seek(0)
            with Popen(command, stdout=PIPE, stdin=f,
                        universal_newlines=True, bufsize=1) as process:
                for line in process.stdout:
                    story_lines.append(line.rstrip())

        thestory = self.from_buf(story_lines)

        # if the command was an integration, we'll get a list
        if isinstance(thestory, list):
            # include the initial conditions
            thestory.insert(0, self)
        return thestory

class Option(object):
    """An option for a starlab command."""
    
    def __init__(self, **kwargs):
        """The basic option is totally empty."""
        
        self.is_required = kwargs.get("is_required", False)
        self.default_value = kwargs.get("default_value", None)
        self.value = kwargs.get("value", None)
        self.long_name = kwargs.get("long_name", "")
        self.parameter = kwargs.get("parameter", "")
        
    def __repr__(self):
        """Short format for command-line use."""
        
        if self.value is None or self.value is False:
            return ""
        elif self.value is True:
            return "-{}".format(self.parameter)
        else:
            return "-{} {}".format(self.parameter, self.value)
        
    def __str__(self):
        """Long format for use in html."""
        string = "-{}: {} [default: {}]".format(self.parameter, self.long_name, self.default_value)
        if self.is_required:
            string += " [required]"
        return string
            
class Command(object):
    def __init__(self):
        
        self.options = []
        # options_dict is set in child classes
        if hasattr(self, 'options_dict'):
            self.options.extend(self.parse_options())
        self.name = ""

    def __repr__(self):
        options_str = " ".join(["{!r} ".format(option) for option in self.options])
        return "{} {}".format(self.name, options_str)
    
    def __str__(self):
        options_str = " ".join(["{!s}\n".format(option) for option in self.options])
        return "{} {} \n Options:\n{}".format(self.name, self.html_description, options_str)
    
    def parse_options(self):
        the_options = []
        for key, opt_dict in self.options_dict.items():
            is_required = opt_dict.get('is_required', False)
            default_value = opt_dict.get('default_value', None)
            long_name = opt_dict.get('long_name', "")
            the_options.append(Option(parameter=key,
                                      long_name=long_name,
                                      is_required=is_required,
                                      default_value=default_value))
        return the_options
        
    def parse_args_options(self, **kwargs):
        # get values from kwargs, if available; otherwise use defaults
        for option in self.options:
            value = kwargs.get(option.parameter, option.default_value)
            if value is None and option.is_required:
                raise ValueError("{}: You must specify a value for option {!s}".format(self.name, option))
            option.value = value

        

class Makeking(Command):
    """Command to construct a King Model."""
    
    def __init__(self, **kwargs):
        
        # options
        self.options_dict = {"b":dict(long_name="specify Steve's rescaling parameter (< 1)",
                                      default_value=0,
                                      is_required=False),
                            "i":dict(long_name="number the particles sequentially",
                                     default_value=False,
                                     is_required=False),
                             "n":dict(long_name="specify number of particles",
                                   is_required=True,
                                   default_value=None),
                             "s":dict(long_name="specify random seed",
                                   is_required=True,
                                   default_value=uuid.uuid4().time_low),
                             "u":dict(long_name="leave final N-body system unscaled",
                                   is_required=False,
                                   default_value=False),
                             "w":dict(long_name="specify King dimensionless depth",
                                   is_required=True,
                                   default_value=None)}
        
        super().__init__()
        self.name = "makeking"
            
        self.parse_args_options(**kwargs)
        
        
class Makesphere(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:14:13

    Construct a simple homogeneous sphere, with (default)

             M = 1, T/U = -1/2, E = -1/4.

    If the "-u" flag is set, the particles are left unscaled, with
    masses 1/n, positions uniformly distributed in a sphere of radius R,
    and velocities uniformly distributed in a range giving approximate
    virial equilibrium.

    Usage:  makesphere [OPTIONS]

    Options:
             -c    add a comment to the output snapshot [false]
             -C    output data in 'col' format [no]
             -i    number the particles sequentially [don't number]
             -l    write sphere radius to dyn story [don't write]
             -n    specify number of particles [no default]
             -o    echo value of random seed [don't echo]
             -R    specify sphere radius [1]
             -s    specify random seed [random from system clock]
             -u    leave unscaled [scale to E=-1/4, M = 1, R = 1]
             -U    leave unscaled and don't place in center of mass
                   frame [scale and center]

    Written by Steve McMillan.
    """

    
class Makeplummer(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:14:12
    
    Construct a Plummer model, with a spatial or mass cut-off to ensure
    finite radius.  The new model system is written to standard output.
    The model system is shifted to place its center of mass at rest at
    the origin of coordinates.  Unscaled systems will be in approximate
    virial equilibrium, based on the continuum limit.

    Usage:   makeplummer [OPTIONS]

    Options:
         -c    add a comment to the output snapshot [false]
         -C    output data in 'col' format [no]
         -i    number the particles sequentially [don't number]
         -m    specify mass cutoff (for finite radius) [0.999]
         -n    specify number of particles [no default]
         -o    echo value of random seed [don't echo]
         -r    specify radius cutoff [22.804 for default mass cutoff]
         -R    toggle reshuffle of particles to remove correlation
               between index and distance from cluster center [true]
         -s    specify random seed [random from system clock]
         -u    leave unscaled [scale to E=-1/4, M = 1, R = 1]

    Written by Piet Hut and Steve McMillan.
    """
    
class Makecube(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:14:11

    Construct a simple homogeneous cube, with (default)

             M = 1, T/U = -1/2, E = -1/4.

    If the "-u" flag is set, the particles are left unscaled, with
    masses 1/n, positions uniformly distributed in [-L, L], and
    velocities uniformly distributed in a range giving approximate
    virial equilibrium.

    Usage:  makecube [OPTIONS]

    Options:
             -c    add a comment to the output snapshot [false]
             -C    output data in 'col' format [no]
             -i    number the particles sequentially [don't number]
             -l    write cube size to dyn story [don't write]
             -L    specify cube size (+/-L) [1]
             -n    specify number of particles [no default]
             -o    echo value of random seed [don't echo]
             -s    specify random seed [random from system clock]
             -u    leave unscaled [scale to E=-1/4, M = 1, R = 1]

    Written by Steve McMillan.
    """
    
class Makemass(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:14:07
    
    Add a mass spectrum to an input snapshot.  Existing node masses
    are overwritten.

    If only one mass limit is set, the other is automatically forced
    to the same value.  In the TwoComponent case, the lower and upper
    limits specify the two component masses.

    Usage: makemass [OPTIONS] < input > output

    Options:
        -C        output in 'col' format (dyn version only) [no]
        -e/E/x/X  exponent [-2.35 (Salpeter)]
        -F/f      mass function option:
                       1) Power-law [default]
                       2) Miller & Scalo
                       3) Scalo
                       4) Kroupa
                       5) GdeMarchi
                       6) Kroupa, Tout & Gilmore 1991
                       7) TwoComponent (uses -h, -l and -u)
                       8) Kroupa 2001
                  option -F requires one of the following strings:
                       Power_Law, Miller_Scalo, Scalo, Kroupa,
                       GdeMarchi, KTG91, TwoComponent, Kroupa01
                  option -f requires the appropriate integer.
        -h/H      fraction of stars in high-mass group (TwoComponent) [0]
        -i        (re)number stellar index from highest to lowest mass.
        -l/L      lower mass limit [1]
        -m/M      scale to specified total mass [don't scale]
        -u/U      upper mass limit [1]
        -s        random seed

    Written by Steve McMillan and Simon Portegies Zwart.
    """
class Makesecondary(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:14:08
    
    Create binary secondary components for randomly selected stars
    in the input snapshot, placing the results in a binary tree.
    Note that only top-level nodes are affected, and the binary
    fraction is determined relative to the number of top-level nodes.
    This function may be called several times to create several
    classes of binaries in a single system.

    Only secondary masses are set here; orbital parameters are set
    by dyn::makebinary.

    No attempt is made to maintain any existing mass or energy scaling.
    Use scale after this function is called, but before makebinary, if
    it is desired to specify energies in kT units.

    Usage: makesecondary [OPTIONS] < input > output

    Options:
         -C    force output in 'col' format (dyn version only) [no]
               (note: loses binary data)
         -f    specify binary fraction for top-level stars having
               masses greater than or equal to the value specified
               with the "-m" option [0.1]
         -i    use (a,b) as component indices [false]
         -I    don't limit masses to primary mass range [false]
         -l    specify lower limit on mass ratio or secondary mass [0]
         -M    specify upper limit for primaries to be binaries [inf]
         -m    specify lower limit for primaries to be binaries [0]
         -q    select choice of minimum mass ratio [false]:
               if true, secondary mass ratio is chosen uniformly
               on [lower_limit, upper_limit];
               if false, secondary mass is chosen uniformly on
               [mmin, primary_mass], where mmin and mmax are
               specified on the command line
         -S    split primary star [false]
         -s    specify random seed [random from system clock]
         -u    specify upper limit on mass ratio or 
               secondary mass [1 or m_primary]

    Written by Steve McMillan and Simon Portegies Zwart.
    """
    
class Scale(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:13:58

    (Re)scale an N-body system to specified M, Q (=T/U), and E.  Note
    that if the required Q implies E > 0, no additional energy scaling
    is applied.

    Note: Only top-level nodes are considered in scale_virial and 
    scale_energy.  Also, only internal positions and velocities
    are modified -- the root pos and vel are left untouched.
    Option "-s" is equivalent to "-M 1 -R 1 -Q 0.5".
    For systems in which stellar data have been specified, the
    physical mass, length, and time scales are already defined.
    Normally those will correspond to the cluster mass, length,
    and time units, so the "-s" option is probably most appropriate
    in most cases.  This tool completes the connection between
    properties and physical units.  In all cases, command-line
    parameters are specified in N-body units.  As of 7/01, systems
    with embedded tidal or other external fields are also properly
    scaled (assuming that the Jacobi radius scales with the virial
    radius).  Note that the virial radius is defined in terms of the
    *internal* potential energy only.  For now, only allow the energy
    to be specified if there are no external (non-tidal) fields.

    Usage: scale [OPTIONS] < input > output

    Options:    
             -c    zero the center of mass position and velocity [no]
             -d    debug mode [off]
             -e    specify softening parameter [0]
             -E    specify total energy [don't scale]
             -m/M  specify total mass [don't scale]
             -q/Q  specify virial ratio [don't scale]
             -r/R  specify virial radius [don't scale]
             -s/S  scale to "standard" units (-m 1 -r 1 -q 0.5) [not set]

    Scale writes the following quantities to the root log story if
    system_time = 0:

     initial_mass
     initial_total_energy
     initial_rvirial
     total_energy

    If no arguments are provided and system_time = 0, scale will compute
    whatever quantities are needed to set these values.

    If a leaf dyn story contains R_eff, it is scaled to follow r_virial.

    Written by Steve McMillan.
    """
    
class Makebinary(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:14:15

    Complete the binary formation process by adding binary orbits to an
    existing binary tree.  It is assumed that the binary tree structure
    and all masses have already been set (e.g. by makesecondary), and
    that positions and velocities of all top-level nodes are already known.

    If possible, use the system parameters to scale the binary parameters.
    If the total system energy is already known (saved in the snapshot
    log or dyn story), then energies are in units of kT.  Otherwise, energies
    are in absolute units.

    Usage:  makebinary [OPTIONS]

    Options:
           -f    function select option [3]

                 1: angular momentum per unit reduced mass
                 (L^2 = am[1-e^2]), solar units;

                 2: semi-major axis or peri/apo, solar units;

                 3: energy

           -e    maximum eccentricity [1]
           -l    lower limit on selected binary parameter [1]

           -o    specify interpretation of limits [1]

                 (-f 1)
                 1: angular momentum,
                 2: angular momentum, detached binary

                 (-f 2) [unit: Rsun]
                 1: semi-major axis,
                 2: semi-major axis, detached and hard
                 (note: -u gives an upper limit on sma),
                 3: -l gives peri, -u gives apo, and detached

                 (-f 3) [N-body units]
                 1: |binary energy|,
                 2: |binary energy| per unit reduced mass,
                 3: |binary energy| per unit binary mass

           -s    specify random seed [take from system clock]
           -u    upper limit on selected binary parameter [1]

    Written by Steve McMillan and Simon Portegies Zwart.
    """

class Kira(Command):
    """Starlab version 4.4.4
    program created on Jan 27 2016 at 22:14:29
    
    Hermite N-body integrator with evolving hierarchical tree structure,
    stellar and binary evolution, and an arbitrary external field.  The
    program reads a snapshot from standard input and writes snapshot(s)
    to standard output.  Periodic log output is sent to standard error.

    Basic options are listed below.  Default values for a new simulation
    are indicated in square brackets.  For restart (continuation of a
    previous kira calculation), the defaults for many options [*] are
    determined from the input snapshot, making it possible to continue
    a run without having to re-specify all the command-line parameters
    previously used.  (These new defaults may still be overridden on
    the command line, of course.)  Some options typically having to do
    with initial setup may be overridden by data from the input
    snapshot (if present), as noted below.  Kira may also turn *on*
    some options (the B, G, S, and u settings) if they were turned
    on in the previous run, but are not specified on the current
    command line.  To prevent this, use the "-o" switch.

    The first page of log output gives detailed information on all
    parameter settings adopted and any modifications made during
    initialization.  In case of doubt, read the log file!

    Usage: kira [OPTIONS] < infile > output

    Options:
             -0    force non-GRAPE operation, if relevant
             -1    suppress density calculation [compute with GRAPE]
             -2    enable DMA GRAPE access (experimental) [no DMA]
             -3    enable special treatment of isolated multiples [no]
             -a    specify accuracy parameter [0.1][*]
             -A    enable "alternate" output [off]
             -b    specify frequency of full binary output, in (integer)
                   units of the log output interval
                   [10; no argument or 0 ==> no output]
             -B    turn on binary evolution [off][*]
             -c    include comment [none]
             -C    specify GRAPE release interval, in seconds [15]
             -d    specify log output interval [1][*]
             -D    specify snapshot interval [end of run]. 
                   Special values:
                               xN: formatted full dump, frequency N;
                               XN: unformatted full dump, frequency N;
                               full/all: same as x1;
                               b: track binary changes only (formatted);
                               B: track binary changes (unformatted);
             -e    specify softening length [0][*]
             -E    use exact calculation [false]
             -f    turn on/off internal dynamical friction on stars [0][*]
             -F    turn on external dynamical friction on the cluster,
                   and optionally specify a scaling coefficient [none]
             -g    specify hysteresis factor [2.5][*]
             -G    specify initial stripping radius [none][*]
             -h    specify stellar-evolution time step [0.015625 = 1/64][*]
             -i    ignore all internal forces (i.e. external only) [false]
             -I    specify (re)initialization timescale [1][*]
             -k    specify perturbation factor [1.e-7][*]
             -K    specify log2(maximum slowdown factor) (integer): [0][*]
             -l    specify close-encounter distance [0.25 --> 0.25/N][*]
                   [option renamed from -f, 7/04]
             -L    specify CPU time limit, in seconds [none]
             -n    stop at specified number of particles [5]
             -N    specify frequency of CPU check output [50000]
             -o    prevent kira from overriding some settings (BGSu)
                   based on input snapshot data [allow]
             -O    save (and overwrite) extra snapshot at each output [no]
             -q    specify initial virial ratio [0.5]
             -r    specify initial virial radius (may not be
                   specified in the input snap) [no]
             -R    specify snapshot file for (re)start [none: use stdin]
             -s    specify random seed [take from system clock]
             -S    turn on stellar evolution [off][*]
             -t    specify time span of calculation [10]
             -T    enable experimental threading and specify n_threads [0]
             -u    enable/disable unperturbed multiples [enabled *NEW*][*]
             -U    toggle all unperturbed motion [enabled][*]
             -v    toggle "verbose" mode [on]
             -W    specify full-dump (worldline) timescale [1]
             -x    toggle output of extended-precision time [on]
             -X    specify escaper removal timescale [reinit][*]
             -y    specify stellar encounter criterion
                   [0 N-body units or solar radii][*]
             -z    specify stellar merger criterion [0 stellar radii][*]
             -Z    specify stellar tidal dissipation criterion
                   [0 stellar radii][*]

    As a convenient shorthand, any "dt" interval specified less than zero
    is interpreted as a power of 2, i.e. "-d -3" sets dt_log = 0.125.  In
    the case of dt_snap, this will also cause snapshot data to be written
    immediately on restart (usually we wait until time dt_snap).

    Written by J. Makino, S. McMillan, S. Portegies Zwart, and P. Hut, .
    """
    
class Simulation(object):
    def __init__(self):
        raise NotImplementedError