# container-interactive-client
Container interactive client.
Try to realize the remote attach to container which has opened the websocket
port.
First will try Docker.
Docker can enable remote api, open and listen to the port.
#How to
1.You need to enable Docker to listen to the port , in this demo, Docker Daemon listen to 0.0.0.0:2375
The doc here will show how to do this: https://docs.docker.com/engine/admin/

2.You can create the docker with the command "-it" and "-d" in docker cmdline.
e.g: sudo docker run -it -d ubuntu /bin/bash

3.Modify the console_url in main.py to set the property link.

4.run "python main.py" to taste.

#Remain issues
1.Websocket-client will need to modify some code when dealing with escape code.
such as: "\x1b[?1049h\x1b[?1h\x1b=\x1b[2;1H\xbd\x1b[6n\x1b[2;1H"
These will be generated when you run "vim"

2.Need to add support to container tty session resize according to current user.

After these done, I will integrate with OpenStack Zun code.

Ref:
Kubectl
Novaconsole
python package websocket-client
