Setup for Ubuntu should happen in this order:
1. python
1. git
1. eclipse
1. pydev



Python
======

Install Python 3.2 on top of existing Python 2.7 (if any). See http://www.giantflyingsaucer.com/blog/?p=2858:
> sudo apt-get install build-essential
> sudo apt-get install libreadline5-dev libncursesw5-dev libssl-dev libsqlite3-dev tk-dev libgdbm-dev libc6-dev libbz2-dev
> wget http://python.org/ftp/python/3.2/Python-3.2.tgz
> tar -xvf Python-3.2.tgz && cd Python-3.2/
> ./configure
> make
> sudo make altinstall
 

Git
====

For coloring in terminal:
> git config --global color.status auto
See http://en.newinstance.it/2010/05/23/git-autocompletion-and-enhanced-bash-prompt/

See changes in current branch:
> git diff --stat


Eclipse
=========

Get Eclipse from the package manager or apt-get. 

PyDev is an Eclipse plug-in for Python development. Get it from within Eclipse: `Help` -> `Install new software` -> http://pydev.org/updates

Unity may hide the scrolling bars of Eclipse's code editor and console. To re-add them:
> vim /usr/bin/eclipse
Then add below the line `GDK_NATIVE_WINDOWS=true`:
> export UBUNTU_MENUPROXY=0
> export LIBOVERLAY_SCROLLBAR=0
See http://askubuntu.com/questions/36448/is-there-a-way-to-blacklist-an-individual-application-from-using-overlay-scrollb


Pygame
======


See http://www.pygame.org/wiki/CompileUbuntu?parent=Compilation

>sudo apt-get install python3.2-dev libsdl-image1.2-dev libsdl-mixer1.2-dev libsdl-ttf2.0-dev libsdl1.2-dev libsmpeg-dev python-numpy subversion libportmidi-dev ffmpeg libswscale-dev libavformat-dev libavcodec-dev
> hg clone https://bitbucket.org/pygame/pygame
(apt-get or package manager if you don't have hg)
> cd pygame

Open `setup.py` and modify line 123: `raw_input(...)` should instead be `input(...)`

> python3.2 setup.py build
> sudo python3.2 setup.py install

Now, you should not have any error running:
> python3.2 examples/chimp.py



