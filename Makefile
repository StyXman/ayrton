# DEBUG_MULTI=strace -tt -T -ff -o runner -s 128
# DEBUG_SIMPLE=strace -tt -T -f -o runner -s 128

all: docs

INSTALL_DIR=$(HOME)/local

tests:
	LC_ALL=C $(DEBUG_MULTI) python3 -m unittest discover -v ayrton

quicktest: fasttest

fasttest:
	LC_ALL=C $(DEBUG_SIMPLE) python3 -m unittest discover -f -v ayrton

docs:
	PYTHONPATH=${PWD} make -C doc html

install: tests
	python3 setup.py install --prefix=$(INSTALL_DIR)

unsafe-install:
	@echo "unsafe install, are you sure?"
	@read foo
	python3 setup.py install --prefix=$(INSTALL_DIR)

upload: tests upload-docs
	python3 setup.py sdist upload

upload-docs: docs
	rsync --archive --verbose --compress --rsh ssh doc/build/html/ www.grulic.org.ar:www/projects/ayrton/

push: tests
	git push

check:
	flake8 --ignore E201,E211,E225,E221,E226,E202 --show-source --statistics --max-line-length 130 ayrton/*.py
