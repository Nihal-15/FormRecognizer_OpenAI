from azure.core.credentials import AzureKeyCredential
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.storage.blob import BlobServiceClient, generate_blob_sas
from datetime import datetime, timedelta
import os,json
from dotenv import load_dotenv
from utilities.azureblobstorage import get_all_files
#from utilities.utils import convert_file_and_add_embeddings,  add_embeddings
from utilities.utils import initialize
from utilities.utils import chunk_and_embed
from utilities.utils import colorprint
#from urllib.request import urlopen
from urllib.parse import *
#import numpy as np
import tiktoken
from openai.embeddings_utils import get_embedding, cosine_similarity
import openai 

load_dotenv()
os.environ['BLOB_ACCOUNT_NAME']
PAGES_PER_EMBEDDINGS = 2
SECTION_TO_EXCLUDE = []


account_name = os.environ['BLOB_ACCOUNT_NAME']
account_key = os.environ['BLOB_ACCOUNT_KEY']
connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
container_name = os.environ['BLOB_CONTAINER_NAME']

os.makedirs('data', mode = 0o777, exist_ok = True) 

files_data = get_all_files()
files_data = list(map(lambda x: {'filename': x['filename']}, files_data))

colorprint('\nALL FILES IN THE BLOB STORAGE:\n')

for fd in files_data:
        #msg = json.dumps(fd).encode('utf-8')
        #print(json.loads(msg.decode('utf-8'))['filename'])
        print(fd['filename'])


file_name = files_data[1]['filename']
colorprint('\nAnalyzing file : '+ file_name)       

file_sas = generate_blob_sas(account_name, container_name, file_name, account_key= account_key, permission='r', expiry=datetime.utcnow() + timedelta(hours=1))
formUrl=f"https://{account_name}.blob.core.windows.net/{container_name}/{quote(file_name)}?{file_sas}" 

document_analysis_client = DocumentAnalysisClient(
        endpoint=os.environ['FORM_RECOGNIZER_ENDPOINT'], credential=AzureKeyCredential(os.environ['FORM_RECOGNIZER_KEY'])
    )
poller = document_analysis_client.begin_analyze_document_from_url(
            "prebuilt-layout", formUrl)
layout = poller.result()

print('Extracted dictionary with keys: ', end='')
txt_layout=str( json.dumps(layout.to_dict()).encode('utf-8'))
print(layout.to_dict().keys())
with open('data\\'+os.path.splitext(file_name)[0]+'_layout.txt', 'w') as f:
   f.write(txt_layout)
colorprint('Writing file with raw results: data\\'+os.path.splitext(file_name)[0]+'_layout.txt','77')

colorprint('\nEXTRACTING:')

results = []
page_result = ''
print('- paragraphs',end ='')
for p in layout.paragraphs:
        print('.',end='')
        page_number = p.bounding_regions[0].page_number
        output_file_id = int((page_number - 1 ) / PAGES_PER_EMBEDDINGS)

        if len(results) < output_file_id + 1:
            results.append('')

        if p.role not in SECTION_TO_EXCLUDE:
            results[output_file_id] += f"{p.content}\n"
print('\n- tables',end='')
for t in layout.tables:
        print('.',end='')
        page_number = t.bounding_regions[0].page_number
        output_file_id = int((page_number - 1 ) / PAGES_PER_EMBEDDINGS)
        
        if len(results) < output_file_id + 1:
            results.append('')
        previous_cell_row=0
        rowcontent='| '
        tablecontent = ''
        for c in t.cells:
            if c.row_index == previous_cell_row:
                rowcontent +=  c.content + " | "
            else:
                tablecontent += rowcontent + "\n"
                rowcontent='|'
                rowcontent += c.content + " | "
                previous_cell_row += 1
        results[output_file_id] += f"{tablecontent}|"

colorprint('\nFORM RECOGNIZER CLEANED RESULTS:')
print(results[0:20][0:100])
text  = results
with open('data\\'+os.path.splitext(file_name)[0]+'_layout_formatted.txt', 'w') as f:
   f.write(str(text))
colorprint('Writing file with formatted formrecognizer results: '+'data\\'+os.path.splitext(file_name)[0]+'_layout_formatted.txt','77')


colorprint('CALCULATING EMBEDDINGS')

initialize()

all_embeddings=[] 
all_text=''
for k, t in enumerate(text):
    print("*****")
    print('vector nr. ' +str(k))
    #print(t)
    all_text= all_text+t # for future use in prompt
    #add_embeddings(t, f"{file_name}_chunk_{k}", os.getenv('OPENAI_EMBEDDINGS_ENGINE_DOC', 'text-embedding-ada-002'))
    embeddings = chunk_and_embed(t, file_name, engine="text-embedding-ada-002")
    all_embeddings.append({f"{file_name}_chunk_{k}":str(embeddings)})
    #those would be normally stored in redisd
   

resultfile='data\\'+os.path.splitext(file_name)[0]+'_embedded.txt'
with open(resultfile, 'w') as f2:
   f2.write(str(all_embeddings))
colorprint('Writing file with embeddings results: '+os.path.splitext(file_name)[0]+'_embedded.txt','77')
print('')
print('those results shold be stored in redis for future search')

colorprint("QUERING OPENAI USING EXTRACTED TEXT:")
question ='What is Hospital Name'
explicit_prompt = all_text
restart_sequence = "\n\n"
prompt = f"{explicit_prompt}{restart_sequence}{question}"

#with open('lastprompt.txt','w')as f3:
#    f3.write(prompt)

model = os.environ['OPENAI_QnA_MODEL'] #e.g. 'text-davinci-003' deployment
temperature =0.0
tokens_response = 100

#df=initialize(engine='davinci')


colorprint('\nGETTING OPENAI API RESPONSE') 


response = openai.Completion.create(
        engine=model,
        prompt=prompt,
        temperature=temperature,
        max_tokens=tokens_response,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
        stop=None
    )


#print(response)
contextcolor='61'
chatcolor='30'
colorprint(explicit_prompt,contextcolor)
colorprint(question,chatcolor)
colorprint(response['choices'][0]['text'],chatcolor)



