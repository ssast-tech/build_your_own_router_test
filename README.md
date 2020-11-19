# Build Your Own Route Test Script
## Set Up

### Get `test.py`
Please copy `test.py` into your project root dir


### Start pox
```bash
/opt/pox/pox.py −−verbose ucla_cs118
```
### Start router
```bash
make
./router
```

### Start test script
```bash
# generate big file uesd to test wget 
dd if=/dev/urandom of=http_server1/tmp bs=1M count=100 iflag=fullblock

# -s or --strict will enable strict mode, including check icmp seq and ...
sudo ./test.py [-s]

```

# FAQ
- Exception: Error creating interface pair (server1-eth0,sw0-eth1): RTNETLINK answers: File exists
    ```bash
    sudo mn -c
    ```

