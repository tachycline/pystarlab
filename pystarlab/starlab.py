from subprocess import Popen, PIPE
import os
import re

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
            
        nextidx = -1
        for index, line in enumerate(lines):
            if index >= nextidx:
                storystart = re.match("^\((\w+)",line)
                if storystart:
                    nextidx, newstory = cls.parse_lines(lines, index+1,
                                                        storystart.group(1))
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

        process = Popen(command, stdout=PIPE, stderr=PIPE)
        result = process.communicate()
        return cls.from_string(result[0])
            
    @classmethod
    def from_command_list(cls, command_list):
        """Generate a story from a list of commands."""
        current_story = cls.from_single_command(command_list.pop(0))
        for command in command_list:
            current_story = current_story.apply_command(command)
        return current_story
    
    @classmethod
    def parse_lines(cls, lines, startidx, name):
        """Recursively define stories from lines of output."""
        thestory = cls()
        thestory.kind = name
        nextidx = -1
        for index,line in enumerate(lines[startidx:]):
            if index >= nextidx-startidx:
                storystart = re.match("^\((\w+)",line)
                storyend = re.match("\)%s"%name, line)
                if storyend: # we've hit the end of our story; get out and pass it back up
                    endindex = index
                    break
                elif storystart: # new story; start up a new parse_lines
                    nextidx, newstory = cls.parse_lines(lines, startidx + index + 1,
                                                        storystart.group(1))
                    thestory.story_subobjects.append(newstory)
                else:
                    thestory.process_line(line)
        return endindex + startidx + 1, thestory
    
    def apply_command(self, command):
        """Apply a starlab command to this story and return the result"""
        if isinstance(command, str):
            command = command.split(" ")
        elif isinstance(command, list):
            pass
        else:
            raise TypeError('command should be a string or list')

        process = Popen(command, stdout=PIPE, stderr=PIPE, stdin=PIPE,
                        universal_newlines=True)
        result = process.communicate(input=str(self))
        return self.from_string(result[0])
    
        
    def integrate(self, kiracmd):
        """Run the kira integrator with this story as initial conditions."""
        #with Popen(cmds, stdout=PIPE, bufsize=1, universal_newlines=True) as p:
        #    for line in p.stdout:
        #        print(line, end='')
        raise NotImplementedError
        
    def process_line(self, line):
        """Deal with lines that hold a single value"""
        # if we can tokenize into an equality, store in the dict, otherwise as a line.
        chunks = re.split('=', line)
        if len(chunks) == 2:
            self.story_vals[chunks[0].strip()] = chunks[1].strip()
        else:
            self.story_lines.append(line)
           

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
