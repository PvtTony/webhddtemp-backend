import subprocess
import json
import re
from datetime import datetime, timedelta
from retpack import ok, fail

'''
    Check smartctl version > 7.0
'''


def check_smartctl_version() -> bool:
    code = 0
    try:
        raw_out = subprocess.check_output(["smartctl", "--version"], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as ex:
        print(ex)
        raw_out = ex.output
        code = ex.returncode
        print("Errcode = {}".format(code))
        print("CLI output = {}".format(raw_out))
    if code != 0:
        return False
    out = raw_out.decode('utf-8')
    fl = out.splitlines()[0]
    m = re.search(r"^smartctl ([\d.]+)", fl)
    ver = float(m.group(1))
    return ver > 7.0


'''
    Scan for disk devices
'''


def get_drives():
    try:
        raw_out = subprocess.check_output(["smartctl", "--scan", "--json"], stderr=subprocess.STDOUT, timeout=5)
    except subprocess.CalledProcessError as ex:
        print(ex)
        raw_out = ex.output
        return_code = ex.returncode
        print("Errcode = {}".format(return_code))
        print("CLI output = {}".format(raw_out))
        return fail(return_code, "Unable to get drives: call process error")
    except subprocess.TimeoutExpired:
        print("Unable to get drives: timeout")
        return fail(-1, "Unable to get drives: timeout")
    out = json.loads(raw_out.decode('utf-8'))
    return ok(data=out['devices'])


'''
    Get Drive Current Temp Data
'''


def get_drive_temp(drive_name: str):
    temp_data = {}
    temp_log = {}
    try:
        raw_out = subprocess.check_output(["smartctl", "--json", "-l", "scttemp", drive_name], stderr=subprocess.STDOUT,
                                          timeout=10)
    except subprocess.CalledProcessError as ex:
        print(ex)
        raw_out = ex.output
        return_code = ex.returncode
        print("Errcode = {}".format(return_code))
        print("CLI output = {}".format(raw_out))
        return fail(return_code,
                    "Unable to get drive {} temperature: call process error".format(drive_name))
    except subprocess.TimeoutExpired:
        print("Unable to get drive {} temperature: timeout".format(drive_name))
        return fail(-1, "Unable to get drive {} temperature: timeout".format(drive_name))
    out = json.loads(raw_out.decode('utf-8'))
    temp_data['temp'] = out['temperature']
    temp_log['sampling_period_minutes'] = out['ata_sct_temperature_history']['sampling_period_minutes']
    temp_log['logging_interval_minutes'] = out['ata_sct_temperature_history']['logging_interval_minutes']
    temp_log_history = []
    log_table = out['ata_sct_temperature_history']['table']
    history_back_minutes = out['ata_sct_temperature_history']['size'] - 1
    now = datetime.now()
    for tb_item in log_table:
        temp_log_item = {}
        dta = timedelta(minutes=history_back_minutes, seconds=now.second, microseconds=now.microsecond)
        ts = int((now - dta).timestamp())
        temp_log_item['est'] = ts
        temp_log_item['temp'] = tb_item
        temp_log_history.append(temp_log_item)
        history_back_minutes -= 1
    temp_log['history'] = temp_log_history
    temp_data['log'] = temp_log
    return ok(data=temp_data)


def main():
    print("Is smartctl version > 7.0: {}".format(check_smartctl_version()))
    drives = get_drives()['data']
    for drive in drives:
        name = drive['name']
        print(name)
        print(get_drive_temp(name))
    return


if __name__ == "__main__":
    main()
