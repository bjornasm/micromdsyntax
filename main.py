from typing import LiteralString
import urllib.request
import json
import re
import os
from ruamel.yaml import YAML
from utils import add_rules_to_items, translate_language_name, remove_invalid_blocks
from ruamel.yaml.comments import CommentedMap
from textwrap import TextWrapper
import textwrap


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


def get_missing_indents(text) -> LiteralString:
    for line in text.splitlines():
        if not re.match(r"^\s*#", line) and line.strip():
            current_indent = len(line) - len(line.lstrip(" "))
            needed_spaces = max(0, 4 - current_indent)
            return " " * needed_spaces
    return ""


def add_missing_rules_block(text):
    adjusted_text = ""
    lines = text.split("\n")
    for i in range(0, len(lines) - 2):
        line = lines[i]
        trimmed_line = line.strip()
        if (
            len(trimmed_line) > 1
            and trimmed_line[0] != "-"
            and trimmed_line[0] != "#"
            and "rules" not in trimmed_line
        ):
            nextline = lines[i + 1].strip()
            if len(nextline) < 2:
                newline = line.replace(trimmed_line, "rules: []")
                line = f"{line}\n{newline}"
            elif (nextline[0] == "-") or (
                (nextline[0] == "#") and (lines[i + 2].strip()[0] == "-")
            ):
                newline = line.replace(trimmed_line, "rules: []")
                line = f"{line}\n{newline}"
        adjusted_text += f"{line}\n"
    return adjusted_text


def extract_rules_block(file):
    if isinstance(file, dict):
        filename = file["name"]
        if filename.endswith(".yaml"):
            with urllib.request.urlopen(file["download_url"]) as raw_response:
                content = raw_response.read().decode("utf-8")
    else:
        filename = os.path.basename(file)
        if filename.endswith(".yaml"):
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
    try:
        language = filename.strip(".yaml").lower()
        if language == "bat":
            print("bat")
        if language == "python3":
            language = "python"
        yamlparts = content.split("rules:", 1)
        if len(yamlparts) < 2:
            raise ValueError(
                f"'rules:' not found in file: {file}"
            )  # Dedent what's after 'rules:'
        else:
            rules = yamlparts[1]
            rules = add_missing_rules_block(rules)
            needed_indents = get_missing_indents(rules)
            rules = textwrap.indent(rules, needed_indents)
            languagetag = f"# ----- Syntaxrules for {language} ----- #"
            languageheader = f"""- comment:\n    start: (?i)^```{language}$\n    end: ^```\n    rules:"""
            return f" {languagetag}\n{languageheader}\n{rules}"
        # indented_block = textwrap.indent(parts[1], "    "

    except Exception:
        raise


def append_all_rules(file_paths, base_yaml):
    # Get indentation of 'rules:' line in base_yaml
    result = base_yaml + "\n"

    # For each file, extract and append
    wrapper = TextWrapper(initial_indent="", subsequent_indent="  ")
    for path in file_paths:
        block = extract_rules_block(path, wrapper)
        # indented_block = textwrap.indent(block, child_indent)
        indented_block = block
        result += indented_block + "\n"

    return result  # remove final trailing newline


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

    ### YAML WAY ###
    # files = retrieve_files(source=source, yamlfilepath=yamlfilepath)

    # yaml_content_list = read_yaml_files(files, numberOfFiles=1000)

    # code_syntax = rebuild_yaml_content(yaml_content_list)

    # create_markdownmdsyntax_yaml(code_syntax, "~/.config/micro/syntax")

    ### TEXTWRAP WAY ###

    base_yaml = r"""filetype: markdown
detect:
    filename: \.(livemd|md|mkd|mkdn|markdown)$
rules:"""

    # Let's say you have multiple rule YAMLs
    files = retrieve_files(source=source, yamlfilepath=yamlfilepath)
    for file in files:
        result = extract_rules_block(file)
        base_yaml += "\n" + result
    #    result = append_all_rules(files, base_yaml)
    # Save result
    with open(
        r"C:\Users\70350163\.config\micro\syntax\markdownsyntaxhighlight.yaml",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(base_yaml)


if __name__ == "__main__":
    main()
