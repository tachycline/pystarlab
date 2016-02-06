import unittest
import os
import re

DATA_DIR = "test_data"

class StoryTest(unittest.TestCase):
    
    def test_from_string(self):        
        from pystarlab.starlab import Story
        king_output = "king.txt"

        king_path = os.path.join(DATA_DIR, king_output)
        with open(king_path, 'r') as f:
            king_str = f.read()
        king_story = Story.from_string(king_str)
        self.assertEquals(king_str, str(king_story)) 

    def test_from_single_command(self):
        from pystarlab.starlab import Story
        king_command = "makeking -w 1.5 -s 1454677882 -n 5 -i"

        king_output = "king.txt"

        king_path = os.path.join(DATA_DIR, king_output)
        with open(king_path, 'r') as f:
            king_str = f.read()
        
        king_story = Story.from_single_command(king_command)
        for line in zip(king_str.splitlines(), str(king_story).splitlines()):
            string_with_date = re.match("^ ===>",line[0])
            if not string_with_date:
                self.assertEquals(line[0], line[1])

        from_list = Story.from_single_command(king_command.split(" "))
        for line in zip(king_str.splitlines(), str(from_list).splitlines()):
            string_with_date = re.match("^ ===>",line[0])
            if not string_with_date:
                self.assertEquals(line[0], line[1])


    def test_apply_command(self):
        from pystarlab.starlab import Story
        king_command = "makeking -w 1.5 -s 1454677882 -n 5 -i"
        mass_command = "makemass -i -l 0.1 -u 20 -s 1454677882"

        mass_output = "mass.txt"

        mass_path = os.path.join(DATA_DIR, mass_output)
        with open(mass_path, 'r') as f:
            mass_str = f.read()
        
        king_story = Story.from_single_command(king_command)
        mass_story = king_story.apply_command(mass_command)

        for line in zip(mass_str.splitlines(), str(mass_story).splitlines()):
            string_with_date = re.match("^ ===>",line[0])
            if not string_with_date:
                self.assertEquals(line[0], line[1])
