from django.test import TestCase

from models import Compiler
from utils import guess_filename


class GuessFilenameTests(TestCase):
    def test_java_1(self):
        self.assertEqual(guess_filename(Compiler.JAVA), 'Solution.java')

    def test_java_2(self):
        code = 'public class solution {}'
        self.assertEqual(guess_filename(Compiler.JAVA, code), 'solution.java')

    def test_java_3(self):
        code = '''
        import java.io.File;
        public class indic_sm extends Thread{
        }
        '''
        self.assertEqual(guess_filename(Compiler.JAVA, code), 'indic_sm.java')

    def test_java_4(self):
        code = '''
        // public class Old implements Runnable {
        public class New implements Runnable {
        '''
        self.assertEqual(guess_filename(Compiler.JAVA, code), 'New.java')
