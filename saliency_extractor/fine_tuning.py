from __future__ import print_function, division
import numpy as np
import tensorflow as tf
import tensorflow.contrib.slim.nets
import cv2
import glob
import os

SNAPSHOT_FILE = "/home/leite/workspace/weights/inception_v3_imagenet_urfd.ckpt"
PRETRAINED_SNAPSHOT_FILE = "/home/leite/workspace/weights/inception_v3.ckpt"

TENSORBOARD_DIR = "/home/leite/workspace/tb_logdir/"

IMG_WIDTH, IMG_HEIGHT = [299, 299]
N_CHANNELS = 3
N_CLASSES = 2

P_CLASS_PATH = "/home/leite/Dropbox/aws/urfd/Falls/"
N_CLASS_PATH = "/home/leite/Dropbox/aws/urfd/notfalls/"

graph = tf.Graph()
with graph.as_default():
    # INPUTS
    with tf.name_scope("inputs") as scope:
        input_dims = (None, IMG_HEIGHT, IMG_WIDTH, N_CHANNELS)
        tf_X = tf.placeholder(tf.float32, shape=input_dims, name="X")
        tf_Y = tf.placeholder(tf.int32, shape=[None], name="Y")
        tf_alpha = tf.placeholder_with_default(0.001, shape=None, name="alpha")
        tf_is_training = tf.placeholder_with_default(False, shape=None, name="is_training")

    # PREPROCESSING STEPS
    with tf.name_scope("preprocess") as scope:
        scaled_inputs = tf.div(tf_X, 255., name="rescaled_inputs")

    # BODY
    arg_scope = tf.contrib.slim.nets.inception.inception_v3_arg_scope()
    with tf.contrib.framework.arg_scope(arg_scope):
        tf_logits, end_points = tf.contrib.slim.nets.inception.inception_v3(
            scaled_inputs,
            num_classes=N_CLASSES,
            is_training=tf_is_training,
            dropout_keep_prob=0.8)

    # PREDICTIONS
    tf_preds = tf.to_int32(tf.argmax(tf_logits, axis=-1), name="preds")

    # LOSS - Sums all losses (even Regularization losses)
    with tf.variable_scope('loss') as scope:
        unrolled_labels = tf.reshape(tf_Y, (-1,))
        tf.losses.sparse_softmax_cross_entropy(labels=unrolled_labels,
                                               logits=tf_logits)
        tf_loss = tf.losses.get_total_loss()

    # OPTIMIZATION - Also updates batchnorm operations automatically
    with tf.variable_scope('opt') as scope:
        tf_optimizer = tf.train.AdamOptimizer(tf_alpha, name="optimizer")
        update_ops = tf.get_collection(tf.GraphKeys.UPDATE_OPS) # for batchnorm
        with tf.control_dependencies(update_ops):
            tf_train_op = tf_optimizer.minimize(tf_loss, name="train_op")

    # PRETRAINED SAVER SETTINGS
    # Lists of scopes of weights to include/exclude from pretrained snapshot
    pretrained_include = [
        'InceptionV3/Conv2d_1a_3x3',
        'InceptionV3/Conv2d_2a_3x3',
        'InceptionV3/Conv2d_2b_3x3',
        'InceptionV3/Conv2d_3b_1x1',
        'InceptionV3/Conv2d_4a_3x3',
        'InceptionV3/MaxPool_3a_3x3',
        'InceptionV3/MaxPool_5a_3x3',
        'InceptionV3/Mixed_5b',
        'InceptionV3/Mixed_5c',
        'InceptionV3/Mixed_5d',
        'InceptionV3/Mixed_6a',
        'InceptionV3/Mixed_6b',
        'InceptionV3/Mixed_6c',
        'InceptionV3/Mixed_6d',
        'InceptionV3/Mixed_6e']
    pretrained_exclude = [
        'InceptionV3/Mixed_7a',
        'InceptionV3/Mixed_7b',
        'InceptionV3/Mixed_7c',
        'InceptionV3/AuxLogits'
        'InceptionV3/PreLogits',
        'InceptionV3/Logits',
        'InceptionV3/Predictions']

    # PRETRAINED SAVER - For loading pretrained weights on the first run
    pretrained_vars = tf.contrib.framework.get_variables_to_restore(
        include=pretrained_include,
        exclude=pretrained_exclude)
    tf_pretrained_saver = tf.train.Saver(pretrained_vars, name="pretrained_saver")

    # MAIN SAVER - For saving/restoring your complete model
    tf_saver = tf.train.Saver(name="saver")

    # TENSORBOARD - To visialize the architecture
    with tf.variable_scope('tensorboard') as scope:
        tf_summary_writer = tf.summary.FileWriter(TENSORBOARD_DIR, graph=graph)
        tf_dummy_summary = tf.summary.scalar(name="dummy", tensor=1)


def initialize_vars(session):
    # INITIALIZE VARS
    if tf.train.checkpoint_exists(SNAPSHOT_FILE):
        print("Loading from Main Checkpoint")
        tf_saver.restore(session, SNAPSHOT_FILE)
    else:
        print("Initializing from Pretrained Weights")
        session.run(tf.global_variables_initializer())
        tf_pretrained_saver.restore(session, PRETRAINED_SNAPSHOT_FILE)

def load_data_path():

    class_path = P_CLASS_PATH
    for folder in os.listdir(class_path):
        for file in glob.glob(class_path + folder + '/frame_*'):
            X_train.append(file)
            Y_train.append(0)
            # img = cv2.imread(file)
            # img = cv2.resize(img, (299, 299), interpolation=cv2.INTER_LINEAR)
            # X_train.append(img)
            # Y_train.append(0)

    class_path = N_CLASS_PATH
    for folder in os.listdir(class_path):
        for file in glob.glob(class_path + folder + '/frame_*'):
            X_train.append(file)
            Y_train.append(1)
            # img = cv2.imread(file)
            # img = cv2.resize(img, (299, 299), interpolation=cv2.INTER_LINEAR)
            # X_train.append(img)
            # Y_train.append(1)

def load_images(begin, end):
    aux_file = []
    aux_label = []

    for file in range(begin, end):
        if end > len(X_train):
            end = len(X_train)

        img = cv2.imread(X_train[file])
        img = cv2.resize(img, (299, 299), interpolation=cv2.INTER_LINEAR)
        aux_file.append(img)
        aux_label.append(Y_train[file])


    return aux_file, aux_label

X_train = []
Y_train = []

load_data_path()

print(len(X_train), ' entries ', len(Y_train), ' labels')

with tf.Session(graph=graph) as sess:
    ops = sess.graph.get_operations()
    for op in ops:
        print(op)

    n_epochs = 1
    print_every = 20
    batch_size = 10 # small batch size so inception v3 can be run on laptops
    steps_per_epoch = len(X_train)//batch_size

    initialize_vars(session=sess)

    for epoch in range(n_epochs):
        print("----------------------------------------------")
        print("EPOCH {}/{}".format(epoch+1, n_epochs))
        print("----------------------------------------------")
        for step in range(steps_per_epoch):
            # EXTRACT A BATCH OF TRAINING DATA
            X_batch, Y_batch = load_images(batch_size*step, batch_size*(step+1))
            # X_batch = X_train[batch_size*step: batch_size*(step+1)]
            # Y_batch = Y_train[batch_size*step: batch_size*(step+1)]

            # RUN ONE TRAINING STEP - feeding batch of data
            feed_dict = {tf_X: X_batch,
                         tf_Y: Y_batch,
                         tf_alpha:0.0001,
                         tf_is_training: True}
            loss, _ = sess.run([tf_loss, tf_train_op], feed_dict=feed_dict)

            # PRINT FEED BACK - once every `print_every` steps
            if (step+1)%print_every == 0:
                print("STEP: {: 4d}  LOSS: {:0.4f}".format(step, loss))

        # SAVE SNAPSHOT - after each epoch
        tf_saver.save(sess, SNAPSHOT_FILE)
