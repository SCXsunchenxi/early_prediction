import tensorflow as tf
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.metrics import roc_auc_score
import sys
import pickle
from LSTMmodel import LSTM

def load_pkl(path):
    with open(path,'rb') as f:
        obj = pickle.load(f)
        return obj


# 训练函数 创建TLSTM实例，得到TLSTM训练后的准确度，使用adam优化器学习
def training(path,learning_rate,training_epochs,train_dropout_prob,hidden_dim,fc_dim,key,model_path):
    # train data
    path_string = path + '/batches_data_train.seqs'
    data_train_batches = load_pkl(path_string)

    path_string = path + '/batches_label_train.seqs'
    labels_train_batches = load_pkl(path_string)

    number_train_batches = len(data_train_batches)

    input_dim = np.array(data_train_batches[0]).shape[2]
    output_dim = np.array(labels_train_batches[0]).shape[1]

    print("Train data is loaded!")

    path_string = path + '/batches_data_test.seqs'
    data_test_batches = load_pkl(path_string)

    path_string = path + '/batches_label_test.seqs'
    labels_test_batches = load_pkl(path_string)

    number_test_batches = len(data_test_batches)

    print("Test data is loaded!")

    # model built
    lstm = LSTM(input_dim, output_dim, hidden_dim, fc_dim,key)
    cross_entropy, y_pred, y, logits, labels = lstm.get_cost_acc()
    optimizer = tf.train.AdamOptimizer(learning_rate=learning_rate).minimize(cross_entropy)
    init = tf.global_variables_initializer()
    saver = tf.train.Saver()

    # train
    with tf.Session() as sess:
        sess.run(init)
        for epoch in range(training_epochs):

            # Loop over all batches
            for i in range(number_train_batches):
                # batch_xs is [number of patients x sequence length x input dimensionality]
                batch_xs, batch_ys = data_train_batches[i], labels_train_batches[i]
                sess.run(optimizer,feed_dict={lstm.input: batch_xs, lstm.labels: batch_ys,lstm.keep_prob:train_dropout_prob})
                print('Training epoch ' + str(epoch) + ' batch ' + str(i) + ' done')

            # test acc
            Y_pred = []
            Y_true = []
            Labels = []
            Logits = []
            for i in range(number_test_batches):  #
                batch_xs, batch_ys = data_test_batches[i], labels_test_batches[i]
                c_train, y_pred_train, y_train, logits_train, labels_train = sess.run(lstm.get_cost_acc(), \
                                   feed_dict={lstm.input:batch_xs, lstm.labels: batch_ys,lstm.keep_prob: train_dropout_prob})

                if i > 0:
                    Y_true = np.concatenate([Y_true, y_train], 0)
                    Y_pred = np.concatenate([Y_pred, y_pred_train], 0)
                    Labels = np.concatenate([Labels, labels_train], 0)
                    Logits = np.concatenate([Logits, logits_train], 0)
                else:
                    Y_true = y_train
                    Y_pred = y_pred_train
                    Labels = labels_train
                    Logits = logits_train

            total_acc = accuracy_score(Y_true, Y_pred)
            total_auc = roc_auc_score(Labels, Logits, average='micro')
            total_auc_macro = roc_auc_score(Labels, Logits, average='macro')
            print("Train Accuracy = {:.3f}".format(total_acc))
            print("Train AUC = {:.3f}".format(total_auc))
            print("Train AUC Macro = {:.3f}".format(total_auc_macro))
            print('Testing epoch ' + str(epoch) + ' done........................')

        print("Training is over!")
        saver.save(sess, model_path)


def testing(path, hidden_dim, fc_dim, key, model_path):
    path_string = path + '/batches_data_test.seqs'
    data_test_batches = load_pkl(path_string)

    path_string = path + '/batches_label_test.seqs'
    labels_test_batches = load_pkl(path_string)

    number_test_batches = len(data_test_batches)

    print("Test data is loaded!")

    input_dim = np.array(data_test_batches[0]).shape[2]
    output_dim = np.array(labels_test_batches[0]).shape[1]

    test_dropout_prob = 1.0
    lstm_load = LSTM(input_dim, output_dim, hidden_dim, fc_dim, key)

    saver = tf.train.Saver()
    with tf.Session() as sess:
        saver.restore(sess, model_path)

        Y_true = []
        Y_pred = []
        Logits = []
        Labels = []
        for i in range(number_test_batches):
            batch_xs, batch_ys = data_test_batches[i], labels_test_batches[i]
            c_test, y_pred_test, y_test, logits_test, labels_test = sess.run(lstm_load.get_cost_acc(),
                                                                             feed_dict={lstm_load.input: batch_xs,
                                                                                        lstm_load.labels: batch_ys, \
                                                                                        lstm_load.keep_prob: test_dropout_prob})
            if i > 0:
                Y_true = np.concatenate([Y_true, y_test], 0)
                Y_pred = np.concatenate([Y_pred, y_pred_test], 0)
                Labels = np.concatenate([Labels, labels_test], 0)
                Logits = np.concatenate([Logits, logits_test], 0)
            else:
                Y_true = y_test
                Y_pred = y_pred_test
                Labels = labels_test
                Logits = logits_test
        total_auc = roc_auc_score(Labels, Logits, average='micro')
        total_auc_macro = roc_auc_score(Labels, Logits, average='macro')
        total_acc = accuracy_score(Y_true, Y_pred)
        print("Test Accuracy = {:.3f}".format(total_acc))
        print("Test AUC Micro = {:.3f}".format(total_auc))
        print("Test AUC Macro = {:.3f}".format(total_auc_macro))


def testing_MC_dropout(path,test_dropout_prob,hidden_dim,fc_dim,key,model_path,test_num):

    path_string = path + '/batches_data_test.seqs'
    data_test_batches = load_pkl(path_string)

    path_string = path + '/batches_label_test.seqs'
    labels_test_batches = load_pkl(path_string)

    number_test_batches = len(data_test_batches)

    print("Test data is loaded!")

    input_dim = np.array(data_test_batches[0]).shape[2]
    output_dim = np.array(labels_test_batches[0]).shape[1]

    test_dropout_prob = test_dropout_prob

    lstm_load = LSTM(input_dim, output_dim, hidden_dim, fc_dim, key)
    saver = tf.train.Saver()

    with tf.Session() as sess:
        saver.restore(sess, model_path)

        acc_in_time_length=[]
        uncertainty_in_time_length=[]
        # 暂且测试第一个batch 序列长度是44
        batch_xs, batch_ys = data_test_batches[0], labels_test_batches[0]
        time_length = len(batch_xs[0])

        for length in range(time_length-12 , time_length):
            # 时间截断
            batch_xs_sub =  np.array(batch_xs)[:, :length].tolist()

            ACCs = []
            AUCs = []
            for j in range(test_num):

                c_test, y_pred_test, y_test, logits_test, labels_test = sess.run(lstm_load.get_cost_acc(),
                                                                                 feed_dict={lstm_load.input: batch_xs_sub,
                                                                                            lstm_load.labels: batch_ys,\
                                                                                           lstm_load.keep_prob: test_dropout_prob})
                Y_true = y_test
                Y_pred = y_pred_test
                Labels = labels_test
                Logits = logits_test

                total_auc = roc_auc_score(Labels, Logits, average='micro')
                total_auc_macro = roc_auc_score(Labels, Logits, average='macro')
                total_acc = accuracy_score(Y_true, Y_pred)
                print("Test Accuracy = {:.3f}".format(total_acc))
                print("Test AUC Micro = {:.3f}".format(total_auc))
                print("Test AUC Macro = {:.3f}".format(total_auc_macro))
                ACCs.append(total_acc)
                AUCs.append(total_auc)

            meanACC=np.mean(ACCs)
            uncertainty=np.std(ACCs, ddof = 1)
            print('mean ACC: '+ str(meanACC)+' uncertainty: '+ str(uncertainty))#variance
            acc_in_time_length.append(meanACC)
            uncertainty_in_time_length.append(uncertainty)
    return acc_in_time_length,uncertainty_in_time_length

#
# def main(argv):
#     training_mode = int(sys.argv[1])
#     path = str(sys.argv[2])
#
#     if training_mode == 1:
#         learning_rate = float(sys.argv[3])
#         training_epochs = int(sys.argv[4])
#         dropout_prob = float(sys.argv[5])
#         hidden_dim = int(sys.argv[6])
#         fc_dim = int(sys.argv[7])
#         model_path = str(sys.argv[8])
#         training(path, learning_rate, training_epochs, dropout_prob, hidden_dim, fc_dim, training_mode, model_path)
#     else:
#         hidden_dim = int(sys.argv[3])
#         fc_dim = int(sys.argv[4])
#         model_path = str(sys.argv[5])
#         testing(path, hidden_dim, fc_dim, training_mode, model_path)


def main(training_mode,data_path, learning_rate,training_epochs,dropout_prob,hidden_dim,fc_dim,model_path,test_num=0):

    training_mode = int(training_mode)
    path = str(data_path)

    # train
    if training_mode == 1:
        learning_rate = float(learning_rate)
        training_epochs = int(training_epochs)
        dropout_prob = float(dropout_prob)
        hidden_dim = int(hidden_dim)
        fc_dim = int(fc_dim)
        model_path = str(model_path)
        training(path, learning_rate, training_epochs, dropout_prob, hidden_dim, fc_dim, training_mode, model_path)

    # test
    elif training_mode==0:
        hidden_dim = int(hidden_dim)
        fc_dim = int(fc_dim)
        model_path = str(model_path)
        testing(path, hidden_dim, fc_dim, training_mode, model_path)

    #test with mc_dropout
    elif training_mode==2:
        dropout_prob = float(dropout_prob)
        hidden_dim = int(hidden_dim)
        fc_dim = int(fc_dim)
        model_path = str(model_path)
        test_num=test_num
        acc_in_time_length,uncertainty_in_time_length=testing_MC_dropout(path, dropout_prob, hidden_dim, fc_dim, training_mode, model_path,test_num)
        print(acc_in_time_length)
        print(uncertainty_in_time_length)

if __name__ == "__main__":
   main(training_mode=2,data_path='../pkl_data', learning_rate=0.001,training_epochs=1,dropout_prob=0.25,hidden_dim=256,fc_dim=128,model_path='../model/',test_num=5)

