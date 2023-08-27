#!/usr/bin/env python
import time
import sys
import os
import requests
import json
from rgbmatrix import graphics, RGBMatrix, RGBMatrixOptions
from PIL import Image
from PIL import ImageDraw
from cairosvg import svg2png
from datetime import datetime
import pytz

# Configuration for the matrix
options = RGBMatrixOptions()
options.rows = 64
options.cols = 64
options.chain_length = 1
options.parallel = 1
options.brightness = 40
options.hardware_mapping = 'regular'  # If you have an Adafruit HAT: 'adafruit-hat'

matrix = RGBMatrix(options = options)

def download_image(save_path, team_id):
    svg_save_path = '/opt/PL-Scores-RGBMatrix/team_logos/%s.svg' % team_id
    image_url = 'https://resources.premierleague.com/premierleague/badges/rb/%s.svg' % team_id
    headers = {'Origin':'https://www.premierleague.com', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'}
    r = requests.get(image_url, allow_redirects=True, headers=headers)
    open(svg_save_path, 'wb').write(r.content)
    svg_read = '\n'.join(open(svg_save_path, 'r').readlines())
    svg2png(bytestring=svg_read, write_to=save_path)

def play_gif(gif_file, x, y):
    goal_gif = Image.open(gif_file)
    for frame in range(0, goal_gif.n_frames):
        goal_gif.seek(frame)
        resized_gif = goal_gif.resize((x,y))
        matrix.SetImage(resized_gif.convert('RGB'))
        time.sleep(0.01)

play_gif("/opt/PL-Scores-RGBMatrix/pl.gif", 64, 64)


white = graphics.Color(255, 255, 255)
gray = graphics.Color(192, 192, 192)
red = graphics.Color(241, 65, 108)
green = graphics.Color(80, 205, 137)
blue = graphics.Color(0, 163, 255)
font = graphics.Font()
font.LoadFont("/opt/PL-Scores-RGBMatrix/fonts/9x18B.bdf")
date_font = graphics.Font()
date_font.LoadFont("/opt/PL-Scores-RGBMatrix/fonts/5x8.bdf")


try:
    print("Press CTRL-C to stop.")
    canvas_off = matrix.CreateFrameCanvas()
    url ='https://footballapi.pulselive.com/football/fixtures?statuses=U,L,C&pageSize=10&page=0&gameweeks=12271&altIds=true'
    headers = {'Origin':'https://www.premierleague.com', 'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.67 Safari/537.36'}
    old_goal_time = {}
    first_run = True
    while True:
      canvas_off.Clear()
      result = requests.get(url, headers=headers)
      json = result.json()
      team_scores = []
      for content in json['content']:
        goal_seconds = []
        status = content['status']
        phase = content['phase']

        # HOME TEAM
        home_abbr_name = content['teams'][0]['team']['club']['abbr']
        home_alt_id = content['teams'][0]['team']['altIds']['opta']
        if 'score' not in content['teams'][0]:
            home_score = None
        else:
            home_score = int(content['teams'][0]['score'])
        home_image_path = '/opt/PL-Scores-RGBMatrix/team_logos/%s.png' % home_alt_id
        if not os.path.isfile(home_image_path):
            download_image(home_image_path, home_alt_id)

        # AWAY TEAM
        away_abbr_name = content['teams'][1]['team']['club']['abbr']
        away_alt_id = content['teams'][1]['team']['altIds']['opta']
        if 'score' not in content['teams'][1]:
            away_score = None
        else:
            away_score = int(content['teams'][1]['score'])
        away_image_path = '/opt/PL-Scores-RGBMatrix/team_logos/%s.png' % away_alt_id
        if not os.path.isfile(away_image_path):
            download_image(away_image_path, away_alt_id)
        if 'clock' not in content:
            clock_label = None
            clock_secs = None
        else:
            clock_label = content['clock']['label']
            clock_secs = content['clock']['secs']
        for goal in content['goals']:
            goal_seconds.append(goal['clock']['secs'])

        team_scores.append(
            { 
                'id': int(content['id']),
                'kickoff': int(content['kickoff']['millis'] / 1000),
                'status': status,
                'phase': phase,
                'goal_times': goal_seconds,
                'home_abbr_name': home_abbr_name,
                'away_abbr_name': away_abbr_name,
                'home_image': home_image_path,
                'away_image': away_image_path,
                'home_score': home_score,
                'away_score': away_score,
                'clock_label' : clock_label,
                'clock_secs' : clock_secs
            }
        )
      if result.status_code != 200:
        time.sleep(60)
        continue
      line = 7
      # Crop Points
      image_x = 32
      image_y = 32
      for scores in team_scores:
          if first_run == False: # IF first run, don't
              if scores['goal_times']:
                if scores['id'] in old_goal_time:
                    if max(scores['goal_times']) > old_goal_time[scores['id']]:
                      play_gif("/opt/PL-Scores-RGBMatrix/goal2.gif", 64, 64)
                      old_goal_time[scores['id']] = max(scores['goal_times'])
                else:
                    old_goal_time[scores['id']] = max(scores['goal_times'])
                    play_gif("/opt/PL-Scores-RGBMatrix/goal2.gif", 64, 64)
          else:
              if scores['goal_times']:
                  old_goal_time[scores['id']] = max(scores['goal_times'])
          matrix.Clear()
          score_string = ''
          score_status = ''
          kickoff = scores['kickoff']
          # Home Image
          home_image = Image.open(scores['home_image'])
          home_background = Image.new("RGBA", home_image.size, "WHITE")
          home_background.paste(home_image, (0,0), home_image)
          home_resize = home_image.resize((image_x,image_y))
          matrix.SetImage(home_resize.convert('RGB'), 0, 0)

          # Away Image
          away_image = Image.open(scores['away_image'])
          away_background = Image.new("RGBA", away_image.size, "WHITE")
          away_background.paste(away_image, (0,0), away_image)
          away_resize = away_image.resize((image_x,image_y))
          matrix.SetImage(away_resize.convert('RGB'), 32, 0)
   
          if scores['home_score'] is None: # Future Day
              tz = pytz.timezone('America/New_York')
              dt = datetime.fromtimestamp(kickoff, tz)
              score_string = '@'
              score_status = dt.strftime('%H:%M %m/%d')
              score_height = 40
          elif scores['phase'] == 'H': # Halftime
              score_string = "%s - %s" % (scores['home_score'], scores['away_score'])
              score_status = '-Halftime-'
          elif scores['status'] == 'U': # Coming Soon
              score_string = "%s - %s" % (scores['home_score'], scores['away_score'])
              tz = pytz.timezone('America/New_York')
              dt = datetime.fromtimestamp(kickoff, tz)
              score_status = dt.strftime('Starts@%H:%M')
          elif scores['clock_label'] is not None and scores['status'] == 'L': # Live
              score_string = "%s - %s" % (scores['home_score'], scores['away_score'])
              score_status = scores['clock_label']
          else: # Final
              score_string = "%s - %s" % (scores['home_score'], scores['away_score'])
              score_status = '-Final-'
              score_height = 40
          score_length = len(score_string)
          status_length = len(score_status)
          graphics.DrawText(matrix, font, 32-(9 * (score_length / 2)), 50, gray, score_string)
          graphics.DrawText(matrix, date_font, 32-(5 * (status_length / 2)), 63, gray, score_status)
          time.sleep(5)

      first_run = False
      canvas_off = matrix.SwapOnVSync(canvas_off)
except KeyboardInterrupt:
  sys.exit(0)
