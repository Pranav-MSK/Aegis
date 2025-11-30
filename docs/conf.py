# -- Imports -----------------------------------------------------------------
from datetime import datetime

# -- Project Information -----------------------------------------------------
project = 'SystemGuard'
author = 'SystemGuard Team'
version = '1.0.5'
copyright = f"{datetime.now().year} {author}"

# -- General Configuration ---------------------------------------------------
extensions = [
    'sphinx.ext.autodoc',          # Document from docstrings
    'sphinx.ext.todo',             # Support for todo notes
    'sphinx.ext.coverage',         # Check documentation coverage
    'sphinx.ext.viewcode',         # Highlighted source code links
    'sphinx.ext.autosectionlabel', # Reference sections automatically
    'sphinx.ext.githubpages',      # Publish HTML docs on GitHub Pages
]
autosectionlabel_prefix_document = True

# PDF generation (requires external tool)
pdf_documents = [
    ('index', 'SystemGuard_Documentation', 'SystemGuard Docs', 'SystemGuard Team')
]

# GitHub Releases Integration
releases_github_path = "SystemGuard-official/systemguard"
releases_unstable_prehistory = True

# Paths and file formats
templates_path = ['_templates']
source_suffix = ".rst"
master_doc = "index"
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store', '.venv']

# -- HTML Output Configuration -----------------------------------------------
html_theme = 'pydata_sphinx_theme'  # Alternatives: 'sphinx_rtd_theme', 'alabaster'
html_static_path = ['_static']

html_theme_options = {
    "show_prev_next": True,
    "navigation_depth": 4,
    "collapse_navigation": True,
    "navbar_align": "content",
    "show_nav_level": 2,
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/SystemGuard-official/systemguard",
            "icon": "fab fa-github",
            "type": "fontawesome"
        },
        {
            "name": "Releases",
            "url": "https://github.com/SystemGuard-official/systemguard/releases",
            "icon": "fas fa-tag",
            "type": "fontawesome"
        }
    ],
    "use_edit_page_button": True,
}

html_context = {
    "github_user": "SystemGuard-official",
    "github_repo": "systemguard",
    "github_version": "production",
    "doc_path": "docs",
}

html_sidebars = {
    '**': [
        'globaltoc.html',    # Global table of contents
        'relations.html',    # Next/previous page links
        'sourcelink.html',   # View source code link
        'searchbox.html',    # Search box
    ]
}

html_css_files = [
    'custom.css'  # Additional styling
]