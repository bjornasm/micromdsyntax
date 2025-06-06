import urllib.request
import json
import re
import os
from ruamel.yaml import YAML
from ruamel.yaml.comments import CommentedMap
from utils import add_rules_to_items, translate_language_name, remove_invalid_blocks


def download_yaml_files(repo_url: str, destination_path="yamlfiles"):
    """Function to download all the syntax yaml files from micro's repo to a local folder

    Args:
        repo_url (str): The full github url to the folder that contains micros syntax files
        destination_path (str, optional): Destination folder. Defaults to "yamlfiles".
    """
    os.makedirs(destination_path, exist_ok=True)

    with urllib.request.urlopen(repo_url) as response:
        data = response.read()
        files = json.loads(data)

    for file in files:
        if file["name"].endswith(".yaml"):
            download_url = file["download_url"]
            save_path = os.path.join(destination_path, file["name"])
            with urllib.request.urlopen(download_url) as raw_response:
                content = raw_response.read()
                with open(save_path, "wb") as f:
                    f.write(content)


def retrieve_files(
    source: str = "files",
    yamlfilepath: str = "yamlfiles",
    repo: str = "https://api.github.com/repos/zyedidia/micro/contents/runtime/syntax",
):
    """Function to retrieve and read in files, either through reading directly from the repo - when source="repo" or from a local folder, when source="files".

    Args:
        source (str, optional): Which source to read files from, either "repo" or "files". Defaults to "files".
        yamlfilepath (str, optional): Path to the local folder that holds the yaml files. Defaults to "yamlfiles".
        repo (_type_, optional): Url to the syntaxfiles in the micro repository. Defaults to "https://api.github.com/repos/zyedidia/micro/contents/runtime/syntax".

    Returns:
        _type_: Files as a json object or a list og filepaths.
    """
    if source == "repo":
        with urllib.request.urlopen(repo) as response:
            data = response.read()
            files = json.loads(data)

    elif source == "files":
        if yamlfilepath:
            files = [
                os.path.join(yamlfilepath, f)
                for f in os.listdir(yamlfilepath)
                if f.endswith(".yaml")
            ]
            if len(files) == 0:
                print(
                    "No files found, consider downloading the files first with download_yaml_files(repo, save_to_folder='yamlfiles') or retrieve files from repo: retrieve_files(source='repo', repo='https://api.github.com/repos/zyedidia/micro/contents/runtime/syntax')"
                )
    return files


def read_yaml_files(files, numberOfFiles=1000, languagelist=[]) -> list[str]:
    """Function to read in and validate the confent of the yaml syntax files from the list of files.

    Args:
        files (_type_): Either a json object or json objects from the github repo or a list of filepaths.
        numberOfFiles (int, optional): The number of files that should be read, mostly added for test purposes. Defaults to 1000.
        languagelist (list, optional): A list of which languages to add syntax highlighting to. f.ex ['python', 'sh', 'scala']. Defaults to [] which means that all languages are added..

    Returns:
        list[str]: Returns the content of the collated markdown yaml file
    """
    yaml_content_list = []

    for file in files[:numberOfFiles]:
        if isinstance(file, dict):
            filename = file["name"]
            if filename.endswith(".yaml"):
                with urllib.request.urlopen(file["download_url"]) as raw_response:
                    content = raw_response.read().decode("utf-8")
        else:
            filename = os.path.basename(file)
            if not filename.endswith(".yaml"):
                continue
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()

        language = filename.removesuffix(".yaml")
        language = translate_language_name(language)
        if (language in languagelist) or not languagelist:
            valid_content = remove_invalid_blocks(content, filename)
            valid_content = valid_content + "\n"
            yaml_content_list.append((language, valid_content))
    return yaml_content_list


def rebuild_yaml_content(yaml_content_list):
    """Rebuilds the yamlfile by adding the correct header for each language, as well as the main header for the markdown yaml syntax file.

    Args:
        yaml_content_list (list[str]): List of yaml segments for each language

    Returns:
        list[CommentedMap]: List of CommentedMap
    """
    rebuilt_yaml_content_list = []
    markdownyamlobj = None
    yaml = YAML(typ="safe", pure=True)
    for yaml_content in yaml_content_list:
        language, content = yaml_content
        match = re.search(r"^rules:\s*\n", content, flags=re.MULTILINE)
        if match:
            rules_index = match.end()
            try:
                rules = yaml.load(content[rules_index:])
                if language == "markdown":
                    markdownyamlobj = add_rules_to_items(rules)
                else:
                    comment_block = CommentedMap(
                        {
                            "start": f"(?i)^```{language}$",
                            "end": "^```$",
                            "rules": rules,
                        }
                    )
                    yamlobj = CommentedMap({"comment": comment_block})
                    yamlobj.yaml_set_start_comment(
                        f"----- Rule set for language: {language} -----",
                    )

                    yamlobj = add_rules_to_items(yamlobj)
                    rebuilt_yaml_content_list.append(yamlobj)
            except Exception as e:
                print(e)

    if markdownyamlobj is not None:
        if isinstance(markdownyamlobj, list):
            rebuilt_yaml_content_list.extend(markdownyamlobj)
        else:
            rebuilt_yaml_content_list.append(markdownyamlobj)

    return rebuilt_yaml_content_list


def create_markdownmdsyntax_yaml(
    code_syntax,
    configpath: str = "~/.config/micro/syntax",
    markdownyaml_filename: str = "markdownsyntaxhighlight.yaml",
):
    """Generates the finished yaml file with syntax for markdown as well as highlighting syntax for all languages selected.

    Args:
        code_syntax (_type_): List of CommentedMap that is the yaml syntax for each language
        configpath (str): The path of the micro config file. Defaults to "~/.config/micro/syntax"
        markdownyaml_filename (str): The name of the yaml file that will hold the new syntax rules for markdownfiles. Defaults to "markdownsyntaxhighlight.yaml"


    Raises:
        e: _description_
    """
    full_yaml = {
        "filetype": "markdown",
        "detect": {"filename": r"\.(livemd|md|mkd|mkdn|markdown)$"},
        "rules": code_syntax,
    }

    try:
        configpath = os.path.expanduser(configpath)
        os.makedirs(configpath, exist_ok=True)
        filepath = os.path.join(configpath, markdownyaml_filename)
        yaml = YAML(typ="rt")
        with open(
            filepath,
            "w",
            encoding="utf-8",
        ) as f:
            yaml.dump(full_yaml, f)
    except Exception as e:
        raise e


def main():
    source = "files"
    yamlfilepath = "yamlfiles"
    languagelist = []

    files = retrieve_files(source=source, yamlfilepath=yamlfilepath)

    yaml_content_list = read_yaml_files(
        files, numberOfFiles=1000, languagelist=languagelist
    )

    code_syntax = rebuild_yaml_content(yaml_content_list)

    create_markdownmdsyntax_yaml(code_syntax, "~/.config/micro/syntax")


if __name__ == "__main__":
    main()
