# Home LLM

This dataset is generated from https://github.com/acon96/home-llm but adapted
to call intents rather than services, so that it is compatible with Home Assistant
`assist`. The background is that home-llm was first developed to call services
but then the intent apis were introduced after. The current maintainer of home-llm
[is not prioritizing](https://github.com/acon96/home-llm/discussions/179#discussioncomment-9929556)
improvements.

## Prepare home-llm environment

Check out the home llm repot https://github.com/acon96/home-llm/tree/develop:

```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
```

Note this installs pytorch and other large dependencies so be prepared, or hack
in your own list of dependencies.

## Generate a home-llm dataset

```bash
$ cd data
$ python3 ./generate_home_assistant_data.py --train --test --large --sharegpt
```
