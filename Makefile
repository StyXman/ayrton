all: bins docs

bins:
	make -C bin

INSTALL_DIR=$(HOME)/local

tests:
	python3.4 -m unittest discover -v ayrton

docs:
	PYTHONPATH=${PWD} make -C doc html

install: tests bins
	python3.4 setup.py install --prefix=$(INSTALL_DIR)

upload: tests upload-docs
	python3.4 setup.py sdist upload

upload-docs: docs
	rsync --archive --verbose --compress --rsh ssh doc/build/html/ www.grulic.org.ar:www/projects/ayrton/

push: tests
	git push
