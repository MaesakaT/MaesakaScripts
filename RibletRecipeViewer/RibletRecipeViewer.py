import cv2
import numpy as np
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


def display_recipe(files_contents, riblet_image):
    # 読み込んだファイルからレシピを抽出して表示する関数

    # コメント行を削除
    for file_name, contents in files_contents.items():
        for content in contents:
            if content[0] == ';':
                contents.remove(content)

    # レシピ行を抽出
    recipe_contents = {}
    for file_name, contents in files_contents.items():
        recipe = []
        for content in contents:
            if content[0] == 'recipe':
                recipe.append(content)
        recipe_contents[file_name] = recipe

    return files_contents


if __name__ == '__main__':

    parser = argparse.ArgumentParser(description="条件出しレシピファイルを可視化するスクリプト")

    # パラメータ設定
    image_folder = os.path.join(os.path.dirname(__file__), "RibletImage")  # リブレットイメージ画像の相対パス

    # 関数実行
    recipe_type = select_recipe_type()
    riblet_image = import_riblet_image(image_folder, recipe_type)
    files_contents = extract_contents()
    display_recipe(files_contents, riblet_image)

    if files_contents:
        print(recipe_type)
    else:
        print("ファイルが選択されませんでした。")
        sys.exit()
