"""Convert datasets labeled in doccano."""

import yaml
import json
import sys


def main():
    lines = sys.stdin.readlines()
    for line in lines:
        record = json.loads(line)
        text = record["text"]
        task = json.loads(text)
        label = record["label"]

        output = {
            "uuid": task["uuid"],
            "task_id": task["task_id"],
            "label": label,
        }
        print(yaml.dump(output, sort_keys=False, explicit_start=True))


if __name__ == "__main__":
    main()
