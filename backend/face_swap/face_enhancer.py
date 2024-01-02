import numpy as np
import cv2

from face_swap.utils.common import Face


def blend_frame(temp_frame, paste_frame):
	face_enhancer_blend = 0.5
	temp_frame = cv2.addWeighted(temp_frame, face_enhancer_blend, paste_frame, 1 - face_enhancer_blend, 0)
	return temp_frame

def paste_back(temp_frame, crop_frame, affine_matrix ):
	inverse_affine_matrix = cv2.invertAffineTransform(affine_matrix)
	temp_frame_height, temp_frame_width = temp_frame.shape[0:2]
	crop_frame_height, crop_frame_width = crop_frame.shape[0:2]
	inverse_crop_frame = cv2.warpAffine(crop_frame, inverse_affine_matrix, (temp_frame_width, temp_frame_height))
	inverse_mask = np.ones((crop_frame_height, crop_frame_width, 3), dtype = np.float32)
	inverse_mask_frame = cv2.warpAffine(inverse_mask, inverse_affine_matrix, (temp_frame_width, temp_frame_height))
	inverse_mask_frame = cv2.erode(inverse_mask_frame, np.ones((2, 2)))
	inverse_mask_border = inverse_mask_frame * inverse_crop_frame
	inverse_mask_area = np.sum(inverse_mask_frame) // 3
	inverse_mask_edge = int(inverse_mask_area ** 0.5) // 20
	inverse_mask_radius = inverse_mask_edge * 2
	inverse_mask_center = cv2.erode(inverse_mask_frame, np.ones((inverse_mask_radius, inverse_mask_radius)))
	inverse_mask_blur_size = inverse_mask_edge * 2 + 1
	inverse_mask_blur_area = cv2.GaussianBlur(inverse_mask_center, (inverse_mask_blur_size, inverse_mask_blur_size), 0)
	temp_frame = inverse_mask_blur_area * inverse_mask_border + (1 - inverse_mask_blur_area) * temp_frame
	temp_frame = temp_frame.clip(0, 255).astype(np.uint8)
	return temp_frame

def normalize_crop_frame(crop_frame):
	crop_frame = np.clip(crop_frame, -1, 1)
	crop_frame = (crop_frame + 1) / 2
	crop_frame = crop_frame.transpose(1, 2, 0)
	crop_frame = (crop_frame * 255.0).round()
	crop_frame = crop_frame.astype(np.uint8)[:, :, ::-1]
	return crop_frame

def prepare_crop_frame(crop_frame):
	crop_frame = crop_frame[:, :, ::-1] / 255.0
	crop_frame = (crop_frame - 0.5) / 0.5
	crop_frame = np.expand_dims(crop_frame.transpose(2, 0, 1), axis = 0).astype(np.float32)
	return crop_frame

def warp_face(target_face : Face, temp_frame):
	template = np.array(
	[
		[ 192.98138, 239.94708 ],
		[ 318.90277, 240.1936 ],
		[ 256.63416, 314.01935 ],
		[ 201.26117, 371.41043 ],
		[ 313.08905, 371.15118 ]
	])
	affine_matrix = cv2.estimateAffinePartial2D(target_face['kps'], template, method = cv2.LMEDS)[0]
	crop_frame = cv2.warpAffine(temp_frame, affine_matrix, (512, 512))
	return crop_frame, affine_matrix





def enhance_face(target_face: Face, temp_frame, face_enhancer_model):
	frame_processor = face_enhancer_model
	crop_frame, affine_matrix = warp_face(target_face, temp_frame)
	crop_frame = prepare_crop_frame(crop_frame)
	frame_processor_inputs = {}
	for frame_processor_input in frame_processor.get_inputs():
		if frame_processor_input.name == 'input':
			frame_processor_inputs[frame_processor_input.name] = crop_frame
		if frame_processor_input.name == 'weight':
			frame_processor_inputs[frame_processor_input.name] = np.array([ 1 ], dtype = np.double)
	
	crop_frame = frame_processor.run(None, frame_processor_inputs)[0][0]
	crop_frame = normalize_crop_frame(crop_frame)
	paste_frame = paste_back(temp_frame, crop_frame, affine_matrix)
	temp_frame = blend_frame(temp_frame, paste_frame)
	return temp_frame