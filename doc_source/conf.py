# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))


# -- Project information -----------------------------------------------------

project = 'Test, Measure, Process Library'
copyright = '2022, RedLegJed'
author = 'RedLegJed'

# The full version, including alpha/beta/rc tags
release = '0.1.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'recommonmark',
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'classic'
pygments_style =  'one-dark' #'stata-dark'  'monokai'#

# # These folders are copied to the documentation's HTML output
# html_static_path = ['_static']

# # These paths are either relative to html_static_path
# # or fully qualified paths (eg. https://...)
# html_css_files = [
#     'custom.css',
# ]

# html_sidebars = {
#     '**': [
#         'about.html',
#         'searchbox.html',
#         'navigation.html',
#         'relations.html',
#     ]
# }

html_theme_options = {
    # 'footerbgcolor':'', # (CSS color): Background color for the footer line.
    # 'footertextcolor':'', # (CSS color): Text color for the footer line.
    # 'sidebarbgcolor':'#003333', # (CSS color): Background color for the sidebar.
    'sidebarbgcolor':'#1F2125', # (CSS color): Background color for the sidebar.
    # 'sidebarbtncolor':'', # (CSS color): Background color for the sidebar collapse button (used when collapsiblesidebar is True).
    # 'sidebartextcolor':'', # (CSS color): Text color for the sidebar.
    # 'sidebarlinkcolor':'', # (CSS color): Link color for the sidebar.
    # 'relbarbgcolor':'', # (CSS color): Background color for the relation bar.
    # 'relbartextcolor':'', # (CSS color): Text color for the relation bar.
    # 'relbarlinkcolor':'', # (CSS color): Link color for the relation bar.
    'bgcolor':'#444444', # (CSS color): Body background color.
    # 'textcolor':'999999', # (CSS color): Body text color.
    'textcolor':'#AAAAAA', # (CSS color): Body text color.
    'linkcolor':'#61afef', # (CSS color): Body link color.
    'visitedlinkcolor':'#61afef', # (CSS color): Body color for visited links.
    'headbgcolor':'#404347', # (CSS color): Background color for headings.
    'headtextcolor':'#efc07c', # (CSS color): Text color for headings.
    # 'headlinkcolor':'', # (CSS color): Link color for headings.
    # 'codebgcolor':'', # (CSS color): Background color for code blocks.
    # 'codetextcolor':'', # (CSS color): Default text color for code blocks, if not set differently by the highlighting style.
    # 'bodyfont':'', # (CSS font-family): Font for normal text.
    # 'headfont':'', # (CSS font-family): Font for headings.
}

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
# html_static_path = ['_static']

html_logo = 'images/tmpl_dark_logo.png'

# html_css_files = ['custom.css']

# Autodoc settings
autoclass_content = 'both'
autodoc_member_order = 'groupwise'


