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

### Contribution guidelines ###

* Write tests so that functionality can be easily reviewed at a later date
* Create a new branch if working on implementing a new feature that will need review or multiple commits
* Add new required packages to requirements.txt

### Who do I talk to? ###

* UAARG Imaging Leads, Autopilot Leads, and VP Technical should be able to help you with any questions
