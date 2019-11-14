import argparse
import os
import data_helper
from text_cnn import TextCNN
from tensorflow import keras
import tensorflow as tf
from pprint import pprint
import time
import tensorflow.keras.backend as K


def micro_f1(y_true, y_pred):
    """F1 metric.

    Computes the micro_f1 and macro_f1, metrics for multi-label classification of
    how many relevant items are selected.
    """
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)), axis=0)
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)), axis=0)
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)), axis=0)

    """Macro_F1 metric.
    """
    precision = true_positives / (predicted_positives + K.epsilon())
    recall = true_positives / (possible_positives + K.epsilon())
    macro_f1 = K.mean(2 * precision * recall / (precision + recall + K.epsilon()))

    """Micro_F1 metric.
    """
    precision = K.sum(true_positives) / (K.sum(predicted_positives)+K.epsilon())
    recall = K.sum(true_positives) / (K.sum(possible_positives)+K.epsilon())
    micro_f1 = 2 * precision * recall / (precision + recall + K.epsilon())
    return micro_f1


def macro_f1(y_true, y_pred):
    """F1 metric.

    Computes the micro_f1 and macro_f1, metrics for multi-label classification of
    how many relevant items are selected.
    """
    true_positives = K.sum(K.round(K.clip(y_true * y_pred, 0, 1)), axis=0)
    predicted_positives = K.sum(K.round(K.clip(y_pred, 0, 1)), axis=0)
    possible_positives = K.sum(K.round(K.clip(y_true, 0, 1)), axis=0)

    """Macro_F1 metric.
    """
    precision = true_positives / (predicted_positives + K.epsilon())
    recall = true_positives / (possible_positives + K.epsilon())
    macro_f1 = K.mean(2 * precision * recall / (precision + recall + K.epsilon()))

    """Micro_F1 metric.
    """
    precision = K.sum(true_positives) / K.sum(predicted_positives)
    recall = K.sum(true_positives) / K.sum(possible_positives)
    micro_f1 = 2 * precision * recall / (precision + recall + K.epsilon())
    return macro_f1


def train(x_train, y_train, vocab_size, feature_size, save_path):
    print("\nTrain...")
    model = TextCNN(vocab_size, feature_size, args.embed_size, args.num_classes,
                    args.num_filters, args.filter_sizes, args.regularizers_lambda, args.dropout_rate)
    model.summary()
    parallel_model = keras.utils.multi_gpu_model(model, gpus=2)
    parallel_model.compile(tf.optimizers.Adam(learning_rate=args.learning_rate), loss='binary_crossentropy',
                           metrics=[micro_f1, macro_f1])
    # keras.utils.plot_model(model, show_shapes=True, to_file=os.path.join(args.results_dir, timestamp, "model.pdf"))
    # y_train = tf.one_hot(y_train, args.num_classes)
    # tb_callback = keras.callbacks.TensorBoard(os.path.join(args.results_dir, timestamp, 'log/'),
    #                                           histogram_freq=0.1, write_graph=True,
    #                                           write_grads=True, write_images=True,
    #                                           embeddings_freq=0.5, update_freq='batch')
    history = parallel_model.fit(x=x_train, y=y_train, batch_size=args.batch_size, epochs=args.epochs,
                                 # callbacks=[tb_callback],
                        validation_split=args.fraction_validation, shuffle=True)
    print("\nSaving model...")
    keras.models.save_model(model, save_path)
    pprint(history.history)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='This is the TextCNN train project.')
    parser.add_argument('-t', '--test_sample_percentage', default=0.1, type=float, help='The fraction of test data.(default=0.1)')
    parser.add_argument('-p', '--padding_size', default=200, type=int, help='Padding size of sentences.(default=128)')
    parser.add_argument('-e', '--embed_size', default=512, type=int, help='Word embedding size.(default=512)')
    parser.add_argument('-f', '--filter_sizes', default='3,4,5', help='Convolution kernel sizes.(default=3,4,5)')
    parser.add_argument('-n', '--num_filters', default=128, type=int, help='Number of each convolution kernel.(default=128)')
    parser.add_argument('-d', '--dropout_rate', default=0.8, type=float, help='Dropout rate in softmax layer.(default=0.5)')
    parser.add_argument('-c', '--num_classes', default=95, type=int, help='Number of target classes.(default=18)')
    parser.add_argument('-l', '--regularizers_lambda', default=0.01, type=float, help='L2 regulation parameter.(default=0.01)')
    parser.add_argument('-b', '--batch_size', default=64, type=int, help='Mini-Batch size.(default=64)')
    parser.add_argument('-lr', '--learning_rate', default=0.005, type=float, help='Learning rate.(default=0.005)')
    parser.add_argument('-vocab_size', default=50000, type=int, help='Limit vocab size.(default=50000)')
    parser.add_argument('--epochs', default=1000, type=int, help='Number of epochs.(default=10)')
    parser.add_argument('--fraction_validation', default=0.005, type=float, help='The fraction of validation.(default=0.05)')
    parser.add_argument('--results_dir', default='./results/', type=str, help='The results dir including log, model, vocabulary and some images.(default=./results/)')
    args = parser.parse_args()
    print('Parameters:', args, '\n')

    if not os.path.exists(args.results_dir):
        os.mkdir(args.results_dir)
    timestamp = time.strftime("%Y-%m-%d-%H-%M", time.localtime(time.time()))
    os.mkdir(os.path.join(args.results_dir, timestamp))
    os.mkdir(os.path.join(args.results_dir, timestamp, 'log/'))

    # if not os.path.exists("./data/train_data.csv") or not os.path.exists("./data/test_data.csv"):
    #     data_helper.load_data_and_write_to_file("./data/fenduan_clean.xlsx", "./data/train_data.csv",
    #                                             "./data/test_data.csv", args.test_sample_percentage)

    x_train, y_train = data_helper.preprocess('./data/baidu_95.csv',
                                              './data/vocab.txt',
                                              './data/label_95.txt')
    train(x_train, y_train, args.vocab_size, args.padding_size, os.path.join(args.results_dir, timestamp, 'TextCNN.h5'))
