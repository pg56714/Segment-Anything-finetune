import os

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import torch
import numpy as np

import cv2
import json
from tqdm import tqdm

from sam import sam_model_registry
from sam.utils.transforms import ResizeLongestSide


# def get_training_files(path):
#     imageists = sorted(os.listdir(os.path.join(path, "images")))
#     img_all = []
#     for image in imageists:
#         i_path = os.path.join(path, "images", image)
#         imglist = sorted(os.listdir(i_path))
#         img_all = img_all + [os.path.join(i_path, img) for img in imglist]
#     return img_all


def get_training_files(path):
    image_dir = os.path.join(path, "images")
    img_all = [os.path.join(image_dir, img) for img in sorted(os.listdir(image_dir))]
    return img_all


def main():
    sam_checkpoint = "./checkpoints/old/200_0202.pth"
    model_type = "vit_b"
    device = "cuda"
    path = "./datasets/test"
    sam_model = sam_model_registry[model_type](checkpoint=sam_checkpoint)
    sam_model.to(device=device)
    sam_model.eval()

    with open("./datasets/sam_test.json", "r") as f:
        meta = json.load(f)

    img_all = get_training_files(path)

    img_all_pbar = tqdm(img_all)

    for i, img_path in enumerate(img_all_pbar):
        image = cv2.imread(img_path)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        # transform
        sam_trans = ResizeLongestSide(sam_model.image_encoder.img_size)  # 1024
        resize_image = sam_trans.apply_image(image)
        image_tensor = torch.as_tensor(resize_image, device=device)
        input_image_torch = image_tensor.permute(2, 0, 1).contiguous()[None, :, :, :]

        input_image = sam_model.preprocess(input_image_torch)
        original_image_size = image.shape[:2]
        input_size = tuple(input_image_torch.shape[-2:])

        file_name = os.path.basename(img_path).replace("jpg", "png")

        bboxes = meta[file_name]["bbox"]
        bboxes = np.array(bboxes)

        with torch.no_grad():
            box = sam_trans.apply_boxes(bboxes, (original_image_size))
            box_torch = torch.as_tensor(box, dtype=torch.float, device=device)
            if len(box_torch.shape) == 2:
                box_torch = box_torch[:, None, :]
                
            image_embedding = sam_model.image_encoder(input_image)
            sparse_embeddings, dense_embeddings = sam_model.prompt_encoder(
                points=None,
                boxes=box_torch,
                masks=None,
            )

        low_res_masks, iou_predictions = sam_model.mask_decoder(
            image_embeddings=image_embedding,
            image_pe=sam_model.prompt_encoder.get_dense_pe(),
            sparse_prompt_embeddings=sparse_embeddings,
            dense_prompt_embeddings=dense_embeddings,
            multimask_output=False,
        )

        low_res_masks = torch.sum(low_res_masks, dim=0, keepdim=True)
        upscaled_masks = sam_model.postprocess_masks(
            low_res_masks, input_size, original_image_size
        ).to(device)

        mask_save = (upscaled_masks > 0.5)[0].detach().squeeze(0).cpu().numpy()
        mask_save = np.array(mask_save * 255).astype(np.uint8)

        vi = os.path.basename(os.path.dirname(img_path))
        fi = os.path.splitext(os.path.basename(img_path))[0] + ".png"
        os.makedirs(
            os.path.join("results", "sam", "labels", vi), mode=0o777, exist_ok=True
        )
        cv2.imwrite(os.path.join("results", "sam", "labels", vi, fi), mask_save)


if __name__ == "__main__":
    main()
