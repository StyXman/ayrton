all: docs

tests:
	python3 -m unittest discover -v ayrton

docs:
	make -C doc html
