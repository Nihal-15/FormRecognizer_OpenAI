
import os
from datetime import datetime, timedelta
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient, generate_blob_sas, generate_container_sas, ContentSettings

def get_all_files():
    # Get all files in the container from Azure Blob Storage
    account_name = os.environ['BLOB_ACCOUNT_NAME']
    account_key = os.environ['BLOB_ACCOUNT_KEY']
    connect_str = f"DefaultEndpointsProtocol=https;AccountName={account_name};AccountKey={account_key};EndpointSuffix=core.windows.net"
    container_name = os.environ['BLOB_CONTAINER_NAME']
    # Create the BlobServiceClient object
    blob_service_client = BlobServiceClient.from_connection_string(connect_str)
    # Get files in the container
    container_client = blob_service_client.get_container_client(container_name)
    blob_list = container_client.list_blobs(include='metadata')
    # sas = generate_blob_sas(account_name, container_name, blob.name,account_key=account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3))
    sas = generate_container_sas(account_name, container_name,account_key=account_key,  permission="r", expiry=datetime.utcnow() + timedelta(hours=3))
    files = []
    converted_files = {}
    for blob in blob_list:
        if not blob.name.startswith('converted/'):
            files.append({
                "filename" : blob.name,
                "converted": blob.metadata.get('converted', 'false') == 'true' if blob.metadata else False,
                "embeddings_added": blob.metadata.get('embeddings_added', 'false') == 'true' if blob.metadata else False,
                "fullpath": f"https://{account_name}.blob.core.windows.net/{container_name}/{blob.name}?{sas}",
                "converted_path": ""
                })
        else:
            converted_files[blob.name] = f"https://{account_name}.blob.core.windows.net/{container_name}/{blob.name}?{sas}"

    for file in files:
        converted_filename = f"converted/{file['filename']}.zip"
        if converted_filename in converted_files:
            file['converted'] = True
            file['converted_path'] = converted_files[converted_filename]
    
    return files