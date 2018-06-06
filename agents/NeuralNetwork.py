import math
import numpy
from keras.models import Sequential
from keras.layers import Dense, Activation, Flatten
from keras.optimizers import SGD
from keras.callbacks import Callback
from keras import backend as K
import os


class NeuralNetwork():
    def __init__(self, nInputs, nOutputs, depth, width, epochs, opponent_race, model_type):
        self.nInputs = nInputs
        self.nOutputs = nOutputs
        self.epochs = epochs

        # Make logs directory if it doesn't exist
        if not os.path.exists("./models"):
            os.mkdir("./models")

        if opponent_race == 1:
            self.fileName = "./models/terran_" + model_type + "_model_{0}{1}{2}{3}".format(nInputs,nOutputs,depth,width)
        elif opponent_race == 2:
            self.fileName = "./models/zerg_" + model_type + "_model_{0}{1}{2}{3}".format(nInputs,nOutputs,depth,width)
        else:
            self.fileName = "./models/protoss_" + model_type + "_model_{0}{1}{2}{3}".format(nInputs,nOutputs,depth,width)
        # self.fileName = "model_{0}{1}{2}{3}".format(nInputs,nOutputs,depth,width)
        self.model = Sequential()
        for i in range(depth):
            self.model.add(Dense(math.floor(nInputs * width), input_dim=nInputs, kernel_initializer='random_uniform'))
            self.model.add(Activation('sigmoid'))
        self.model.add(Dense(nOutputs, kernel_initializer='random_uniform'))
        self.model.add(Activation('sigmoid'))
        sgd = SGD(lr=.1)
        self.model.compile(optimizer=sgd, loss='mean_squared_error')

    def train(self, inputs, outputs):
        self.model.fit(numpy.array(inputs), numpy.array(outputs), epochs=self.epochs, verbose=0)

    def predict(self, inputs):
        return self.model.predict(numpy.array(inputs))

    def saveWeights(self):
        try:
            self.model.save_weights(self.fileName)
        except:
            print("failed to save weights")
            pass

    def loadWeights(self):
        try:
            self.model.load_weights(self.fileName)
        except:
            print("failed to load weights")
            pass
#Example run of our neural network with specified inputs and outputs
#This neural network has input width 2, output width 2, depth of 1, neural width of input width * 2, and runs for 10000 epochs
#We can see that the inputs must be arrays of arrays, and must be normalized
#Even though this NN uses a sigmoid activation function, it still can predict linear results well
if __name__ == '__main__':
    network = NeuralNetwork(2,2,1,2,10000, 1, "test")
    network.loadWeights()
    inputs = [[2,1],[4,1],[16,8],[21,11]]
    outputs=[[1,2],[3,4],[8,16],[10,21]]
    maxin = [max(a[i] for a in inputs) for i in range(len(inputs[0]))]
    minin = [min(a[i] for a in inputs) for i in range(len(inputs[0]))]
    maxout = [max(a[i] for a in outputs) for i in range(len(outputs[0]))]
    minout = [min(a[i] for a in outputs) for i in range(len(outputs[0]))]
    #Normalize with (x - min)/(max-min) to bring to a range from 0 to 1
    normalizedInputs = [[(inputs[j][i] - minin[i])/(maxin[i]-minin[i]) for i in range(len(inputs[0]))] for j in range(len(inputs))]
    normalizedOutputs = [[(outputs[j][i] - minout[i])/(maxout[i]-minout[i]) for i in range(len(outputs[0]))] for j in range(len(outputs))]
    print(normalizedInputs)
    print(normalizedOutputs)
    print(network.predict(normalizedInputs))
    network.train(normalizedInputs, normalizedOutputs)
    predY = network.predict(normalizedInputs)
    deNormalized = [[(predY[j][i] * (maxout[i]-minout[i]) + minout[i]) for i in range(len(predY[0]))] for j in range(len(predY))]
    print(deNormalized)
    network.saveWeights()
