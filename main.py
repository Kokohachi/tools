from flask import *
import yt_dlp
import os
import glob
import uuid
import io
import json

from sus_tools.event import *
from sus_tools.score import *
from sus_tools.sus_draw import *



app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

@app.route('/media_dl')
def index():
    return render_template('index.html')

@app.route('/media_dl/admin')
def strage():
    lists = []
    for i in glob.glob('*.mp3'):
        lists.append(i)
    for i in glob.glob('*.mp4'):
        lists.append(i)
    for i in glob.glob('*.wav'):
        lists.append(i)
    data = {
        "MusicList": lists
    }
    return jsonify(data)


@app.route('/media_dl/info', methods=['GET', 'POST'])
def info():
    url = request.form['url']
    format_type = request.form['format']
    access_id = uuid.uuid4()
    if url == "":
        return "urlを入力してください。"
    
    with yt_dlp.YoutubeDL() as ydl:
        info_dict = ydl.extract_info(url, download=False)
        json.dump(info_dict, open(f"media_info/{access_id}.json", "w", encoding="utf-8"), indent=4, ensure_ascii=False)
        
    if "youtu" in url:
        return render_template('info_youtube.html', title=info_dict['fulltitle'], url=url, format=format_type, display_id=info_dict["display_id"], access_id=access_id)
    elif "nico" in url:
        return render_template('info_niconico.html', title=info_dict['fulltitle'], url=url, format=format_type, display_id=info_dict["display_id"], access_id=access_id)
    else:
        return render_template('info.html', thumbnail=info_dict['thumbnail'], title=info_dict['fulltitle'], url=url, format=format_type, access_id=access_id)
        

@app.route('/media_dl/download', methods=['GET', 'POST'])
def download():
    access_id = request.args['access_id']
    with open(f"media_info/{access_id}.json", encoding="utf-8") as f:
        info = json.load(f)
    
    url = info["original_url"]
    format_type = request.args['format']
    
    print(f"---ダウンロード情報---\nurl: {url}\nフォーマット: {format_type}\nIP: {request.environ['REMOTE_ADDR']}\n----------------------")

    ydl_opts = {
        'format': 'bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080][ext=mp4]/best[ext=mp4]',
        'outtmpl': 'media/%(id)s.%(ext)s',
        'noplaylist': True,
    }

    if format_type == 'mp3':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192'
        }]
        ydl_opts['format'] = 'bestaudio/best'

    elif format_type == 'wav':
        ydl_opts['postprocessors'] = [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'wav'
        }]
        ydl_opts['format'] = 'bestaudio/best'

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(url, download=False)
        filename = ydl.prepare_filename(info_dict)
        
        ydl.download([url])

    filename = os.path.split(filename)[1]
    filename = os.path.splitext(os.path.basename(filename))[0]
    return send_file(f"media/{filename}.{format_type}", as_attachment=True)


@app.route('/sus2svg', methods=['GET'])
def sus2svg():
    return render_template("sus2svg.html")

@app.route('/sus2svg/generate', methods=['POST', 'GET'])
def generate_svg():
    # たてよこ
    xy_type = request.args.get("type")
    susId = str(uuid.uuid4())

    susData = io.TextIOWrapper(io.BytesIO(request.get_data()))
    sus_lines = susData.readlines()
    sus = SUS(sus_lines)
    rebase = eventdump(sus_lines)

    sus.score = sus.score.rebase([
        Event(
            bar=event.get('bar'),
            bpm=event.get('bpm'),
            bar_length=event.get('barLength'),
            sentence_length=event.get('sentenceLength'),
            section=event.get('section'),
        )
        for event in rebase['events']
    ])


    if xy_type == "x":
        sus.export_xdraw(file_name=f"svgdata/{susId}.svg")
    if xy_type == "y":
        sus.export_ydraw(file_name=f"svgdata/{susId}.svg")

    return send_file(f"svgdata/{susId}.svg")
    

if __name__ == '__main__':
    app.run(debug=True, port=80, host="0.0.0.0")