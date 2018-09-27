from django.test import TestCase

from proglangs.models import Compiler
from proglangs.utils import guess_filename


class GuessFilenameTests(TestCase):
    def test_java_1(self):
        self.assertEqual(guess_filename(Compiler.JAVA, ''), None)

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

    def test_java_5(self):
        code = '''
        public   class BinaryTree <T extends Comparable <T>>  {
        '''
        self.assertEqual(guess_filename(Compiler.JAVA, code), 'BinaryTree.java')

    def test_java_6(self):
        code = '''
        public class BinaryTree<T extends Comparable <T>>  {
        '''
        self.assertEqual(guess_filename(Compiler.JAVA, code), 'BinaryTree.java')

    def test_java_7(self):
        code = '''\
import java.io.File;

class Parameter {
}

class Tree<T extends Comparable<T>> {
    class Node<E extends Comparable<E>> {
    }

    public class PrintFile implements Method<T> {
    }
}

public class Lab4 {
    public static void main(String[] args) {
    }
}
'''
        self.assertEqual(guess_filename(Compiler.JAVA, code), 'Lab4.java')
