import urllib.request
import json
import re
import yaml


def add_rules_to_items(yamlobj, markdown=False):
    if markdown:
        for rule in yamlobj:
            for key, value in rule.items():
                if isinstance(value, dict) and "rules" not in value:
                    value["rules"] = []
    else:
        for rule in yamlobj["comment"]["rules"]:
            for key, value in rule.items():
                if isinstance(value, dict) and "rules" not in value:
                    value["rules"] = []

    return yamlobj


def add_rules_to_items2(yamlobj, markdownobject=False):
    def ensure_rules(obj):
        if isinstance(obj, list):
            for item in obj:
                ensure_rules(item)
        elif isinstance(obj, dict):
            for key, value in obj.items():
                if isinstance(value, dict):
                    # If value is a dict and does not already contain "rules", add it
                    if "rules" not in value:
                        value["rules"] = []
                    ensure_rules(value)  # Recurse into nested dict
                elif isinstance(value, list):
                    ensure_rules(value)  # Recurse into nested list

    ensure_rules(yamlobj)
    return yamlobj


def retrieveYamlfiles(repo, path, numberOfFiles=100):
    yamlcollection = []
    markdownyamlobj = None
    api_url = f"https://api.github.com/repos/{repo}/contents/{path}"

    with urllib.request.urlopen(api_url) as response:
        data = response.read()
        files = json.loads(data)

    for file in files[:numberOfFiles]:
        if file["name"].endswith(".yaml"):
            with urllib.request.urlopen(file["download_url"]) as raw_response:
                content = raw_response.read().decode("utf-8")
                match = re.search(r"^rules:\s*\n", content, flags=re.MULTILINE)
                if match:
                    if "python3" in file["name"]:
                        language = file["name"].removesuffix("3.yaml")
                    else:
                        language = file["name"].removesuffix(".yaml")
                    rules_index = match.end()
                    rules = yaml.safe_load(content[rules_index:])
                    if language == "markdown":
                        markdownyamlobj = add_rules_to_items2(rules)

                    else:
                        yamlobj = {
                            "comment": {
                                "start": f"(?i)^```{language}$",
                                "end": "^```$",
                                "rules": rules,
                            }
                        }
                        yamlobj = add_rules_to_items2(yamlobj)
                        yamlcollection.append(yamlobj)

    if markdownyamlobj is not None:
        if isinstance(markdownyamlobj, list):
            yamlcollection.extend(markdownyamlobj)
        else:
            yamlcollection.append(markdownyamlobj)
    return yamlcollection


def insert_blank_lines(yaml_text):
    lines = yaml_text.splitlines()
    new_lines = []
    for i, line in enumerate(lines):
        if line.startswith("  - comment:"):
            new_lines.append("")
        new_lines.append(line.replace("/", "//"))
        # If current line is a dict item (- key:) and next is also a dict item, insert blank line

    return "\n".join(new_lines) + "\n"


class IndentDumper(yaml.Dumper):
    def increase_indent(self, flow=False, indentless=False):
        # Override to control indentation behavior
        return super().increase_indent(
            flow, False
        )  # force indentless=False for better indentation


def main():
    yamllist = retrieveYamlfiles(
        repo="zyedidia/micro", path="runtime/syntax", numberOfFiles=1000
    )
    full_yaml = {
        "filetype": "markdownmod",
        "detect": {"filename": r"\.(livemd|md|mkd|mkdn|markdown)$"},
        "rules": yamllist,
    }
    with open(
        r"C:\Users\bjornbsm\.config\micro\syntax\markdownmod.yaml",
        "w",
        encoding="utf-8",
    ) as f:
        f.write(
            insert_blank_lines(
                yaml.dump(
                    full_yaml,
                    allow_unicode=False,
                    Dumper=IndentDumper,
                    sort_keys=False,
                    width=4096,
                    default_flow_style=False,
                )
            )
        )


if __name__ == "__main__":
    main()
