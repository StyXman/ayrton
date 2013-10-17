CFLAGS= $(shell python3-config --cflags)
LDFLAGS=$(subst -lpython3.3m,,$(shell python3-config --ldflags))

all: foo

foo: ast.o python.o
	$(CC) $(LDFLAGS) -o $@ $^ \
		/usr/lib/python3.3/config-3.3m-x86_64-linux-gnu/libpython3.3m.a \
		-lexpat -lz

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<
