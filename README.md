# broadway-grader

## Starting Grader Instance
- Requires Python 3.5+
- To install virtual env:
```shell
sudo apt-get install python-pip
export LC_ALL="en_US.UTF-8"
export LC_CTYPE="en_US.UTF-8"
sudo pip install virtualenv
virtualenv -p python3 venv
```
- Install the required packages specified in [requirements.txt](requirements.txt) by:
```shell
pip install -r requirements.txt
```
- Install Docker using this [convinience script](https://get.docker.com/)
- Complete [post-installation steps](https://docs.docker.com/install/linux/linux-postinstall/)
- Install Node [guide](https://websiteforstudents.com/install-the-latest-node-js-and-nmp-packages-on-ubuntu-16-04-18-04-lts/)
- Install node packages specified in [package.json](package.json) by:
```shell
npm install
```
- Make sure `API_HOST` and `API_PORT` in the [config file](config.py) is pointing to the [API](https://github.com/illinois-cs241/broadway-api). Start the [grader](grader.py) using:
```shell
nohup sudo venv/bin/python grader.py <cluster token> &
```
Note that under `sudo` the python interpreter path changes to `/usr/bin/python` even when inside a virtual environment. So the above command is required.
