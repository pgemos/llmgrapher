"""LLMGrapher entry point script"""

from llmgrapher import __app_name__
from llmgrapher import cli

def main():
    cli.app(prog_name=__app_name__)

if __name__ = "__main__":
    main()