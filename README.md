# Search YouTube Creators

## Overview

This Application allows you to search for YouTube Creaters based on the Query and Type.

It also provides a download process for results with email which is existed in description as an Excel file.

You need to have a [YouTube Data API](https://developers.google.com/youtube/v3) key to use this application.

Get your API key from the [Google Cloud Console](https://console.cloud.google.com/apis/credentials).


## Usage

This application is running on [pipenv](https://github.com/pypa/pipenv) with Python 3.12 and above.


### MacOS/Linux

```zsh
$ pip install pipenv
$ pipenv install
$ pipenv run streamlit run server.py
```

To run on background

```zsh
$ nohup pipenv run streamlit run server.py > server.log 2>&1 &
```