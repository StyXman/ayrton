CFLAGS= $(shell python3-config --cflags)
LDFLAGS=$(subst -lpython3.4m,,$(shell python3.4-config --ldflags))

all: foo ast.diff

foo: ast.o python.o
	$(CC) $(LDFLAGS) -o $@ $^ \
		/usr/lib/python3.4/config-3.4m-x86_64-linux-gnu/libpython3.4m.a \
		-lexpat -lz

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

ast.diff: ast.c.orig ast.c
	diff -uw $^ > $@
