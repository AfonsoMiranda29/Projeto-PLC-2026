"""
Testes do analisador léxico.

  python3 tests/test_lexer.py

1. Verificações pontuais (casos-limite) com o resultado esperado.
2. Corre o lexer sobre todos os ficheiros tests/lexer/*.f, grava a lista
   de tokens em tests/lexer/<nome>.tokens e confirma que:
     - os exemplos (ex*.f, limite_*.f) não têm erros léxicos;
     - os ficheiros erro_*.f têm pelo menos um erro léxico.
"""

import glob
import io
import os
import sys
from contextlib import redirect_stderr

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(AQUI, '..', 'src'))

from lexer import FortranLexer  # noqa: E402

lx = FortranLexer()


def tipos(codigo):
    return [t.type for t in lx.tokenize(codigo)]


def pares(codigo):
    return [(t.type, t.value) for t in lx.tokenize(codigo)]


falhas = 0


def verifica(nome, obtido, esperado):
    global falhas
    if obtido == esperado:
        print(f"  OK     {nome}")
    else:
        falhas += 1
        print(f"  FALHA  {nome}\n         esperado: {esperado}\n         obtido:   {obtido}")


print("1. Casos-limite")

verifica("case-insensitivity nas palavras-chave e identificadores",
         pares("program Teste\n"),
         [('PROGRAM', 'PROGRAM'), ('ID', 'TESTE'), ('NEWLINE', '\n')])

verifica("strings mantêm maiúsculas/minúsculas",
         pares("print *, 'Ola Mundo'\n")[3],
         ('STRING', 'Ola Mundo'))

verifica("plica duplicada dentro da string",
         pares("print *, 'It''s'\n")[3],
         ('STRING', "It's"))

verifica("1.EQ.2 é INT EQ INT (não o real 1.)",
         tipos("X = 1.EQ.2\n"),
         ['ID', 'ASSIGN', 'INT_CONST', 'EQ', 'INT_CONST', 'NEWLINE'])

verifica("reais: 3.14  .5  2.  1.5E-3",
         [v for t, v in pares("X = 3.14 + .5 + 2. + 1.5E-3\n") if t == 'REAL_CONST'],
         [3.14, 0.5, 2.0, 0.0015])

verifica("literais lógicos em minúsculas",
         pares("b = .true. .or. .False.\n")[2:5],
         [('LOGICAL_CONST', True), ('OR', '.OR.'), ('LOGICAL_CONST', False)])

verifica("operadores relacionais",
         tipos("A .EQ. B .NE. C .LT. D .LE. E .GT. F .GE. G\n")[1::2][:6],
         ['EQ', 'NE', 'LT', 'LE', 'GT', 'GE'])

verifica("** é POWER e * é TIMES",
         tipos("X = A ** 2 * B\n"),
         ['ID', 'ASSIGN', 'ID', 'POWER', 'INT_CONST', 'TIMES', 'ID', 'NEWLINE'])

verifica("label no início da instrução; inteiro no DO é constante",
         tipos("      DO 10 I = 1, N\n   10 CONTINUE\n"),
         ['DO', 'INT_CONST', 'ID', 'ASSIGN', 'INT_CONST', 'COMMA', 'ID', 'NEWLINE',
          'LABEL', 'CONTINUE', 'NEWLINE'])

verifica("comentário 'C' na coluna 1 é ignorado",
         tipos("C isto e um comentario\n      X = 1\n"),
         ['ID', 'ASSIGN', 'INT_CONST', 'NEWLINE'])

verifica("comentário '*' na coluna 1 e '!' no fim da linha",
         tipos("* comentario\n      X = 1 ! outro\n"),
         ['ID', 'ASSIGN', 'INT_CONST', 'NEWLINE'])

verifica("CALL na coluna 1 NÃO é comentário",
         tipos("CALL TROCA(A, B)\n")[0],
         'CALL')

verifica("continuação com '&'",
         tipos("X = A + &\n    B\n"),
         ['ID', 'ASSIGN', 'ID', 'PLUS', 'ID', 'NEWLINE'])

verifica("linhas vazias não geram NEWLINE repetidos",
         tipos("\n\nX = 1\n\n\nY = 2\n"),
         ['ID', 'ASSIGN', 'INT_CONST', 'NEWLINE', 'ID', 'ASSIGN', 'INT_CONST', 'NEWLINE'])

verifica("NEWLINE final mesmo sem '\\n' no fim do ficheiro",
         tipos("END"),
         ['END', 'NEWLINE'])

with redirect_stderr(io.StringIO()):
    list(lx.tokenize("A = 5 # 3\n"))
verifica("carácter inválido gera erro com linha e coluna",
         lx.errors,
         ["Erro léxico: carácter inesperado '#' na linha 1, coluna 7"])

print("\n2. Ficheiros de teste (tests/lexer/*.f)")

for caminho in sorted(glob.glob(os.path.join(AQUI, 'lexer', '*.f'))):
    nome = os.path.basename(caminho)
    with open(caminho, encoding='utf-8') as f:
        codigo = f.read()
    with redirect_stderr(io.StringIO()):
        toks = list(lx.tokenize(codigo))
    erros = list(lx.errors)

    with open(caminho[:-2] + '.tokens', 'w', encoding='utf-8') as out:
        for t in toks:
            out.write(f"{t.lineno:4}  {t.type:<14} {t.value!r}\n")
        for e in erros:
            out.write(f"# {e}\n")

    espera_erro = nome.startswith('erro_')
    ok = bool(erros) == espera_erro
    if not ok:
        falhas += 1
    estado = "OK    " if ok else "FALHA "
    detalhe = f"{len(toks)} tokens, {len(erros)} erro(s)"
    print(f"  {estado} {nome:<22} {detalhe}")

print(f"\n{'Todos os testes passaram.' if falhas == 0 else f'{falhas} teste(s) falharam.'}")
sys.exit(1 if falhas else 0)
