#!/bin/sh

rm -fr doc
sphinx-apidoc -o doc_builder src/quartjes
cd doc_builder
make html
cp -R _build/html ../doc
