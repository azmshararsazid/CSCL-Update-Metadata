import unittest
import os
import sys
import csv
import contextlib
import io
import arcpy

sys.path.insert(0, os.path.abspath("UpdatingTheGDB"))
import metadata

class CsclelementmgrTestCase(unittest.TestCase):

    @classmethod
    def setUpClass(cls):

        # setUpClass sets up one time only. before everything
        # these are variables to use everywhere 
        # in the special setup class they are prefixed with cls.
        #   cls.xyz
        # everywhere else they are prefixed with self.
        #   self.xyz

        # input do not touch this one
        cls.inputgdb = os.path.join(os.path.dirname(__file__)
                                   ,'testdata'
                                   ,'notcscl.gdb')

        # copy to this one as a testing scratch geodatabase
        # we will trash this one after each test
        cls.testgdb = os.path.join(os.path.dirname(__file__)
                                  ,'testdata'
                                  ,'test.gdb')

        cls.testfeatureclass = 'Centerline'

        # add more tricky csvs or rows to test more stuff

        cls.goodcsv = os.path.join(os.path.dirname(__file__)
                                  ,'testdata'
                                  ,'good.csv')
                                  
        cls.badcsv = os.path.join(os.path.dirname(__file__)
                                 ,'testdata'
                                 ,'bad.csv')

    def setUp(self):

        # setUp executes before every test
        # we want a fresh testing geodatabase
        # for every one of our tests

        try:
            arcpy.Delete_management(self.testgdb)
        except:
            pass

        arcpy.Copy_management(self.inputgdb
                             ,self.testgdb)

        # this is mildly annoying
        # https://github.com/azmshararsazid/CSCL-Update-Metadata/issues/6

        self.log_path = os.path.join(os.path.dirname(__file__)
                                   ,'UpdatingTheGDB'
                                   ,'log.txt')
        self.log_file = open(self.log_path, "w")


    def tearDown(self): 

        # tearDown executes after every test
        # we want to get rid of our testing geodatabase
        # no matter what happens
        arcpy.Delete_management(self.testgdb)
        # log file too
        try:
            self.log_file.close()
        except:
            pass

    def test_anoheaders(self):

        # tests should be self-contained and executable in any order
        # they do however run alphabetically by name (I think)
        # I am a rule follower. I like order, not lawlessness.
        # hence the test names test_axx test_bxx...
        # so be it so be it

        # validate headers should return false 

        # UpdatingTheGDB is chatty!
        # lets redirect so we have a clean pass/fail result
        f = io.StringIO()
        with contextlib.redirect_stdout(f):
            self.assertFalse(metadata.validate_headers(None
                                                      ,self.log_file))
        
        # we could check for printout words if we wanted to get nuts
        printout = f.getvalue()

    def test_bbadheaders(self):

        with open(self.badcsv, mode='r', newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            headers = next(reader)

            # the subset check is interesting
            # allows a csv with extra columns I guess

            f = io.StringIO()
            with contextlib.redirect_stdout(f):

                self.assertFalse(metadata.validate_headers(headers
                                                          ,self.log_file))

    def test_csimpleupdate(self):

        # might be better to pull the core arcpy.metadata.Metadata
        # calls into a more manageable/testable subroutine
        # here we override the sys.argv values which is awkward    
        sys.argv = ['metadata.py'
                   ,self.testgdb
                   ,self.goodcsv]

        # first test keep it simple
        # does it work or not?        
        result = metadata.main()

    #def test_dchecktheupdate(self):

        # here's where we might call
        # metadata.main()
        # and then read the gdb and see if the metadata from good.csv
        # actually got written
        # As they say in school, we will "leave this as an exercise for the reader"

if __name__ == '__main__':
    # this the unit test magic
    unittest.main()