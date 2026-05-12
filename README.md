# OpenAEV Payloads Repository

## Purpose

This repository hosts default payloads collected by the OpenAEV datasets collector. 

## How to contribute to new payloads

### 1. Create your payload within OpenAEV

The first step is to create the payload in an OpenAEV Platform. Be sure to fill the description, associate it with relevant MITRE ATT&CK TTPs and put any relevant tagging.

![Create Payload](./.github/img/create-payload.png "Create Payload")

### 2. Test your payload

Please ensure that your payload is working in the supported environments by testing it using atomic testing or a more complex scenario if necessary.

### 3. Export your payload

Once tested, you can export your payload directly from the platform. 

![Export Payload](./.github/img/export-payload.png "Export Payload")

### 4. Extract the payload content within the relevant directory

The downloaded ZIP file contain another ZIP file named with the payload name. This ZIP file should be extracted as a directory in the relevant folder of this repository.

![Export Overview](./.github/img/export-overview.png "Export Overview")

In the example above, just take `Activate Guest Account.zip` and extract it to create a folder `Activate Guest Account` within this repository.

![Extract Payload](./.github/img/extract-payload.png "Extract Payload")

### 5. Verify directory structure and generate manifest

In a payload directory, you should only have the `payload.json` file and an optional `attachments.zip` containing a potential malicious file (encrypted archive). *Do not unzip this file, let it as it is*.

![File Structure](./.github/img/file-structure.png "File Structure")

Before opening your pull request, the JSON file(s) must be passed through our convenience script. You'll first need to install the requirements `python -m pip install -r scripts/requirements.txt`, then run the Python script `scripts/generate_manifest.py` (minimum Python version: 3.12).

```bash
$ python3 -m pip install -r scripts/requirements.txt
$ python3 scripts/generate_manifest.py
```

## How to review payloads

### 1. Create a zip from the payload folder

You can just select the payload folder and create a ZIP file.

![Create Archive](./.github/img/create-archive.png "Create Archive")

### 2. Import the payload in OpenAEV

Then, just import the payload in OpenAEV.

![Import Payload](./.github/img/import-payload.png "Import Payload")

### 3. Test the payload

Then, test the payload and validate it works before marging the pull request.

## About

OpenAEV is a product designed and developed by the company [Filigran](https://filigran.io).

<a href="https://filigran.io" alt="Filigran"><img src="https://github.com/OpenAEV-Platform/openaev/raw/master/.github/img/logo_filigran.png" width="300" /></a>
