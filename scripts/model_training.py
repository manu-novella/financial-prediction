import os
import pandas as pd
import psycopg2
import numpy as np
from datetime import datetime
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, InputLayer, Dropout
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score
from sklearn.preprocessing import MinMaxScaler

from db import get_db_params


def load_feature_matrix() -> pd.DataFrame:
    '''Extract precomputed feature matrix from DB.'''

    print('Extracting feature matrix from database...')

    params =                get_db_params()
    feature_matrix_tbl =    params['feature_matrix']
    assets_price_tbl =      params['assets_price']
    db_conn_params =        params['db_conn']

    columns_of_prices = ['p.open', 'p.close', 'p.high', 'p.low', 'p.volume']
    columns_of_matrix = ['m.ticker', 'm.date', 'm.sma_10', 'm.sma_20', 'm.ema_10', 'm.ema_20', 'm.rsi_14',
                         'm.daily_return', 'm.volume_sma_10', 'm.sentiment_score', 'm.next_day_up'
    ]

    select_query = f'''SELECT {', '.join(columns_of_prices + columns_of_matrix)}
                        FROM {feature_matrix_tbl} m
                        LEFT JOIN {assets_price_tbl} p
                        ON m.ticker = p.ticker
                        AND m.date = p.date
                        WHERE m.ticker = 'SPY'
                        ORDER BY ticker, date;
    '''

    try:
        with psycopg2.connect(**db_conn_params) as conn:
            with conn.cursor() as cur:
                cur.execute(select_query)
                conn.commit()
                records = cur.fetchall()
    except psycopg2.Error as e:
        print(f'Database error: {e}')

    matrix = pd.DataFrame(records, columns=columns_of_prices + columns_of_matrix)

    return matrix


def get_train_test_split(matrix: pd.DataFrame, sequence_length: int =10) -> tuple:
    '''Create sequences and splits into train/val/test sets.'''

    print('Computing train/test split...')

    features_of_prices = ['p.open', 'p.close', 'p.high', 'p.low', 'p.volume']
    features_of_matrix = ['m.sma_10', 'm.sma_20', 'm.ema_10', 'm.ema_20', 'm.rsi_14',
                          'm.daily_return', 'm.volume_sma_10', 'm.sentiment_score'
    ]

    X_all, y_all = [], []

    for _, group in matrix.groupby('m.ticker'):
        X_seq, y_seq = create_sequences(group, features_of_prices + features_of_matrix, sequence_length)
        X_all.append(X_seq)
        y_all.append(y_seq)

    X = np.concatenate(X_all)
    y = np.concatenate(y_all)

    X_train, X_val, X_test, y_train, y_val, y_test = rolling_window_split(X, y)

    #Scale test set and return scaler for production #!
    '''scaler = MinMaxScaler(feature_range=(0, 1))
    scaler.fit(X_train)
    X_train_scaled = scaler.transform(X_train)
    X_test_scaled = scaler.transform(X_test)'''

    return X_train.astype(np.float64), X_val.astype(np.float64), X_test.astype(np.float64), y_train, y_val, y_test#, scaler


def create_sequences(group: object, features: list, sequence_length: int =10) -> tuple:
    '''Break down the matrix in time-series sequences and return inputs and class.'''

    X, y = [], []

    for i in range(len(group) - sequence_length):
        seq = group[features].iloc[i:i+sequence_length].values
        label = group['m.next_day_up'].iloc[i+sequence_length]
        X.append(seq)
        y.append(label)

    return np.array(X), np.array(y)


def rolling_window_split(X: np.ndarray, y: np.ndarray, train_ratio: float =0.7, val_ratio: float =0.15) -> tuple:
    '''Split X and y into train, validation, and test using time-series order.'''

    n = len(X)
    train_end = int(n * train_ratio)
    val_end = int(n * (train_ratio + val_ratio))

    X_train = X[:train_end]
    y_train = y[:train_end]

    X_val = X[train_end:val_end]
    y_val = y[train_end:val_end]

    X_test = X[val_end:]
    y_test = y[val_end:]

    return X_train, X_val, X_test, y_train, y_val, y_test


def build_LSTM(sequence_length: int, num_features: int) -> object:
    '''Define and build neural network.'''

    print('Setting up LSTM model...')

    model = Sequential([
        InputLayer(input_shape=(sequence_length, num_features)),
        LSTM(90),
        Dropout(0.1),
        Dense(90, activation='relu'),
        Dense(1, activation='sigmoid')
    ])

    adam = Adam(learning_rate=10e-3)

    model.compile(
        optimizer=adam,
        loss='binary_crossentropy',
        metrics=['accuracy']
    )

    return model


def train_model(model: object, X_train: np.ndarray, y_train: np.ndarray, X_val: np.ndarray, y_val: np.ndarray) -> object:
    '''Train LSTM network on matrix data.'''

    print('Training model...')

    epochs = 3#00
    early_stopping_callback = EarlyStopping(patience=epochs / 3, restore_best_weights=True)

    model.fit(X_train, y_train, 
              validation_data=(X_val, y_val),
              epochs=epochs,
              batch_size=64,
              validation_split=0.2,
              callbacks=early_stopping_callback,
              shuffle=False  #Time series mustn't be shuffled
    )

    return model


def evaluate_model(model: object, X_val: np.ndarray, y_val: np.ndarray, X_test: np.ndarray, y_test: np.ndarray):
    '''Evaluate model performance.'''

    #Assess performance with validation set
    y_val_pred = model.predict(X_val).flatten()
    y_val_pred_class = (y_val_pred > 0.5).astype(int)
    print('\nConfusion matrix on validation data\n', confusion_matrix(y_val, y_val_pred_class))
    print('\nClassification report on validation data\n', classification_report(y_val, y_val_pred_class))

    #Further assess model performance with validation set
    accuracy = accuracy_score(y_val, y_val_pred_class)
    precision = precision_score(y_val, y_val_pred_class)
    recall = recall_score(y_val, y_val_pred_class)
    f1 = f1_score(y_val, y_val_pred_class)
    auc = roc_auc_score(y_val, y_val_pred)
    print('\nMetrics on validation data:')
    print('\nAccuracy: ', accuracy, 'Precision: ', precision, 'Recall: ', recall, 'F1: ', f1, 'AUC: ', auc, '\n')

    #Assess model performance with test set
    y_test_pred = model.predict(X_test).flatten()
    y_test_pred_class = (y_test_pred > 0.5).astype(int)
    test_set_accuracy = accuracy_score(y_test, y_test_pred_class)
    print('\nAccuracy on test set: ', test_set_accuracy, '\n')

    #Calculate optimal threshold using validation set
    thresholds = np.linspace(0, 1, 100)
    accuracies = []

    for thresh in thresholds:
        preds = (y_val_pred > thresh).astype(int)
        acc = accuracy_score(y_val, preds)
        accuracies.append(acc)

    best_index = np.argmax(accuracies)
    best_threshold = thresholds[best_index]
    best_accuracy = accuracies[best_index]

    print(f'\nBest threshold: {best_threshold:.3f}', '\n')
    print(f'\nBest accuracy: {best_accuracy:.4f}', '\n')

    #Assess model performance with test set using optimal threshold for validation set
    y_test_pred = model.predict(X_test).flatten()
    y_test_pred_class = (y_test_pred > best_threshold).astype(int)
    final_accuracy = accuracy_score(y_test, y_test_pred_class)
    print('\nAccuracy on test set using best threshold for validation set: ', final_accuracy, '\n')


def save_model(model: object):
    '''Save ML model so it can be used later.'''

    print('Saving model...')

    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(scripts_dir)
    model_dir = os.path.join(parent_dir, 'models')

    model.save(model_dir + '/lstm_model.keras')


def run_model_training():
    start_time = datetime.now()
    print(f'Starting training process at {start_time.strftime("%Y-%m-%d %H:%M:%S")}')

    SEQUENCE_LENGTH = 10

    matrix = load_feature_matrix()
    X_train, X_val, X_test, y_train, y_val, y_test = get_train_test_split(matrix, SEQUENCE_LENGTH)

    num_features = X_train.shape[2]
    lstm = build_LSTM(sequence_length=SEQUENCE_LENGTH, num_features=num_features)
    lstm = train_model(lstm, X_train, y_train, X_val, y_val)
    evaluate_model(lstm, X_val, y_val, X_test, y_test)
    
    save_model(lstm)

    end_time = datetime.now()
    print(f'Model Training finished at {end_time.strftime("%Y-%m-%d %H:%M:%S")}')
    elapsed_time = end_time - start_time
    print(f'Elapsed time: {elapsed_time.seconds // 60} minutes and {elapsed_time.seconds % 60} seconds')


if __name__ == '__main__':
    run_model_training()