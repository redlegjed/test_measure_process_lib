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