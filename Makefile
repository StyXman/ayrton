all: bin/gerhard docs

bin/gerhard:
	make -C bin

INSTALL_DIR=$(HOME)/local

tests: bin/gerhard
	bin/gerhard -m unittest discover -v ayrton

docs:
	PYTHONPATH=${PWD} make -C doc html

install: tests bin/gerhard
	bin/gerhard setup.py install --prefix=$(INSTALL_DIR)

upload: tests upload-docs bin/gerhard
	bin/gerhard setup.py sdist upload

upload-docs: docs
	rsync --archive --verbose --compress --rsh ssh doc/build/html/ www.grulic.org.ar:www/projects/ayrton/

push: tests
	git push
