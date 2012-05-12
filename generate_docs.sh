#!/bin/sh

rm -fr doc/*.html
sphinx-apidoc -f -o doc_builder src/quartjes
cd doc_builder
make clean
make html
cp -R _build/html/* ../doc/
