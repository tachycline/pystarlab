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

class StarlabCommand(Enum):
    """Enumerator class for starlab commands.

    Each command takes three parameters:

    1. A dictionary of required arguments (with default values),
    2. A list of optional arguments that take a value, and
    3. A list of optional arguments that don't take a value.

    If there are parameters which are not, strictly speaking, required
    (i.e., the underlying starlab command will execute without them being
    supplied) but I want to make sure they get into the database, I will
    include them in the required list. The most common example of this is
    random seed for those commands that use one.
    """
    def __init__(self, required, with_value, without_value):
        """Initialize."""

        self.required = required
        self.with_value = with_value
        self.without_value = without_value

    def build_command(self, **cmd_args):
        """Build a command list suitable for passing to subprocess.Run()"""

        command_list = [self.name]
        for arg, default in self.required.items():
            val = cmd_args.get(arg, default)
            command_list.extend(['-'+arg, val])
        for arg in self.with_value:
            val = cmd_args.get(arg, None)
            if val is not None:
                command_list.extend(['-'+arg, val])
        for arg in self.without_value:
            val = cmd_args.get(arg, False)
            if val:
                command_list.append('-'+arg)
        return command_list

class StarlabCreationCommand(StarlabCommand):
    """Starlab cluster creation commands.
    
    The required args dictionaries here don't include the number of stars or the
    random seed, which are required of all these commands and are passed in the
    same way in all cases.
    """

    makesphere = ({}, ['R'], list('ilouU'))
    makecube = ({}, ['L'], list('ilou'))
    makeplummer = ({}, ['m', 'r'], list('iRou'))
    makeking = ({'w':5.0}, ['b'], list('iou'))

    def __init__(self, required, with_value, without_value):
        """Initialize.

        All creation methods require a number of stars, and I'm adding
        random seed to the required list."""
        super().__init__(required, with_value, without_value)

        self.required['n'] = 500
        self.required['s'] = 123456789
        
class StarlabTransformationCommand(StarlabCommand):
    """Starlab cluster transformation commands."""
    makemass = ({'e':-2.35, 'f':1, 's':123456789}, list('hlu'), ['i', 'm'])
    makesecondary = ({'s':123456789}, list('flmMu'), list('iIqS'))
    scale = ({}, list('eEmqr'), ['c', 's'])
    makebinary = ({'s':123456789}, list('felou'), [])

class StarlabIntegrationCommand(StarlabCommand):
    """Time integration"""
    kira = ({'d':1, 's':123456789, 't':10},
            list('bDefFgGhIkKlLnNqRTWXyzZ'),
            list('aABEioOrSuUvx'))

class ArchivedRun(Base):
    """Class for archiving Run objects via SQLAlchemy."""
    __tablename__ = "runs"

    run_id = Column(Integer, primary_key=True)
    creation_command_string = Column(String, length=80)
    creation_command = Column(Enum(StarlabCreationCommand))
    creation_command_args = Column(String, length=80)
    random_seed = Column(Integer)
    n_stars = Column(Integer)
    creation_scale_1 = Column(Float)
    creation_scale_2 = Column(Float)

    def __repr__(self):
        return "<Run %d>" % self.run_id

class Run(object):
    """Metadata for a cluster simulation."""

    def __init__(self, random_seed=None, nstars=500):
        """Initialize."""
        self.creation_command = (None, None)
        self.transform_commands = []
        self.integration_command = (None, None)
        if random_seed is None:
            self.random_seed = uuid.uuid4().time_low
        else:
            self.random_seed = random_seed
        self.nstars = nstars

    def set_creation_command(self, creation_command, **args):
        """Set the creation command."""
        self.creation_command = (creation_command, args)

        self.nstars = args.get('n', self.nstars)
        self.random_seed = args.get('s', self.random_seed)

        self.creation_command[0].required['n'] = self.nstars
        self.creation_command[0].required['s'] = self.random_seed

    def add_transform_command(self, transform_command, **args):
        """Add a transformation command."""
        if 's' in transform_command.required.keys():
            transform_command.required['s'] = args.get('s', self.random_seed)
        self.transform_commands.append((transform_command, args))

    def set_integration_command(self, integration_command, **args):
        """Set the integration command and its arguments."""
        self.integration_command = (integration_command, args)

    def generate_command_list(self):
        """Build the list of commands for execution by Popen."""
        all_commands = [self.creation_command]
        all_commands.extend(self.transform_commands)
        all_commands.append(self.integration_command)

        command_list = [cmd[0].build_command(cmd[1]) for cmd in all_commands]
        return command_list
