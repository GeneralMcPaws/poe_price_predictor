# Price prediction and forecasting for items in the online game Path of Exile using Machine and Deep Learning methods

LSTM built using the Keras Python package to predict time series steps and sequences. Includes sine wave and stock market data.

[Diploma Thesis paper written on the project](http://bit.ly/2WGUu74)

## Requirements

* Python 3.6.x
* TensorFlow 1.12.0
* Numpy 1.15.4
* Keras 2.2.4
* Matplotlib 2.2.2
* Seaborn 0.9.0
* Scikit-learn 0.20.2
* Scipy 1.2.0


## Description
For my diploma thesis i analysed the item transactions of the online game Path of Exile using Machine Learning and Deep Learning. The project consisted of digesting the API feed of the game, creating the dataset of transactions of items to use and finally analysing it. 
The dataset was split into two types of items. The first was analysed using LSTM techniques as a stock price and i forecasted the future momentum of the price of specific unique, in name and features, items. The second dataset, consisted of a observations with a variable number of features and my goal was to predict the price of an item given the features it had.


**Technologies used:** Python, Jupyter Notebooks


The architecture consists of :

**Data Pipeline**

* **Digesting the API feed** and processing it. Going through the whole ETL procedure, the data was extracted from the api feed, it was transformed to be loaded into a document based database and then loaded into it.

* **Feature engineering** which was paramount for the conversion of the dataset to a time series one and for better results.

* **Creating the dataset.** The scraping of multiple websites was important to get the required information to create the dataset. 

* **Storing the dataset.** The feed schema was highly nested so MongoDB was chosen as storage for the final processed 

**Machine Learning Pipeline**

* **Feature engineering** using domain knowledge as well as partial dependence of features to the price of an item. 

* **Feature Selection** using sklearn library’s RFE,Random Forest etc and machine learning algorithms like Linear Regression and K-Means.


* **Outlier Removal** either by using z-score or IQR methods.

* **Converting irregular time series dataset to regular** using interpolation techniques with the help of the pandas’ library methods.

* **Analysing the dataset of unique items with LSTM,** dealing with the price of the items like it is a stock price. After converting the dataset to a time series one and training a machine learning agent with LSTM layers on a starting test set of the dataset, i was able to use the same model to forecast the changes of the price of the items for a specific time sequence length in the future.

* **Analysing the dataset of observations with a variable number of features,** to predict the price of an item knowing its features. The approach was mainly via Regression but also by converting the problem to a Classification one with price ranges instead of specific prices.

* **Ensemble Learning** to produce better results in the Regression approach.

* **Using GridSearch and K-fold cross validation** to optimise the machine learning models.
