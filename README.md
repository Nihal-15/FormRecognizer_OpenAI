# FormRecognizer_OpenAI
This repo is a simple example how to stitch together two of Microsoft cognitive services - Formrecognizer and Azure Open AI. The assumption is that when asking a question to OpenAI you want to have the input from ONE document incuded as context and that it doesn't exclude prompt limit. 
If you would like to add a larger knowledge base to your solution you will need to embedd it and add it and we recommend using approach in this repository:
https://github.com/ruoccofabrizio/azure-open-ai-embeddings-qna/

Our document is a scan of a document with multiple tables so is first 'cracked' by form recognizer (layout model) and then the result is formatted, cleaned and passed to OpenAI as prompt context.  

There is no UI for now. 

For it to work you will need several resources and preparation:


1. Blob storage with some data to extract - we used scanned documents with medicine prescriptions
2. Form recognizer resource
3. OpenAI resource and deployment of relevant models

Then:

1. Upload the data to the storage, note the storage name, container, endpoint and key
2. Note key and endpoint of the other services in Azure
3. Clone this repo 
4. Fill the .env file with data from your resources in the Azure portal
5. Create virtual environment for the project and install requirements:
  ```
  python -m venv .venv
  pip install  -r requirements.txt
  Run the QnA_automated.py to automate the process and extract information from all the files in the blob storage
  ```

enjoy
