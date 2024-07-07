"""Command Line Interface Module for LLMGrapher."""

import typer

from pathlib import Path
from typing import List, Optional, Annotated
from rich import print

# Local Imports #
from llmgrapher import __app_name__, __version__
from llmgrapher import utils

# Secure mode not showing locals (e.x variables containing passwords)
app = typer.Typer(pretty_exceptions_show_locals=False) # pretty_exceptions_short=False) # non-secure detailed info
# Non-secure detailed info
# app = typer.Typer(pretty_exceptions_short=False)



def _version_callback(value: bool) -> None:
    if value:
        typer.echo(f"{__app_name__} v{__version__}")
        raise typer.Exit()

# Techinal Note:
# When used with Annotated, the first argument to Option is not the default value (although defined like this
# in the function definition) but the first option parameter (maybe there is an appropriate handling for that in
# the typer library source code to insert the value of the `default` parameter as the first item of the param_decls tuple).

# Opinion Note:
# I find sometimes confusing the usage of Annotated in comparison with the old way, especially when the Option or Argument
# initialization code is large. For me it is more readable to have the default value as a first value to the constructor,
# rather than defining it in the end as a default parameter value of the function.

# OLD WAY
# @app.callback()
# def main(
#     version: Optional[bool] = typer.Option(
#         None,
#         "--version", "-v",
#         help="Show the application's version and exit.",
#         callback=_version_callback,
#         is_eager=True,
#     )
# ) -> None:
#     return

@app.callback()
def main(
    version: Annotated[Optional[bool], typer.Option(
        "--version", "-v",
        help="Show the application's version and exit.",
        callback=_version_callback,
        is_eager=True
    )] = None  # default value
) -> None:
    return

@app.command()
def run(
    files: Annotated[Optional[List[str]], typer.Argument(
        help=("Paths or URLs of the files to be parsed and/or downloaded from which to extract their text and "
             "turn it to graph")
    )] = None,
    file_list: Annotated[Optional[str], typer.Option(
        "--file-list", "-f",
        help="Path to the file containing the list of files (file paths and URLs) to parse and/or download."
    )] = None
) -> None:
    """
    Runs the LLMGrapher by parsing and/or downloading the files defined as arguments to the command line and in the
    file list, if it was set with the option `--file-list`.
    """
    input_files = []
    if len(files) != 0:
        input_files.extend(files)
    if file_list is not None:
        with open(file_list, "r") as f:
            input_files.extend(f.read().splitlines())
    if len(input_files) == 0:
        raise typer.BadParameter("No files where provided")

    print(input_files)
    loc_parser = utils.FileLocationParser(input_files)
    loc_parser.parse()
    urls = loc_parser.get_urls()
    paths = loc_parser.get_paths()
    uri_paths = loc_parser.get_paths(as_uri=True)
    print(urls)
    print(paths)
    print(uri_paths)

@app.command()
def download(urls: List[str]) -> None:
    print(urls)

if __name__ == "__main__":
    app()