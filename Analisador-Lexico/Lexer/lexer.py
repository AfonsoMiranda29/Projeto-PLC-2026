"""
Analisador léxico para Fortran 77 (Projeto PL2026) — ply.lex

"""
import re
import sys
import ply.lex as lex

# Palavras-chave (reconhecidas a partir do token ID)

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




   