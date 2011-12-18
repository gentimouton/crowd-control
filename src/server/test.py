#from http://docs.python.org/release/3.1.3/library/unittest.html
import random
import unittest

class TestSequenceFunctions(unittest.TestCase):

    #When a setUp() method is defined, the test runner will run that method prior to each test
    def setUp(self):
        #create a fresh sequence for each test
        self.seq = list(range(10))

    def test_shuffle(self):
        # make sure the shuffled sequence does not lose any elements
        random.shuffle(self.seq)
        self.seq.sort()
        self.assertEqual(self.seq, list(range(10)))

    def test_choice(self):
        element = random.choice(self.seq)
        self.assertIn(element, self.seq)

    def test_sample(self):
        self.assertRaises(ValueError, random.sample, self.seq, 20)
        for element in random.sample(self.seq, 5):
            self.assertIn(element, self.seq)
    
    #if a tearDown() method is defined, the test runner will invoke that method after each test. 
    def tearDown(self):
        pass
        
#simple way to run the tests. unittest.main() provides a command line interface to the test script. 
#if __name__ == '__main__':
#    unittest.main()

#Instead of unittest.main(), there are other ways to run the tests 
#with a finer level of control, less terse output, 
#and no requirement to be run from the command line. 
#For example, the last two lines may be replaced with:
#
suite = unittest.TestLoader().loadTestsFromTestCase(TestSequenceFunctions)
unittest.TextTestRunner(verbosity=2).run(suite)


