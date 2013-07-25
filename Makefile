all: docs

tests:
	python3 -m unittest discover ayrton

docs:
	make -C doc html
