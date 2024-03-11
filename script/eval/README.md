
```bash
$ python3 -m venv venv
$ source venv/bin/activate
$ pip3 install -r requirements.txt
$ export PYTHONPATH="${PYTHONPATH}:${PWD}/../home-assistant-synthetic-home/cus
tom_components/"
$ pip3 install -r ../home-assistant-synthetic-home/requirements.txt
$ python3 -m script.eval --config datasets/summaries/ --output_dir="/tmp/2024-03-10/"
```
