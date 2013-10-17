CFLAGS= $(shell python3-config --cflags)
LDFLAGS=$(shell python3-config --ldflags)

all: foo

foo: ast.o python.o
	$(CC) $(LDFLAGS) -o $@ $?

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<
