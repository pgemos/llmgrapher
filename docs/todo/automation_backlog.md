# Knowledge-Graph Automation Backlog

## Ver. 0.0.1

### Delete Unecessary Files

`assets`
- [x] INDIA NON JUDICIAL.pdf (added by mistake)

`docs`
- [x] Remove all folder contents. HTML files are now put in the `ui` folder. Repurpose folder to include all documentation files.

`ollama`
- [x] Remove whole folder. Access to `ollama` is now achieved through the the PIP Python `ollama` package.

`old_notebooks`
- [x] Remove whole folder. Old notebooks that are not needed.

`.github`
- [x] Remove whole folder. Not needed.

### Add git support

- [x] Add `jupyterlab-git` extension to environment.yaml
- [x] Add .gitignore based on Python and Jupyter Notebook [gitignore templates](https://github.com/toptal/gitignore/tree/master/templates) .

### Add logging support

- [x] Use logging library to output info to both screen and log files.
- [x] Set logging levels accordinly and setup descriptive log formats including timestamp, log level and message.

### Refactoring

- [x] Have a single `data` folder and move data_input and data_ouput inside it.
- [x] Convert extract_graph.ipynb to a working .py file

### Package Update and Install
- [x] Update Langchain to the newest version which has the new hierarchy of packages and install those too.
- [x] Change code to accomodate changes due to the update.
- [x] Install PyArrow and add it to the project dependencies (environment.yml) as suggested by the new update of Pandas.

## Ver. 0.0.2

### New Features
- [x] Create a new branch `productionize-dev` which will be a work-in-progress branch to be pulled when work is done and merged to `productionze` branch.
- [x] (Vague) Continue using Jupyter Notebooks for Experimentation and Testing. Store these notebooks inside a separate folder.
- [x] Adopt a standard way of building a .py project. Use [Cookiecutter Data Science V2](https://github.com/drivendata/cookiecutter-data-science/tree/v2)
    - [x] Organize files accordingly.
    - [x] Change file paths in code accordingly
- [x] Clean-up unnecessary files

## Ver. 0.0.3

### New Features
- [ ] Have a standalone .py file that can be invoked from command-line, which can automatically load files in either `txt`, `html` or `pdf` form, extracting (entity1, relatonship, entity2) triplets and producing an `html` file containing a graph visualization.
- [x] Ability to keep downloaded matterial offline and check if already downloaded in order not to download again.
    - [x] (Optional) Have a download only mode.