from operator import attrgetter
from llava.model.builder import load_pretrained_model
from llava.mm_utils import get_model_name_from_path, process_images, tokenizer_image_token
from llava.constants import IMAGE_TOKEN_INDEX, DEFAULT_IMAGE_TOKEN, DEFAULT_IM_START_TOKEN, DEFAULT_IM_END_TOKEN, IGNORE_INDEX
from llava.conversation import conv_templates, SeparatorStyle

import torch
import cv2
import numpy as np
from PIL import Image
import requests
import copy
import warnings
from decord import VideoReader, cpu

import pandas as pd
import json
import tempfile

warnings.filterwarnings("ignore")
def load_model():
    pretrained = "lmms-lab/llava-onevision-qwen2-0.5b-ov"
    model_name = "llava_qwen"
    device = "cuda"
    device_map = "auto"
    llava_model_args = {
        "multimodal": True,
    }
    tokenizer, model, image_processor, max_length = load_pretrained_model(pretrained, None, model_name, device_map=device_map, attn_implementation="sdpa", **llava_model_args)
    return tokenizer, model, image_processor

def excel_to_json(excel_path, json_path):
    df = pd.read_excel(excel_path)
    df.to_json(json_path, orient='records', lines=True)



def load_video(video_path, max_frames_num):
    if isinstance(video_path, str):
        vr = VideoReader(video_path, ctx=cpu(0))
    else:
        # Write the file-like object to a temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(video_path.read())
            temp_file_path = temp_file.name
        vr = VideoReader(temp_file_path, ctx=cpu(0))
    total_frame_num = len(vr)
    uniform_sampled_frames = np.linspace(0, total_frame_num - 1, max_frames_num, dtype=int)
    frame_idx = uniform_sampled_frames.tolist()
    spare_frames = vr.get_batch(frame_idx).asnumpy()
    return spare_frames  # (frames, height, width, channels)

def describeVideo(video_path, tokenizer, model, image_processor, device):
    model.eval()
    # Load and process video
    video_frames = load_video(video_path, 16)
    print(video_frames.shape) # (16, 1024, 576, 3)
    image_tensors = []
    frames = image_processor.preprocess(video_frames, return_tensors="pt")["pixel_values"].half().to(device)
    image_tensors.append(frames)

    # Prepare conversation input
    conv_template = "qwen_1_5"
    question = f"{DEFAULT_IMAGE_TOKEN}\nDescribe what's happening in this video."

    conv = copy.deepcopy(conv_templates[conv_template])
    conv.append_message(conv.roles[0], question)
    conv.append_message(conv.roles[1], None)
    prompt_question = conv.get_prompt()

    input_ids = tokenizer_image_token(prompt_question, tokenizer, IMAGE_TOKEN_INDEX, return_tensors="pt").unsqueeze(0).to(device)
    image_sizes = [frame.size for frame in video_frames]

    # Generate response
    cont = model.generate(
        input_ids,
        images=image_tensors,
        image_sizes=image_sizes,
        do_sample=False,
        temperature=0,
        max_new_tokens=4096,
        modalities=["video"],
    )
    description = tokenizer.batch_decode(cont, skip_special_tokens=True)[0]
    return description