# Documentation building

* Documentation is built using [Sphinx](https://www.sphinx-doc.org/en/master/)
* Published on github pages following [these instructions](https://coderefinery.github.io/documentation/gh_workflow/#)

## Checking links

```bash
sphinx-build docs/source -W -b linkcheck -d docs/build/doctrees docs/build/html
```

## Build

Build the documentation from *test_measure_process_lib* with:

```bash
sphinx-build -b html doc_source docs
```

## Publishing in github-pages

There must be a file called *.nojekyll* in the docs directory. If not then github-pages won't format the page correctly because it can't find all the *.css* files in the *_static* directory.

It also seems to be necessary to reset github-pages by selecting 'None' for the branch used for docs, saving it, then selecting 'master' again and setting it all up again.