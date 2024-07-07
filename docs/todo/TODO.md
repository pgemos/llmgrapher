# TODO

# extract_graph automation
- [ ] Clean `extract_graph.py` from the unnecessary code inserted during the conversion from jupyter notebook.
- [ ] Better organize `extract_graph.py` code.
- [ ] Remove hardcoded data loading and add command line invoked data loading.
      For the beginning, test using only one data type.
- [ ] Add support for multiple data types (txt, html, pdf)

# utils.py
- [ ] Organize inner code to other modules.
    - [ ] Create utils package and inside it the file module
    - [ ] Create misc module for miscaleneous functions
    - [ ] Create an args module for argument processsing
    - [ ] Add functionality for Parser to save its processed files to avoid processing the same text for a second time
        - [ ]  Keep hash value along with text on first line to compare if need to reparse file if it was changed

## Minor
- [ ] Add requirements.txt
- [ ] Find a way to ignore loguru logs and coordinate it with builtin logger module
- [ ] Add logging support to other modules and make them sync to the same logger
- [ ] Add support for keeping track the hashsums of the files so if the online file has been updated,
      download it and overwrite the old one.

## Super Minor
- [ ] Compare Makefile of new CCDS in GitHub with current one and take features from it.

# Future
- [ ] Select the LLM to use for the prompt. Ask user to download it if necessary.
- [ ] (Super hard, find a way to customize prompt results by having the user modify part of the prompt that dictates how the
      resulting graph will be.

## Features
- [ ] Ability to insert via command line the maximum number of files to load