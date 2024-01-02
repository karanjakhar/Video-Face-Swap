import os


UPLOAD_FOLDER = "./uploaded_videos"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


BASE_DIR = os.path.abspath(UPLOAD_FOLDER)


