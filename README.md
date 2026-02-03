# WRWC Water Quality

<a target="_blank" href="https://cookiecutter-data-science.drivendata.org/">
    <img src="https://img.shields.io/badge/CCDS-Project%20template-328F97?logo=cookiecutter" />
</a>

Water quality analysis for teh Woonasquatucket River Watershed Coucil

## Project Organization

```
├── README.md          <- The top-level README for developers using this project.
├── data
│   ├── external       <- Data from third party sources.
│   ├── interim        <- Intermediate data that has been transformed.
│   ├── processed      <- The final, canonical data sets for modeling.
│   └── raw            <- The original, immutable data dump.
│
├── notebooks          <- Jupyter notebooks
│
├── pyproject.toml     <- Project configuration file with package metadata for 
│                         wrwc and configuration for tools like black
│
├── references         <- Data dictionaries, manuals, and all other explanatory materials.
│
├── reports            <- Generated analysis as HTML, PDF, LaTeX, etc.
│   └── figures        <- Generated graphics and figures to be used in reporting
│
└── wrwc   <- Source code for use in this project.
    │
    ├── __init__.py             <- Makes wrwc a Python module
    │
    ├── config.py               <- Store useful variables and configuration
    │
    ├── dataset.py              <- Scripts to download or generate data
    │
    └── plots.py                <- Code to create visualizations
```

--------
## 🔧 Development Setup (with uv)

To set up a development environment using uv, a fast Python package manager:

1. Install uv (if not already installed): [Installing uv](https://docs.astral.sh/uv/getting-started/installation/)
2. Clone the repository:

    ```bash
    git clone https://github.com/brown-ccv/wrwc-water-quality.git
    cd wrwc-water-quality
    ```

3. Create the virtual environment and install dev dependencies:

    ```bash
    uv venv
    uv sync
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
    > ⚙️ This installs the package in editable mode with development dependencies 
   > defined in pyproject.toml. The local source code is installed and changes 
   > take effect immediately.

4. Verify the installation (optional):
    ```bash
    pytest
    ```
