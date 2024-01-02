import os


UPLOAD_FOLDER = "./uploaded_videos"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


BASE_DIR = os.path.abspath(UPLOAD_FOLDER)


RETINAFACE_MODEL_PATH = "./face_swap/weights/det_10g.onnx"
ARCFACE_MODEL_PATH = "./face_swap/weights/w600k_r50.onnx"
FACE_SWAPPER_MODEL_PATH = "./face_swap/weights/inswapper_128.onnx"
FACE_ENHANCER_MODEL_PATH = './face_swap/weights/gfpgan_1.4.onnx'


PROVIDERS = ['CUDAExecutionProvider', 'CPUExecutionProvider']