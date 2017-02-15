# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from question import SingleAnswerQuestion, MultipleAnswersQuestion, TextAnswerQuestion


class IQuestionFactory(object):
    def make_question(self, rng):
        raise NotImplementedError()


class BinomialHeapQuestionFactory(IQuestionFactory):
    slug = 'binary-heap-tree-count'
    name = 'Подсчёт деревьев в биномиальной куче'

    def make_question(self, rng):
        n = rng.randint(1, 31)
        ans = self._solve(n)

        q = SingleAnswerQuestion()
        q.text = 'Если в биномиальной куче $n = {}$ вершин, то сколько биномиальных деревьев будет в этой куче?'.format(n)
        for x in range(1, 6):
            q.add_choice('${}$'.format(x), x == ans)

        return q

    def _solve(self, n):
        return bin(n).count('1')


class GraphClassesQuestionFactory(IQuestionFactory):
    slug = 'graph-classes'
    name = 'Классы графов'

    def make_question(self, rng):
        n = 6
        a = self._gen_graph(rng, n)

        q = MultipleAnswersQuestion()
        q.text = (
            'Для графа, заданного матрицей смежности $A$, определить, какие из следующих утверждений верны.\n'
            '$$\n'
            'A={}\n'
            '$$'
        ).format(self._to_tex(a))

        is_connected, is_bipartie = self._run_bfs(a, n)

        q.add_choice('граф связный', is_connected)
        q.add_choice('граф содержит не менее двух компонет связности', not is_connected)
        q.add_choice('граф двудольный', is_bipartie)
        q.add_choice('граф недвудольный', not is_bipartie)
        q.add_choice('граф связный и содержит эйлеров цикл', is_connected and self._all_degrees_even(a))
        q.add_choice('граф является деревом', is_connected and (self._count_edges(a) == n - 1))
        return q

    def _to_tex(self, a):
        return '\\begin{pmatrix}' + '\\\\\n'.join(' & '.join((str(x) for x in row)) for row in a) + '\\end{pmatrix}'

    def _gen_graph(self, rng, n):
        a = [[0] * n for _ in range(n)]
        for i in range(n):
            for j in range(i + 1, n):
                a[i][j] = a[j][i] = rng.randint(0, 1)
        return a

    def _run_bfs(self, a, n):
        is_connected = True
        is_bipartie = True

        color = [None] * n

        for start in range(n):
            if color[start] is None:
                if start != 0:
                    is_connected = False

                color[start] = 0
                queue = [start]
                while queue:
                    v = queue[0]
                    queue = queue[1:]
                    for u in range(n):
                        if a[v][u]:
                            if color[u] is None:
                                color[u] = color[v] ^ 1
                                queue.append(u)
                            else:
                                if color[u] == color[v]:
                                    is_bipartie = False

        return (is_connected, is_bipartie)

    def _all_degrees_even(self, a):
        for row in a:
            if sum(row) % 2 == 1:
                return False
        return True

    def _count_edges(self, a):
        return sum(sum(row) for row in a) // 2


class RecurrentQuestionFactory(IQuestionFactory):
    slug = 'recurrent'
    name = 'Решение рекуррентных соотношений'

    a_variants = [
        ('', (1, 1)),
        ('2', (2, 1)),
        ('3', (3, 1)),
        ('4', (4, 1)),
        ('5', (5, 1)),
        ('6', (6, 1)),
        ('7', (7, 1)),
        ('\\frac{1}{2}', (1, 2)),
        ('\\frac{1}{4}', (1, 4)),
    ]

    def make_question(self, rng):
        n = 2 ** rng.randint(7, 9)
        a_tex, a_frac = rng.choice(self.a_variants)
        b = rng.randint(1, 9)

        q = TextAnswerQuestion()
        q.text = (
            'Решить рекуррентное уравнение и вычислить его значение при $n = {n}$.\n'
            '\n'
            '$$\n'
            'T(n) = \\begin{{cases}}\n'
            '2T\\left(\\frac{{n}}{{2}}\\right) + {a} n^2, & n=2^k,\\:k \\ge 1; \\\\\n'
            '{b}, & n = 1.\n'
            '\\end{{cases}}\n'
            '$$\n'
        ).format(n=n, a=a_tex, b=b)

        q.set_answer('{}'.format(self._solve(n, a_frac, b)))
        return q

    def _solve(self, n, a_frac, b):
        return n * (2 * a_frac[0] * n - 2 * a_frac[0] + b * a_frac[1]) // a_frac[1]


class HashTableQuestionFactory(IQuestionFactory):
    slug = 'hash-table'
    name = 'Хеш-таблицы'

    def make_question(self, rng):
        n = 10
        q = TextAnswerQuestion()

        numbers = rng.sample(xrange(100), n)
        target = rng.choice(numbers)

        q.text = (
            'Хеш-таблица состоит из ${0}$ сегментов (сегменты нумеруются целыми числами от $0$ до ${1}$). '
            'Для разрешения коллизий используется метод открытой адресации. '
            'Функция $$h(x,i)=((x \\bmod {0})+i) \\bmod {0}$$ задаёт линейную последовательность проб свободных сегментов. '
            'При хешировании элементы добавлялись в таблицу в следующем порядке: ${2}$. '
            'Указать номер сегмента, в котором находится число ${3}$.'
        ).format(n, n - 1, ', '.join([str(x) for x in numbers]), target)

        result = self._run_hash_table(numbers)
        q.set_answer('{}'.format(result.index(target)))
        return q

    def _run_hash_table(self, elems):
        a = [None] * len(elems)
        for x in elems:
            i = 0
            while True:
                pos = (x + i) % len(a)
                if a[pos] is None:
                    a[pos] = x
                    break
                i += 1
        return a


FACTORIES = [
    BinomialHeapQuestionFactory(),
    GraphClassesQuestionFactory(),
    RecurrentQuestionFactory(),
    HashTableQuestionFactory(),
]
