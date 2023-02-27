# FormRecognizer_OpenAI
This repo is a simple example how to sticht together two of Microsoft cognitive services - Form recotnizer and Azure Open AI.

It doesn't include any UI for now.

For it to work you will need several resources and preparartion:


1. Blob storage with some data to extract - we used scanned documetns with med prescriptiosn
2. Form recognizer and transaltor resources 
3. OpenAI resource and deployments of relevant models

Then:

1. Upload the data to the storage, note the storage name, container, endpoint and key
2. Note key and endpoint to other services in Azure
3. clone this repo 
4. fill the .env file with data from your resources
5. create virtual environment for the project and install requirements:
  ```
  python -m venv .venv
  pip install  -r requirements.txt
  ```

enjoy
