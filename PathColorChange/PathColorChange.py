import argparse
import sys
from tkinter import filedialog
from tkinter import messagebox


def open_files():
    # 複数の骨格パステキストファイルを読み込み、リストで返す関数
    file_paths = filedialog.askopenfilenames(title="ファイルを選択",
                                             filetypes=(("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")))

    if file_paths:
        file_contents = []
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    file_contents.append(content)

            except Exception as e:
                messagebox.showerror("エラー", f"ファイル {file_path} を読み込めませんでした。\n{e}")

        return file_contents


def extract_pitch_coord(file_contents, path_info_line):
    # 骨格パスファイルからピッチと座標を抽出する関数
    pitch_coord = []
    for content in file_contents:
        lines = content.split('\n')
        pitch_coord.append([line.split() for line in lines])

    return pitch_coord


# def display_paths(paths_info):
    # 骨格パスをピッチごとに色分けして表示する関数

    # 18行目以降から"Pitch"の文字列を探し、Pitchの値ごとに座標情報を取得してリスト化


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="ピッチごとに骨格パスの色を変えるプログラム")

    # パラメータ設定
    # 骨格パスファイルにて、パス情報が記載開始される行番号
    path_info_line = 18

    # 関数実行
    file_contents = open_files()

    if file_contents:
        print(file_contents)
    else:
        print("ファイルが選択されませんでした。")
        sys.exit()
