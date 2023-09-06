# UAARG Onboard Script #

This repository holds the scripts for:

* Recording and logging images, positional information and messages
* Making pathing decisions based on current data and mission objectives
* Making inferences on images for object identification and location
* Communications between PixHawk controller board

### How do I get set up? ###

This script is designed to run on a system with a USB or UART connection to a PixHawk Board, and a camera system. Some functions may not work if the above requirements are not met, but our systems should be designed in a robust way to allow most functions to still work.

## For X86 or arm64 Systems (ie Desktop + Laptop Computers + RPi)

* Install Python3
* Optional Step: It's highly recommended, you create a virtual env before installing dependencies. Activate the virtual environment and proceed. OS specific steps are available in the docs [https://packaging.python.org/guides/installing-using-pip-and-virtual-environments/]
* Initialize all submodules ```git submodule update --init --recursive```
* Install the required dependancies via ```pip install -r requirements.txt```
* You should now be able to run testing python scripts and launch the application

## For armv7l Systems (ie ODroid XU4)

* Install Python3
* Initialize all submodules ```git submodule update --init --recursive```
* Install via apt ```sudo apt install opencv-python```
* Download and install the pip wheels for torch and torchvision on armv7l
* Install the required dependancies via ```pip install -r requirements.txt```
* You should now be able to run testing python scripts and launch the application

## Deploying to the rpi

Extra pi-specific dependencies need to be installed when deploying to an rpi.
These can be done with:

```sh
pip install -r pi-requirements.txt
```

## How to setup for auto-running on a rpi

To setup a systemd service so that shepard will automatically start and
restart.

```sh
uaarg@raspberrypi:~/shepard $ sudo ln shepard.service /etc/systemd/system
uaarg@raspberrypi:~/shepard $ sudo systemctl enable shepard.service 
Created symlink /etc/systemd/system/multi-user.target.wants/shepard.service → /etc/systemd/system/shepard.service.
uaarg@raspberrypi:~/shepard $ sudo systemctl start shepard.service
```

Then you can confirm that everything is working by running:

```sh
uaarg@raspberrypi:~/shepard $ sudo systemctl status shepard.service 
● shepard.service - Shepard
     Loaded: loaded (/etc/systemd/system/shepard.service; enabled; vendor preset: enabled)
     Active: active (running) since Mon 2023-04-03 18:40:55 MDT; 8min ago
   Main PID: 2210 (python)
      Tasks: 9 (limit: 3933)
        CPU: 15min 59.449s
     CGroup: /system.slice/shepard.service
             ├─2210 python /home/uaarg/shepard/main.py
             ├─2220 python /home/uaarg/shepard/main.py
             ├─2221 python /home/uaarg/shepard/main.py
             └─2222 python /home/uaarg/shepard/main.py
```

## How to Solve Permission Errors on Linux

* If you have permission errors accessing ports, you may need to add your user to the 'tty' and 'dialout' groups
* ```sudo usermod -a -G tty {your username}```
* ```sudo usermod -a -G dialout {your username}```
* You will then need to logout and login completely to update your permissions

### Contribution guidelines ###

* Write tests so that functionality can be easily reviewed at a later date
* Create a new branch if working on implementing a new feature that will need review or multiple commits
* Add new required packages to requirements.txt

We have several tools setup, please use them. These are:

- `./scripts/lint.sh` Run a linter over all python files
- `./scripts/fmt.sh` Run a formatter over all python files

Also, keep in mind that the tests and linter is run on every commit and/or PR in our CI.

### Who do I talk to? ###

* UAARG Imaging Leads, Autopilot Leads, and VP Technical should be able to help you with any questions
