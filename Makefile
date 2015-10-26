all: docs

INSTALL_DIR=$(HOME)/local

tests:
	bash -c 'while true; do nc -l -s 127.0.0.1 -p 2233 -e /bin/bash; done' & \
	pid=$!; \
	LC_ALL=C python3 -m unittest discover -v ayrton; \
	kill $pid

docs:
	PYTHONPATH=${PWD} make -C doc html

install: tests
	python3 setup.py install --prefix=$(INSTALL_DIR)

unsafe-install:
	echo "unsafe install, are you sure?"
	read foo
	python3 setup.py install --prefix=$(INSTALL_DIR)

upload: tests upload-docs
	python3 setup.py sdist upload

upload-docs: docs
	rsync --archive --verbose --compress --rsh ssh doc/build/html/ www.grulic.org.ar:www/projects/ayrton/

push: tests
	git push
