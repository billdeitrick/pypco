# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line.
SPHINXOPTS    =
SPHINXBUILD   = sphinx-build
SOURCEDIR     = source
BUILDDIR      = build
SPHINXAPIDOC  = sphinx-apidoc
MODULEDIR     = ../pypco

# Put it first so that "make" without argument is like "make help".
help:
	$(info ** Run `make apidoc` first to build automatic API docs. **)
	$(info Generally, run `make apidoc` then `make html` to build pypco docs.)
	$(info `make apidoc` produces output that should be committed.)
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile

apidoc:
	@$(SPHINXAPIDOC) -f -o "$(SOURCEDIR)" "$(MODULEDIR)"

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)