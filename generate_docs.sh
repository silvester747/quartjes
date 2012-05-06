#!/bin/sh

rm -fr doc
sphinx-apidoc -o doc_builder src/quartjes
cd doc_builder
make html
cd ..
cp doc_builder/_build/doc doc
