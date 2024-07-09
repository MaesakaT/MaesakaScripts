import cv2
import argparse
import sys
import os
from tkinter import filedialog
from tkinter import messagebox
import tkinter as tk
from tkinter import simpledialog


def extract_contents():
    # 条件出しレシピファイルを読み込み、内容を辞書化して返す関数 {key:ファイル名, value: レシピ内容}

    file_paths = filedialog.askopenfilenames(title="ファイルを選択",
                                             filetypes=(("テキストファイル", "*.txt"), ("すべてのファイル", "*.*")))

    files_contents = {}

    if file_paths:
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    file_name = os.path.basename(file_path)
                    contents = file.read()
                    lines = contents.split('\n')
                    split_lines = [line.split() for line in lines if line]  # 空行、空白を除外
                    files_contents[file_name] = split_lines
            except Exception as e:
                messagebox.showerror("エラー", f"ファイル {file_path} を読み込めませんでした。\n{e}")

    return files_contents


class CustomDialog(simpledialog.Dialog):
    def body(self, master):
        self.title("")
        tk.Label(master, text="リブレットレシピの種類を選択してください。").grid(row=0, column=0, columnspan=2)
        return None

    def buttonbox(self):
        box = tk.Frame(self)

        self.positive_button = tk.Button(box, text="Positive", width=10, command=self.positive)
        self.positive_button.grid(row=0, column=0, padx=5, pady=5)

        self.negative_button = tk.Button(box, text="Negative", width=10, command=self.negative)
        self.negative_button.grid(row=0, column=1, padx=5, pady=5)

        box.pack()

    def positive(self):
        self.result = "Positive"
        self.destroy()

    def negative(self):
        self.result = "Negative"
        self.destroy()


def select_recipe_type():
    root = tk.Tk()
    root.withdraw()  # メインウィンドウを表示しない

    dialog = CustomDialog(root)
    result = dialog.result

    return result


def import_riblet_image(image_folder, recipe_type):
    # select_recipe_type()で選択されたレシピに対応するリブレットのイメージ画像を読み込む。

    # レシピに対応するリブレットのテンプレート画像を読み込む
    if recipe_type == "Positive":
        image_path = image_folder + "\positive_riblet.png"
    elif recipe_type == "Negative":
        image_path = image_folder + "\\negative_riblet.png"

    riblet_image = cv2.imread(image_path)

    return riblet_image


def display_recipe(files_contents, riblet_image, command, subcommand):
    # 読み込んだファイルからレーザースキャン位置を抽出し、リブレットイメージに矢印を描画する。

    recipe_command = command[0]   # レーザースキャン位置を記述するコマンド "recipe"
    offset_subcommand = subcommand[0]   # レーザースキャン位置のオフセットを記述するサブコマンド "D"

    # ファイルごとにrecipeコマンドの内容を抽出
    recipe_contents = {}
    for file_name, contents in files_contents.items():
        recipe = []
        for content in contents:
            if content[0] == recipe_command:
                recipe.append(content)
        recipe_contents[file_name] = recipe

    offset_set = {}  # ファイルごとのオフセットを格納する辞書　{key:ファイル名, value: オフセットリスト}

    # ファイルごとにオフセットを抽出
    for file_name, recipe in recipe_contents.items():
        offset_set[file_name] = []
        for row in recipe:
            if offset_subcommand in row:
                i = row.index(offset_subcommand)
                offset = row[i + 1:]
                offset = [float(value) for value in offset]
                offset_set[file_name].append(offset)

    # --------------------------------------------------------------
    # リブレットイメージに矢印を描画

    height, width, _ = riblet_image.shape   # 画像のサイズを取得
    image_right_x = width - 1   # 画像の右端のx座標
    image_bottom_y = height - 1   # 画像の下端のy座標

    # 矢印の設定
    allow_color = (0, 255, 0)  # 矢印の色 緑
    allow_thick = 2   # 矢印の太さ

    # ファイルごとにオフセットの最大値と最小値を検索
    max_offset = {}
    for file_name, offsets in offset_set.items():
        max_offset[file_name] = 0
        for offset in offsets:
            if abs(max(offset)) > max_offset[file_name]:
                max_offset[file_name] = abs(max(offset))
            elif abs(min(offset)) > max_offset[file_name]:
                max_offset[file_name] = abs(min(offset))

    # 矢印を描画する座標を算出。
    image_xcoord = {}  # key:ファイル名, value: x座標リスト
    image_ycoord = {}  # key:ファイル名, value: y座標リスト
    for file_name, offsets in offset_set.items():
        # オフセットの値を画像のx座標に変換。オフセットの最小値を画像の左端、最大値を画像の右端に合わせる。
        image_xcoord[file_name] = []
        for offset in offsets:
            offset = [((value + max_offset[file_name]) / (max_offset[file_name] * 2)) * image_right_x for value in offset]
            image_xcoord[file_name].append(offset)

        # レシピの階層に応じたy座標を算出
        layers = image_bottom_y / len(offsets)
        image_ycoord[file_name] = []
        for i in range(len(offsets)):
            image_ycoord[file_name].append(layers * i)

    # リブレットイメージに矢印を描画
    for file_name, xcoords in image_xcoord.items():
        layers = image_bottom_y / len(xcoords)
        image_copy = riblet_image.copy()
        for i, xcoord in enumerate(xcoords):
            for value in xcoord:
                arrow_x = int(value)
                arrow_ystart = int(image_ycoord[file_name][i])
                arrow_yend = int(image_ycoord[file_name][i] + layers / 2 - 1)
                image_add_arrow = cv2.arrowedLine(image_copy, (arrow_x, arrow_ystart), (arrow_x, arrow_yend),
                                                  allow_color, allow_thick, tipLength=0.1)
        cv2.imshow(file_name, image_add_arrow)
        cv2.waitKey(0)
        cv2.destroyAllWindows()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="条件出しレシピファイルを可視化するスクリプト")

    # パラメータ設定
    image_folder = os.path.join(os.path.dirname(__file__), "RibletImage")   # リブレットイメージ画像の相対パス
    command = ["recipe"]  # レシピファイルのコマンド
    subcommand = ["D"]  # レシピファイルのサブコマンド

    # 関数実行
    recipe_type = select_recipe_type()
    riblet_image = import_riblet_image(image_folder, recipe_type)
    files_contents = extract_contents()
    test = display_recipe(files_contents, riblet_image, command, subcommand)

    if files_contents:
        print(test)
    else:
        print("ファイルが選択されませんでした。")
        sys.exit()
