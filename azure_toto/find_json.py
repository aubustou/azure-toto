from __future__ import annotations

from dataclasses import dataclass
import logging

import json5 as json
from pathlib import Path
from typing import Any, Optional, Type, TypedDict, cast


class MandatoryAzureDeployParameter(TypedDict):
    """AzureDeployParameter type."""

    type: str


class OptionalAzureDeployParameter(TypedDict, total=False):
    defaultValue: str
    allowedValues: list[str]
    minValue: int
    maxValue: int
    minLength: int
    maxLength: int
    description: str


class AzureDeployParameter(MandatoryAzureDeployParameter, OptionalAzureDeployParameter):
    """AzureDeployParameter type."""


class AzureDeployVariable(TypedDict):
    """AzureDeployVariable type."""

    type: str
    defaultValue: str
    allowedValues: list[str]
    metadata: dict[str, Any]


class MandatoryAzureDeployResource(TypedDict):
    type: str
    apiVersion: str
    name: str
    properties: dict[str, str]


class OptionalAzureDeployResource(TypedDict, total=False):
    location: str
    dependsOn: list[str]
    copy: dict[str, str]
    scope: str
    kind: str
    sku: dict[str, str]


class AzureDeployResource(MandatoryAzureDeployResource, OptionalAzureDeployResource):
    pass


class AzureDeployOutput(TypedDict):
    """AzureDeployOutput type."""

    type: str
    value: str
    condition: str


class MandatoryAzureDeployMetadata(TypedDict):
    """AzureDeployMetadata type."""

    _generator: dict[str, str]


class OptionalAzureDeployMetadata(TypedDict, total=False):
    """AzureDeployMetadata type."""

    _templateHash: str
    _schema: str
    description: str
    author: str


class AzureDeployMetadata(MandatoryAzureDeployMetadata, OptionalAzureDeployMetadata):
    pass


MandatoryAzureDeploy = TypedDict(
    "MandatoryAzureDeploy",
    {
        "$schema": str,
        "contentVersion": str,
        "resources": list[AzureDeployResource],
    },
)


class OptionalAzureDeploy(TypedDict, total=False):
    functions: list[str]
    metadata: AzureDeployMetadata
    outputs: dict[str, Any]
    parameters: dict[str, Any]
    variables: dict[str, Any]


class AzureDeploy(MandatoryAzureDeploy, OptionalAzureDeploy):
    """AzureDeploy type."""


def find_json(path: Path) -> list[Path]:
    """Find all JSON files in a directory tree."""
    return list(path.glob("**/azuredeploy.json"))


def get_data_from_json(path: Path) -> Optional[AzureDeploy]:
    """Get data from JSON file."""
    try:
        return cast(AzureDeploy, json.load(path.open()))
    except ValueError as error:
        logging.warning("Error on file %s: %s", path, error)
        return None


def get_subkeys(value: Any, key: str, found_subkeys) -> None:
    if isinstance(value, dict):
        for subkey in value:
            found_subkeys.setdefault(key, {}).setdefault(subkey, 0)
            found_subkeys[key][subkey] += 1


def main() -> None:
    """Run the main function."""
    logging.basicConfig(level=logging.INFO)

    path = Path(".")

    found_keys: dict[str, int] = {}
    found_subkeys: dict[str, dict[str, int]] = {}
    found_items_in_list: dict[str, int] = {}
    total_number_of_files: int = 0

    for index, file in enumerate(find_json(path)):
        if index > 10_000:
            break
        if (data := get_data_from_json(file)) is not None:
            total_number_of_files += 1
            for key, value in data.items():
                if key not in found_keys:
                    found_keys[key] = 0
                found_keys[key] += 1

                if isinstance(value, list):
                    for item in value:
                        found_items_in_list.setdefault(key, 0)
                        found_items_in_list[key] += 1
                        get_subkeys(item, key, found_subkeys)
                else:
                    get_subkeys(value, key, found_subkeys)

    logging.info("Found %s files", total_number_of_files)

    logging.info("Root keys:")
    for key, count in found_keys.items():
        if count == total_number_of_files:
            count = "\x1b[31;21mALL\x1b[0m"
        # log with red color on count
        logging.info(" %s: %s", key, count)

        if key in found_subkeys:
            if key in found_items_in_list:
                count = found_items_in_list[key]
            logging.info("  Subkeys:")
            for subkey, subcount in found_subkeys.get(key, {}).items():
                if subcount == count:
                    subcount = "\x1b[31;21mALL\x1b[0m"
                # log with red color on subcount
                logging.info("   %s: %s", subkey, subcount)


if __name__ == "__main__":
    main()
