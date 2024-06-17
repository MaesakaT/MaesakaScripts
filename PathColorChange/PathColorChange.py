import argparse
import sys
from tkinter import filedialog
from tkinter import messagebox
import matplotlib.pyplot as plt
import matplotlib.cm as cm


def extract_contents():
    # 複数の骨格パステキストファイルを読み込み、内容をリスト化して返す関数

    file_paths = filedialog.askopenfilenames(title="ファイルを選択",
                                             filetypes=(("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")))

    if file_paths:
        files_contents = []
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    contents = file.read()
                    files_contents.append(contents)
            except Exception as e:
                messagebox.showerror("エラー", f"ファイル {file_path} を読み込めませんでした。\n{e}")

        return files_contents


def extract_pitch_and_coord(files_contents, keywards):
    # 骨格パスファイルからパスの座標を抽出して、ピッチごとに辞書化する関数

    pitch_keyward = keywards[0]  # Pitch
    coord_keyward = keywards[1]  # poly3d

    pitch_and_paths = {}
    # 座標をピッチごとに辞書化　{key:ピッチ, value:パス座標リスト}
    for file_contents in files_contents:
        lines = file_contents.split('\n')
        for line in lines:
            if pitch_keyward in line:
                pitch = line.split()[1]
                if pitch not in pitch_and_paths:
                    pitch_and_paths[pitch] = []
            elif line.startswith(coord_keyward):
                pitch_and_paths[pitch].append(line.split()[1:])

    for pitch, paths in pitch_and_paths.items():
        if not pitch or not paths:
            messagebox.showerror("エラー", "該当しないファイルが含まれています。")
            sys.exit()
    if pitch_and_paths == {}:
        messagebox.showerror("エラー", "該当しないファイルが含まれています。")
        sys.exit()

    return pitch_and_paths


def display_paths(pitch_and_paths):
    # ピッチごとに色分けして座標にプロットする関数

    # ピッチの数を取得
    num_pitches = len(pitch_and_paths)

    # カラーマップを使用して色を均等に生成
    colormap = cm.get_cmap('hsv')
    pitch_colors = {pitch: colormap(i / num_pitches)[:3] for i, pitch in enumerate(pitch_and_paths)}

    ax = plt.figure().add_subplot(111, projection='3d')

    # ピッチごとに色分けして座標にプロット
    for pitch, paths in pitch_and_paths.items():
        x_coords = [float(path[0]) for path in paths]
        y_coords = [float(path[1]) for path in paths]
        z_coords = [float(path[2]) for path in paths]

        ax.scatter(x_coords, y_coords, z_coords, color=pitch_colors[pitch], label=pitch)

    # 凡例の追加
    ax.legend()

    # 軸の目盛りを非表示にする
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_zticks([])

    # 軸のラベルを非表示にする
    ax.set_xlabel('')
    ax.set_ylabel('')
    ax.set_zlabel('')

    # 軸のパネルを非表示にする
    ax.xaxis.pane.fill = False
    ax.yaxis.pane.fill = False
    ax.zaxis.pane.fill = False

    # 軸のラインを非表示にする
    ax.w_xaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.w_yaxis.line.set_color((1.0, 1.0, 1.0, 0.0))
    ax.w_zaxis.line.set_color((1.0, 1.0, 1.0, 0.0))

    # 軸のパネルのエッジカラーを透明にする
    ax.xaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
    ax.yaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))
    ax.zaxis.pane.set_edgecolor((1.0, 1.0, 1.0, 0.0))

    # グリッドを非表示にする
    ax.grid(False)

    # プロットを表示
    plt.show()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="ピッチごとに骨格パスの色を変えるスクリプト")

    # パラメータ設定
    # 骨格パスファイルに含まれるピッチと座標情報を抽出するためのキーワード
    search_keywards = ["Pitch", "poly3d"]

    # 関数実行
    files_contents = extract_contents()

    if files_contents:
        pitch_and_paths = extract_pitch_and_coord(files_contents, search_keywards)
        display_paths(pitch_and_paths)
    else:
        print("ファイルが選択されませんでした。")
        sys.exit()
