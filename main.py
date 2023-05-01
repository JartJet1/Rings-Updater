import sys
import os
import requests
import json
import time
import re
import ijson
import threading
from PyQt5.QtCore import Qt, QRect, QPoint, QRectF, QTimer
from PyQt5.QtGui import QPixmap, QColor, QBrush, QFont, QPalette, QIcon, QCursor, QRegion, QPainterPath, QBitmap, QPainter
from PyQt5.QtWidgets import QApplication, QLabel, QPushButton, QDesktopWidget, QMainWindow, QVBoxLayout, QFrame

def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError("Unserializable object {} of type {}".format(obj, type(obj)))
def merge_objects(merged_obj):
    with open('output.json', 'rb') as f:
        objects = ijson.items(f, 'item')
        for obj in objects:
            if obj['SystemAddress'] == merged_obj['SystemAddress'] and obj['BodyID'] == merged_obj['BodyID']:
                obj.update(merged_obj)
                yield obj
            else:
                yield obj
class AppClass(QMainWindow):
    def __init__(self):
        super().__init__()
        with open("files.txt", "r") as f:
            self.dataold = f.read()
        palette = self.palette()
        palette.setBrush(QPalette.Background, QBrush(QPixmap("bg.png")))
        self.setWindowIcon(QIcon('Rings.ico'))
        self.setPalette(palette)
        self.setWindowTitle("Rings Updater v1.0.0")
        self.setGeometry(0, 0, 800, 450)
        self.center()
        self.setWindowFlag(Qt.FramelessWindowHint)
        radius = 3
        path = QPainterPath()
        path.addRoundedRect(QRectF(self.rect()), radius, radius)
        mask = QBitmap(self.size())
        mask.clear()
        painter = QPainter(mask)
        painter.setRenderHint(QPainter.HighQualityAntialiasing)
        painter.setBrush(Qt.black)
        painter.drawPath(path)
        painter.end()
        region = QRegion(mask)
        self.setMask(region)
        self.frame = QFrame(self)
        self.frame.setFrameShape(QFrame.NoFrame)
        self.frameLayout = QVBoxLayout(self.frame)

        self.label = QLabel("Press the button")
        self.label.setFont(QFont("Arial", 12))
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("color: white; background-color: rgba(0,0,0,0.5); border-radius: 5px; padding:5 10px;")

        self.frameLayout.addWidget(self.label)
        self.frameLayout.setAlignment(Qt.AlignCenter)

        self.setCentralWidget(self.frame)
        self.button = QPushButton(self)
        self.button.setGeometry(QRect(250, 250, 300, 30))
        self.button.setStyleSheet("border: none; border-radius: 5px; background-color: #3ab542; color: white; font-size: 12px;")
        self.button.setText("Press to start log upload")
        self.button.setCursor(QCursor(Qt.PointingHandCursor))
        self.button.enterEvent = lambda event: self.button.setStyleSheet('border: none; border-radius: 5px; background-color: #319437; color: white; font-size: 12px;')
        self.button.leaveEvent = lambda event: self.button.setStyleSheet('border: none; border-radius: 5px;  background-color: #3ab542; color: white; font-size: 12px;')
        self.button.clicked.connect(lambda: self.print_message())
    def update_text(self):
        file_name = ""
        while True:
            with open("files.txt", "r") as f:
                self.dataold = f.read()
            folder_path = os.path.expanduser('~/Saved Games/Frontier Developments/Elite Dangerous')
            folder_path = folder_path.replace('%username%', os.getlogin())
            file_names = [f for f in os.listdir(folder_path) if "Journal" in f and f.endswith(".log")]
            with open("files.txt", "r") as f:
                content = f.read()
            for file_name in file_names[:]:
                pattern = re.compile(file_name)
                if pattern.search(content):
                    file_names.remove(file_name)
            x = 5
            new_objects = []
            num_objects = len(file_names)
            self.label.setText("Searching logs")
            if num_objects <= x:
                for file_name in file_names:
                    if os.path.getsize(os.path.join(folder_path, file_name)) == 0:
                        with open("files.txt", "a") as f:
                            f.write(file_name + "\n")
                    else:
                        gameversionstatus = False
                        with open(os.path.join(folder_path, file_name), "r", encoding="utf-8") as file:
                            text = file.read()
                            for line in text.splitlines()[:1]:
                                line = ""+line+""
                                try:
                                    linedata = json.loads(line)
                                except json.JSONDecodeError as e:
                                    continue
                                else:
                                    if "gameversion" in linedata:
                                        gameversion = linedata["gameversion"]
                                        if gameversion.startswith("4"):
                                            gameversionstatus = True
                                            break
                            for line in text.split('\n'):
                                if line.strip():
                                    if gameversionstatus == True:
                                        try:
                                            line_data = json.loads(line)
                                        except json.JSONDecodeError as e:
                                            continue
                                        else:
                                            obj = json.loads(line.strip())
                                            if 'Rings' in obj or 'StarPos' in obj or 'Signals' in obj or 'ProbesUsed' in obj:
                                                if obj.get('event') == 'Scan' or obj.get('event') == 'SAASignalsFound' or obj.get('event') == 'SAAScanComplete' or obj.get('event') == 'Location' or obj.get('event') == 'FSDJump':
                                                    if obj.get('event') == 'SAAScanComplete':
                                                        obj['Detailed'] = True
                                                    if 'event' in obj and obj['event'] == 'SAAScanComplete' and 'BodyName' in obj and 'A Ring' not in obj['BodyName'] and 'B Ring' not in obj['BodyName']:
                                                        continue
                                                    obj.pop('FuelLevel', None)
                                                    obj.pop('FuelUsed', None)
                                                    obj.pop('JumpDist', None)
                                                    obj.pop('Docked', None)
                                                    obj.pop('Taxi', None)
                                                    obj.pop('EfficiencyTarget', None)
                                                    obj.pop('ProbesUsed', None)
                                                    obj.pop('SRV', None)
                                                    obj.pop('In SRV', None)
                                                    obj.pop('BoostUsed', None)
                                                    obj.pop('OnStation', None)
                                                    obj.pop('OnPlanet', None)
                                                    obj.pop('Multicrew', None)
                                                    obj.pop('RemainingJumpsInRoute', None)
                                                    obj.pop('ID', None)
                                                    if 'StationType' in obj:
                                                        continue
                                                    if 'Body' in obj:
                                                        obj['BodyName'] = obj['Body']
                                                        obj.pop('Body', None)
                                                    if 'StarClass' in obj:
                                                        obj['StarType'] = obj['StarClass']
                                                        obj.pop('ScanType', None)
                                                    if 'SystemEconomy_Localised' in obj:
                                                        obj['SystemEconomy'] = obj['SystemEconomy_Localised']
                                                        obj.pop('SystemEconomy_Localised', None)
                                                    if 'SystemSecondEconomy_Localised' in obj:
                                                        obj['SystemSecondEconomy'] = obj['SystemSecondEconomy_Localised']
                                                        obj.pop('SystemSecondEconomy_Localised', None)
                                                    if 'SystemGovernment_Localised' in obj:
                                                        obj['SystemGovernment'] = obj['SystemGovernment_Localised']
                                                        obj.pop('SystemGovernment_Localised', None)
                                                    if 'SystemSecurity_Localised' in obj:
                                                        obj['SystemSecurity'] = obj['SystemSecurity_Localised']
                                                        obj.pop('SystemSecurity_Localised', None)
                                                    if 'Factions' in obj:
                                                        dataFactions = obj['Factions']
                                                        for Faction in dataFactions:
                                                            if 'Happiness_Localised' in Faction:
                                                                Faction['Happiness'] = Faction['Happiness_Localised']
                                                                Faction.pop('Happiness_Localised', None)
                                                    signaltrue = True
                                                    if 'Signals' in obj:
                                                        data3 = obj['Signals']
                                                        for signal in data3:
                                                            if signal['Type'].startswith('$') or signal['Type'] == "LowTemperatureDiamond" or signal['Type'] == "Opal":
                                                                signal['Type'] = signal['Type_Localised']
                                                                signal.pop('Type_Localised', None)
                                                            elif signal['Type'] == "tritium":
                                                                signal['Type'] = "Tritium"
                                                            if signal['Type'] == 'Thargoid' or signal['Type'] == 'Other' or signal['Type'] == 'Human' or signal['Type'] == 'Guardian' or signal['Type'] == 'Geological' or signal['Type'] == 'Biological':
                                                                signaltrue = False
                                                    if signaltrue == True:
                                                        new_objects.append(obj)
                            if gameversionstatus == True:
                                filetext = "Searching logs: {}".format(file_name)
                                self.label.setText(filetext)
                                with open("files.txt", "a") as f:
                                    f.write(file_name + "\n")
                            else:
                                with open("files.txt", "a") as f:
                                    f.write(file_name + "\n")
                with open('output.json', 'w') as f:
                    json.dump(new_objects, f, indent=4)  
            else:
                num_parts = num_objects // x + (num_objects % x != 0)
                for i in range(num_parts):
                    start_idx = i * x
                    end_idx = (i + 1) * x
                    part_data = file_names[start_idx:end_idx]
                    part_list = list(part_data)
                    for file_name in part_list:
                        if os.path.getsize(os.path.join(folder_path, file_name)) == 0:
                            with open("files.txt", "a") as f:
                                f.write(file_name + "\n")
                        else:
                            gameversionstatus = False
                            with open(os.path.join(folder_path, file_name), "r", encoding="utf-8") as file:
                                text = file.read()
                                for line in text.splitlines()[:1]:
                                    line = ""+line+""
                                    try:
                                        linedata = json.loads(line)
                                    except json.JSONDecodeError as e:
                                        continue
                                    else:
                                        if "gameversion" in linedata:
                                            gameversion = linedata["gameversion"]
                                            if gameversion.startswith("4"):
                                                gameversionstatus = True
                                                break
                                for line in text.split('\n'):
                                    if line.strip():
                                        if gameversionstatus == True:
                                            try:
                                                line_data = json.loads(line)
                                            except json.JSONDecodeError as e:
                                                continue
                                            else:
                                                obj = json.loads(line.strip())
                                                if 'Rings' in obj or 'StarPos' in obj or 'Signals' in obj or 'ProbesUsed' in obj:
                                                    if obj.get('event') == 'Scan' or obj.get('event') == 'SAASignalsFound' or obj.get('event') == 'SAAScanComplete' or obj.get('event') == 'Location' or obj.get('event') == 'FSDJump':
                                                        if obj.get('event') == 'SAAScanComplete':
                                                            obj['Detailed'] = True
                                                        if 'event' in obj and obj['event'] == 'SAAScanComplete' and 'BodyName' in obj and 'A Ring' not in obj['BodyName'] and 'B Ring' not in obj['BodyName']:
                                                            continue
                                                        obj.pop('FuelLevel', None)
                                                        obj.pop('FuelUsed', None)
                                                        obj.pop('JumpDist', None)
                                                        obj.pop('Docked', None)
                                                        obj.pop('Taxi', None)
                                                        obj.pop('EfficiencyTarget', None)
                                                        obj.pop('ProbesUsed', None)
                                                        obj.pop('SRV', None)
                                                        obj.pop('In SRV', None)
                                                        obj.pop('BoostUsed', None)
                                                        obj.pop('OnStation', None)
                                                        obj.pop('OnPlanet', None)
                                                        obj.pop('Multicrew', None)
                                                        obj.pop('RemainingJumpsInRoute', None)
                                                        obj.pop('ID', None)
                                                        if 'StationType' in obj:
                                                            continue
                                                        if 'Body' in obj:
                                                            obj['BodyName'] = obj['Body']
                                                            obj.pop('Body', None)
                                                        if 'StarClass' in obj:
                                                            obj['StarType'] = obj['StarClass']
                                                            obj.pop('ScanType', None)
                                                        if 'SystemEconomy_Localised' in obj:
                                                            obj['SystemEconomy'] = obj['SystemEconomy_Localised']
                                                            obj.pop('SystemEconomy_Localised', None)
                                                        if 'SystemSecondEconomy_Localised' in obj:
                                                            obj['SystemSecondEconomy'] = obj['SystemSecondEconomy_Localised']
                                                            obj.pop('SystemSecondEconomy_Localised', None)
                                                        if 'SystemGovernment_Localised' in obj:
                                                            obj['SystemGovernment'] = obj['SystemGovernment_Localised']
                                                            obj.pop('SystemGovernment_Localised', None)
                                                        if 'SystemSecurity_Localised' in obj:
                                                            obj['SystemSecurity'] = obj['SystemSecurity_Localised']
                                                            obj.pop('SystemSecurity_Localised', None)
                                                        if 'Factions' in obj:
                                                            dataFactions = obj['Factions']
                                                            for Faction in dataFactions:
                                                                if 'Happiness_Localised' in Faction:
                                                                    Faction['Happiness'] = Faction['Happiness_Localised']
                                                                    Faction.pop('Happiness_Localised', None)
                                                        signaltrue = True
                                                        if 'Signals' in obj:
                                                            data3 = obj['Signals']
                                                            for signal in data3:
                                                                if signal['Type'].startswith('$') or signal['Type'] == "LowTemperatureDiamond" or signal['Type'] == "Opal":
                                                                    signal['Type'] = signal['Type_Localised']
                                                                    signal.pop('Type_Localised', None)
                                                                elif signal['Type'] == "tritium":
                                                                    signal['Type'] = "Tritium"
                                                                if signal['Type'] == 'Thargoid' or signal['Type'] == 'Other' or signal['Type'] == 'Human' or signal['Type'] == 'Guardian' or signal['Type'] == 'Geological' or signal['Type'] == 'Biological':
                                                                    signaltrue = False
                                                        if signaltrue == True:
                                                            new_objects.append(obj)
                                if gameversionstatus == True:
                                    filetext = "Searching logs: {}".format(file_name)
                                    self.label.setText(filetext)
                                    with open("files.txt", "a") as f:
                                        f.write(file_name + "\n")
                                else:
                                    with open("files.txt", "a") as f:
                                        f.write(file_name + "\n")
                with open('output.json', 'w') as f:
                    json.dump(new_objects, f, indent=4)
            self.label.setText("Data sorting")
            latest_timestamps = {}
            for obj in new_objects:
                key = (obj['event'], obj['BodyID'], obj['SystemAddress'])
                timestamp = obj['timestamp']
                if key not in latest_timestamps or timestamp > latest_timestamps[key]:
                    latest_timestamps[key] = timestamp
            filtered_data = []
            for obj in new_objects:
                key = (obj['event'], obj['BodyID'], obj['SystemAddress'])
                if obj['timestamp'] == latest_timestamps[key]:
                    filtered_data.append(obj)
            with open('output.json', 'w') as f:
                json.dump(filtered_data, f, indent=4)
            self.label.setText("Data transfer")
            x = 100
            with open("output.json", 'r') as file:
                data = json.load(file)
            num_objects = len(data)
            num = 0
            if num_objects <= x:
                json_data = json.dumps(data)
                headers = {'Content-type': 'application/json'}
                response = None
                while response is None:
                    try:
                        response = requests.post('https://apporsite.com/elitebase/bodies.php', data=json_data, headers=headers, timeout=10)
                        break
                    except requests.exceptions.HTTPError as errh:
                        print("HTTPError")
                        continue
                    except requests.exceptions.ConnectionError as errc:
                        print("ConnectionError")
                        continue
                    except requests.exceptions.Timeout as errt:
                        print("Timeout")
                        continue
                    except requests.exceptions.RequestException as err:
                        print("RequestException")
                        continue
                tekstloop = 'Data transfer, {}'.format(response.text)
                self.label.setText(tekstloop)
            else:
                num_parts = num_objects // x + (num_objects % x != 0)
                for i in range(num_parts):
                    start_idx = i * x
                    end_idx = (i + 1) * x
                    part_data = data[start_idx:end_idx]
                    json_data = json.dumps(part_data)
                    tekstloop = 'Uploading batches of data: {}'.format(num)
                    self.label.setText(tekstloop)
                    headers = {'Content-type': 'application/json'}
                    response = None
                    timet = (int(num) + 1) * 10
                    while response is None:
                        try:
                            response = requests.post('https://apporsite.com/elitebase/bodies.php', data=json_data, headers=headers, timeout=timet)
                            break
                        except requests.exceptions.HTTPError as errh:
                            print("HTTPError")
                            continue
                        except requests.exceptions.ConnectionError as errc:
                            print("ConnectionError")
                            continue
                        except requests.exceptions.Timeout as errt:
                            print("Timeout")
                            continue
                        except requests.exceptions.RequestException as err:
                            print("RequestException")
                            continue
                    tekstloop = 'Uploading batches of data: {}, {}'.format(num, response.text)
                    self.label.setText(tekstloop)
                    num = num + 1
                    time.sleep(30)
            folder_path = os.path.expanduser('~/Saved Games/Frontier Developments/Elite Dangerous')
            folder_path = folder_path.replace('%username%', os.getlogin())
            files = [(f, os.path.getmtime(os.path.join(folder_path, f))) for f in os.listdir(folder_path)]
            pattern = re.compile('.*Journal.*\.log')
            matching_files = [f[0] for f in files if pattern.match(f[0])]
            latest_file = max(matching_files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))

            with open('files.txt', 'r') as f:
                lines = f.readlines()

            with open('files.txt', 'w') as f:
                for line in lines:
                    if not line.strip().endswith(latest_file):
                        f.write(line)
            self.label.setText("End of upload. I'm waiting for the next search")
            time.sleep(900)
    def print_message(self):
        self.button.deleteLater()
        QTimer.singleShot(0, lambda: self.create_new_button())
    def create_new_button(self):
        self.button = QPushButton(self)
        self.button.setGeometry(QRect(250, 250, 300, 30))
        self.button.setStyleSheet("border: none; border-radius: 5px;  background-color: #cc3939; color: white; font-size: 12px;")
        self.button.setText("Press to exit")
        self.button.setCursor(QCursor(Qt.PointingHandCursor))
        self.button.enterEvent = lambda event: self.button.setStyleSheet('border: none; border-radius: 5px; background-color: #7d2323; color: white; font-size: 12px;')
        self.button.leaveEvent = lambda event: self.button.setStyleSheet('border: none; border-radius: 5px;  background-color: #cc3939; color: white; font-size: 12px;')
        self.button.clicked.connect(lambda: self.close_app())
        self.button.show()
        threading.Thread(target=self.update_text).start()
    def close_app(self):
        with open('files.txt', 'w') as f:
            f.write(str(self.dataold))
        dataold = []
        with open("output.json", "w") as f:
            json.dump(dataold, f)
        os._exit(0)
    def center(self):
        screen = QDesktopWidget().screenGeometry()
        self.move((screen.width() - self.width()) // 2, (screen.height() - self.height()) // 2)
    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()
    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()
if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = AppClass()
    ex.show()
    sys.exit(app.exec_())