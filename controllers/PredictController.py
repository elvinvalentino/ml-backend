import numpy as np
import pandas as pd
import os
import pickle
import joblib
import sys
from sklearn.preprocessing import StandardScaler
from datetime import datetime, timedelta
import holidays
from json import loads
from flask import request


class PredictController:
    @staticmethod
    def index():
        try:
            data = PredictController.predict(
                start_date=request.json["startDate"], end_date=request.json["endDate"]
            )

            return {"success": True, "data": data}
        except (IOError, FileNotFoundError, pickle.PickleError) as e:
            return {"success": False, "message": f"Error loading model: {e}"}, 503
        # except:
        #     return {"message": f"Something when wrong"}, 503

    @staticmethod
    def predict(start_date, end_date):
        le_nama = joblib.load(
            open(
                os.path.join(
                    os.path.dirname(__file__), "..", "assets", "leNama.joblib"
                ),
                "rb",
            )
        )

        le_unit = joblib.load(
            open(
                os.path.join(
                    os.path.dirname(__file__), "..", "assets", "leUnit.joblib"
                ),
                "rb",
            )
        )

        dfItems = pd.read_excel(
            open(
                os.path.join(
                    os.path.dirname(__file__), "..", "assets", "master_data_item.xls"
                ),
                "rb",
            )
        )

        dfItems = dfItems.drop(
            ["SPACE", "ID", "SKU", "CURRENCY", "PER", "QUANTITY"], axis=1
        )

        def weekend_or_weekday(year, month, day):
            d = datetime(year, month, day)
            if d.weekday() > 4:
                return 1
            else:
                return 0

        # Adding holdiays in a separate columnn - For Indonesia
        def is_holiday(x):
            indonesia_holidays = holidays.country_holidays("ID")

            if indonesia_holidays.get(x):
                return 1
            else:
                return 0

        names = list(le_nama.classes_)
        date_list = []
        item_list = []
        current_date = datetime.strptime(start_date, "%Y-%m-%d")

        while current_date <= datetime.strptime(end_date, "%Y-%m-%d"):
            date_list.append(
                [
                    current_date.strftime("%Y-%m-%d"),
                    weekend_or_weekday(
                        current_date.year, current_date.month, current_date.day
                    ),
                    is_holiday(current_date),
                    np.sin(current_date.month * (2 * np.pi / 12)),
                    np.cos(current_date.month * (2 * np.pi / 12)),
                    datetime(
                        current_date.year, current_date.month, current_date.day
                    ).weekday(),
                ]
            )
            current_date += timedelta(days=1)

        rows = []
        box = []
        for name in names:
            dfItem = dfItems[dfItems["NAME"] == name.strip()]
            dfItem = dfItem.iloc[0]

            if dfItem["UNIT"] == "BOX":
                box.append(name)
            item_list.append([name, dfItem["UNIT"], dfItem["PRICE"], dfItem["PRICE"]])

        for date in date_list:
            for item in item_list:
                rows.append(item + date)

        df = pd.DataFrame(
            rows,
            columns=[
                "Nama",
                "Unit",
                "Harga Per Item",
                "Total",
                "Tanggal",
                "Weekend",
                "Hari Libur",
                "M1",
                "M2",
                "Hari",
            ],
        )
        df["Nama"] = le_nama.transform(df["Nama"])
        df["Unit"] = le_unit.transform(df["Unit"])

        df["Tanggal"] = pd.to_datetime(df["Tanggal"])
        df["Tanggal"] = df["Tanggal"].astype(str)
        parts = df["Tanggal"].str.split("-", n=3, expand=True)
        df["Tahun"] = parts[0].astype("int")
        df["Bulan"] = parts[1].astype("int")
        df["Di Tanggal"] = parts[2].astype("int")

        df_backup = df[["Tanggal", "Tahun"]].copy()
        df.drop(["Tanggal", "Tahun"], axis=1, inplace=True)

        model_path = os.path.join(
            os.path.dirname(__file__), "..", "assets", "model.pkl"
        )
        model = joblib.load(open(model_path, "rb"))
        scaler = StandardScaler()
        df_scaled = scaler.fit_transform(df)
        pred_Y = model.predict(df_scaled)

        df["Nama"] = le_nama.inverse_transform(df["Nama"])
        df["Unit"] = le_unit.inverse_transform(df["Unit"])
        df["Quantity"] = pred_Y
        df["Quantity"] = df["Quantity"].round()
        df["Tanggal"] = df_backup["Tanggal"]
        df["Tahun"] = df_backup["Tahun"]

        # df_grouped = df.groupby(
        #     [df["Nama"], df["Bulan"], df["Tahun"], df["Harga Per Item"]]
        # ).aggregate({"Quantity": "sum"})
        # df_grouped.reset_index(inplace=True)
        # df_grouped_sorted = df_grouped.sort_values(
        #     by=["Tahun", "Bulan"], ascending=True
        # )

        return loads(
            df[
                [
                    "Nama",
                    "Harga Per Item",
                    "Quantity",
                    "Di Tanggal",
                    "Bulan",
                    "Tahun",
                    "Tanggal",
                    "Hari",
                    "Weekend",
                    "Hari Libur",
                ]
            ].to_json(orient="records")
        )
