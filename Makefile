all: docs

INSTALL_DIR=$(HOME)/local

tests:
	python3 -m unittest discover -v ayrton

docs:
	make -C doc html

install: tests
	python3 setup.py install --prefix=$(INSTALL_DIR)

upload: tests upload-docs
	python3 setup.py sdist upload

upload-docs: docs
	rsync --archive --verbose --compress --rsh ssh doc/build/html/ www.grulic.org.ar:www/projects/ayrton/

push: tests
	git push github
