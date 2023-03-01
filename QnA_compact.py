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

load_dotenv()
os.environ['BLOB_ACCOUNT_NAME']
PAGES_PER_EMBEDDINGS = 2
SECTION_TO_EXCLUDE = []


account_name = os.environ['BLOB_ACCOUNT_NAME']
account_key = os.environ['BLOB_ACCOUNT_KEY']
connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
container_name = os.environ['BLOB_CONTAINER_NAME']

model = os.environ['OPENAI_QnA_MODEL'] #e.g. 'text-davinci-003' deployment
temperature =0.0
tokens_response = 15
restart_sequence = "\n\n"
question ='What is Hospital Name'
with open('question.txt') as f:
    question = f.read().splitlines()
f.close()

colorprint('THE QUESTION: ' + str(question), '44')

colorprint('INITIALIZING OPENAI CONNECTION')
initialize()

os.makedirs('data', mode = 0o777, exist_ok = True) 

files_data = get_all_files()
files_data = list(map(lambda x: {'filename': x['filename']}, files_data))

colorprint('DISCOVERING ALL FILES IN THE BLOB STORAGE:')

for fd in files_data:
        print(fd['filename'])


file_name = files_data[10]['filename']
file_name_root = os.path.splitext(file_name)[0]
colorprint('ANALYZING FILE : '+ file_name) 
try: 
    with open(os.path.join('data',file_name_root+'_fr_context.txt')) as f:
        context =f.read()
        colorprint(f"Found file {file_name_root}_fr_context.txt with extracted content for context. \nReading file, NOT sending document to Form Recognizer.",'44')
except:
    colorprint('Sending the document to Form Recognizer to extract content')
    file_sas = generate_blob_sas(account_name, container_name, file_name, account_key= account_key, permission='r', expiry=datetime.utcnow() + timedelta(hours=1))
    formUrl=f"https://{account_name}.blob.core.windows.net/{container_name}/{quote(file_name)}?{file_sas}" 
    text = analyze_read(formUrl,verbose=True)
    context=''
    for k, t in enumerate(text):
        context = context+t # for future use in prompt
    with open(os.path.join('data',file_name_root+'_fr_context.txt'), 'w') as f:
        f.write(context)  # text has to be string not a list
    colorprint(f"Writing file {file_name_root}_fr_context.txt",'44')
colorprint("QUERING OPENAI USING EXTRACTED TEXT AS CONTEXT:")
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
            top_p=1,
            frequency_penalty=1,
            presence_penalty=1,
            stop=None
        )
    except:
        time.sleep(5)
        response = openai.Completion.create(
            engine=model,
            prompt=prompt,
            temperature=temperature,
            max_tokens=tokens_response,
            top_p=1,
            frequency_penalty=1,
            presence_penalty=1,
            stop=None
        )
    r=response['choices'][0]['text'].strip(' \n\:?')
    colorprint(q, '33', end=' ')
    colorprint(r,'22')
    #print(q+': '+ r)
    response_text.append(r)
    question_text.append(q)



context_file_name = os.path.join('data','context'+os.path.splitext(file_name)[0]+'txt')
with open(context_file_name, 'w') as f1:
   f1.write(str(context))
response_file_name =os.path.join('data','response'+os.path.splitext(file_name)[0]+'txt')
with open(response_file_name, 'w') as f2:
   f2.write(str(response_text))  

import pandas as pd

df = pd.DataFrame(question_text,columns =['Q'])
df['A']=response_text

df.to_csv(f"data/{file_name_root}.csv")

print(df)