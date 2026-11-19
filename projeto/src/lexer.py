"""
Analisador léxico para Fortran 77 (Projeto PL2026) — ply.lex

Decisões de formato (documentar no relatório):
  * Formato LIVRE (free-form): as instruções podem começar em qualquer coluna.
  * Comentários:
      - '!' em qualquer ponto da linha (fora de strings) até ao fim da linha;
      - linhas com 'C', 'c' ou '*' na coluna 1 seguidos de espaço (ou sozinhos),
        como no formato clássico (exemplo 6 do enunciado).
  * Continuação de linha: '&' no fim da linha.
  * Insensível a maiúsculas/minúsculas: palavras-chave e identificadores são
    normalizados para MAIÚSCULAS; o conteúdo das strings fica intacto.
  * O fim de cada instrução é marcado por um token NEWLINE (o Fortran é
    orientado à linha). Linhas vazias/comentários não geram NEWLINE repetidos.
  * Um inteiro no início de uma instrução é um LABEL (ex.: '10 CONTINUE').

Uso:
  from lexer import FortranLexer
  lx = FortranLexer()
  for tok in lx.tokenize(codigo): ...

  python3 lexer.py programa.f        (imprime os tokens)
"""

import re
import sys
import ply.lex as lex

# ---------------------------------------------------------------------------
# Palavras-chave (reconhecidas a partir do token ID)
# ---------------------------------------------------------------------------
reserved = {
    'PROGRAM': 'PROGRAM',
    'END': 'END',
    'INTEGER': 'INTEGER',
    'REAL': 'REAL',
    'LOGICAL': 'LOGICAL',
    'CHARACTER': 'CHARACTER',
    'IF': 'IF',
    'THEN': 'THEN',
    'ELSE': 'ELSE',
    'ENDIF': 'ENDIF',
    'DO': 'DO',
    'CONTINUE': 'CONTINUE',
    'GOTO': 'GOTO',
    'GO': 'GO',          # para 'GO TO'
    'TO': 'TO',
    'READ': 'READ',
    'PRINT': 'PRINT',
    'WRITE': 'WRITE',
    'STOP': 'STOP',
    'FUNCTION': 'FUNCTION',
    'SUBROUTINE': 'SUBROUTINE',
    'CALL': 'CALL',
    'RETURN': 'RETURN',
}

tokens = [
    # literais e nomes
    'ID', 'INT_CONST', 'REAL_CONST', 'STRING', 'LOGICAL_CONST',
    # operadores relacionais e lógicos (.EQ. ...)
    'EQ', 'NE', 'LT', 'LE', 'GT', 'GE',
    'AND', 'OR', 'NOT', 'EQV', 'NEQV',
    # operadores aritméticos
    'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'POWER',
    # pontuação e delimitadores
    'LPAREN', 'RPAREN', 'COMMA', 'ASSIGN', 'COLON',
    # estrutura
    'LABEL', 'NEWLINE',
] + sorted(set(reserved.values()))

DOTTED = {
    'EQ': 'EQ', 'NE': 'NE', 'LT': 'LT', 'LE': 'LE', 'GT': 'GT', 'GE': 'GE',
    'AND': 'AND', 'OR': 'OR', 'NOT': 'NOT', 'EQV': 'EQV', 'NEQV': 'NEQV',
}


class LexerRules:
    tokens = tokens

    # Operadores simples (ply ordena estas regras por comprimento da ER,
    # por isso '**' é testado antes de '*')
    t_POWER  = r'\*\*'
    t_PLUS   = r'\+'
    t_MINUS  = r'-'
    t_TIMES  = r'\*'
    t_DIVIDE = r'/'
    t_LPAREN = r'\('
    t_RPAREN = r'\)'
    t_COMMA  = r','
    t_ASSIGN = r'='
    t_COLON  = r':'

    t_ignore = ' \t\r'

    # As regras-função são testadas PELA ORDEM em que aparecem.

    # Comentário de linha completa: C / c / * na coluna 1
    def t_COMMENT_FIXED(self, t):
        r'^[Cc*](?=[ \t\r\n]|$)[^\n]*'
        pass  # ignorado

    # Comentário com '!' até ao fim da linha
    def t_COMMENT_BANG(self, t):
        r'![^\n]*'
        pass

    # Continuação: '&' no fim da linha -> junta com a seguinte
    def t_CONTINUATION(self, t):
        r'&[ \t\r]*\n'
        t.lexer.lineno += 1

    # .TRUE. / .FALSE.
    def t_LOGICAL_CONST(self, t):
        r'\.(TRUE|FALSE)\.'
        t.value = t.value.upper() == '.TRUE.'
        return t

    # .EQ. .NE. .LT. .LE. .GT. .GE. .AND. .OR. .NOT. .EQV. .NEQV.
    def t_DOTTED_OP(self, t):
        r'\.(EQ|NE|LT|LE|GT|GE|AND|OR|NOT|EQV|NEQV)\.'
        op = t.value.upper()[1:-1]
        t.type = DOTTED[op]
        t.value = '.' + op + '.'
        return t

    # Real: 3.14  2.  .5  1E10  2.5E-3
    # O lookahead impede que '1.EQ.2' seja lido como '1.' seguido de 'EQ.2'
    def t_REAL_CONST(self, t):
        r'(\d+\.(?!(EQ|NE|LT|LE|GT|GE|AND|OR|NOT|EQV|NEQV|TRUE|FALSE)\.)\d*([ED][+-]?\d+)?|\.\d+([ED][+-]?\d+)?|\d+[ED][+-]?\d+)'
        t.value = float(t.value.upper().replace('D', 'E'))
        return t

    def t_INT_CONST(self, t):
        r'\d+'
        t.value = int(t.value)
        return t

    # Strings entre plicas (ou aspas); '' dentro da string representa uma plica
    def t_STRING(self, t):
        r"'([^'\n]|'')*'|\"([^\"\n]|\"\")*\""
        q = t.value[0]
        t.value = t.value[1:-1].replace(q + q, q)   # NÃO converte para maiúsculas
        return t

    def t_ID(self, t):
        r'[A-Za-z][A-Za-z0-9_]*'
        t.value = t.value.upper()
        t.type = reserved.get(t.value, 'ID')
        return t

    def t_NEWLINE(self, t):
        r'\n+'
        t.lexer.lineno += len(t.value)
        return t

    def t_error(self, t):
        col = self.find_column(t.lexer.lexdata, t.lexpos)
        msg = f"Erro léxico: carácter inesperado {t.value[0]!r} na linha {t.lineno}, coluna {col}"
        self.errors.append(msg)
        print(msg, file=sys.stderr)
        t.lexer.skip(1)

    @staticmethod
    def find_column(data, pos):
        inicio = data.rfind('\n', 0, pos) + 1
        return pos - inicio + 1


class FortranLexer(LexerRules):
    """Envolve o lexer do ply e faz o pós-processamento:
       - inteiros no início de uma instrução passam a LABEL;
       - NEWLINE repetidos (ou no início do ficheiro) são removidos;
       - garante um NEWLINE final."""

    def __init__(self, **kwargs):
        self.errors = []
        self.lexer = lex.lex(module=self, reflags=re.IGNORECASE | re.MULTILINE, **kwargs)

    def input(self, data):
        self.errors = []
        self.lexer.lineno = 1
        self.lexer.input(data)
        self._prev = None        # tipo do último token emitido
        self._fim = False

    def token(self):
        while True:
            tok = self.lexer.token()
            if tok is None:
                # NEWLINE final, para o parser saber que a última instrução acabou
                if not self._fim and self._prev not in (None, 'NEWLINE'):
                    self._fim = True
                    tok = lex.LexToken()
                    tok.type, tok.value = 'NEWLINE', '\n'
                    tok.lineno, tok.lexpos = self.lexer.lineno, self.lexer.lexpos
                    self._prev = 'NEWLINE'
                    return tok
                return None
            if tok.type == 'NEWLINE':
                if self._prev in (None, 'NEWLINE'):
                    continue                     # linha vazia ou comentário
                tok.value = '\n'
            elif tok.type == 'INT_CONST' and self._prev in (None, 'NEWLINE'):
                tok.type = 'LABEL'               # ex.: '10 CONTINUE'
            self._prev = tok.type
            return tok

    def tokenize(self, data):
        self.input(data)
        while True:
            tok = self.token()
            if tok is None:
                break
            yield tok


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 lexer.py programa.f", file=sys.stderr)
        sys.exit(1)
    with open(sys.argv[1], encoding='utf-8') as f:
        codigo = f.read()
    lx = FortranLexer()
    for tok in lx.tokenize(codigo):
        valor = repr(tok.value)
        print(f"{tok.lineno:4}  {tok.type:<14} {valor}")
    if lx.errors:
        sys.exit(1)


if __name__ == '__main__':
    main()
