from fastapi import APIRouter, UploadFile, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid


import numpy as np
import json
from pydantic import BaseModel
from typing import List

from config import UPLOAD_FOLDER, BASE_DIR
from face_swap.face_swap import run_face_swap, get_images_from_group, crop_faces



router = APIRouter()



@router.post('/uploadnewfaces/{uid}/{group_id}')
def upload_new_faces( uid: str, group_id: str, file: UploadFile = None):
    if not file:
        raise HTTPException(status_code=400, detail="File not found")

    if not os.path.exists(os.path.join(UPLOAD_FOLDER, uid, 'new_faces')):
        os.mkdir(os.path.join(UPLOAD_FOLDER, uid, 'new_faces'))

    file_location = os.path.join(UPLOAD_FOLDER,uid,'new_faces',str(group_id)+'.jpg')
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
        
    return JSONResponse(content={"message": "File "+uid+" uploaded successfully!", 'uid':uid}, status_code=200)







class FaceSwapRequest(BaseModel):
    group_ids: List[int]

@router.post('/faceswap/{uid}')
def face_swap(uid: str, request: FaceSwapRequest): 
    group_ids = request.group_ids
    print("Received group_ids:", group_ids)
    
    with open(os.path.join(UPLOAD_FOLDER, uid,'all_info.json'), 'r') as file:
        loaded_dict = json.load(file)
    
    for group_id in group_ids:
        if int(group_id) >= int(loaded_dict['max_groups']):
            raise HTTPException(status_code=400, detail="Group ID not found")

    # Paths to the files
    embeddings_file = os.path.join(UPLOAD_FOLDER, uid, 'face_embeddings.npy')
    bboxes_file = os.path.join(UPLOAD_FOLDER, uid, 'face_bboxes.npy')
    kps_file = os.path.join(UPLOAD_FOLDER, uid, 'face_kps.npy')

    # Load the data from each file
    all_embeddings = np.load(embeddings_file)
    all_bboxes = np.load(bboxes_file)
    all_kps = np.load(kps_file)
    all_face_info = loaded_dict['all_face_info']

    result_file_path = os.path.join(UPLOAD_FOLDER, uid, 'result.mp4')
    input_file_path = os.path.join(UPLOAD_FOLDER, uid, 'input.mp4')

    run_face_swap(uid, all_face_info,group_ids, all_embeddings, all_bboxes, all_kps,input_file_path, result_file_path)
    






    return JSONResponse(content={"message": "Face swroutered successfully!", 'uid':uid}, status_code=200)




@router.post("/uploadvideo/")
async def upload_video(file: UploadFile = None):
    if not file:
        raise HTTPException(status_code=400, detail="File not found")
    uid = str(uuid.uuid4())
    if not os.path.exists(os.path.join(UPLOAD_FOLDER, uid)):
        os.mkdir(os.path.join(UPLOAD_FOLDER, uid))

    file_location = os.path.join(UPLOAD_FOLDER,uid, 'input.mp4')
    with open(file_location, "wb+") as file_object:
        file_object.write(file.file.read())
    crop_faces(file_location, uid)
    return JSONResponse(content={"message": "File "+uid+" uploaded successfully!", 'uid':uid}, status_code=200)




@router.get("/get_images/{uid}")
async def read_images(uid: str):
    images = get_images_from_group(uid)
    return images

@router.get("/images/{uid}/{cropped}/{group}/{filename}")
async def serve_image(uid: str, group: str, filename: str):
    image_path = os.path.join(BASE_DIR, uid, "cropped_faces", group, filename)
    if not os.path.isfile(image_path):
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(image_path)

@router.get("/download_result_video/{uid}")
async def download_video(uid: str):
    video_path = os.path.join(UPLOAD_FOLDER, uid, 'result.mp4')

    if not os.path.exists(video_path):
        raise HTTPException(status_code=400, detail="File not found")

    return FileResponse(video_path, media_type='video/mp4', filename=f"result_{uid}.mp4")


