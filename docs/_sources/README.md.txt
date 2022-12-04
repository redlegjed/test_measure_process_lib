# Documentation building

* Documentation is built using [Sphinx](https://www.sphinx-doc.org/en/master/)
* Published on github pages following [these instructions](https://coderefinery.github.io/documentation/gh_workflow/#)

## Checking links

```bash
sphinx-build docs/source -W -b linkcheck -d docs/build/doctrees docs/build/html
```