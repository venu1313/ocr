from __future__ import print_function
import fnmatch
import io
import os
import re
import httplib2
from googleapiclient import discovery
from apiclient.http import MediaFileUpload, MediaIoBaseDownload
from oauth2client import file, client, tools

SCOPES = ("https://www.googleapis.com/auth/drive")

# Authentication
store = file.Storage('token.json')
creds = store.get()
if not creds or creds.invalid:
    flow = client.flow_from_clientsecrets('credentials.json', SCOPES)
    creds = tools.run_flow(flow, store)

http = creds.authorize(httplib2.Http())
service = discovery.build("drive", "v3", http=http)


def get_file_names():
    # Create a dictionary of supported file types
    #  file_names = {filetype: list of files of this filetype}
    file_names = {"pdf": [], "jpg": [], "png": [], "gif":[], "bmp":[], "doc":[]}

    for x in os.listdir('.'):
        # os.listdir('.') returns all the files in the current folder
        for file_type in file_names.keys():
            if fnmatch.fnmatch(x, "*." + file_type):
                # If the file is of the file_type append it to the
                # corresponding list in the file_names dictionary
                file_names[file_type].append(x.replace("." + file_type,""))
    return file_names

# print a the file lists by type
files = get_file_names()
for type in files:
    print(type)
    for file in files[type]:
        print("\t"+ file)


def ocr(input, input_filetype, output):
    # get the mimetype based on the file extension
    mime_types = {"pdf": 'application/pdf', "jpg": 'image/jpeg', "png": 'image/png',
                 "gif": 'image/gif', "bmp": 'image/bmp', "doc": 'application/msword'}
    input_mime_type = mime_types[input_filetype]

    file_metadata = {'name': input, 'mimeType': 'application/vnd.google-apps.spreadsheet'}
    # Upload the file to Google Drive
    media = MediaFileUpload(input, mimetype=input_mime_type, resumable=True)
    file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    # Print the file id
    print('File ID: %s' % file.get('id'))
    # Export the file to txt and download it
    request = service.files().export_media(fileId=file.get('id'), mimeType="text/plain")
    dl = MediaIoBaseDownload(io.FileIO(output, "wb"), request)
    is_complete = False
    while not is_complete:
        status, is_complete = dl.next_chunk()
    # Delete the uploaded file
    service.files().delete(fileId=file["id"]).execute()
    print("Output saved to " + output + ".")
    f = open(output, 'r')
    contents = f.read()
    contents = contents.replace('\n', ' ').replace('\r', '')
    contents = contents.replace('  ', ' ').replace(' ', '')
    unwanted = [':',',']
    for i in unwanted :
        contents = contents.replace(i, '')
    #print("the output of OCR : "+contents)
    vehicle_regex = re.compile(r'[A-Z]{2}[0-9]{2}[A-Z]{2}[0-9]{4}')
    vehicle_nos = vehicle_regex.search(contents)
    if vehicle_nos is not None:
        print(vehicle_nos)
    
# Search for the files
files = get_file_names()

for file_type in files.keys():
    # Convert files for every file type
    print("Converting: ", file_type)
    for file in files[file_type]:
        ocr(file + "." + file_type, file_type, file + "_" + file_type + ".txt")

