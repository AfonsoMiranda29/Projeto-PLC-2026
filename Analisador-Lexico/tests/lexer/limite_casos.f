! Casos-limite do lexer
      program Casos
      real x, y
      logical b
      x = 1.EQ.2            ! inteiro seguido de .EQ. (nao e o real '1.')
      y = 3.14 + .5 - 2. * 1.5E-3 ** 2
      b = .not. (x .ne. y) .or. .True.
      print *, 'It''s ok', "aspas"   ! plica dentro da string
      y = x + &
          y
      End
