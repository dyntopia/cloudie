.PHONY: all install install-dev test qa

all:

install:
	pip3 install -r requirements/requirements.txt
	./setup.py install

install-dev:
	pip3 install -r requirements/requirements.txt
	pip3 install -r requirements/requirements-dev-1.txt
	pip3 install -r requirements/requirements-dev-2.txt
	pip3 install -r requirements/requirements-dev-3.txt
	./setup.py develop

test:
	python3 -m unittest -q

qa:
	coverage run -m unittest -q
	coverage report -m
	isort --check-only --diff --recursive .
	mypy .
	pycodestyle .
	pyflakes .
	pylint --output-format parseable setup.py cloudie tests
	yapf --diff --recursive .
