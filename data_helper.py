import re
import pandas as pd
import csv
from tensorflow.keras import preprocessing
import numpy as np
import json
import jieba
from sklearn.preprocessing import MultiLabelBinarizer


def text_preprocess(text):
    """
    Clean and segment the text.
    Return a new text.
    """
    text = re.sub(r"[\d+\s+\.!\/_,?=\$%\^\)*\(\+\"\'\+——！:；，。？、~@#%……&*（）·¥\-\|\\《》〈〉～]",
                  "", text)
    text = re.sub("[<>]", "", text)
    text = re.sub("[a-zA-Z0-9]", "", text)
    text = re.sub(r"\s", "", text)
    if not text:
        return ''
    return ' '.join(string for string in text)


def load_data_and_write_to_file(data_file, train_data_file, test_data_file, test_sample_percentage):
    """
    Loads xlsx from files, splits the data to train and test data, write them to file.
    """
    # Load and clean data from files
    df = pd.read_csv(data_file, header=None, names=["x_text", "y_label"], dtype=str)
    x_text, y = [], []
    x_new = []
    empty_idx = []
    for idx, each_text in enumerate(x_text):
        tmp = text_preprocess(each_text)
        if tmp:
            x_new.append(tmp)
        else:
            empty_idx.append(idx)

    # Generate labels
    y_new = []
    for idx, label in enumerate(y):
        if idx in empty_idx:
            continue
        label = label.split('，')[0]
        if label == '99':
            y_new.append(0)
        else:
            y_new.append(int(label))

    # Shuffle data and split data to train and test
    np.random.seed(323)
    np.random.shuffle(x_new)
    np.random.seed(323)
    np.random.shuffle(y_new)
    test_sample_index = -1 * int(test_sample_percentage * len(y_new))
    x_train, x_test = x_new[:test_sample_index], x_new[test_sample_index:]
    y_train, y_test = y_new[:test_sample_index], y_new[test_sample_index:]

    # Write to CSV file
    with open(train_data_file, 'w', newline='', encoding='utf-8-sig') as f:
        print('Write train data to {} ...'.format(train_data_file))
        writer = csv.writer(f)
        writer.writerows(zip(x_train, y_train))
    with open(test_data_file, 'w', newline='', encoding='utf-8-sig') as f:
        print('Write test data to {} ...'.format(test_data_file))
        writer = csv.writer(f)
        writer.writerows(zip(x_test, y_test))


def preprocess(data_file, vocab_file, label_file, multi_class=94, vocab_size=50000, padding_size=200):
    """
    Text to sequence, compute vocabulary size, padding sequence.
    Return sequence and label.
    """
    print("Loading data from {} ...".format(data_file))
    df = pd.read_csv(data_file, header=None, names=["labels", "item"], dtype=str)

    # Texts to sequences
    df['item'] = df.item.apply(lambda x: list(jieba.cut(x)))
    corpus = df.item.tolist()
    text_preprocesser = preprocessing.text.Tokenizer(num_words=vocab_size)#, oov_token="<UNK>")
    text_preprocesser.fit_on_texts(corpus)
    x = text_preprocesser.texts_to_sequences(corpus)
    word_dict = text_preprocesser.word_index
    # save word2id
    with open(vocab_file, 'w', encoding='UTF8') as f:
        for k,v in word_dict.items():
            f.write(f'{k}\t{str(v)}\n')
    # json.dump(word_dict, open(vocab_file, 'w'), ensure_ascii=False)
    # max_doc_length = max([len(each_text) for each_text in x])
    x = preprocessing.sequence.pad_sequences(x, maxlen=padding_size,
                                             padding='post', truncating='post')
    print("Find words: {:d}".format(len(word_dict)))
    print("Vocabulary size: {:d}".format(vocab_size))
    print("Shape of train data: {}".format(np.shape(x)))

    y = df.labels.apply(lambda x: set(x.split())).tolist()
    mlb = MultiLabelBinarizer()
    y = mlb.fit_transform(y)

    # save label
    with open(label_file, 'w', encoding='utf8') as f:
        for label in mlb.classes_:
            f.write(f'{label}\n')

    return x, y

if __name__ == '__main__':
    dataset = r'd:\Dataset\百度题库\baidu_95.csv'
    preprocess(dataset, './data/vocab.txt', './data/label_95.txt')