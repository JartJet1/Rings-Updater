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
def transfer(data, timet, num, self):
    json_data = json.dumps(data)
    tekstloop = 'Uploading batches of data: {}'.format(num)
    self.label.setText(tekstloop)
    headers = {'Content-type': 'application/json'}
    response = None
    while response is None:
        try:
            response = requests.post('https://apporsite.com/elitebase/bodies0.2.php', data=json_data, headers=headers, timeout=timet)
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
    print(response.text)
    tekstloop = 'Uploading batches of data: {}, {}'.format(num, response.text)
    self.label.setText(tekstloop)
def remove_duplicates(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    unique_body_names = set()
    unique_data = []
    for item in data:
        body_name = item.get("RingName")
        if body_name not in unique_body_names:
            unique_body_names.add(body_name)
            unique_data.append(item)
        data = unique_data
        sorted_keys = [
            'SystemName',
            'SystemAddress',
            'SystemPosition',
            'SystemSecurity',
            'ParentBodyName',
            'ParentBodyTypeName',
            'ParentBodyType',
            'ParentBodyClass',
            'RingName',
            'RingDistanceFromArrivalLS',
            'RingTypeName',
            'RingType',
            'RingStateName',
            'RingState',
            'RingHotspots'
        ]
        sorted_data = []
        for obj in data:
            sorted_obj = {key: obj[key] for key in sorted_keys if key in obj}
            sorted_data.append(sorted_obj)

        with open(file_path, 'w') as file:
            json.dump(sorted_data, file, indent=4)
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
def process(file_names, folder_path, self, data):
    for file_path in file_names:
        if os.path.getsize(os.path.join(folder_path, file_path)) == 0:
            with open("files.txt", "a") as f:
                f.write(file_path + "\n")
        else:
            gameversionstatus = False
            p1 = False
            p2 = False
            p3 = False
            p4 = False
            with open(os.path.join(folder_path, file_path), "r", encoding="utf-8") as file:
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
            if gameversionstatus == True:
                with open(os.path.join(folder_path, file_path), "r", encoding="utf-8") as file:
                    for line in file:
                        if '"event":"Scan"' in line:
                            json_data = json.loads(line)
                            body_name = json_data.get('BodyName')
                            if 'A Ring' in body_name or 'B Ring' in body_name:
                                p1 = True
                                try:
                                    line_1 = json.loads(line)
                                except json.JSONDecodeError as e:
                                    continue
                                new_objects = {}
                                with open(os.path.join(folder_path, file_path), "r", encoding="utf-8") as file3:
                                    for line3 in file3:
                                        try:
                                            line_3 = json.loads(line3)
                                        except json.JSONDecodeError as e:
                                            continue
                                        if 'FSDJump' in line3 or 'Location' in line3:
                                            if line_1.get('SystemAddress') == line_3.get('SystemAddress'):
                                                p3 = True
                                                new_objects['SystemPosition'] = line_3.get('StarPos')
                                                new_objects['SystemSecurity'] = line_3.get('SystemSecurity_Localised')
                                with open(os.path.join(folder_path, file_path), "r", encoding="utf-8") as file2:
                                    for line2 in file2:
                                        try:
                                            line_2 = json.loads(line2)
                                        except json.JSONDecodeError as e:
                                            continue
                                        if '"event":"SAA' in line2:
                                            if body_name in line_2.get('BodyName'):
                                                new_objects['SystemName'] = line_1.get('StarSystem')
                                                new_objects['SystemAddress'] = line_1.get('SystemAddress')
                                                result = body_name[:-7].replace(line_1.get('StarSystem'), '')[1:]
                                                result_parts = result.split(" ")
                                                num_parts = len(result_parts)
                                                if num_parts > 0:
                                                    first_part = result_parts[-1]
                                                    is_alpha = first_part.isalpha()
                                                    is_upper = first_part.isupper()
                                                    is_lower = first_part.islower()
                                                    if is_alpha:
                                                        if is_upper:
                                                            new_objects['ParentBodyTypeName'] = "Star"
                                                            new_objects['ParentBodyType'] = 4
                                                        elif is_lower:
                                                            if 'Star' in line_1.get('Parents')[0]:
                                                                new_objects['ParentBodyTypeName'] = "Companion star"
                                                                new_objects['ParentBodyType'] = 3
                                                            else:
                                                                new_objects['ParentBodyTypeName'] = "Moon"
                                                                new_objects['ParentBodyType'] = 1
                                                    else:
                                                        if 'Star' in line_1.get('Parents')[0]:
                                                            new_objects['ParentBodyTypeName'] = "Companion star"
                                                            new_objects['ParentBodyType'] = 3
                                                        else:
                                                            new_objects['ParentBodyTypeName'] = "Planet"
                                                            new_objects['ParentBodyType'] = 2
                                                else:
                                                    new_objects['ParentBodyTypeName'] = "Star"
                                                    new_objects['ParentBodyType'] = 4
                                                new_objects['RingDistanceFromArrivalLS'] = line_1.get('DistanceFromArrivalLS')
                                                if 'Signals' in line2:
                                                    p2 = True
                                                    Signals = line_2.get('Signals')
                                                    for Signal in Signals:
                                                        if Signal.get("Type_Localised") is not None:
                                                            Signal['Type'] = Signal['Type_Localised']
                                                            Signal.pop('Type_Localised', None)
                                                        elif Signal['Type'] == "tritium":
                                                            Signal['Type'] = "Tritium"
                                                        Signal['Count'] = Signal['Count']
                                                        if Signal['Type'] == 'Alexandrite':
                                                            Signal['Type'] = 1
                                                            Signal['TypeName'] = "Alexandrite"
                                                        elif Signal['Type'] == 'Benitoite':
                                                            Signal['Type'] = 2
                                                            Signal['TypeName'] = "Benitoite"
                                                        elif Signal['Type'] == 'Bromellite':
                                                            Signal['Type'] = 3
                                                            Signal['TypeName'] = "Bromellite"
                                                        elif Signal['Type'] == 'Grandidierite':
                                                            Signal['Type'] = 4
                                                            Signal['TypeName'] = "Grandidierite"
                                                        elif Signal['Type'] == 'Low Temp. Diamonds' or Signal['Type'] == 'Low Temperature Diamonds':
                                                            Signal['Type'] = 5
                                                            Signal['TypeName'] = "Low Temperature Diamonds"
                                                        elif Signal['Type'] == 'Monazite':
                                                            Signal['Type'] = 6
                                                            Signal['TypeName'] = "Monazite"
                                                        elif Signal['Type'] == 'Musgravite':
                                                            Signal['Type'] = 7
                                                            Signal['TypeName'] = "Musgravite"
                                                        elif Signal['Type'] == 'Painite':
                                                            Signal['Type'] = 8
                                                            Signal['TypeName'] = "Painite"
                                                        elif Signal['Type'] == 'Platinum':
                                                            Signal['Type'] = 9
                                                            Signal['TypeName'] = "Platinum"
                                                        elif Signal['Type'] == 'Rhodplumsite':
                                                            Signal['Type'] = 10
                                                            Signal['TypeName'] = "Rhodplumsite"
                                                        elif Signal['Type'] == 'Serendibite':
                                                            Signal['Type'] = 11
                                                            Signal['TypeName'] = "Serendibite"
                                                        elif Signal['Type'] == 'Tritium':
                                                            Signal['Type'] = 12
                                                            Signal['TypeName'] = "Tritium"
                                                        elif Signal['Type'] == 'Void Opal':
                                                            Signal['Type'] = 13
                                                            Signal['TypeName'] = "Void Opal"
                                                        else:
                                                            Signals.remove(Signal)
                                                    new_objects['RingHotspots'] = Signals
                                with open(os.path.join(folder_path, file_path), "r", encoding="utf-8") as file4:
                                    for line4 in file4:
                                        try:
                                            line_4 = json.loads(line4)
                                        except json.JSONDecodeError as e:
                                            continue
                                        if line_4.get('event') == 'Scan':
                                            if 'Rings' in line_4:
                                                Rings = line_4.get('Rings')
                                                for Ring in Rings:
                                                    if Ring.get('Name') == line_1.get('BodyName'):
                                                        new_objects['ParentBodyName'] = line_4.get('BodyName')
                                                        new_objects['RingName'] = Ring.get('Name')
                                                        p4 = True
                                                        new_objects['RingStateName'] = line_4.get('ReserveLevel')
                                                        new_objects['RingTypeName'] = Ring.get('RingClass')
                                                        new_objects['ParentBodyClass'] = line_4.get('PlanetClass')
                                                        if not line_4.get('PlanetClass'):
                                                            new_objects['ParentBodyClass'] = "None"
                                                        if new_objects['RingTypeName'] == 'eRingClass_Rocky':
                                                            new_objects['RingType'] = 1
                                                            new_objects['RingTypeName'] = "Rocky"
                                                        elif new_objects['RingTypeName'] == 'eRingClass_MetalRich':
                                                            new_objects['RingType'] = 2
                                                            new_objects['RingTypeName'] = "Metal Rich"
                                                        elif new_objects['RingTypeName'] == 'eRingClass_Icy':
                                                            new_objects['RingType'] = 3
                                                            new_objects['RingTypeName'] = "Icy"
                                                        elif new_objects['RingTypeName'] == 'eRingClass_Metalic':
                                                            new_objects['RingType'] = 4
                                                            new_objects['RingTypeName'] = "Metalic"
                                                        elif new_objects['RingTypeName'] is None:
                                                            new_objects['RingType'] = 0
                                                            new_objects['RingTypeName'] = "None"
                                                        else:
                                                            new_objects['RingType'] = 0
                                                            new_objects['RingTypeName'] = "None"
                                                        if new_objects['RingStateName'] == 'PristineResources':
                                                            new_objects['RingState'] = 5
                                                            new_objects['RingStateName'] = "Pristine"
                                                        elif new_objects['RingStateName'] == 'MajorResources':
                                                            new_objects['RingState'] = 4
                                                            new_objects['RingStateName'] = "Major"
                                                        elif new_objects['RingStateName'] == 'CommonResources':
                                                            new_objects['RingState'] = 3
                                                            new_objects['RingStateName'] = "Common"
                                                        elif new_objects['RingStateName'] == 'LowResources':
                                                            new_objects['RingState'] = 2
                                                            new_objects['RingStateName'] = "Low"
                                                        elif new_objects['RingStateName'] == 'DepletedResources':
                                                            new_objects['RingState'] = 1
                                                            new_objects['RingStateName'] = "Depleted"
                                                        elif new_objects['RingStateName'] is None:
                                                            new_objects['RingState'] = 0
                                                            new_objects['RingStateName'] = "None"
                                                        else:
                                                            new_objects['RingState'] = 0
                                                            new_objects['RingStateName'] = "None"
                        if p1 and p2 and p3 and p4:
                            print(new_objects['RingName'])
                            data.append(new_objects)
                        p1 = False
                        p2 = False
                        p3 = False
                        p4 = False
                    filetext = "Searching logs: {}".format(file_path)
                    self.label.setText(filetext)
                    with open("files.txt", "a") as f:
                        f.write(file_path + "\n")
            else:
                with open("files.txt", "a") as f:
                    f.write(file_path + "\n") 
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
            data = []
            x = 5
            num_objects = len(file_names)
            self.label.setText("Searching logs")
            if num_objects <= x:
                process(file_names, folder_path, self, data)
            else:
                num_parts = num_objects // x + (num_objects % x != 0)
                for i in range(num_parts):
                    start_idx = i * x
                    end_idx = (i + 1) * x
                    part_data = file_names[start_idx:end_idx]
                    part_list = list(part_data)
                    process(part_list, folder_path, self, data)
            with open('output.json', 'w') as f:
                json.dump(data, f, indent=4)
            self.label.setText("Data sorting")    
            file_path = 'output.json'
            remove_duplicates(file_path)
            self.label.setText("Data transfer")
            x = 100
            with open("output.json", 'r') as file:
                data = json.load(file)
            num_objects = len(data)
            num = 0
            if num_objects <= x:
                timet = (int(num) + 1) * 10
                transfer(data, timet, num, self)
            else:
                num_parts = num_objects // x + (num_objects % x != 0)
                for i in range(num_parts):
                    start_idx = i * x
                    end_idx = (i + 1) * x
                    part_data = data[start_idx:end_idx]
                    timet = (int(num) + 1) * 10
                    transfer(part_data, timet, num, self)
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
            with open("files.txt", "r") as f:
                self.dataold = f.read()
            self.label.setText("End of upload. I'm waiting for the next search")
            time.sleep(900)
    def print_message(self):
        self.button.deleteLater()
        QTimer.singleShot(0, lambda: self.create_new_button())
    def create_new_button(self):
        self.button = QPushButton(self)
        self.button.setGeometry(QRect(250, 250, 300, 30))
        self.button.setStyleSheet("border: none; border-radius: 5px;  background-color: #cc3939; color: white; font-size: 12px;")
        self.button.setText("Exit")
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