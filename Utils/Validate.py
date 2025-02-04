import cv2
import torch
from sklearn.metrics import recall_score, precision_score
from torch.utils.data.dataset import Dataset

from Deep_Learning.Models.AG_UNet.model import AGUNet
# from Deep_Learning.Models.ASPP_U2Net.model import ASPPU2Net
from Deep_Learning.Models.Segformer_UNet_Simplifier.model import SegFormer
# from Deep_Learning.Models.Segformer.model import SegFormer
from Deep_Learning.Models.UNet.model import UNet


from Deep_Learning.Utils.I2L1_DEPLOY import DataLoader
import numpy as np

import warnings
warnings.filterwarnings("ignore")

def pth_push(image_path, model_path):
    file_path = "test logs.txt"
    file = open(file_path, "w", encoding="utf-8")
    image_path_list = []

    model= SegFormer(num_classes=1, phi="b3",in_channel=5)
    # model = UNet(classes=1,channels=5)
    # model = ASPPU2Net(image_channels=4,texture_channels=1,classes=1)



    model_path = model_path#pth权重文件地址
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')#cpu or gpu
    model.load_state_dict(torch.load(model_path, map_location=device))#加载pth文件
    model.to(device=device)
    model  = model.eval()

    dataloader = DataLoader(image_path)
    data = torch.utils.data.DataLoader(
        dataset=dataloader,
        batch_size=1,
        shuffle=False
    )
    file.writelines("      " +"recall" + "   " + "precision" + "\n")

    recall_weight = []
    precision_weight = []
    recall_list = []
    precision_list = []


    step = 0
    for image, texture, label, path, label_pixels in data:
        # if label_pixels == 0:
        #     continue
        image = torch.cat([image, texture], dim=1).to(device=device, dtype=torch.float32)
        # image = image.to(device=device, dtype=torch.float32)

        texture = texture.to(device=device, dtype=torch.float32)
        label = label.to(device=device, dtype=torch.float32)

        # pred = model(image)
        pred = model(image, texture)

        pred = torch.sigmoid(pred)

        pred[pred  > 0.30] = 1
        pred[pred <= 0.30] = 0

        pred = np.array(pred.data.cpu())
        label = np.array(label.data.cpu())
        # cv2.imshow("pred", pred[0][0])
        # cv2.waitKey(0)
        cv2.imwrite("image"+str(step+1)+".tif",pred[0][0])
        pred_pixels = np.sum(pred>0)
        # if pred_pixels == 0:
        #     continue
        pred  = pred.reshape(-1)
        label = label.reshape(-1)

        recall = recall_score(label, pred)
        precision = precision_score(label, pred)

        step += 1
        file.writelines(format(str(step), '>03') +":"+format(str(round(recall, 4)), '<06') + "   "
                                      +format(str(round(precision, 4)), '<06') + "\n")

        recall_weight.append(label_pixels)
        precision_weight.append(pred_pixels)
        recall_list.append(recall)
        precision_list.append(precision)

        image_path_list.append(path)
    file.writelines("\n"+"各验证样本路径："+ "\n")

    step = 0
    for path in image_path_list:
        step += 1
        file.writelines(format(str(step), '>03') +": "+path[0] + "\n")

    file.writelines("整体精度："+"\n")
    recall_all_weight = sum(recall_weight)
    precision_all_weight = sum(precision_weight)

    recall = []
    precision = []
    for each_sample in range(len(recall_list)):
        recall.append(recall_list[each_sample]*(recall_weight[each_sample]/recall_all_weight))
        precision.append(precision_list[each_sample]*(precision_weight[each_sample]/precision_all_weight))

    precision = sum(precision)
    recall = sum(recall)

    file.writelines("recall："+str(np.array(recall))+"\n")
    file.writelines("precision：" + str(precision) + "\n")

    file.close()
if __name__ == "__main__":
    image_path = r"D:\Github_Repo\Deploy"
    model_path = (r"D:\Github_Repo\logs\SegFormer_U\model logs\model2.pth")
    pth_push(image_path, model_path)
