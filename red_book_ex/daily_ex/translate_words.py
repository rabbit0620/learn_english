#!/usr/bin/env python3
"""
将 md 文件中每行的单词/短语，用本地 JSONL 词典翻译出来。
词典路径：endict/dict/*.json
输入：一个文本文件，每行一个要查的词
输出：在原文件同目录下生成 _translated.md，包含“单词 → 翻译”的对照表
"""

import json
import os
import sys
from pathlib import Path

# ==================== 配置部分 ====================
# 词典目录（包含 0001.json ~ 0608.json）
DICT_DIR = Path("/home/randy/hdddata/downloads_hdd/endict/dict")  # 请改成你的实际路径
# 要翻译的 md 文件
INPUT_FILE = Path("round_part4")  # 请改成你的实际文件
# 是否忽略大小写（推荐 True）
IGNORE_CASE = True
# 使用哪个字段作为查询键（自动构建两个索引：word 和 sw）
# 查询时优先匹配 sw（已去除空格、小写的标准化形式），其次 word
# =================================================


def load_dictionary(dict_dir):
    """遍历所有 JSONL 文件，构建 word -> translation 和 sw -> translation 两个索引"""
    word_dict = {}
    sw_dict = {}
    json_files = sorted(dict_dir.glob("*.json"))
    print(f"找到 {len(json_files)} 个词典文件，正在加载...", file=sys.stderr)

    for jf in json_files:
        with open(jf, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                word = entry.get("word", "").strip()
                sw = entry.get("sw", "").strip()
                translations = entry.get("translation", [])
                if not translations:
                    continue
                # 取第一个翻译作为默认结果
                trans = translations[0].strip()

                if IGNORE_CASE:
                    word_lower = word.lower()
                    sw_lower = sw.lower()
                    # 使用小写作为键，但原始翻译不变
                    if word_lower:
                        word_dict[word_lower] = trans
                    if sw_lower:
                        sw_dict[sw_lower] = trans
                else:
                    if word:
                        word_dict[word] = trans
                    if sw:
                        sw_dict[sw] = trans

    print(f"加载完成，共 {len(word_dict)} 个词条（word索引）", file=sys.stderr)
    return word_dict, sw_dict


def normalize_query(text):
    """将用户输入的短语标准化，模拟 sw 字段生成方式"""
    # sw 一般是：去掉所有空格、转为小写
    return text.replace(" ", "").lower() if IGNORE_CASE else text


def translate_line(line, word_dict, sw_dict):
    """查询一行文本，返回翻译结果"""
    original = line.strip()
    if not original:
        return ""  # 空行保留

    # 准备查询键
    query_word = original.lower() if IGNORE_CASE else original
    query_sw = normalize_query(original)

    # 优先 sw 精确匹配，其次 word 精确匹配
    if query_sw in sw_dict:
        return f"{original} → {sw_dict[query_sw]}"
    elif query_word in word_dict:
        return f"{original} → {word_dict[query_word]}"
    else:
        return f"{original} → [未找到]"


def main():
    dict_dir = DICT_DIR
    input_file = INPUT_FILE

    if not dict_dir.exists():
        print(f"错误：词典目录不存在 {dict_dir}", file=sys.stderr)
        sys.exit(1)
    if not input_file.exists():
        print(f"错误：输入文件不存在 {input_file}", file=sys.stderr)
        sys.exit(1)

    # 加载词典
    word_dict, sw_dict = load_dictionary(dict_dir)

    # 读取输入文件
    with open(input_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # 翻译每一行
    translated_lines = []
    for line in lines:
        translated_lines.append(translate_line(line, word_dict, sw_dict))

    # 生成输出文件
    output_path = input_file.with_name(
        input_file.stem + "_translated" + input_file.suffix
    )
    with open(output_path, "w", encoding="utf-8") as f:
        for tl in translated_lines:
            f.write(tl + "\n")

    print(f"翻译完成！结果保存在：{output_path}")


if __name__ == "__main__":
    main()
