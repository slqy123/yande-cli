import os

os.chdir(os.path.split(os.path.abspath(__file__))[0])

from flask import Flask, send_file, jsonify
from settings import IMG_PATH, STATUS
from database import *
from yandecli.tools.history import YandeHistory

app = Flask(__name__)


@app.route('/history')
def get_history():
    resp = []
    histories = YandeHistory.get_all_unfinished_histories()
    for history in histories:
        yande_history = YandeHistory.select(history)
        if yande_history.platform == PLATFORM.MOBILE:
            resp.append({
                'id': yande_history.id,
                'star': yande_history.start,
                'from_to': f'from {yande_history.start} to {yande_history.end}',
                'date': str(yande_history.date)
            })
    print(resp)
    return jsonify(resp)

@app.route('/image/<int:img_id>')
def main(img_id: int):
    img = check_exists(Image, id=img_id)
    if img:
        return send_file(
            os.path.join(IMG_PATH, img.name),
            as_attachment=True
        )
    else:
        return '<p> image not found </p>'


if __name__ == '__main__':
    app.run('0.0.0.0', debug=True)
