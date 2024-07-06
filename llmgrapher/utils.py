import os
import urllib
import requests
import mimetypes
import magic

from pathlib import Path
from llmgrapher.logger import logger
from tqdm.auto import tqdm

# Create a set of known extensions
EXTENSIONS = set(ext for ext, _ in mimetypes.types_map.items())
EXTENSIONS = EXTENSIONS | {'.docx', '.pptx', '.xlsx'}  # add custom extensions

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

def guess_filetype(obj: requests.Response | str | Path):
    """
    Guesses the file type of a file, given either the response object of the file to be downloaded via an HTTP request or
    the path to the file in local storage.

    Args:
        obj: Object from which the guess will be based
        
    Returns:
        the guessed file extension with a "." (e.x ".pdf")
    """
    if type(obj) is requests.Response:
        mime = guess_obj.headers['content-type']
    elif type(obj) in (str, Path):
        mime = magic.Magic(mime=True).from_file(obj)
    else: 
        raise ValueError(f"Invalid argument: {obj}")

    guessed_ext = mimetypes.guess_extension(mime)
    return guessed_ext


class FileLocationParser:
    """Class used for parsing file locations (i.e URIs or file paths)"""
    
    def __init__(self, locs, silent=True):
        """
        Initializes FileLocationParser object.

        locs:
            locs: list of file locations as URIs and/or file paths
            silent: If `True`, it ignores parse errors, else it throws exception.
        
        Returns:
            initialized FileLocationParser object
        """
        self.locs = locs
        self.silent = silent

    def _parse_loc(self, loc):
        """
        Parses a given file location into a URI.
        
        Args:
            loc: file location to be parsed (accepts either URI or file path)
        
        Returns:
            parsed URI
        """
        try:
            uri = None
            loc_type = is_path_or_uri(loc)
            if loc_type == "uri":
                uri = loc
            elif loc_type == "path":
                uri = convert_to_file_uri(loc)
            else: # Unsupported File Location - possibly nonexistent path
                if self.silent == False:
                    raise ValueError(f"Unsupported File Location Type for location: `{loc}`. Possibly nonexistent path.")
                return None, None        
        except Exception as e:
            print(f"Illegal File Location: {loc}")
            raise e

        return uri

    def parse(self):
        """
        Parses the file locations into URIs.

        File locations can be either URIs or file paths.

        Returns:
            parsed URIs
        """
        return [self._parse_loc(loc) for loc in self.locs]

class Downloader:
    """
    Downloader class for downloading files from a list of URLs and keeping track
    which already exist in order not to re-download them.
    """
    def __init__(self, download_path, urls):
        """
        Initializes Downloader object.
        
        Args:
            download_path: Path to download files.
            urls: urls to download files from.
        """
        if not os.path.exists(download_path):
            raise ValueError(f"Download path: `{download_path}` does not exist")
        self.download_path = Path(download_path)
        self.urls = urls

    def download(self, check_existing=True):  # check_updates=True (check hashsum - overwrite old)
        """
        Downloads the files defined by the urls of the initialized Downloader object.
        
        Args:
            check_existing: Checks if any of the files have already been downloaded in order not to re-download them.
        """
        for url in tqdm(self.urls, "Downlading Files"):
            file_exists = False
            parsed_url = urllib.parse.urlparse(url)
            url_path = Path(parsed_url.path)
            file_path = self.download_path / url_path.name

            # Download the file only if it does not exist
            if check_existing:
                if os.path.exists(file_path):  # exact match search (name + extension)
                    file_exists = True
                else:  # exact match unsuccessful, maybe file extension is missing or it is wrong,
                       # therefore, check for name of the file without extension
                    downloads = os.listdir(self.download_path)
                    for download in downloads:
                        url_filename_splits = url_path.name.rsplit(".", maxsplit=1)
                        download_filename_splits = download.rsplit(".", maxsplit=1)

                        # First part is name of file
                        remote_name = url_filename_splits[0]
                        local_name = download_filename_splits[0]
                        
                        # If less than two splits (no dot found), set extension to empty string,
                        # otherwise set it as the last split
                        remote_ext = '' if len(url_filename_splits) < 2 else url_filename_splits[-1]
                        local_ext = '' if len(download_filename_splits) < 2 else download_filename_splits[-1]
                        
                        # Configure filename to be checked. In case it is an unknown extension, the extension 
                        # may possibly be part of the file, so add this too to the filename for comparison. Otherwise,
                        # use only the name of the file for the comparison.
                        remote_filename = remote_name if remote_ext in EXTENSIONS else remote_name + remote_ext
                        local_filename = local_name if local_ext in EXTENSIONS else local_name + local_ext
                        
                        if remote_filename == local_filename:
                            file_exists = True
                            break
                
            if not file_exists:
                Downloader.download_file(url, self.download_path)

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

        # Handling missing or wrong file extension #
        if ext == "":  # file extension is missing
            guessed_ext = guess_filetype(response)
            if guessed_ext is not None:
                ext = guessed_ext 
            # if guessed_ext is None, the file type could not be determined and another try to guess
            # it will be made after downloading the file, using python-magic
            filename += ext            
        elif ext not in EXTENSIONS: # possibly the file ending does not represent an extension
            ext = ""  # set it to empty string in order to try the guess later using python-magic
            
        # Save File #
        file_path = os.path.join(save_path, filename)
        with open(file_path, "wb") as f:
            if stream:
                for chunk in response.iter_content(chunk_size):
                    f.write(chunk)
            else:
                f.write(response.content)

        # Try to guess extension by reading the file contents using python-magic under-the-hood
        if ext == "":
            guessed_ext = guess_filetype(file_path)
            if guessed_ext is None:
                logger.info(f"File {filename} has unknown file type")
            else:
                os.rename(file_path, file_path + guessed_ext)
        
        return True