from subprocess import Popen, PIPE
import os
import re
from tempfile import SpooledTemporaryFile as tempfile

class Story:
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

        :param buffered_result: Results of a starlab command in an iterable format
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
            storystart = re.match("^\((\w+)",line)
            if storystart:
                thestory = cls()
                thestory.kind = storystart.group(1)
                story_stack.append(thestory)
            else:
                storyend = re.match("\)%s" % story_stack[-1].kind, line)
                if storyend:
                    thestory = story_stack.pop()
                    if len(story_stack) > 0:
                        story_stack[-1].story_subobjects.append(thestory)
                    else:
                        stories_to_return.append(thestory)
                else:
                    chunks = re.split('=', line)
                    if ((len(chunks) == 2) and story_stack[-1].kind != "Log"):
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

        Assumes the string contains a single story (possibly with story subobjects).
        If there's more than one story in the string (e.g., output from kira), this
        will grab the last and discard the rest.

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

        The command should be a creation command (e.g., makeking, makeplummer, etc.).
        It should also include all of the necessary command line options.

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

        with Popen(command, stdout=PIPE, bufsize=1, universal_newlines=True) as process:
            for line in process.stdout:
                story_lines.append(line.rstrip())

        thestory = cls.from_buf(story_lines)

        return thestory

    @classmethod
    def from_command_list(cls, command_list):
        """Generate a story from a list of commands."""
        current_story = cls.from_single_command(command_list.pop(0))
        for command in command_list:
            current_story = current_story.apply_command(command)
        return current_story

    def apply_command(self, command):
        """Apply a starlab command to this story and return the result"""
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

        return thestory


class Run:
    """Metadata for a cluster simulation."""

    def __init__(self,
                 kingmodel=True,
                 w0=1.5,
                 nstars=2500,
                 masstype=1,
                 runlength=100,
                 exponent=-2.35):
        """Initialize."""
        self.kingmodel = kingmodel
        self.w0 = w0
        self.nstars = nstars

        # mass scaling
        self.masstype = masstype
        self.exponent = exponent
        self.lowerlimit = 0.1
        self.upperlimit = 20

        # kira parameters
        self.runlength = runlength
        self.diagout = 0.5
        self.dumpout = 0.5
