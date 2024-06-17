import argparse
import sys
from tkinter import filedialog
from tkinter import messagebox
import open3d as o3d
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def extract_contents():
    # 複数の骨格パステキストファイルを読み込み、リストで返す関数

    file_paths = filedialog.askopenfilenames(title="ファイルを選択",
                                             filetypes=(("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")))

    if file_paths:
        files_contents = []
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    files_contents.append(content)
            except Exception as e:
                messagebox.showerror("エラー", f"ファイル {file_path} を読み込めませんでした。\n{e}")

        return files_contents


def extract_pitch_and_coord(files_contents, search_texts):
    # 骨格パスファイルからパスの座標を抽出して、ピッチごとに辞書化する関数

    pitch_keyward = search_texts[0]  # Pitch
    coord_keyward = search_texts[1]  # poly3d

    pitch_and_paths = {}
    # 座標をピッチごとに辞書化　key:ピッチ, value:パス座標リスト
    for file_contents in files_contents:
        lines = file_contents.split('\n')
        for line in lines:
            if pitch_keyward in line:
                pitch = line.split()[1]
                if pitch not in pitch_and_paths:
                    pitch_and_paths[pitch] = []
            elif line.startswith(coord_keyward):
                pitch_and_paths[pitch].append(line.split()[1:])

    return pitch_and_paths


def display_paths(pitch_and_paths):
    # ピッチの数を取得
    num_pitches = len(pitch_and_paths)

    # カラーマップを使用して色を均等に生成
    colormap = cm.get_cmap('hsv')
    pitch_colors = {pitch: colormap(i / num_pitches)[:3] for i, pitch in enumerate(pitch_and_paths)}

    geometries = []

    # ピッチごとに色分けして座標にプロット
    for pitch, paths in pitch_and_paths.items():
        x_coords = [float(path[0]) for path in paths]
        y_coords = [float(path[1]) for path in paths]
        z_coords = [float(path[2]) for path in paths]

        points = np.vstack((x_coords, y_coords, z_coords)).T
        colors_array = np.array([pitch_colors[pitch]] * len(points))

        point_cloud = o3d.geometry.PointCloud()
        point_cloud.points = o3d.utility.Vector3dVector(points)
        point_cloud.colors = o3d.utility.Vector3dVector(colors_array)

        geometries.append(point_cloud)

    # open3d で 3D プロットを表示
    o3d.visualization.draw_geometries(geometries)

    # matplotlib でピッチと対応する色の凡例を表示
    plt.figure()
    for pitch, color in pitch_colors.items():
        plt.scatter([], [], color=color, label=pitch)
    plt.legend()
    plt.title('Pitch and Corresponding Colors')
    plt.show()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="ピッチごとに骨格パスの色を変えるプログラム")

    # パラメータ設定
    # 骨格パスファイルに含まれるピッチと座標情報を抽出するためのキーワード
    search_texts = ["Pitch", "poly3d"]

    # 関数実行
    files_contents = extract_contents()

    if files_contents:
        pitch_and_paths = extract_pitch_and_coord(files_contents, search_texts)
        display_paths(pitch_and_paths)
    else:
        print("ファイルが選択されませんでした。")
        sys.exit()
