all: docs

INSTALL_DIR=$(HOME)/local

tests:
	python3 -m unittest discover -v ayrton

docs:
	make -C doc html

install:
	python3 setup.py install --prefix=$(INSTALL_DIR)
