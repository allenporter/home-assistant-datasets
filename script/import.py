"""Convert model output records into doccano dataset json."""

import yaml
import json
import sys


def main() -> None:
    for doc in yaml.safe_load_all(sys.stdin.read()):
        print(json.dumps({"text": json.dumps(doc, indent=2)}))


if __name__ == "__main__":
    main()
