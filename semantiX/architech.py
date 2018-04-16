import h5py
import numpy as np
from keras.models import Model, Sequential
from keras.layers import Convolution2D, MaxPooling2D, Flatten, Activation, \
                         Dense, Dropout, ZeroPadding2D
from keras import backend as K
K.set_image_dim_ordering('th')

''' This code is based on Núñez-Marcos, A., Azkune, G., & Arganda-Carreras, 
    I. (2017). "Vision-Based Fall Detection with Convolutional Neural Networks"
    Wireless Communications and Mobile Computing, 2017.
    Also, new features were added by Gabriel Pellegrino Silva working in 
    Semantix. 
'''

''' Documentation: class Architech
    
    This class has only one method:

    weight_init

    The methods that should be called outside of this class are:

    weight_init: receives as parameter a 

'''

class Architech: 

    def __init__(self, name, num_features, x_size, y_size):
        '''
        Input: TODO
        Output: TODO
        '''

        self.name = name
        self.model = None
        self.layers_name = []
        self.num_features = num_features
        self.x_size = x_size
        self.y_size = y_size

        if name == 'VGG16':
            self.layers_name = ['conv1_1', 'conv1_2', 'conv2_1', 'conv2_2', 
                    'conv3_1', 'conv3_2', 'conv3_3', 'conv4_1', 'conv4_2', 
                    'conv4_3', 'conv5_1', 'conv5_2', 'conv5_3', 'fc6', 'fc7', 
                    'fc8']
            self.model = Sequential()

            self.model.add(ZeroPadding2D((1, 1), input_shape=(20, self.x_size, 
                           self.y_size)))
            self.model.add(Convolution2D(64, (3, 3), activation='relu', 
                           name='conv1_1'))
            self.model.add(ZeroPadding2D((1, 1)))
            self.model.add(Convolution2D(64, (3, 3), activation='relu', 
                           name='conv1_2'))
            self.model.add(MaxPooling2D((2, 2), strides=(2, 2)))

            filters = [128, 256, 512, 512]
            layer_p = 2
            for num_filters in filters: 
                layer = self.layers_name[layer_p]
                self.model.add(ZeroPadding2D((1, 1)))
                self.model.add(Convolution2D(num_filters, (3, 3), 
                               activation='relu', name=layer))
                layer_p += 1
                self.model.add(ZeroPadding2D((1, 1)))
                layer = self.layers_name[layer_p]
                self.model.add(Convolution2D(num_filters, (3, 3),
                               activation='relu', name=layer))
                layer_p += 1
                self.model.add(MaxPooling2D((2, 2), strides=(2, 2)))

            self.model.add(Flatten())
            self.model.add(Dense(self.num_features, name='fc6', 
                kernel_initializer='glorot_uniform'))

    def weight_init(self, weights_file):
        '''
        Input:
        * weights_file: path to a hdf5 file containing weights and biases to a
        trained network
        
        Output: TODO
        '''

        h5 = h5py.File(weights_file)
        
        layer_dict = dict([(self.layers_name, layer) 
                            for layer in self.model.layers])

        # Copy the weights stored in the 'weights_file' file to the feature 
        # extractor part of the CNN architecture
        for layer in self.layers_name[:-3]:
            w2, b2 = h5['data'][layer]['0'], h5['data'][layer]['1']
            w2 = np.transpose(np.asarray(w2), (3,2,1,0))
            w2 = w2[::-1, ::-1, :, :]
            b2 = np.asarray(b2)
            K.set_value(layer_dict[layer].kernel, w2)
            K.set_value(layer_dict[layer].bias, b2)
          
        # Copy the weights of the first fully-connected layer (fc6)
        layer = self.layers_name[-3]
        w2, b2 = h5['data'][layer]['0'], h5['data'][layer]['1']
        w2 = np.transpose(np.asarray(w2), (1,0))
        b2 = np.asarray(b2)
        K.set_value(layer_dict[layer].kernel, w2)
        K.set_value(layer_dict[layer].bias, b2)

