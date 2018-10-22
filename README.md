Installation
============
```
git clone https://github.com/assafmuller/trello-sprint.git
sudo dnf install -y python3-virtualenv
virtualenv-3 .venv
. .venv/bin/activate
pip install -r requirements.txt
mv trello_sprint/auth.sample trello_sprint/auth.conf
```

Configuration
============
Edit trello_sprint/auth.conf with your Trello api_key, api_secret and token. The API key is generated at https://trello.com/app-key. The token is generated via a link at the top of the page, and the API secret is found at the bottom of the page.

Usage
=====
```
cd trello_sprint
python3 main.py --board "DFG-Networking-vNES Squad" --sprint 0
```

Assumptions
===========
* The board must contain the following columns: Backlog, Doing, and Done
* trello-sprint will only print cards that have the appropriate sprint label: 'Sprint %s', %s filled in by the 'sprint' CLI argument
* The boards' cards must have an 'Hours' custom attribute