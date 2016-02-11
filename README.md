# Introduction

Welcome to `pystarlab`. This is work by the computational physics group at Marietta College to build a python-based web framework around [`starlab`](http://www.sns.ias.edu/~starlab/index.html), an astronomical n-body simulation backage developed by Piet Hut (IAS), Steve McMillan (Drexel U.), Jun Makino (U. Tokyo), and Simon Portegies Zwart (U. of Amsterdam). Our goal is to make it easier for (especially undergraduate) students to build and analyze a library of data without having to climb the whole learning curve associated with using the Unix command line.

In that same spirit, the project includes a Docker image for development work. The resulting docker container exposes a Jupyter notebook server on port 8888 for python development, and exposes port 5000 for the web app. The working directory of the docker container is mounted as an external volume to allow this repository to be maintained asynchronously from the Docker image.

# Getting Started
To start development work, you will want to do three things:

1. Fork this repository and clone your fork.
2. Make sure Docker is installed and launch the appropriate Docker container.
3. Associate your clone of this repository with the volume mounted in the Docker container.

### Forking and cloning
If you are signed in to GitHub and visit the [page for this repository](https://github.com/tachycline/pystarlab), you will notice a button in the upper right region of the page that is labeled `Fork`. Click it. You have successfully forked the repository!

Now, if you actually want to get any work done, you will need to make a *clone* of the repository on your local machine. Open Terminal (for Mac and Linux users) or the command prompt (for Windows users) and issue the following command:

    $ git clone https://github.com/YOUR_USERNAME/pystarlab

with `YOUR_USERNAME` replaced by your username. The files will be copied to your local machine.
For more information, you can look at the [GitHub tutorial](https://help.github.com/articles/fork-a-repo/) on forking and cloning.

### Launching Docker
The details of launching Docker vary a little bit by platform, but the easiest way to get things going if you're on a Mac or Windows machine is to use the Docker GUI `Kitematic`. In Kitematic, search for the image `tachycline/pystarlab` and run it. Container Launched!

### Associate your clone with the container
Once your container is running, you can select it in Kitematic, click on the `Settings` tab, and then 
`Volumes`. You'll see that the `/home/pystarlab` folder has no local folder associated with it. Click the Change button, and open the folder you cloned into above.

You're now ready to go.

# Use
If you're comfortable at the linux command line, you probably already know what to do. If not (and especially if you're running the container on a Mac or Windows machine) the easiest way to start using this image is to click on the web preview in Kitematic. This will open a browser window for you and point it to the container, which is running a Jupyter notebook server. If nothing comes up, it's possible Kitematic sent you to the wrong port (there are two ports open, but only one of them is connected to Jupyter; the other is for our web interface that isn't running yet). You can check the port numbers in the Settings->ports section of your container; you want the one connected to port 8888 on the container.

Jupyter is able to edit any kind of text file (not just notebooks), and can also spawn a shell for you to interact directly with the container. Both of these options are available in the `New` menu.

## Contributing
When you've made some changes and are ready to contribute, you'll need to create a pull request. There is a [section of GitHub's help system](https://help.github.com/articles/proposing-changes-to-a-project-with-pull-requests/) that deals with pull requests.
