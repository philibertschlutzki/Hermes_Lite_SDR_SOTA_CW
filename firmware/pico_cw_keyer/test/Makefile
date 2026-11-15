# Host-Tests der Keyer-Logik (ohne Pico SDK)
CC ?= gcc
CFLAGS ?= -std=c11 -Wall -Wextra -Werror -O1
SRC = test_keyer.c ../src/keyer.c ../src/cw_morse.c

test: test_keyer
	./test_keyer

test_keyer: $(SRC) ../src/keyer.h ../src/ioboard_regs.h ../src/cw_morse.h
	$(CC) $(CFLAGS) -I../src -o $@ $(SRC)

clean:
	rm -f test_keyer

.PHONY: test clean
