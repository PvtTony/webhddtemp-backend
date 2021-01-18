from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from controller import build_fan_controller
from retpack import ok, fail
from smart import check_smartctl_version, get_drives, get_drive_temp

app = Flask(__name__)
CORS(app)
socket_io = SocketIO(app, cors_allowed_origins='*')
fan_controller = build_fan_controller()

smartctl_valid = check_smartctl_version()


@app.route('/')
def hello_world():
    return jsonify(ok(message="hello world!"))


@app.route('/fan', methods=['GET'])
def get_fan_status():
    return jsonify(ok(data=fan_controller.get_fan_status()))


@app.route('/fan', methods=['PUT'])
def set_fan_status():
    status = request.json
    speed = int(status['speed'])
    fan_controller.set_speed(speed)
    return jsonify(ok())


@app.route('/drives', methods=['GET'])
def get_drives_list():
    return jsonify(get_drives())


@app.route('/temp', methods=['GET'])
def get_drive_temperature():
    args = request.args
    if 'drive_name' not in args:
        return fail(-10, "lack of argument: drive_name")
    return jsonify(get_drive_temp(args['drive_name']))


@app.errorhandler(500)
def internal_error(e):
    return jsonify(fail(500, "Internal Error! Exception: {}".format(str(e)))), 500


@app.errorhandler(404)
def not_found(e):
    return jsonify(fail(404, "Not found! Exception: {}".format(str(e)))), 404


def emit_update(speed, rpm):
    socket_io.emit('fan_status_update', {'speed': speed, 'rpm': rpm})
    pass


fan_controller.emit_update = emit_update

if __name__ == '__main__':
    if not smartctl_valid:
        print("Unable to get hdd temp! Please install or upgrade your smartmontools to the latest version(>7.0)!")
    # app.run()
    socket_io.run(app)
