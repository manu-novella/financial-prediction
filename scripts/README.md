# Scripts

This directory contains the scripts that define the main logic of this project. It currently contains 1 helper file and 6 main files.

- ```db.py```: helper file that serves as an interface to the secrets used for connecting to the database.

- ```asset_price_etl.py```: connects to Alphavantage API to retrieve the stock market data that later saves to the database. The assets whose data is fetched, such as stocks, are defined beforehand in the database.

- ```sentiment_sources_etl.py```: connects to Yahoo Finance RSS to extract news in which assets of interest are mentioned. Uses NLP techniques to improve the detection of mentions of such assets. The assets whose data is fetched, such as stocks, are defined beforehand in the database.

- ```technical_analysis_etl.py```: extracts from the database the historical market value of stored assets and calculates metrics of technical analysis. Stores the results in the database.

- ```sentiment_analysis_etl.py```: extracts from the database the news where assets of interest are mentioned and calculates the sentiment with help of an ML model specialized in financial news. Stores the results in the database.

- ```feature_matrix_build.py```: aggregates the technical and sentiment analysis data in a single table. The sentiment analysis results are aggregated per date and asset and are only considered if their confidence score is high. The variable to predict via ML methods, involving the price of an asset for the next day, is then computed so a model can later be trained on it. The resulting matrix is stored in the database.

- ```model_training.py```: loads the feature matrix and shapes its data in a way an LSTM neural network can be trained on it, by means of creating temporal sequences in a rolling window fashion. It then build the LSTM, trains it, evaluates the model performance and stores the model in a local directory for future deployment.


The temporal dependences of the execution of these files are reflected in the file ```dags/main_dag.py```. They should be run in the following order:

1. ```asset_price_etl.py``` and ```sentiment_sources_etl.py```, which are independent of each other. These scripts retrieve the project's source data.

2. ```technical_analysis_etl.py``` and ```sentiment_analysis_etl.py```, which again are independent. These scripts analyze the previously retrieved data.

3. ```feature_matrix_build.py```. This script joins the two types of data.

4. ```model_training.py```. This script trains a model on the unified data.