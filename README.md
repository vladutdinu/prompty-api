<div align="center">

<a href="https://promptyapi.com">
    <img src="images/logo.png" width="180px" alt="logo">
</a>

**An Easy-to-use REST API to protect your LLM-based applications.**

![](https://img.shields.io/badge/version-v0.1-blue)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
![Static Badge](https://img.shields.io/badge/last_commit-May-blue)
![](https://img.shields.io/badge/PRs-Welcome-red)

---

<p align="center">
  <a href="#requirements">Installation</a> •
  <a href="#use-prompty">QuickStart</a> •
  <a href="https://api.promptyapi.com/docs">API Documentation</a> •
  <a href="#demo">Demo</a> •
  <a href="#contributors">Contributors</a> •
</p>
</div>

## 🔔News

- **2024-04-30 First public release!!! 🙌😎🎉

## Requirements

#### 🔧Pip Installation

**Note: Please use Python 3.11 for EasyEdit**
To get started, simply install conda and run:

```shell
git clone https://github.com/vladutdinu/prompty-api.git
cd prompty-api
conda create -n EasyEdit python=3.11.9
pip install -r requirements.txt
```

#### 🐳Docker Installation

You can download Docker from [this link](https://docs.docker.com/get-docker/).

To create the Docker image, run the following commands in the root folder of this project:

```shell
git clone https://github.com/vladutdinu/prompty-api.git
cd prompty-api
docker build -t prompty-api:v1 .
```

Before create a container fill in the `.env_example` file.

To create the container run the following command:
```bash
docker run -it -d --env_file .env_example -p 'external_port:port_defined_in_env' -v $PWD/count/count_file.json:path_defined_in_env_for_COUNT_FILE --name prompty-api prompty-api:v1
```

Example:
```bash
docker run -it -d --env_file .env_example -p '8000:8000' -v $PWD/count/count_file.json:/count/count_file.json --name prompty-api prompty-api:v1
```

## Use Prompty

<b>This can be used to determine if a user has sent a malicious prompt to your LLM-based application<b> 

### Use Prompty to check for prompt injection

#### Using Python 🐍

Create a `prompty.py` Python script with the following content:

```python
## We need to import requests and json
import requests
import json
url = 'https://api.promptyapi.com/check_prompt' #http://localhost:port if you use Docker
myobj = {'prompt': 'your prompt with more than 3 words'}

result = requests.post(url, json = myobj)

print(json.loads(result.text))
```

Then run the script:
```bash
python prompty.py
```

#### Using Javascript 🟨

Create a `prompty.js` Javascript file with the following content:

```javascript
const fetch = require('node-fetch');

async function checkPrompt() {
    const url = 'https://api.promptyapi.com/check_prompt'; //http://localhost:port if you use Docker
    const myobj = { prompt: 'your prompt with more than 3 words' };

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: JSON.stringify(myobj),
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

checkPrompt();
```

Then run the script:
```bash
node prompty.js
```
![Prompty-API-Clean-Prompt](/images/check_prompt.PNG)

<b>This can be used to determine if a user has sent a malicious prompt to your LLM-based application, using NLP Models<b> 

```
The NLP Model will need to be set in the environment variables
```

### Use Prompty to check for prompt injection using NLP Models

#### Using Python 🐍

Create a `prompty.py` Python script with the following content:

```python
## We need to import requests and json
import requests
import json
url = 'https://api.promptyapi.com/check_prompt_with_nlp' #http://localhost:port if you use Docker
myobj = {'prompt': 'your prompt with more than 3 words'}

result = requests.post(url, json = myobj)

print(json.loads(result.text))
```

Then run the script:
```bash
python prompty.py
```

#### Using Javascript 🟨

Create a `prompty.js` Javascript file with the following content:

```javascript
const fetch = require('node-fetch');

async function checkPrompt() {
    const url = 'https://api.promptyapi.com/check_prompt_with_nlp'; //http://localhost:port if you use Docker
    const myobj = { prompt: 'your prompt with more than 3 words' };

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: JSON.stringify(myobj),
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

checkPrompt();
```

Then run the script:
```bash
node prompty.js
```
![Prompty-API-Check-Prompt-NLP](/images/check_prompt_nlp.PNG)


### Use Prompty to clean a prompt

<b>This can be used to clean a prompt from possible prompt-injection tokens<b> 

#### Using Python 🐍

Create a `prompty.py` Python script with the following content:

```python
## We need to import requests and json
import requests
import json
url = 'https://api.promptyapi.com/clean_prompt' #http://localhost:port if you use Docker
myobj = {'prompt': 'your infected prompt with more than 3 words'}

result = requests.post(url, json = myobj)

print(json.loads(result.text))
```

Then run the script:
```bash
python prompty.py
```

#### Using Javascript 🟨

Create a `prompty.js` Javascript file with the following content:

```javascript
const fetch = require('node-fetch');

async function checkPrompt() {
    const url = 'https://api.promptyapi.com/clean_prompt'; //http://localhost:port if you use Docker
    const myobj = { prompt: 'your infected prompt with more than 3 words' };

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: JSON.stringify(myobj),
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

checkPrompt();
```

Then run the script:
```bash
node prompty.js
```

![Prompty-API-Clean-Prompt](/images/clean_prompt.PNG)

### Use Prompty to check for similar pre-defined actions

<b>This can be used to determine if the user has requested an action similar to the actions you have defined in the database<b> 

#### Using Python 🐍

Create a `prompty.py` Python script with the following content:

```python
## We need to import requests and json
import requests
import json
url = 'https://api.promptyapi.com/check_prompt_from_database' #http://localhost:port if you use Docker
myobj = {'prompt': 'your prompt with more than 3 words'}

result = requests.post(url, json = myobj)

print(json.loads(result.text))
```

Then run the script:
```bash
python prompty.py
```

#### Using Javascript 🟨

Create a `prompty.js` Javascript file with the following content:

```javascript
const fetch = require('node-fetch');

async function checkPrompt() {
    const url = 'https://api.promptyapi.com/check_prompt_from_database'; //http://localhost:port if you use Docker
    const myobj = { prompt: 'your prompt with more than 3 words' };

    try {
        const response = await fetch(url, {
            method: 'POST',
            body: JSON.stringify(myobj),
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();
        console.log(data);
    } catch (error) {
        console.error('Error:', error.message);
    }
}

checkPrompt();
```

Then run the script:
```bash
node prompty.js
```
<!-- ![Prompty-API-Clean-Prompt](/images/check_prompt.PNG) -->

## Demo

#### Video
![Prompty-API-Demo](/images/demo.gif)

#### Injected? Do not forget to like the result if its as you expected
![Prompty-API-Demo](/images/like.gif)

## Use-cases

### We call it `the bread slice 🍞🔪` method do protect your LLM-based application 

![Usecase-1](/images/usecase-1.png)

### We call it `the half-sandwich 🥪🔪` method do protect your LLM-based application 

![Usecase-1](/images/usecase-2.png)

### We call it `the sandwich 🥪` method do protect your LLM-based application 

![Usecase-1](/images/usecase-3.png)


## 🎉Contributors

- [ConstantinAndrei](https://github.com/andrei-ctn)
- [BogdanMusat](https://github.com/musateduardbogdan)
- [MihneaHututui](https://github.com/mihneahututui)