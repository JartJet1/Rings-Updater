import os
import requests
import json
import time
import re
import fileinput
import ijson
from datetime import datetime
def merge_objects(merged_obj):
    with open('output.json', 'rb') as f:
        objects = ijson.items(f, 'item')
        for obj in objects:
            if obj['SystemAddress'] == merged_obj['SystemAddress'] and obj['BodyID'] == merged_obj['BodyID']:
                obj.update(merged_obj)
                yield obj
            else:
                yield obj
def date_handler(obj):
    if hasattr(obj, 'isoformat'):
        return obj.isoformat()
    else:
        raise TypeError("Unserializable object {} of type {}".format(obj, type(obj)))
file_name = ""
while True:
    folder_path = os.path.expanduser('~/Saved Games/Frontier Developments/Elite Dangerous')
    folder_path = folder_path.replace('%username%', os.getlogin())
    file_names = [f for f in os.listdir(folder_path) if "Journal" in f and f.endswith(".log")]
    with open("files.txt", "r") as f:
        content = f.read()
    for file_name in file_names[:]:  # skopiuj listę plików
        pattern = re.compile(file_name)
        if pattern.search(content):
            file_names.remove(file_name)
    x = 5
    new_objects = []
    num_objects = len(file_names)
    print("Przeszukiwanie dzienników")
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
                            print('Błąd parsowania JSON:', e)
                            continue  # przejdź do kolejnej linii, jeśli jest błąd
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
                                    print('Błąd parsowania JSON:', e)
                                    continue  # przejdź do kolejnej linii, jeśli jest błąd
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
                                            obj.pop('OnStation', None)
                                            obj.pop('OnPlanet', None)
                                            obj.pop('Multicrew', None)
                                            obj.pop('RemainingJumpsInRoute', None)
                                            obj.pop('ID', None)
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
                        print(file_name)
                        with open("files.txt", "a") as f:
                            f.write(file_name + "\n")
                    else:
                        with open("files.txt", "a") as f:
                            f.write(file_name + "\n")
        with open('output.json', 'w') as f:
            json.dump(new_objects, f, indent=4)  
    else:
        num_parts = num_objects // x + (num_objects % x != 0)  # zaokrąglamy w górę
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
                                print('Błąd parsowania JSON:', e)
                                continue  # przejdź do kolejnej linii, jeśli jest błąd
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
                                        print('Błąd parsowania JSON:', e)
                                        continue  # przejdź do kolejnej linii, jeśli jest błąd
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
                                                obj.pop('OnStation', None)
                                                obj.pop('OnPlanet', None)
                                                obj.pop('Multicrew', None)
                                                obj.pop('RemainingJumpsInRoute', None)
                                                obj.pop('ID', None)
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
                            print(file_name)
                            with open("files.txt", "a") as f:
                                f.write(file_name + "\n")
                        else:
                            with open("files.txt", "a") as f:
                                f.write(file_name + "\n")
        with open('output.json', 'w') as f:
            json.dump(new_objects, f, indent=4)
    print("Segregowanie danych")
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
    print("Przesylanie danych")
    x = 1000
    with open("output.json", 'r') as file:
        data = json.load(file)
    num_objects = len(data)
    if num_objects <= x:
        json_data = json.dumps(data)
        headers = {'Content-type': 'application/json'}
        response = None
        while response is None:
            try:
                response = requests.post('https://apporsite.com/elitebase/bodies.php', data=json_data, headers=headers, timeout=300)
                break
            except requests.exceptions.RequestException as e:
                if isinstance(e, requests.exceptions.ConnectionError) or isinstance(e, ConnectionResetError):
                    print('Błąd połączenia:', e)
                    print('Ponawiam zapytanie...')
                    time.sleep(5)
                elif isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 500:
                    print('Błąd serwera wewnętrznego:', e)
                elif requests.exceptions.Timeout:
                    print("Timeout occurred. Retrying...")
                else:
                    raise e
        print(response.text)
    else:
        num_parts = num_objects // x + (num_objects % x != 0)
        for i in range(num_parts):
            start_idx = i * x
            end_idx = (i + 1) * x
            part_data = data[start_idx:end_idx]
            json_data = json.dumps(part_data)
            headers = {'Content-type': 'application/json'}
            response = None
            while response is None:
                try:
                    response = requests.post('https://apporsite.com/elitebase/bodies.php', data=json_data, headers=headers, timeout=300)
                    break
                except requests.exceptions.RequestException as e:
                    if isinstance(e, requests.exceptions.ConnectionError) or isinstance(e, ConnectionResetError):
                        print('Błąd połączenia:', e)
                        print('Ponawiam zapytanie...')
                        time.sleep(5)
                    elif isinstance(e, requests.exceptions.HTTPError) and e.response.status_code == 500:
                        print('Błąd serwera wewnętrznego:', e)
                    elif requests.exceptions.Timeout:
                        print("Timeout occurred. Retrying...")
                    else:
                        raise e
            print(response.text)
            time.sleep(5)
    folder_path = os.path.expanduser('~/Saved Games/Frontier Developments/Elite Dangerous')
    folder_path = folder_path.replace('%username%', os.getlogin())
    files = [(f, os.path.getmtime(os.path.join(folder_path, f))) for f in os.listdir(folder_path)]
    pattern = re.compile('.*Journal.*\.log')
    matching_files = [f[0] for f in files if pattern.match(f[0])]
    latest_file = max(matching_files, key=lambda f: os.path.getmtime(os.path.join(folder_path, f)))
    for line in fileinput.input('files.txt', inplace=True):
        if not line.strip().endswith(latest_file):
            print(line.rstrip())
    print("Koniec przesyłania. Oczekiwanie na kolejne pobranie danych")
    time.sleep(900)
