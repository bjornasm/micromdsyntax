from ruamel.yaml import YAML
import re


def add_rules_to_items(yamlobj, markdownobject=False):
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


def remove_invalid_blocks(yaml_content, filename):
    yaml = YAML(typ="safe", pure=True)
    res = ""
    for block in re.split(r"(?m)^(?=\s*-\s)", yaml_content):
        try:
            yaml.load(block)
            res += block + "\n"
        except Exception as e:
            print(
                f"""Removed following block from {filename}:\n{block}\nRemoved due to error:\n{e}\nproceeding without it, consider adding it manually."""
            )

            commented_block = (
                "\n# REMOVED THE FOLLOWING DUE TO AN FORMATTING ERROR\n".join(
                    f"# {line}" for line in block.splitlines()
                )
            )
            res += commented_block + "\n"
    return res


def translate_language_name(language):
    mapping = {
        "bash": "sh",
        "python3": "python",
        # add more specific aliases if needed
    }
    lang = language.lower()
    for key in mapping:
        if key in lang:
            return mapping[key]
    return language
