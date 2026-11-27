.PHONY: build test clean

build:
	.venv/bin/python3 motor/build_all.py

test:
	.venv/bin/python3 motor/validate_google_fonts.py

clean:
	rm -rf __pycache__ motor/__pycache__
