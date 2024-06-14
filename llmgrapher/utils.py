import os
import urllib
import requests
import mimetypes

from pathlib import Path
from llmgrapher.logger import logger

# Create a set of known extensions
extensions = set(ext for ext, _ in mimetypes.types_map.items())
extensions = extensions | {'docx', 'pptx', 'xlsx'}  # add custom extensions

def convert_to_file_uri(path):
    return Path(path).absolute().as_uri()

def traverse_paths(folder):
    """
    Traverses all files and folders inside the given folder path and does this recursively for every subfolder.
    
    :param folder: folder to traverse
    :return: a generator object for traversing through each path
    """
    for root, dirs, files in os.walk(folder):
        for file in files:
            yield os.path.join(root, file)

def is_path_or_uri(s):
    """
    Checks if the given argument is an existing path or a URI.

    Note: Valid but nonexistent paths are marked as None.

    :param s: string to be investigated
    :return: "path" if it's an existing path, "uri" if it's a URI or None if none of the above
    """
    parsed_uri = urllib.parse.urlparse(s)
    # only allow the bellow file supporting URIs
    if parsed_uri.scheme in ('http', 'https', 'ftp', 'file'):
        return 'uri'
    elif os.path.exists(s):  # does not allow inexistent, although valid, paths
        return 'path'
    else:
        return None

def guess_filetype(guess_obj: requests.Response | str | Path):
    """
    Guesses the file type of a file, given either the response object of the file to be downloaded via an HTTP request or
    the path to the file in local storage.

    Args:
        guess_obj: Object from which the guess will be based
        
    Returns:
        the guessed file extension with a "." (e.x ".pdf")
    """
    if type(guess_obj) is requests.Response:
        # TODO
    elif:

class ArgumentProcessor:
    
    def __init__(self, args, silent=True):
        self.args = args
        self.silent = silent

    def _parse_argument(self, arg):
        """
        Parses given argument into URI and file type.
        
        :param arg: argument to be parsed
        :return: tuple of URI and file type
        """
        try:
            uri = None
            arg_type = is_path_or_uri(arg)
            if arg_type == "uri":
                parsed_uri = urllib.parse.urlparse(arg)
                file_path = parsed_uri.path
                uri = arg
            elif arg_type == "path":
                file_path = arg
                uri = convert_to_file_uri(file_path)
            else: # Unsupported Argument - possibly nonexistent path
                if self.silent == False:
                    raise ValueError(f"Unsupported Argument Type for argument: `{arg}`. Possibly nonexistent path.")
                return None, None
            file_type = Path(file_path).suffix[1:] # suffix excluding "."
        
        except Exception as e:
            print(f"Illegal Argument: {arg}")
            raise e

        return uri, file_type
 
    def parse_arguments(self):
        """
        Parses the arguments into two lists. One containing the URIs of the
        arguments and one containing their file types.

        :return: tuple of two lists: URIs and file types
        """
        uris = []
        file_types = []
        for arg in self.args:
            uri, file_type = self._parse_argument(arg)
            uris.append(uri)
            file_types.append(file_type)
        return uris, file_types

class Downloader:
    """
    Downloader class for downloading files from a list of URLs and keeping track
    which already exist in order not to re-download them.
    """
    def __init__(self, download_path, *urls):
        self.download_path = download_path
        self.urls = urls

    def download(self, check_existing=True):
        for url in self.urls:
            filename = url.split("/")[-1]
            file_path = os.path.join(self.download_path, filename)

            # Download the file only if it does not exist
            if not os.path.exists(file_path):
                Downloader.download_file(url, download_path)

    @staticmethod
    def download_file(url, save_path, guess_type=True, stream=False, chunk_size=None, ignore_errors=False):
        """
        Downloads a file.
        
        Args:
            url: URL to download file
            save_path: where to save the file
            guess_type: tries to guess the type of the file if it is missing, appending the guessed file extension to
                        the filename. If file extension cannot be guess, then the filename is not altered.
            stream: weather to download file as a stream
            chunk_size: relevant only if stream=True, it defines the chunk size of the streaming process. If set to None,
                        then, there will be no explicit chunk size, and the chunk size will depend on the streaming process.
            ignore_errors: Does not throw exceptions in case of an error (usually HTTP request errors).
            If it is set to True and error happens, it returns False.

        Returns:
            float: True on succesfull download of the file or False on failure (assumes that ignore_errors is set to True)
        """
        # Execute get request #
        
        if stream:
            response = requests.Session().get(url, stream=True)
        else:
            response = requests.get(url)

        try:
            response.raise_for_status()
        except Exception as e:
            if ignore_errors:
                logger.info(e)
                return False
            else:
                raise e

        # Handle file extension #
        
        # Get the file name from the URL
        filename = os.path.basename(url)
        _, ext = os.path.splitext(filename)
    
        if ext == "":  # file extension is missing
            # Guess file type and get the extension
            content_type = response.headers['content-type']
            guessed_ext = mimetypes.guess_extension(content_type)
    
            if guessed_ext is not None:
                ext = guessed_ext 
            # if guessed_ext is None, the file type could not be determined and another try to guess
            # it will be made after downloading the file, using python-magic
            filename += ext            
        elif ext not in extensions: # possibly the file ending does not represent an extension
            ext = ""  # set it to empty string in order to try the guess later using python-magic
        else:
            error_msg = f"Unexpected value for extension: `{ext}`"
            if ignore_errors:
                logger.warning(error_msg)
            else:
                raise ValueError(error_msg)
            
        # Save File #
        
        file_path = os.path.join(download_path, filename)
        with open(save_path, "wb") as f:
            if stream:
                for chunk in response.iter_content(chunk_size):
                    f.write(chunk)
            else:
                f.write(response.content)

        # Try to guess extension by reading the file contents using python-magic
        if ext == "":
            m = magic.Magic(mime=True).from_file('temp.pdf.tmp')
        
        return True