import unittest
import os
import re

DATA_DIR = "test_data"

class StoryTest(unittest.TestCase):
    """Tests for the Story class."""
    
    def test_from_string(self):
        """Test story creation from a string."""
        from pystarlab.starlab import Story
        king_output = "king.out"

        king_path = os.path.join(DATA_DIR, king_output)
        with open(king_path, 'r') as f:
            king_str = f.read()
        king_story = Story.from_string(king_str)
        self.assertEquals(king_str, str(king_story))

    def test_from_buf(self):
        """Test story creation from an iterable source."""
        from pystarlab.starlab import Story
        king_output = "king.out"

        king_path = os.path.join(DATA_DIR, king_output)
        with open(king_path, 'r') as f:
            king_str = f.read()
        king_story = Story.from_buf(king_str.splitlines())
        self.assertEquals(king_str, str(king_story))

    def test_from_single_command(self):
        """Create a story from a starlab command."""
        from pystarlab.starlab import Story
        king_command = "makeking -w 1.5 -s 1454677882 -n 5 -i"

        king_output = "king.out"

        king_path = os.path.join(DATA_DIR, king_output)
        with open(king_path, 'r') as f:
            king_str = f.read()

        king_story = Story.from_single_command(king_command)
        self.assertEquals(len(king_str), len(str(king_story)))
        for line in zip(king_str.splitlines(),
                        str(king_story).splitlines()):
            string_with_date = re.match("^ ===>",line[0])
            if not string_with_date:
                self.assertEquals(line[0], line[1])

        from_list = Story.from_single_command(king_command.split(" "))
        for line in zip(king_str.splitlines(),
                        str(from_list).splitlines()):
            string_with_date = re.match("^ ===>",line[0])
            if not string_with_date:
                self.assertEquals(line[0], line[1])

    def test_apply_command(self):
        """Test chaining a command onto an story, using it as input."""
        from pystarlab.starlab import Story
        king_command = "makeking -w 1.5 -s 1454677882 -n 5 -i"
        mass_command = "makemass -i -l 0.1 -u 20 -s 1454677882"

        mass_output = "mass.out"

        mass_path = os.path.join(DATA_DIR, mass_output)
        with open(mass_path, 'r') as f:
            mass_str = f.read()

        king_story = Story.from_single_command(king_command)
        mass_story = king_story.apply_command(mass_command)

        for line in zip(mass_str.splitlines(),
                        str(mass_story).splitlines()):
            string_with_date = re.match("^ ===>",line[0])
            if not string_with_date:
                self.assertEquals(line[0], line[1])

    def test_command_list(self):
        """Check that we can create a story from a list of commands."""
        from pystarlab.starlab import Story
        commands = ["makeking -w 1.5 -s 1454677882 -n 5 -i",
                    "makemass -i -l 0.1 -u 20 -s 1454677882"]

        mass_output = "mass.out"

        mass_path = os.path.join(DATA_DIR, mass_output)
        with open(mass_path, 'r') as f:
            mass_str = f.read()

        mass_story = Story.from_command_list(commands)
        for line in zip(mass_str.splitlines(),
                        str(mass_story).splitlines()):
            string_with_date = re.match("^ ===>",line[0])
            if not string_with_date:
                self.assertEquals(line[0], line[1])

    def test_story_list_from_kira_command(self):
        """Make sure from_buf returns a list of stories when needed.

        I'm not trying to test that kira works and I've already
        tested that from_buf works correctly for a single story,
        so I don't need to test for content here, only the number of
        stories returned.

        In this case, a run for 10 time units with output every 2 will
        give 5 snapshots, not including the initial conditions. Including
        initial conditions will bump the number up to 6.
        """

        from pystarlab.starlab import Story
        commands = ["makeking -w 1.5 -s 1454677882 -n 50 -i",
                    "makemass -i -l 0.1 -u 20 -s 1454677882",
                    "kira -t 10 -d 1 -D 2"]

        kira_snaps = Story.from_command_list(commands)
        self.assertEquals(len(kira_snaps), 6)

class OptionTest(unittest.TestCase):
    """Tests for the Option class."""
    
    def test_creation(self):
        """Test that the option is created with the right values in the right places."""
        
        from pystarlab.starlab import Option
        opt = Option(parameter="n",
                     long_name="specify number of particles",
                     is_required=True,
                     default_value=None)
        
        self.assertIsInstance(opt, Option)
        self.assertEquals(opt.parameter, "n")
        self.assertTrue(opt.is_required)
        self.assertEquals(opt.long_name, "specify number of particles")
        self.assertIsNone(opt.default_value)
        self.assertIsNone(opt.value)
        
    def test_str(self):
        """Test that the __str__() gives the correctly formatted description."""
        
        from pystarlab.starlab import Option
        opt = Option(parameter="n",
                     long_name="specify number of particles",
                     is_required=True,
                     default_value=None)
        self.assertEquals(str(opt), "-n:  specify number of particles [default: None] [required]")

    def test_repr(self):
        """Test that the __repr__() is what is needed on the command line.
        
        Also check the cases that lead to the option being omitted on the command line.
        
        If the value is True, just print the option and not the value.
        """
        
        from pystarlab.starlab import Option
        opt = Option(parameter="n",
                     long_name="specify number of particles",
                     is_required=True,
                     default_value=None)
        self.assertEquals(repr(opt), "")
        opt.value = False
        self.assertEquals(repr(opt), "")
        opt.value = True
        self.assertEquals(repr(opt), "-n")
        opt.value = 500
        self.assertEquals(repr(opt), "-n 500")

class MakekingTest(unittest.TestCase):
    def test_required(self):
        """Test that missing the required options throws an exception.
        
        And, that having both required arguments doesn't.
        """
        
        from pystarlab.starlab import Makeking
        self.assertRaises(ValueError, Makeking)
        
        self.assertRaises(ValueError, Makeking, n=500)
        
        self.assertRaises(ValueError, Makeking, w=1.4)
        
        # this will fail if it raises any exceptions
        king_nonfailing = Makeking(n=500, w=1.4)
        
    def test_repr(self):
        """Test that the __repr__() gives us a command with appropriate arguments."""
        
        from pystarlab.starlab import Makeking
        king_nonfailing = Makeking(n=500, w=1.4)
        
        # command is first
        self.assertEquals("makeking", repr(king_nonfailing).split(" ")[0])
        
        # order of arguments doesn't matter, so use assertIn()
        self.assertIn("-w 1.4", repr(king_nonfailing))
        self.assertIn("-n 500", repr(king_nonfailing))
        self.assertIn("-s", repr(king_nonfailing)) # actual seed will be random
        
        # Note: other arguments with default values can be supplied,
        # but we don't care about them, so there's no need to test.