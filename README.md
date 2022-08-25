# enviromux-exporter
Prometheus exporter for Enviromux

This has been tested with NTI Enviromux E16DDP, exported metrics are things like temperature (celsius), humidity (percent), voltage, status codes and some hardware info.

## Requirements
Python 3.9+  
requests module  
prometheus-client module  

Mandatory enviroment variables:  
```
ENVIROMUX_LOGIN_URL
ENVIROMUX_JSON_URL
ENVIROMUX_IP
ENVIROMUX_USER
ENVIROMUX_PSWD
ENVIROMUX_LISTENING_PORT
```

## Usage
### Command line:
```
source enviromux-example-vars.txt
pip install -r requirements.txt

python enviromux-exporter.py
```
