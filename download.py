from __future__ import print_function
from typing import Optional
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


def downloadfiles(dowid, dfilespath, folder=None):
    request = service.files().get_media(fileId=dowid)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while done is False:
        status, done = downloader.next_chunk()
        print("Download %d%%." % int(status.progress() * 100))
    if folder:
        with io.open(folder + "/" + dfilespath, "wb") as f:
            fh.seek(0)
            f.write(fh.read())
    else:
        with io.open(dfilespath, "wb") as f:
            fh.seek(0)
            f.write(fh.read())


def listfolders(filid, des):
    page_token = None
    while True:
        results = (
            service.files()
            .list(
                pageSize=1000,
                q="'" + filid + "'" + " in parents",
                fields="nextPageToken, files(id, name, mimeType)",
            )
            .execute()
        )
        page_token = results.get("nextPageToken", None)
        if page_token is None:
            folder = results.get("files", [])
            for item in folder:
                if str(item["mimeType"]) == str("application/vnd.google-apps.folder"):
                    if not os.path.isdir(des + "/" + item["name"]):
                        os.mkdir(path=des + "/" + item["name"])
                    listfolders(item["id"], des + "/" + item["name"])
                else:
                    FolderDownload(item["id"], item["name"], item['mimeType'], des+ "/" + item["name"])
                    print(item["name"])
        break
    return folder

def FolderDownload(file_id, file_name, mimeType):
    folder = service.files().get(fileId=file_id).execute()
    folder_name = folder.get("name")
    page_token = None
    while True:
        results = (
            service.files()
            .list(
                q=f"'{file_id}' in parents",
                spaces="drive",
                fields="nextPageToken, files(id, name, mimeType)",
            )
            .execute()
        )
        page_token = results.get("nextPageToken", None)
        if page_token is None:
            items = results.get("files", [])
            print(f"Start downloading folder '{folder_name}'.")
            for item in items:
                if item["mimeType"] == "application/vnd.google-apps.folder":
                    if not os.path.isdir(folder_name):
                        os.mkdir(folder_name)
                    bfolderpath = os.path.join(os.getcwd(), folder_name)
                    if not os.path.isdir(
                        os.path.join(bfolderpath, item["name"])
                    ):
                        os.mkdir(os.path.join(bfolderpath, item["name"]))

                    folderpath = os.path.join(bfolderpath, item["name"])
                    listfolders(item["id"], folderpath)
                else:
                    if not os.path.isdir(folder_name):
                        os.mkdir(folder_name)
                    bfolderpath = os.path.join(os.getcwd(), folder_name)

                    filepath = os.path.join(bfolderpath, item["name"])
                    print('filepath = ',filepath)
                    FileDownload(item["id"], item['name'], item['mimeType'],filepath)
                    print(item["name"])
        break

def FileDownload(file_id, file_name,mimeType, location:Optional[str] = ''):
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
            

            # request = service.files().get_media(fileId=file_id)

        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request, chunksize=204800)
        done = False

        try:
            while not done:
                status, done = downloader.next_chunk()
            fh.seek(0)
            if location == '':
                with open('file/'+file_name, 'wb') as f:
                    shutil.copyfileobj(fh, f)
            else:
                with open(location, 'wb') as f:
                    shutil.copyfileobj(fh, f)
            print("File Downloaded")
            return True
        except:
            traceback.print_exc()
            print("Something went wrong.")
            return False

def FileUpload(filepath, folder_id:Optional[str] = ''):
        
        # Extract the file name out of the file path
    name = filepath.split('/')[-1]
        
    # Find the MimeType of the file
    mimetype = MimeTypes().guess_type(name)[0]
        
    # create file metadata
    file_metadata = {'name': name}
    if folder_id != '':
        file_metadata = {'name': name,
        'parents': [folder_id]}
        

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

def getListOfFiles(dirName):
    # create a list of file and sub directories 
    # names in the given directory 
    listOfFile = os.listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = os.path.join(dirName, entry)
        # If entry is a directory then get the list of files in this directory 
        if os.path.isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)
                
    return allFiles 

def CreateFolder(folder_name):
    try:
        # create drive api client
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {
            'name': folder_name,
            'mimeType': 'application/vnd.google-apps.folder'
        }

        # pylint: disable=maybe-no-member
        file = service.files().create(body=file_metadata, fields='id'
                                      ).execute()
        print(F'Folder ID: "{file.get("id")}".')
        return file.get('id')

    except HttpError as error:
        print(F'An error occurred: {error}')
        return None

if __name__ == '__main__':
    # data = get_list()
    # for detail in data:
    #     if 'application/vnd.google-apps.folder' == detail['mimeType']:
    #         FolderDownload(
    #             detail['id'],detail['name'],detail['mimeType']
    #         )
    #     else:
    #         FileDownload(detail['id'],detail['name'],detail['mimeType'])
    #     print(detail)
        # exit()
    # dir_list = os.listdir('/Users/alienpdev/Workspace/Research/DriveAPI/file')
    # for path in dir_list:
    #     print(path)
    #     FileUpload('/Users/alienpdev/Workspace/Research/DriveAPI/file/'+path)
    folder_ids = {'testFolder': '1cpE6IWxqarUx7VVdld0s1azzZCHt_0It', 'Arsitektur dan Organisasi Komputer': '160xCjy8M8Rgit1Iy3xRh4O_YpBhiRKY9', 'Communicative Eng.': '13pF3s-3i2e_yUrc1z9K4KAxYLyr8wCed', 'file': '1M4EgNiTR3VyLHgesELx5bhLf4G_y1vrw', 'Matematika Diskrit': '1k2zFgANBQJkxA3jxSVAi97yRCTybhHgf', 'Struktur Data Teori + Praktek': '1lhP38v0yfoP-onlKrY9NCXjlGdsc_bIu'}
    # names = '/Users/alienpdev/Workspace/Research/DriveAPI'
    # for name in os.listdir(names):
    #     if os.path.isdir(name):
    #         if not 'venv' in name and not '.git' in name:
    #             folder_id = CreateFolder(name)
    #             folder_ids[name] = folder_id
    #             print(name)
    # print(folder_ids)
# 
    # exit()
    listOfFiles = getListOfFiles('/Users/alienpdev/Workspace/Research/DriveAPI')

    listOfFiles = list()
    for (dirpath, dirnames, filenames) in os.walk('/Users/alienpdev/Workspace/Research/DriveAPI'):
        for file in filenames:
            if not 'venv' in dirpath and not '.git' in dirpath:
                listOfFiles.append(os.path.join(dirpath, file))
    for elem in listOfFiles:
        folders = str(elem).split('/')[6]
        if folders in folder_ids:
            FileUpload(elem, folder_ids[folders])
        else:
            FileUpload(elem)