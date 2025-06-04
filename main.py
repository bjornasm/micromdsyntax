import urllib.request
import json
import re
import os
from ruamel.yaml import YAML
from utils import add_rules_to_items, translate_language_name, remove_invalid_blocks
from ruamel.yaml.comments import CommentedMap


def download_yaml_files(repo, save_to_folder="yamlfiles"):
    os.makedirs(save_to_folder, exist_ok=True)

    with urllib.request.urlopen(repo) as response:
        data = response.read()
        files = json.loads(data)

    for file in files:
        if file["name"].endswith(".yaml"):
            download_url = file["download_url"]
            save_path = os.path.join(save_to_folder, file["name"])
            with urllib.request.urlopen(download_url) as raw_response:
                content = raw_response.read()
                with open(save_path, "wb") as f:
                    f.write(content)


def retrieve_files(
    source="files",
    yamlfilepath="yamlfiles",
    repo="https://api.github.com/repos/zyedidia/micro/contents/runtime/syntax",
):
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


def read_yaml_files(files, numberOfFiles=1000):
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
        valid_content = remove_invalid_blocks(content, filename)
        valid_content = valid_content + "\n"
        yaml_content_list.append((language, valid_content))
    return yaml_content_list


def rebuild_yaml_content(yaml_content_list):
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


def create_markdownmdsyntax_yaml(code_syntax, configpath):
    full_yaml = {
        "filetype": "markdown",
        "detect": {"filename": r"\.(livemd|md|mkd|mkdn|markdown)$"},
        "rules": code_syntax,
    }

    try:
        configpath = os.path.expanduser(configpath)
        os.makedirs(configpath, exist_ok=True)
        filepath = os.path.join(configpath, "markdownsyntaxhighlight.yaml")
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
    repo = "https://api.github.com/repos/zyedidia/micro/contents/runtime/syntax"
    source = "files"
    yamlfilepath = "yamlfiles"

    files = retrieve_files(source=source, yamlfilepath=yamlfilepath)

    yaml_content_list = read_yaml_files(files, numberOfFiles=1000)

    code_syntax = rebuild_yaml_content(yaml_content_list)

    create_markdownmdsyntax_yaml(code_syntax, "~/.config/micro/syntax")


if __name__ == "__main__":
    main()
