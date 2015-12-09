DEBUG_MULTI=strace -tt -T -ff -o runner -s 128
DEBUG_SIMPLE=strace -tt -T -o runner -s 128
PYTHON=python3.4

all: docs

INSTALL_DIR=$(HOME)/local

tests:
	LC_ALL=C $(PYTHON) -m unittest discover -v ayrton

slowtest:
	# LC_ALL=C $(DEBUG_SIMPLE) $(PYTHON) -m unittest discover -f -v ayrton
	LC_ALL=C $(DEBUG_MULTI) $(PYTHON) -m unittest discover -f -v ayrton

quicktest:
	LC_ALL=C $(PYTHON) -m unittest discover -f -v ayrton

docs:
	PYTHONPATH=${PWD} make -C doc html

install: tests
	$(PYTHON) setup.py install --prefix=$(INSTALL_DIR)

unsafe-install:
	@echo "unsafe install, are you sure?"
	@read foo
	$(PYTHON) setup.py install --prefix=$(INSTALL_DIR)

upload: tests upload-docs
	$(PYTHON) setup.py sdist upload

upload-docs: docs
	rsync --archive --verbose --compress --rsh ssh doc/build/html/ www.grulic.org.ar:www/projects/ayrton/

push: tests
	git push

check:
	flake8 --ignore E201,E211,E225,E221,E226,E202 --show-source --statistics --max-line-length 130 ayrton/*.py

testclean:
	rm -rfv ayrton.*log runner.*

debugserver:
	# TODO: generate the server key
	if ! [ -f rsa_server_key ]; then \
		true; \
	fi
	# TODO: discover path?
	/usr/sbin/sshd -dd -e -h $(shell pwd)/rsa_server_key -p 2244
