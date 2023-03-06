from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas
from datetime import datetime, timedelta
import os,json
from dotenv import load_dotenv
from utilities.azureblobstorage import get_all_files
#from utilities.utils import convert_file_and_add_embeddings,  add_embeddings
from utilities.utils import initialize
from utilities.utils import colorprint
from utilities.formrecognizer import analyze_read
#from urllib.request import urlopen
from urllib.parse import *
#import numpy as np
import tiktoken
from openai.embeddings_utils import get_embedding, cosine_similarity
import openai 
import time
import pandas as pd


load_dotenv()
account_name = os.environ['BLOB_ACCOUNT_NAME']
account_key = os.environ['BLOB_ACCOUNT_KEY']
connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
container_name = os.environ['BLOB_CONTAINER_NAME']
model = os.environ['OPENAI_QnA_MODEL'] #e.g. 'text-davinci-003' deployment
os.makedirs('data', mode = 0o777, exist_ok = True) 

def get_context(formUrl,file_name):
    file_name_root = os.path.splitext(file_name)[0] 
    context_file_name = os.path.join('data','context_'+file_name_root+'txt') 
    colorprint('ANALYZING FILE : '+ file_name)

    try: 
        with open(context_file_name) as f:
            context =f.read()
            colorprint(f"Found file {context_file_name} with extracted content for context. \nReading file, NOT sending document to Form Recognizer.",'87')
    except:
        colorprint('Sending the document to Form Recognizer to extract content')
        #file_sas = generate_blob_sas(account_name, container_name, file_name, account_key= account_key, permission='r', expiry=datetime.utcnow() + timedelta(hours=1))
        #formUrl=f"https://{account_name}.blob.core.windows.net/{container_name}/{quote(file_name)}?{file_sas}" 
        text = analyze_read(formUrl,verbose=True)
        context=''
        for k, t in enumerate(text):
            context = context+t # for future use in prompt
        with open(context_file_name, 'w') as f:
            f.write(context)  # text has to be string not a list
        colorprint(f"Writing context file {context_file_name}",'44')
    colorprint("QUERING OPENAI USING EXTRACTED TEXT AS CONTEXT:")
    return(context)

def get_openAI_response(context='lores ipsum',question=['tl;dr'],model='text-davinci-003',temperature=1,tokens_response=15,restart_sequence=15):
    question_text=[]
    response_text=[]
    instruction = question[0]
    colorprint(instruction,'20')
    for q in question[1:]:
        prompt = f"{context}{restart_sequence}{instruction}{''+q}"
        try:
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=tokens_response,
                top_p=0.5,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
        except:
            time.sleep(7)
            response = openai.Completion.create(
                engine=model,
                prompt=prompt,
                temperature=temperature,
                max_tokens=tokens_response,
                top_p=0.5,
                frequency_penalty=0,
                presence_penalty=0,
                stop=None
            )
        r=response['choices'][0]['text'].strip(' \n\:?')
        colorprint(q, '33', end=' ')
        colorprint(r,'22')
        response_text.append(r)
        question_text.append(q)
    return([question_text,response_text])


##############################################################################
with open('question.txt') as f:
    question = f.read().splitlines()
f.close()
colorprint('THE QUESTION: ' + str(question), '44')
colorprint('INITIALIZING OPENAI CONNECTION')
initialize()

df = pd.DataFrame(question[1:],columns =['Q'])

colorprint('DISCOVERING ALL FILES IN THE BLOB STORAGE:')
files_data = get_all_files()
files_data = list(map(lambda x: {'filename': x['filename']}, files_data))
for fd in files_data:
        print(fd['filename'])

file_name = files_data[1]['filename']
for file in files_data:
    file_name=file['filename']
    try:
        file_name_root = os.path.splitext(file_name)[0] 
        file_sas = generate_blob_sas(account_name, container_name, file_name, account_key= account_key, permission='r', expiry=datetime.utcnow() + timedelta(hours=1))
        formUrl=f"https://{account_name}.blob.core.windows.net/{container_name}/{quote(file_name)}?{file_sas}" 


        context = get_context(formUrl,file_name)
        openAIresponse = get_openAI_response(context,question,model=model,temperature =0.0, tokens_response=15,restart_sequence='\n\n')
        question_text = openAIresponse[0]
        response_text = openAIresponse[1]

        response_file_name =os.path.join('data','response_'+file_name_root+'txt')
        with open(response_file_name, 'w') as f2:
            f2.write(str(response_text))  
        df[file_name_root]=response_text
    except:
        colorprint("File couldn't be processed",'9')


df.to_csv(f"data/result.csv")
print(df)
