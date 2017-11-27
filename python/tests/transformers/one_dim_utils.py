"""
Utility methods for working with Keras & Tensorflow models that operate on 1D inputs, specifically:
* Loading 1D Keras/TF models, persisting them to disk
* Loading input data for 1D Keras/TF models.
* Transforming data directly with 1D Keras/TF models (i.e. not using the DLP APIs).

"""

import numpy as np
from keras.models import load_model

# Methods for getting some test data to work with.


def executeKerasImdb(seq_df, model_file, seq_col="inputCol", id_col="id"):
    """
    Apply Keras IMDB sequence-classification model on input DataFrame (without using DLP APIs)
    :param seq_df: Dataset. contains a column (seq_col) of tokenized sequences.
    :param seq_col: str. Input column name.
    :return: numpy array of predictions, sorted by row ID
    """
    # Load keras model from disk
    model = load_model(model_file)
    # Collect dataframe, sort rows by ID column
    rows = seq_df.select(seq_col).collect()
    rows.sort(key=lambda row: row[id_col])
    # Get numpy array (num_examples, num_features) containing input data
    x_predict = np.array([row[seq_col] for row in rows])
    return model.predict(x_predict)

def getImdbKerasModel():
    """
    Build and return keras model for (binary) sentiment classification on IMDB 1D text data:
    https://github.com/fchollet/keras/blob/master/examples/imdb_cnn.py

    TODO(sid): Check correctness
    NOTE: The returned model may have different (randomly-initialized) weights each time this method
    is called.
    """
    model = Sequential()
    # we start off with an efficient embedding layer which maps
    # our vocab indices into embedding_dims dimensions
    model.add(Embedding(max_features,
                        embedding_dims,
                        input_length=maxlen))
    model.add(Dropout(0.2))

    # we add a Convolution1D, which will learn filters
    # word group filters of size filter_length:
    model.add(Conv1D(filters,
                     kernel_size,
                     padding='valid',
                     activation='relu',
                     strides=1))
    # we use max pooling:
    model.add(GlobalMaxPooling1D())

    # We add a vanilla hidden layer:
    model.add(Dense(hidden_dims))
    model.add(Dropout(0.2))
    model.add(Activation('relu'))

    # We project onto a single unit output layer, and squash it with a sigmoid:
    model.add(Dense(1))
    model.add(Activation('sigmoid'))
    return model

def prepImdbKerasModelFile(fileName):
    """
    Saves (to specified file name) a keras model for (binary) sentiment classification
    on IMDB 1D text data:
    https://github.com/fchollet/keras/blob/master/examples/imdb_cnn.py
    """
    model = getImdbKerasModel()
    model_dir_tmp = tempfile.mkdtemp("sparkdl_keras_tests", dir="/tmp")
    path = model_dir_tmp + "/" + fileName
    model.save(path)
    return path


class ImdbDatasetOutputComparisonTestCase(unittest.TestCase):
    """
    Methods for making comparisons between outputs of using different frameworks.
    For IMDB text dataset.
    """
    def loadOneDimInputData(self, max_features=5000, maxlen=400):
        """
        Load IMDB text-classification dataset, returning a tuple of tuples
        ((x_train, y_train), (x_test, y_test))
        Code from https://github.com/fchollet/keras/blob/master/examples/imdb_cnn.py
        """
        print('Loading data...')
        (x_train, y_train), (x_test, y_test) = imdb.load_data(num_words=max_features)
        print(len(x_train), 'train sequences')
        print(len(x_test), 'test sequences')

        print('Pad sequences (samples x time)')
        x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
        x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
        return ((x_train, y_train), (x_test, y_test))

    def getImdbDataframes(self, sqlContext):
        ((x_train, y_train), (x_test, y_test)) = self.loadOneDimInputData()
        train_rows = [{'id' : i, 'features' : x_train[i], 'label' : y_train[i]} for i in range(len(x_train))]
        test_rows = [{'id' : i, 'features' : x_test[i], 'label' : y_test[i]} for i in range(len(x_test))]
        train_df = sqlContext.createDataFrame(train_rows)
        test_df = sqlContext.createDataFrame(test_rows)
        return (train_df, test_df)

    def transformOutputToComparables(self, collected, id_col, output_col):
        """
        Returns a list of model predictions ordered by row ID
        params:
        :param collected: Output (DataFrame) of KerasTransformer.transform()
        :param id_col: Column containing row ID
        :param output_col: Column containing transform() output
        """
        collected.sort(key=lambda row: row[id_col])
        return [row[output_col][0] for row in collected]
