from serial import Serial
from time import sleep
from threading import Thread, Semaphore, Event
import re
from singleton import singleton
import configparser


@singleton
class FanController(object):
    def __init__(self, port, baudrate):
        self.ser = Serial(port, baudrate)
        self.init_semaphore = Semaphore()
        self.init_semaphore.acquire()
        self.latch = Event()
        self.latch.set()
        self.initialized = False
        self.fan_speed = 0
        self.fan_rpm = 0
        self.init_controller()
        self.emit_update = lambda *args: None

    def update_fan_info(self):
        ser = self.ser
        while self.latch.is_set():
            sleep(1)
            line = ser.readline().decode('utf-8')
            mat = re.search(r"^INIT", line)
            if mat is not None and not self.initialized:
                self.initialized = True
                self.init_semaphore.release()
            if self.initialized:
                mat = re.search(
                    r"^\[([\d.]+)]Speed=([\d]+),RPM=([\d]+)", line)
                if mat is None:
                    continue
                # millis = float(mat.group(1))
                self.fan_speed = int(mat.group(2))
                self.fan_rpm = int(mat.group(3))
                self.emit_update(self.fan_speed, self.fan_rpm)
                # print("[{}] Speed = {}, RPM = {}".format(
                #     millis, self.fan_speed, self.fan_rpm))

    def is_initialized(self):
        return self.initialized

    def get_fan_status(self):
        return {'speed': self.fan_speed, 'rpm': self.fan_rpm}

    def init_controller(self):
        update_thread = Thread(target=self.update_fan_info, daemon=True)
        update_thread.start()
        print('Serial connection established. Waiting for init signal...')
        self.init_semaphore.acquire(blocking=True)
        print("Init ok!")

    def pause_update(self):
        self.latch.clear()

    def set_speed(self, speed: int):
        if speed <= 0 or speed > 100:
            return
        self.ser.write("{}\n".format(speed).encode('utf-8'))


def build_fan_controller():
    config = configparser.ConfigParser()
    config.read('config.ini')
    port = config['Controller']['port']
    baudrate = config['Controller']['baudrate']
    return FanController(port, baudrate)


def main():
    controller = FanController('/dev/ttyACM0', 9600)
    sleep(20)
    status = controller.get_fan_status()
    print("Speed = {}, RPM = {}".format(status['speed'], status['rpm']))
    controller.set_speed(10)
    print("Speed set")
    sleep(5)
    controller.set_speed(20)
    print("Speed set")
    sleep(5)
    controller.set_speed(5)
    print("Speed set")
    sleep(5)
    controller.pause_update()
    print("Update has been paused.")
    sleep(5)
    print("OK")
    return


if __name__ == "__main__":
    main()
