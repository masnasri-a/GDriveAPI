from __future__ import print_function

import io
from mimetypes import MimeTypes
import shutil
import traceback
import google.auth
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseDownload, MediaFileUpload

import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

creds = None

SCOPES = ['https://www.googleapis.com/auth/drive']

if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)

service = build('drive', 'v3', credentials=creds)


def get_list():
  

    try:
        results = service.files().list(
            pageSize=100, fields="files(id, name, mimeType)").execute()
        items = results.get('files', [])
        return items

    except HttpError as error:
        print(F'An error occurred: {error}')
        file = None


def FileDownload(file_id, file_name,mimeType):
        print(file_id)
        print(file_name)
        print(mimeType)
        request = service.files().get_media(fileId=file_id)

        if 'vnd.google-apps.' in mimeType:
            if mimeType == 'application/vnd.google-apps.spreadsheet':
                mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'  
                file_name = file_name +'.xlsx'
            if mimeType == 'application/vnd.google-apps.document':
                mimeType = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                file_name = file_name +'.docx'
            if mimeType == 'application/vnd.google-apps.presentation':
                mimeType = 'application/vnd.openxmlformats-officedocument.presentationml.presentation'
                file_name = file_name +'.pptx'

            request = service.files().export_media(fileId=file_id, mimeType=mimeType)
        if 'application/vnd.google-apps.folder' == mimeType:
            request = service.files().get_media(fileId=file_id)


        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            while not done:
                status, done = downloader.next_chunk()
  
            fh.seek(0)
              
            with open('file/'+file_name, 'wb') as f:
                shutil.copyfileobj(fh, f)
  
            print("File Downloaded")
            return True
        except:
            traceback.print_exc()
            print("Something went wrong.")
            return False

def FileUpload(filepath):
        
        # Extract the file name out of the file path
    name = filepath.split('/')[-1]
        
    # Find the MimeType of the file
    mimetype = MimeTypes().guess_type(name)[0]
        
    # create file metadata
    file_metadata = {'name': name}

    try:
        media = MediaFileUpload(filepath, mimetype=mimetype)
            
        # Create a new file in the Drive storage
        file = service.files().create(
            body=file_metadata, media_body=media, fields='id').execute()
        print("File Uploaded.")
        
    except:
        traceback.print_exc()
        # Raise UploadError if file is not uploaded.
        print("Can't Upload File.")

if __name__ == '__main__':
    # data = get_list()
    # for detail in data:
        # FileDownload(detail['id'],detail['name'],detail['mimeType'])
        # print(detail)
        # exit()
    dir_list = os.listdir('/Users/alienpdev/Workspace/Research/DriveAPI/file')
    for path in dir_list:
        FileUpload('/Users/alienpdev/Workspace/Research/DriveAPI/file/'+path)