import cv2
import os
import sys
import numpy as np
import csv
import re
import math
import argparse

# リブレット加工面が映っている画像から、加工領域以外のノイズ成分を除去
# averaging_kernel_size、opening_kernel_sizeの値によって検出精度が決定
def remove_noise_from_image(file_path: str, averaging_kernel_size, opening_kernel_size):

    if (os.path.splitext(file_path)[1] != ".jpg"):
        raise Exception("ファイルの拡張子が異なります。")

    # リブレット加工面が映っている画像ファイルをグレースケールに変換し、色を反転
    # 色の反転を行うことで、後に行う加工面のコーナー検出が正常に動作する
    raw_img = np.fromfile(file_path, dtype=np.uint8)
    raw_img = cv2.imdecode(raw_img, cv2.IMREAD_UNCHANGED)
    grayscale_img = cv2.cvtColor(raw_img, cv2.COLOR_BGR2GRAY)
    grayscale_img = cv2.bitwise_not(grayscale_img)
    
    # 平均化フィルタリングを行い、ノイズ成分を平滑化
    averaged_img = cv2.blur(grayscale_img, (averaging_kernel_size, averaging_kernel_size))

    # 大津の二値化によりThresholdを決定
    threshold, bin_img = cv2.threshold(averaged_img, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # thresholdを閾値として画像を白と黒に二値化し、小さなノイズ成分を除去
    ret, binarization_img = cv2.threshold(
        averaged_img, threshold, 255, cv2.THRESH_BINARY)

    # オープニング処理により、除去しきれなかったノイズ成分を除去
    opening_param = np.ones((opening_kernel_size, opening_kernel_size), np.uint8)
    noise_free_img = cv2.morphologyEx(
        binarization_img, cv2.MORPH_OPEN, opening_param)

    return (noise_free_img)

# 顕微鏡のティーチングファイルから対物レンズの倍率情報を読み込み
def read_lens_magnification(microscope_status_csv, lens_info_row, lens_info_column):

    # csvファイルの2行4列目に倍率情報が入っている前提
    with open(microscope_status_csv, 'r', encoding='utf-8') as file:

        reader = csv.reader(file)
        rows = list(reader)
        lens_info = rows[lens_info_row][lens_info_column]

        pattern = r'{}\s*,\s*([\d\.]+)'.format("Plan")
        match = re.search(pattern, lens_info)

        if match:
            return float(match.group(1))
        else:
            raise Exception("対物レンズの情報が見つかりません。")


# 顕微鏡のティーチングファイルから対物レンズの倍率情報とSTG情報を読み込み
def read_lens_magnification(microscope_status_csv, lens_info_row, lens_info_column):

    # csvファイルの2行4列目に倍率情報が入っている前提
    with open(microscope_status_csv, 'r', encoding='utf-8') as file:

        reader = csv.reader(file)
        rows = list(reader)
        lens_info = rows[lens_info_row][lens_info_column]
        
        print(lens_info)

        pattern = r'{}\s*,\s*([\d\.]+)'.format("Plan")
        match = re.search(pattern, lens_info)

        if match:
            return float(match.group(1))
        else:
            raise Exception("対物レンズの情報が見つかりません。")

# 全リブレット加工面の中心座標と、画像の中心座標の差分を求め、顕微鏡の機械座標系に変換
def calculate_offset(noise_free_img, lens_magnification):

    riblet_contours, hierarchy = cv2.findContours(
        noise_free_img,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE
    )

    # リブレット加工面を矩形と捉えて、矩形４隅の座標をcorners_arrayに格納
    # リブレット加工面が傾いている場合にも検出可能
    riblet_corners_box = []

    for i, contour in enumerate(riblet_contours):
        riblet_rect = cv2.minAreaRect(contour)
        riblet_corners = cv2.boxPoints(riblet_rect)
        riblet_corners = np.intp(riblet_corners)
        riblet_corners_box.insert(i, riblet_corners)

    if (riblet_corners_box is None):
        raise Exception("リブレット加工面を検出できません。")

    else:
        # 画像の中心座標を算出
        img_disp = cv2.cvtColor(noise_free_img, cv2.COLOR_GRAY2BGR)
        height, width, _ = img_disp.shape
        img_center_x = width // 2
        img_center_y = height // 2

        # 加工面ごとの中心座標を算出
        riblet_centers_array = []
        distance = []

        riblet_centers_array = [np.mean(corners, axis=0) for corners in riblet_corners_box]

        # 画像の中心から最も近いリブレット加工面の中心座標を算出
        for riblet_center in riblet_centers_array:
            x_squared = (riblet_center[0] - img_center_x) ** 2
            y_squared = (riblet_center[1] - img_center_y) ** 2
            distance.append(math.sqrt(x_squared + y_squared))

        min_dist_index = distance.index(min(distance))

        riblet_center_x = riblet_centers_array[min_dist_index][0]
        riblet_center_y = riblet_centers_array[min_dist_index][1]

        # 画像中心に最も近いリブレット加工面の中心座標と、画像の中心座標の差分を算出
        # 画像の座標系が左上を（0, 0）としているので、機械座標系と合わせるように減算を行う。
        img_offset_x = img_center_x - riblet_center_x
        img_offset_y = riblet_center_y - img_center_y
        
        riblet_corners_box = np.array(riblet_corners_box)
        riblet_centers_array = np.array(riblet_centers_array)

        # 画像の1pixが顕微鏡の機械座標系で何umになるのかを計算
        # 現状、顕微鏡のレンズは2.5倍（画角：5400×4050 um）を想定
        try:
            reduction_ratio_x = (2.5 / lens_magnification) * 5400
            reduction_ratio_y = (2.5 / lens_magnification) * 4050
            pix_offset_x = reduction_ratio_x / img_disp.shape[1]
            pix_offset_y = reduction_ratio_y / img_disp.shape[0]
            machine_offset_x = pix_offset_x * img_offset_x
            machine_offset_y = pix_offset_y * img_offset_y
            riblet_corners_box[:, :, 0] = (riblet_corners_box[:, :, 0] - img_center_x) * pix_offset_x
            riblet_corners_box[:, :, 1] = (img_center_y - riblet_corners_box[:, :, 1]) * pix_offset_y
            riblet_centers_array[:, 0] = (riblet_centers_array[:, 0] - img_center_x) * pix_offset_x
            riblet_centers_array[:, 1] = (img_center_y - riblet_centers_array[:, 1]) * pix_offset_y
        except ZeroDivisionError:
            raise Exception("入力されたデータが想定されているものと異なります。")

        # 加工面と画像の中心位置確認用
        # cv2.circle(img_disp, (img_center_x, img_center_y), 10, (0, 255, 0), -1)
        # cv2.circle(img_disp, (int(riblet_center_x), int(riblet_center_y)), 10, (0, 255, 0), -1)
        # output_img = cv2.resize(img_disp, dsize = None, fx = 0.5, fy = 0.5)
        # cv2.imshow("imgage", output_img)
        # cv2.waitKey()
        
        # 出力する4隅の座標の格納順を左下→左上→右下→右上に入れ替え
        riblet_corners_box_copy = riblet_corners_box
        for riblet_corners in range(riblet_corners_box.shape[0]):
            riblet_corners_box_copy[riblet_corners, 0], riblet_corners_box_copy[riblet_corners, 1] = riblet_corners_box[riblet_corners, 1].copy(), riblet_corners_box[riblet_corners, 0].copy()
            riblet_corners_box_copy[riblet_corners, 0], riblet_corners_box_copy[riblet_corners, 3] = riblet_corners_box[riblet_corners, 3].copy(), riblet_corners_box[riblet_corners, 0].copy()

        return (machine_offset_x, machine_offset_y, riblet_corners_box, riblet_centers_array)

if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description = 'リブレット加工面が映っている顕微鏡画像から、加工面四隅の座標を出力するスクリプト') 
        
        parser.add_argument('arg1', help = 'リブレット加工面が映っている顕微鏡画像(ファイル形式：jpg)')
        parser.add_argument('arg2', help = '顕微鏡のティーチングファイル（ファイル形式：csv）')
        
        args = parser.parse_args()

        print(f"arg1:"+args.arg1)
        print(f"arguments:"+args.arg2)
        
        # フィルタリングのカーネルサイズを設定
        averaging_kernel_size = 35
        opening_kernel_size = 55
        
        # 顕微鏡の倍率データが入っているセルを指定。2行4列目を想定。
        lens_info_row = 1
        lens_info_column = 3

        output_img = remove_noise_from_image(args.arg1, averaging_kernel_size, opening_kernel_size)
        lens_magnification = read_lens_magnification(args.arg2, lens_info_row, lens_info_column)
        machine_offset = calculate_offset(output_img, lens_magnification)
        print(machine_offset)

    except Exception as e:
        print(e)
        print("Failure!!")
        sys.exit(-1)
