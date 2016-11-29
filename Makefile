DEBUG_MULTI=strace -tt -T -ff -o debug/runner -s 128
DEBUG_SIMPLE=strace -tt -T -o debug/runner -s 128
RUNNER=python3.5
# RUNNER=python3-coverage run
# can't use --buffer because:
#   File "/home/mdione/src/projects/ayrton/ayrton/__init__.py", line 191, in polute
#     self[std]= getattr (sys, std).buffer
# AttributeError: '_io.StringIO' object has no attribute 'buffer'
UNITTEST_OPTS=--verbose

all: docs

INSTALL_DIR=$(HOME)/local

tests:
	LC_ALL=C $(RUNNER) -m unittest discover $(UNITTEST_OPTS) ayrton

slowtest: debug
	# LC_ALL=C $(DEBUG_SIMPLE) $(RUNNER) -m unittest discover --failfast \
	#       $(UNITTEST_OPTS) ayrton
	LC_ALL=C $(DEBUG_MULTI) $(RUNNER) -m unittest discover --failfast \
		$(UNITTEST_OPTS) ayrton

quicktest:
	LC_ALL=C $(RUNNER) -m unittest discover --failfast $(UNITTEST_OPTS) ayrton

docs:
	RUNNERPATH=${PWD} make -C doc html

install:
	$(RUNNER) setup.py install --prefix=$(INSTALL_DIR)

unsafe-install:
	@echo "unsafe install, are you sure?"
	@read foo
	$(RUNNER) setup.py install --prefix=$(INSTALL_DIR)

upload: tests upload-docs
	$(RUNNER) setup.py sdist upload

upload-docs: docs
	rsync --archive --verbose --compress --rsh ssh doc/build/html/ www.grulic.org.ar:www/projects/ayrton/

push: tests
	git push

check:
	flake8 --ignore E201,E211,E225,E221,E226,E202 --show-source --statistics --max-line-length 130 ayrton/*.py

testclean:
	rm -f ayrton.*log debug/runner* debug/remote* *.ayrtmp

debug:
	mkdir -pv debug

rsa_server_key:
	# generate a rsa server key
	ssh-keygen -f rsa_server_key -N '' -t rsa; \

debugserver: rsa_server_key
	# TODO: discover sshd's path?
	# sshd re-exec requires execution with an absolute path
	/usr/sbin/sshd -dd -e -h $(shell pwd)/rsa_server_key -p 2244

covreport:
	python3-coverage report -m | grep ayrton | egrep -v '/(parser|tests)/'
