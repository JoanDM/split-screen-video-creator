# Split screen video creator
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Python 3.9.5=0](https://img.shields.io/badge/python-3.9.5-blue.svg)](https://www.python.org/downloads/release/python-395/)

This tool will create a split screen video composition by stitching videos side by side, as shown in the demo below:

https://user-images.githubusercontent.com/29776287/173233919-bb23ecc6-3147-4135-8d2f-155a1b834c00.mov

The script can not only create a split screen composition but can also add timers, slow-down the video speed, and more.

```python
usage: create_split_screen_video.py [-h] -dir DIR [-out OUT] [-nosubs] [-smf SMF] [-fd FD] [-timers] [-noaudio]

Create a split screen video composition by stitching videos in a directory

optional arguments:
  -h, --help  show this help message and exit
  -dir DIR    Directory containing videos
  -out OUT    Output directory to store video composition. Defaults to same folder containing input video
  -nosubs     Flag to deactivate default video subtitle insertion
  -smf SMF    Slow-motion factor. E.g. x2 will slowdown frame rate by two. N.B. Audio cannot be preserved if smf>2
  -fd FD      Last frame freezing duration in seconds
  -timers     insert timers
  -noaudio    remove audio from final composition
```

# QuickStart: One-time setup

Make sure you have installed `ffmpeg` ([How to get FFMPEG with Homebrew](https://formulae.brew.sh/formula/ffmpeg)) on our machine and the paths in `config.py` are correct.

You can use `which ffmpeg` and `which ffprobe` to locate their path in your system.

Then run:
```bash
cd split-screen-video-creator
python3 -mvenv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
export PYTHONPATH=$(pwd)
```
Now you should be able to run the scripts!

In order to not increase the repository size too much, store big files on git LFS. Make sure you have it installed on your Mac
([How to get git LFS with Homebrew](https://formulae.brew.sh/formula/git-lfs)).

You might have to run `git lfs pull` to download the files in `resources/`.

If you want to contribute to the codebase, make sure you set the pre-commit hooks before committing code changes.
[How to set pre-commit hooks](#code-formatting)

# Code formatting
Code formatting is enforced with [Black](https://black.readthedocs.io/).
 
On your local repo, you can automatically run Black formatting using a pre-commit hook. 
The required configuration is in the file `.pre-commit-config.yaml`. 
You will need Python packages `black` and `pre-commit` install for this.

To install the pre-commit hook, run the following command inside your repo
```shell
$ pre-commit install
```

After having installed the pre-commit hook, a commit that is not formatted correctly will be aborted, 
and the offending code will automatically be reformatted. 
Review the formatting changes, stage them and re-run the commit.
