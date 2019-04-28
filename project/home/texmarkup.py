# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from pygments import highlight
from pygments.lexers import TexLexer
from pygments.formatters import HtmlFormatter

TEX_EXAMPLES = [
    [
        'Списки',
        (
            'Нумерованный список\n'
            '\\begin{enumerate}\n'
            '    \\item Пункт 1\n'
            '    \\item Пункт 2\n'
            '\\end{enumerate}\n'
        ),
        (
            'Маркированный список\n'
            '\\begin{itemize}\n'
            '    \\item Пункт 1\n'
            '    \\item Пункт 2\n'
            '\\end{itemize}\n'
        ),
        (
            'Вложенный список\n'
            '\\begin{enumerate}\n'
            '  \\item Пункт 1\n'
            '    \\begin{itemize}\n'
            '      \\item Подпункт 1.1\n'
            '      \\item Еще один подпункт\n'
            '    \\end{itemize}\n'
            '  \\item Пункт 2\n'
            '    \\begin{itemize}\n'
            '      \\item Подпункт 2.1\n'
            '      \\item Еще один подпункт\n'
            '    \\end{itemize}\n'
            '\\end{enumerate}\n'
        )
    ],
    [
        'Формулы',
        (
            'Inline-формула $f(x) = x$ не \n'
            'переносится на новую строку\n'
        ),
        (
            'Block-формула $$f(x) = x$$ \n'
            'форматируется по центру \n'
            'новой строки'
        ),
    ],
    [
        'Греческие буквы',
        (
            'Названия с маленькой буквы,\n'
            'например $\\lambda$, $\\alpha$, $\\mu$\n'
        ),
        (
            'Названия с большой буквы,\n'
            'например $\\Lambda$, $\\Theta$, $\\Phi$\n'
        ),
    ],
    [
        'Степень и индексы',
        '$x^5$, $x^{13}$, $2^{2^2}$',
        '$x_i$, $x_{12}$, $x_{i_j}$',
        '$x^5_3$, $x_4^6$, $x_{i, j}^{10}$',
    ],
    [
        'Логические операции',
        '$\\overline{A}$, $\\neg A$, $\\lnot A$',
        '$AB$, $A \\cdot B$, $A \\wedge B$, $A \\land B$',
        '$A \\vee B$, $A \\lor B$',
        '$A \\to B$, $A \\rightarrow B$',
        '$A \\sim B$',
        '$A \\equiv B$',
        '$A \\Longleftarrow B$, $A \\Longrightarrow B$, $A \\iff B$',
    ],
    [
        'Операции над множествами',
        '$\\overline{A}$',
        '$A \\cap B$',
        '$A \\cup B$',
        '$A \\setminus B$',
        '$A \\bigtriangleup B$',
        (
            '$A \\subset B$, $A \\supset B$,\n'
            '$A \\not\\subset B$, $A \\not\\supset B$\n'
        ),
        (
            '$A \\subseteq B$, $A \\supseteq B$,\n'
            '$A \\nsubseteq B$, $A \\nsupseteq B$\n'
        )
    ],
    [
        'Отображения',
        '$f \\circ g$',
        '$f \\colon X \\to Y$',
        '$x \\mapsto y$',
    ],
    [
        'Множества',
        '$\\mathbb{N}$, $\\mathbb{R}$',
        '$x \\in X$, $X \\ni x$, $x \\notin X$',
        (
            '$x = y$, $x \\neq y$, $x \\le y$,\n'
            '$x < y$, $x \\ge y$, $x > y$,\n'
            '$x \\nleq y$, $x \\nless y$,\n'
            '$x \\ngeq y$, $x \\ngtr y$\n'
        ),
        '$X = \\{x_1, x_2, \\ldots, x_n\\}$',
        (
            '$R = \\{(x, y) \\mid x \\in \\mathbb{N},\n'
            'y \\in \\mathbb{R}, x \\le y\\}$\n'
        ),
        '$R \\subseteq A \\times B$',
    ],
    [
        'Дроби',
        '$\\frac{x + 2}{y - 1} + 2$',
        '$\\dfrac{x + 2}{y - 1} + 2$',
    ],
    [
        'Большие операторы',
        '$\\sum\\limits_{i = 1}^n x^i$',
        '$\\bigcap\\limits_{i = 1}^n X_i$',
        '$\\bigcup\\limits_{i = 1}^n X_i$',
    ],
    [
        'Скобки',
        (
            '$(\\sum\\limits_{i = 1}^n\n'
            '\\dfrac{(x + 2)^2}{i})^n$\n'
        ),
        (
            '$\\left( \\sum\\limits_{i = 1}^n\n'
            '\\dfrac{\\left( x + 2 \\right)^2}{i}\n'
            '\\right)^n$\n'
        )
    ],
    [
        'Пробелы',
        '$A B$',
        '$A\\, B$',
        '$A\\: B$',
        '$A\\; B$',
        '$A\\quad B$',
        '$A\\qquad B$',
    ],
    [
        'Ещё немного о форматировании текста',
        'Выделение текста \\textit{курсивом}',
        'Выделение текста \\textbf{полужирным}',
        '\\texttt{Моноширинный} шрифт',
        (
            'Строки, не разделённые пустой \n'
            'строкой, будут одним абзацем.\n'
            'Это ещё продолжение прошлого\n'
            'абзаца.\n'
        ),
        (
            'Строки, разделенные пустой строкой,\n'
            'относятся к разным абзацам.\n'
            '\n'
            'Это уже новый абзац.\n'
        ),
        (
            'Маленький-маленький дефис и\n'
            'тире~--- это разные символы.\n'
        ),
        (
            'Некоторые выражения можно брать в <<кавычки>>.'
        )
    ]
]


def highlight_tex(code):
    lexer = TexLexer()
    formatter = HtmlFormatter(nowrap=True)
    return highlight(code, lexer, formatter)
