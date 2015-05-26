CFLAGS= $(shell python3.4-config --cflags)
LDFLAGS=$(subst -lpython3.4m,,$(shell python3.4-config --ldflags))

all: gerhard ast.diff

# x86_64-linux-gnu-gcc
# -pthread -Wl,-z,relro  -Wno-unused-result -DNDEBUG -g -fwrapv -O3 \
# -Wall -Wstrict-prototypes -g -fstack-protector-strong -Wformat -Werror=format-security  \
# -fprofile-generate -g -flto -fuse-linker-plugin -ffat-lto-objects -Xlinker -export-dynamic \
# -Wl,-O1 -Wl,-Bsymbolic-functions \
# -o python Modules/python.o libpython3.4m.a \
# -lpthread -ldl  -lutil -lgcov -lrt   -lexpat                   \
# -L/usr/lib -lz  -lexpat                     -lm

# cc -L/usr/lib/python3.4/config-3.4m-x86_64-linux-gnu \
# -L/usr/lib  -lpthread -ldl  -lutil -lm  -Xlinker -export-dynamic \
# -Wl,-O1 -Wl,-Bsymbolic-functions \
# -o gerhard ast.o python.o \
#        /usr/lib/python3.4/config-3.4m-x86_64-linux-gnu/libpython3.4m.a \
#        -lexpat -lz
gerhard: ast.o python.o
	$(CC) $(LDFLAGS) -o $@ $^ \
		/usr/lib/python3.4/config-3.4m-x86_64-linux-gnu/libpython3.4m.a \
		-lexpat -lz -lm -lgcov -lrt \
		-Wl,--trace -Wl,--print-map -Wl,--cref

%.o: %.c
	$(CC) $(CFLAGS) -o $@ -c $<

ast.diff: ast.c.orig ast.c
	diff -uw $^ > $@
