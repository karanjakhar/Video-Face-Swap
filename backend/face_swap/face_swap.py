
import cv2
import onnxruntime
import numpy as np
import os
import json

from face_swap.utils.common import Face
from face_swap.retinaface import RetinaFace 
from face_swap.arcface_onnx import ArcFaceONNX
from face_swap.inswapper import INSwapper
from face_swap.face_enhancer import enhance_face
from config import UPLOAD_FOLDER, BASE_DIR
from config import RETINAFACE_MODEL_PATH, ARCFACE_MODEL_PATH, FACE_SWAPPER_MODEL_PATH, FACE_ENHANCER_MODEL_PATH
from config import PROVIDERS


retinaface_det_model = RetinaFace(RETINAFACE_MODEL_PATH, providers=PROVIDERS)
retinaface_det_model.prepare(ctx_id=1, input_size=(640, 640), det_thresh=0.5)
arcface_emedding_model = ArcFaceONNX(ARCFACE_MODEL_PATH, providers=PROVIDERS)
face_swapper_model = INSwapper(FACE_SWAPPER_MODEL_PATH, providers=PROVIDERS)
face_enhancer_model = onnxruntime.InferenceSession(FACE_ENHANCER_MODEL_PATH,providers=PROVIDERS)




def crop_faces(video_path: str, uid: str):
    cap = cv2.VideoCapture(video_path)
    face_distance = 1.5
    embeddings = []
    frame_number = -1
    all_bboxes = []
    all_kps = []
    all_face_info = {}
    filename_counter = 1
    directory = os.path.join(UPLOAD_FOLDER, uid,"cropped_faces")
    if not os.path.exists(directory):
        os.mkdir(directory)
    
    
    all_faces = {0:[]} # key id and value is Faces
    unique_id = 0

    while True:
        # Read a frame from the video
        ret, frame = cap.read()
        frame_number += 1

        # Break the loop if we are at the end of the video
        if not ret:
            break

       
        
        bboxes, kpss = retinaface_det_model.detect(frame,max_num=0,metric='default')

        
        print(bboxes.shape)

        for i in range(bboxes.shape[0]):
        # if bboxes.shape[0] > 0:
            similarity_ids = {}
            bbox = bboxes[i, 0:4]
            det_score = bboxes[i, 4]
            x1,y1,x2,y2 = bbox.astype(int)
            if (x2 - x1) > 80 and (y2 - y1) > 80:
                
                kps = None
                if kpss is not None:
                    kps = kpss[i]
                face = Face(bbox=bbox, kps=kps, det_score=det_score)
                face['frame_number'] = frame_number
                face['embedding'] = arcface_emedding_model.get(frame, face)
                
                if unique_id == 0:
                    max_sim = 1
                    max_index = 0
                    unique_id += 1
                else:
                    max_sim = 0
                    max_index = unique_id
                    for i in range(unique_id):
                        similarity_ids[i] = 0
                        for known_face in all_faces[i]:
                            current_face_distance = np.sum(np.square(face.normed_embedding - known_face.normed_embedding))
                            if current_face_distance < face_distance:
                               similarity_ids[i] += 1
                                
                        similarity_ids[i] /= len(all_faces[i])
                        if similarity_ids[i] > max_sim:
                            max_sim = similarity_ids[i]
                            max_index = i
                if max_sim > 0.25:
                    sim_id = max_index

                else:
                    sim_id = unique_id
                    unique_id += 1

                
                face['group_id'] = sim_id

                if sim_id in all_faces.keys():
                    all_faces[sim_id].append(face)
                else:
                    all_faces[sim_id] = [face]
                
                face_crop = frame[y1:y2, x1:x2]
                
                
                sim_id_directory = os.path.join(directory, str(sim_id))
                if not os.path.exists(sim_id_directory):
                    os.mkdir(sim_id_directory)
                filename = f"images_{filename_counter}.jpg"
                filename_counter += 1

                cv2.imwrite(os.path.join(sim_id_directory, filename), face_crop)
                
                
                if frame_number in all_face_info:
                    if face['group_id'] in all_face_info[frame_number]:
                        all_face_info[frame_number][face['group_id']].append(len(embeddings))
                    else:
                        all_face_info[frame_number][face['group_id']]= [len(embeddings)]
                else:
                    all_face_info[frame_number]= {face['group_id']:[len(embeddings)]}



                embeddings.append(face['embedding'])
                all_bboxes.append(face['bbox'])
                all_kps.append(face['kps'])

    np.save(os.path.join(UPLOAD_FOLDER, uid,'face_embeddings.npy'),embeddings)
    np.save(os.path.join(UPLOAD_FOLDER, uid,"face_bboxes.npy"), all_bboxes)
    np.save(os.path.join(UPLOAD_FOLDER, uid,"face_kps.npy"), all_kps)

    # Write the dictionary to a file
    info = {'max_groups': unique_id, 'all_face_info': all_face_info}
    with open(os.path.join(UPLOAD_FOLDER, uid,'all_info.json'), 'w') as file:
        json.dump(info, file, indent=4)

    # Release the video capture object
    cap.release()



def get_processed_face(img_path):
    image = cv2.imread(img_path)
    bboxes, kpss = retinaface_det_model.detect(image,max_num=1,metric='default')
    print(bboxes)
    bbox = bboxes[0, 0:4]
    det_score = bboxes[0, 4]
    kps = kpss[0]
    face = Face(bbox=bbox, kps=kps, det_score=det_score)
    face['embedding'] = arcface_emedding_model.get(image, face)
    return face


def run_face_swap(uid,all_face_info, group_ids, all_embeddings, all_bboxes, all_kps,input_file_path, result_file_path):
    group_new_faces = {}
    for gi in group_ids:
        new_face = get_processed_face(os.path.join(UPLOAD_FOLDER, uid, 'new_faces', f'{gi}.jpg'))
        group_new_faces[gi] = new_face

    # Create a VideoCapture object
    cap = cv2.VideoCapture(input_file_path)

    # Check if camera opened successfully
    if (cap.isOpened() == False): 
        print("Unable to read camera feed")
    
    # Default resolutions of the frame are obtained.The default resolutions are system dependent.
    # We convert the resolutions from float to integer.
    frame_width = int(cap.get(3))
    frame_height = int(cap.get(4))
    fps = cap.get(cv2.CAP_PROP_FPS)

    # Define the codec and create VideoWriter object.The output is stored in 'outpy.avi' file.
    out = cv2.VideoWriter(result_file_path,cv2.VideoWriter_fourcc(*'mp4v'), fps, (frame_width,frame_height))
    frame_number = 0

    while(True):
        ret, frame = cap.read()
        
        if ret == True:
            if str(frame_number) in all_face_info:
                for group_id in all_face_info[str(frame_number)]:
                    if int(group_id) in group_ids:
                        for gi in all_face_info[str(frame_number)][str(group_id)]:
                            old_face = Face(bbox=all_bboxes[gi], kps=all_kps[gi])
                            old_face['embedding'] = all_embeddings[gi]
                            frame = face_swapper_model.get(frame, old_face, group_new_faces[int(group_id)], paste_back=True)
                            frame = enhance_face(old_face, frame, face_enhancer_model)
            out.write(frame)
            frame_number += 1
        else:
            break

    # When everything done, release the video capture and video write objects
    cap.release()
    out.release()

def get_images_from_group(uid: str, num_images: int = 5) -> dict:
    base_path = os.path.join(BASE_DIR, uid, "cropped_faces")
    groups = os.listdir(base_path)
    group_images = {}

    for group in groups:
        group_path = os.path.join(base_path, group)
        images = os.listdir(group_path)[:num_images]
        # Store relative paths
        images = [f"{uid}/cropped_faces/{group}/{img}" for img in images]
        group_images[group] = images

    return group_images