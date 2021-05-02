import json
import os
import pandas as pd

class reading_components:

    @staticmethod
    def config_json(filename):
        # filename = os.path.basename(__file__).split(".")[0] + ".json"
        for files in os.listdir(os.getcwd()):
            if files == filename:
                json_file = open(os.path.join(os.getcwd(), filename))
                data = json.load(json_file)
                data = data["trading_parameters"]
                return data


    def read_files(self, data_path):
        """
        :param data_path: string [file path]
        :return: dataframe
        """

        self.path= data_path
        file_extention = os.path.join(os.getcwd(),self.path).split(".")[-1]
        if file_extention == "csv":
            df=pd.read_csv(os.path.join(os.getcwd(),self.path))
        elif file_extention == "xlsx":
            df= pd.read_excel(os.path.join(os.getcwd(),self.path))
        return df

if __name__=="__main__":
    c= reading_components()
    c.config_json()