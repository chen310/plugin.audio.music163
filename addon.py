# -*- coding:utf-8 -*-
from api import NetEase
from xbmcswift2 import Plugin, xbmcgui, xbmcplugin, xbmc
import re
import sys
import hashlib
import time
import os


PY3 = sys.version_info.major >= 3
if not PY3:
    reload(sys)
    sys.setdefaultencoding('utf-8')

plugin = Plugin()

account = plugin.get_storage('account')
if 'uid' not in account:
    account['uid'] = ''
if 'logined' not in account:
    account['logined'] = False
if 'first_run' not in account:
    account['first_run'] = True
if 'follow' not in account:
    account['follow'] = False

music = NetEase()

# login
if not account['logined'] and xbmcplugin.getSetting(int(sys.argv[1]), 'login') == 'true':
    username = xbmcplugin.getSetting(int(sys.argv[1]), 'username').strip()
    password = xbmcplugin.getSetting(int(sys.argv[1]), 'password').strip()

    if len(password) > 0 and len(password) > 0:
        password = hashlib.md5(password.encode('UTF-8')).hexdigest()
        # 登录
        login = music.login(username, password)
        if login['code'] == 200:
            account['logined'] = True
            account['uid'] = login['profile']['userId']
            dialog = xbmcgui.Dialog()
            dialog.notification('登录成功', '请重启软件以解锁更多功能',
                                xbmcgui.NOTIFICATION_INFO, 800, False)
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification('登录失败', '账号或密码错误',
                                xbmcgui.NOTIFICATION_INFO, 800, False)
# logout
if account['logined'] and xbmcplugin.getSetting(int(sys.argv[1]), 'login') == 'false':
    account['logined'] = False
    account['MUSIC_U'] = ''
    account['__csrf'] = ''
    account['__remember_me'] = ''
    account['uid'] = ''
    dialog = xbmcgui.Dialog()
    dialog.notification(
        '退出成功', '账号退出成功', xbmcgui.NOTIFICATION_INFO, 800, False)

#limit = int(xbmcplugin.getSetting(int(sys.argv[1]),'number_of_songs_per_page'))
limit = xbmcplugin.getSetting(int(sys.argv[1]), 'number_of_songs_per_page')
if limit == '':
    limit = 100
else:
    limit = int(limit)

quality = xbmcplugin.getSetting(int(sys.argv[1]), 'quality')
if quality == '0':
    bitrate = 128000
elif quality == '1':
    bitrate = 192000
elif quality == '2':
    bitrate = 320000
elif quality == '3':
    bitrate = 999000
else:
    bitrate = 128000


def tag(info, color='red'):
    return '[COLOR ' + color + ']' + info + '[/COLOR]'


def trans_num(num):
    if num > 100000000:
        return str(round(num/100000000, 1)) + '亿'
    elif num > 10000:
        return str(round(num/10000, 1)) + '万'
    else:
        return str(num)


def trans_time(t):
    return time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(t//1000))


def trans_date(t):
    return time.strftime('%Y-%m-%d', time.localtime(t//1000))


def B2M(size):
    return str(round(size/1048576, 1))


def get_songs(songs, privileges=[], picUrl=None, source=''):
    datas = []
    for i in range(len(songs)):
        song = songs[i]

        # song data
        if 'song' in song:
            song = song['song']
        # 云盘
        elif 'simpleSong' in song:
            tempSong = song
            song = song['simpleSong']
        elif 'songData' in song:
            song = song['songData']
        elif 'mainSong' in song:
            song = song['mainSong']
        data = {}

        # song id
        if 'id' in song:
            data['id'] = song['id']
        elif 'songId' in song:
            data['id'] = song['songId']
        data['name'] = song['name']

        # mv id
        if 'mv' in song:
            data['mv_id'] = song['mv']
        elif 'mvid' in song:
            data['mv_id'] = song['mvid']
        elif 'mv_id' in song:
            data['mv_id'] = song['mv_id']

        artist = ""
        data['picUrl'] = None
        if 'ar' in song:
            if song['ar'] is not None:
                artist = "/".join([a["name"]
                                  for a in song["ar"] if a["name"] is not None])
                if artist == "" and "pc" in song:
                    artist = "未知艺术家" if song["pc"]["ar"] is None else song["pc"]["ar"]

                if picUrl is not None:
                    data['picUrl'] = picUrl
                elif 'picUrl' in song['ar'] and song['ar']['picUrl'] is not None:
                    data['picUrl'] = song['ar']['picUrl']
                elif 'img1v1Url' in song['ar'] and song['ar']['img1v1Url'] is not None:
                    data['picUrl'] = song['ar']['img1v1Url']
            else:
                if 'simpleSong' in tempSong and 'artist' in tempSong and tempSong['artist'] != '':
                    artist = tempSong['artist']
                else:
                    artist = "未知艺术家"

        elif 'artists' in song:
            artist = "/".join([a["name"] for a in song["artists"]])

            if picUrl is not None:
                data['picUrl'] = picUrl
            elif 'picUrl' in song['artists'][0] and song['artists'][0]['picUrl'] is not None:
                data['picUrl'] = song['artists'][0]['picUrl']
            elif 'img1v1Url' in song['artists'][0] and song['artists'][0]['img1v1Url'] is not None:
                data['picUrl'] = song['artists'][0]['img1v1Url']
        else:
            artist = "未知艺术家"
            # if 'simpleSong' in tempSong and 'ar' not in song and 'artist' in tempSong and tempSong['artist']!='':
            #     artist = tempSong['artist']
            # else:
            #     artist = "未知艺术家"
        data['artist'] = artist

        if "al" in song:
            if song["al"] is not None:
                album_name = song["al"]["name"]
                album_id = song["al"]["id"]
                if 'picUrl' in song['al']:
                    data['picUrl'] = song['al']['picUrl']
            else:
                if 'simpleSong' in tempSong and 'album' in tempSong and tempSong['album'] != '':
                    album_name = tempSong['album']
                    album_id = 0
                else:
                    album_name = "未知专辑"
                    album_id = 0

        elif "album" in song:
            if song["album"] is not None:
                album_name = song["album"]["name"]
                album_id = song["album"]["id"]
            else:
                album_name = "未知专辑"
                album_id = 0

            if 'picUrl' in song['album']:
                data['picUrl'] = song['album']['picUrl']

        data['album_name'] = album_name
        data['album_id'] = album_id

        if 'alia' in song and song['alia'] is not None and len(song['alia']) > 0:
            data['alia'] = song['alia'][0]

        if 'cd' in song:
            data['disc'] = song['cd']
        elif 'disc' in song:
            data['disc'] = song['disc']
        else:
            data['disc'] = 1

        if 'no' in song:
            data['no'] = song['no']
        else:
            data['no'] = 1

        if 'dt' in song:
            data['dt'] = song['dt']
        elif 'duration' in song:
            data['dt'] = song['duration']

        if 'privilege' in song:
            privilege = song['privilege']
        elif len(privileges) > 0:
            privilege = privileges[i]
        else:
            privilege = None

        if privilege is None:
            data['privilege'] = None
        else:
            data['privilege'] = privilege

        # 搜索歌词
        if source == 'search_lyric' and 'lyrics' in song:
            data['lyrics'] = song['lyrics']
            data['second_line'] = ''
            txt = song['lyrics']['txt']

            index_list = [i.start() for i in re.finditer('\n', txt)]
            temps = []
            for words in song['lyrics']['range']:
                first = words['first']
                second = words['second']
                left = -1
                right = -1
                for index in range(len(index_list)):
                    if index_list[index] <= first:
                        left = index
                    if index_list[index] >= second:
                        right = index
                        break
                temps.append({'first': first, 'second': second,
                             'left': left, 'right': right})
            skip = []
            for index in range(len(temps)):
                if index in skip:
                    break
                line = ''
                if left == -1:
                    line += txt[0:temps[index]['first']]
                else:
                    line += txt[index_list[temps[index]['left']] +
                                1:temps[index]['first']]
                line += tag(txt[temps[index]['first']:temps[index]['second']], 'blue')

                for index2 in range(index+1, len(temps)):
                    if temps[index2]['left'] == temps[index]['left']:
                        line += txt[temps[index2-1]['second']:temps[index2]['first']]
                        line += tag(txt[temps[index2]['first']:temps[index2]['second']], 'blue')
                        skip.append(index2)
                    else:
                        break
                if right == -1:
                    line += txt[temps[index]['second']:len(txt)]
                else:
                    line += txt[temps[index]['second']:index_list[temps[index]['right']]] + '...'

                data['second_line'] += line
        else:
            if xbmcplugin.getSetting(int(sys.argv[1]), 'show_album_name') == 'true':
                data['second_line'] = data['album_name']
        datas.append(data)
    return datas


def get_songs_items(datas, privileges=[], picUrl=None, offset=0, getmv=True, source='', sourceId=0):
    songs = get_songs(datas, privileges, picUrl, source)
    items = []
    for play in songs:
        # 隐藏不能播放的歌曲
        if play['privilege']['pl'] == 0 and xbmcplugin.getSetting(int(sys.argv[1]), 'hide_songs') == 'true':
            continue
        # 显示序号
        if xbmcplugin.getSetting(int(sys.argv[1]), 'show_index') == 'true':
            offset += 1
            if offset < 10:
                str_offset = '0' + str(offset) + '.'
            else:
                str_offset = str(offset) + '.'
        else:
            str_offset = ''

        ar_name = play['artist']

        mv_id = play['mv_id']

        label = str_offset + ar_name + ' - ' + play['name']
        if 'alia' in play:
            label += tag('('+play['alia']+')', 'gray')
        if play['privilege'] is not None:
            if play['privilege']['st'] < 0:
                label = tag(label, 'grey')
            if play['privilege']['fee'] == 1 and xbmcplugin.getSetting(int(sys.argv[1]), 'vip_tag') == 'true':
                label += tag(' vip')
            if play['privilege']['cs'] and xbmcplugin.getSetting(int(sys.argv[1]), 'cloud_tag') == 'true':
                label += tag(' 云')
            if (play['privilege']['flag'] & 64) > 0 and xbmcplugin.getSetting(int(sys.argv[1]), 'exclusive_tag') == 'true':
                label += tag(' 独家')
            # if play['privilege']['downloadMaxbr']>=999000 and xbmcplugin.getSetting(int(sys.argv[1]),'sq_tag') == 'true':
            if play['privilege']['maxbr'] >= 999000 and xbmcplugin.getSetting(int(sys.argv[1]), 'sq_tag') == 'true':
                label += tag(' SQ')
            # payed: 0 未付费 | 3 付费单曲 | 5 付费专辑
            if 'preSell' in play['privilege'] and play['privilege']['preSell'] == True and xbmcplugin.getSetting(int(sys.argv[1]), 'presell_tag') == 'true':
                label += tag(' 预售')
            elif play['privilege']['fee'] == 4 and play['privilege']['pl'] == 0 and xbmcplugin.getSetting(int(sys.argv[1]), 'pay_tag') == 'true':
                label += tag(' 付费')
        if mv_id > 0 and xbmcplugin.getSetting(int(sys.argv[1]), 'mv_tag') == 'true':
            label += tag(' MV', 'green')

        if 'second_line' in play and play['second_line'] != '':
            label += '\n' + play['second_line']

        if mv_id > 0 and xbmcplugin.getSetting(int(sys.argv[1]), 'mvfirst') == 'true' and getmv:
            context_menu = [
                ('播放歌曲', 'RunPlugin(%s)' % plugin.url_for('song_contextmenu', action='play_song', meida_type='song',
                 song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000))),
                ('收藏到歌单', 'RunPlugin(%s)' % plugin.url_for('song_contextmenu', action='sub_playlist', meida_type='song',
                 song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000))),
                ('收藏到视频歌单', 'RunPlugin(%s)' % plugin.url_for('song_contextmenu', action='sub_video_playlist', meida_type='song',
                 song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000))),
            ]
            items.append({
                'label': label,
                'path': plugin.url_for('play', meida_type='mv', song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000)),
                'is_playable': True,
                'icon': play.get('picUrl', None),
                'thumbnail': play.get('picUrl', None),
                'context_menu': context_menu,
                'info': {
                    'mediatype': 'video',
                    'title': play['name'],
                    'album': play['album_name'],
                },
                'info_type': 'video',
            })
        else:
            context_menu = [
                ('收藏到歌单', 'RunPlugin(%s)' % plugin.url_for('song_contextmenu', action='sub_playlist', meida_type='song',
                 song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000))),
                ('歌曲ID:'+str(play['id']), ''),
            ]

            if mv_id > 0:
                context_menu.append(('收藏到视频歌单', 'RunPlugin(%s)' % plugin.url_for('song_contextmenu', action='sub_video_playlist',
                                    meida_type='song', song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000))))
                context_menu.append(('播放MV', 'RunPlugin(%s)' % plugin.url_for('song_contextmenu', action='play_mv', meida_type='song', song_id=str(
                    play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000))))

            # 歌曲不能播放时播放MV
            if play['privilege'] is not None and play['privilege']['st'] < 0 and mv_id > 0 and xbmcplugin.getSetting(int(sys.argv[1]), 'auto_play_mv') == 'true':
                items.append({
                    'label': label,
                    'path': plugin.url_for('play', meida_type='song', song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000)),
                    'is_playable': True,
                    'icon': play.get('picUrl', None),
                    'thumbnail': play.get('picUrl', None),
                    'context_menu': context_menu,
                    'info': {
                        'mediatype': 'video',
                        'title': play['name'],
                        'album': play['album_name'],
                    },
                    'info_type': 'video',
                })
            else:
                items.append({
                    'label': label,
                    'path': plugin.url_for('play', meida_type='song', song_id=str(play['id']), mv_id=str(mv_id), sourceId=str(sourceId), dt=str(play['dt']//1000)),
                    'is_playable': True,
                    'icon': play.get('picUrl', None),
                    'thumbnail': play.get('picUrl', None),
                    'fanart': play.get('picUrl', None),
                    'context_menu': context_menu,
                    'info': {
                        'mediatype': 'music',
                        'title': play['name'],
                        'artist': ar_name,
                        'album': play['album_name'],
                        'tracknumber': play['no'],
                        'discnumber': play['disc'],
                        'duration': play['dt']//1000,
                        'dbid': play['id'],
                    },
                    'info_type': 'music',
                })
    return items


@plugin.route('/song_contextmenu/<action>/<meida_type>/<song_id>/<mv_id>/<sourceId>/<dt>/')
def song_contextmenu(action, meida_type, song_id, mv_id, sourceId, dt):
    if action == 'sub_playlist':
        ids = []
        names = []
        names.append('+ 新建歌单')
        playlists = music.user_playlist(account['uid'], includeVideo=False)
        for playlist in playlists:
            if str(playlist['userId']) == str(account['uid']):
                ids.append(playlist['id'])
                names.append(playlist['name'])
        dialog = xbmcgui.Dialog()
        ret = dialog.contextmenu(names)
        if ret == 0:
            keyboard = xbmc.Keyboard('', '请输入歌单名称')
            xbmc.sleep(1500)
            keyboard.doModal()
            if (keyboard.isConfirmed()):
                name = keyboard.getText()
            else:
                return

            create_result = music.playlist_create(name)
            if create_result['code'] == 200:
                playlist_id = create_result['id']
            else:
                dialog = xbmcgui.Dialog()
                dialog.notification(
                    '创建失败', '歌单创建失败', xbmcgui.NOTIFICATION_INFO, 800, False)
        elif ret >= 1:
            playlist_id = ids[ret-1]

        if ret >= 0:
            result = music.playlist_tracks(playlist_id, [song_id], op='add')
            msg = ''
            if result['code'] == 200:
                msg = '收藏成功'
            elif 'message' in result and result['message'] is not None:
                msg = str(result['code'])+'错误:'+result['message']
            else:
                msg = str(result['code'])+'错误'
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '收藏', msg, xbmcgui.NOTIFICATION_INFO, 800, False)
    elif action == 'sub_video_playlist':
        ids = []
        names = []
        playlists = music.user_playlist(
            account['uid'], includeVideo=True).get("playlist", [])
        for playlist in playlists:
            if str(playlist['userId']) == str(account['uid']) and playlist['specialType'] == 200:
                ids.append(playlist['id'])
                names.append(playlist['name'])
        dialog = xbmcgui.Dialog()
        ret = dialog.contextmenu(names)
        if ret >= 0:
            result = music.playlist_add(ids[ret], [mv_id])
            xbmc.log('sub_result:%s' % result)
            msg = ''
            if result['code'] == 200:
                msg = '收藏成功'
            elif 'msg' in result:
                msg = result['message']
            else:
                msg = '收藏失败'
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '收藏', msg, xbmcgui.NOTIFICATION_INFO, 800, False)
    elif action == 'play_song':
        songs = music.songs_url([song_id], bitrate=bitrate).get("data", [])
        urls = [song['url'] for song in songs]
        url = urls[0]
        if url is None:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '播放', '该歌曲无法播放', xbmcgui.NOTIFICATION_INFO, 800, False)
        else:
            xbmc.executebuiltin('PlayMedia(%s)' % url)
    elif action == 'play_mv':
        mv = music.mv_url(mv_id).get("data", {})
        url = mv['url']
        if url is None:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '播放', '该视频已删除', xbmcgui.NOTIFICATION_INFO, 800, False)
        else:
            xbmc.executebuiltin('PlayMedia(%s)' % url)


@plugin.route('/play/<meida_type>/<song_id>/<mv_id>/<sourceId>/<dt>/')
def play(meida_type, song_id, mv_id, sourceId, dt):
    if meida_type == 'mv':
        mv = music.mv_url(mv_id).get("data", {})
        url = mv['url']
        if url is None:
            dialog = xbmcgui.Dialog()
            dialog.notification('MV播放失败', '自动播放歌曲',
                                xbmcgui.NOTIFICATION_INFO, 800, False)

            songs = music.songs_url([song_id], bitrate=bitrate).get("data", [])
            urls = [song['url'] for song in songs]
            if len(urls) == 0:
                url = None
            else:
                url = urls[0]
    elif meida_type == 'song':
        songs = music.songs_url([song_id], bitrate=bitrate).get("data", [])
        urls = [song['url'] for song in songs]
        # 一般是网络错误
        if len(urls) == 0:
            url = None
        else:
            url = urls[0]
            xbmc.log('%s - %s' % (song_id, url))
        if url is None:
            if int(mv_id) > 0 and xbmcplugin.getSetting(int(sys.argv[1]), 'auto_play_mv') == 'true':
                mv = music.mv_url(mv_id).get("data", {})
                url = mv['url']
                if url is not None:
                    msg = '该歌曲无法播放，自动播放MV'
                else:
                    msg = '该歌曲和MV无法播放'
            else:
                msg = '该歌曲无法播放'
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '播放失败', msg, xbmcgui.NOTIFICATION_INFO, 800, False)
        else:
            if xbmcplugin.getSetting(int(sys.argv[1]), 'upload_play_record') == 'true':
                music.daka(song_id, time=dt)
    elif meida_type == 'dj':
        result = music.dj_detail(song_id)
        song_id = result['program']['mainSong']['id']
        songs = music.songs_url([song_id], bitrate=bitrate).get("data", [])
        urls = [song['url'] for song in songs]
        if len(urls) == 0:
            url = None
        else:
            url = urls[0]
        if url is None:
            msg = '该节目无法播放'
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '播放失败', msg, xbmcgui.NOTIFICATION_INFO, 800, False)
    elif meida_type == 'mlog':
        result = music.mlog_detail(mv_id)
        url = result['data']['resource']['content']['video']['urlInfo']['url']

    # else:
    #     music.daka(song_id,sourceId,dt)
    # xbmc.log('play_url:%s'%url)
    plugin.set_resolved_url(url)


def follow():
    author_uid = 347837981
    music.user_follow(author_uid)
    account['follow'] = True


# 主目录
@plugin.route('/')
def index():
    if account['first_run']:
        account['first_run'] = False
        xbmcgui.Dialog().ok('使用提示', '在设置中登录账号以解锁更多功能')
    items = []
    status = account['logined']

    if xbmcplugin.getSetting(int(sys.argv[1]), 'follow') == 'true' and not account['follow']:
        follow()

    if xbmcplugin.getSetting(int(sys.argv[1]), 'daily_recommend') == 'true' and status:
        items.append(
            {'label': '每日推荐', 'path': plugin.url_for('recommend_songs')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'personal_fm') == 'true' and status:
        items.append({'label': '私人FM', 'path': plugin.url_for('personal_fm')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'my_playlists') == 'true' and status:
        items.append({'label': '我的歌单', 'path': plugin.url_for(
            'user_playlists', uid=account['uid'])})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'sublist') == 'true' and status:
        items.append({'label': '我的收藏', 'path': plugin.url_for('sublist')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'recommend_playlists') == 'true' and status:
        items.append(
            {'label': '推荐歌单', 'path': plugin.url_for('recommend_playlists')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'rank') == 'true':
        items.append({'label': '排行榜', 'path': plugin.url_for('toplists')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'top_artist') == 'true':
        items.append({'label': '热门歌手', 'path': plugin.url_for('top_artists')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'top_mv') == 'true':
        items.append(
            {'label': '热门MV', 'path': plugin.url_for('top_mvs', offset='0')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'search') == 'true':
        items.append({'label': '搜索', 'path': plugin.url_for('search')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'cloud_disk') == 'true' and status:
        items.append(
            {'label': '我的云盘', 'path': plugin.url_for('cloud', offset='0')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'home_page') == 'true' and status:
        items.append(
            {'label': '我的主页', 'path': plugin.url_for('user', id=account['uid'])})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'new_albums') == 'true':
        items.append(
            {'label': '新碟上架', 'path': plugin.url_for('new_albums', offset='0')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'new_albums') == 'true':
        items.append({'label': '新歌速递', 'path': plugin.url_for('new_songs')})
    if xbmcplugin.getSetting(int(sys.argv[1]), 'mlog') == 'true':
        items.append(
            {'label': 'Mlog', 'path': plugin.url_for('mlog_category')})

    return items


# Mlog广场
@plugin.route('/mlog_category/')
def mlog_category():
    categories = {
        '广场': 1001,
        '热门': 2124301,
        'MV': 1002,
        '演唱': 4,
        '现场': 2,
        '情感': 2130301,
        'ACG': 2131301,
        '明星': 2132301,
        '演奏': 3,
        '生活': 8001,
        '舞蹈': 6001,
        '影视': 3001,
        '知识': 2125301,
    }

    items = []
    for category in categories:
        if categories[category] == 1001:
            items.append({'label': category, 'path': plugin.url_for(
                'mlog', cid=categories[category], pagenum=1)})
        else:
            items.append({'label': category, 'path': plugin.url_for(
                'mlog', cid=categories[category], pagenum=0)})
    return items


# Mlog
@plugin.route('/mlog/<cid>/<pagenum>/')
def mlog(cid, pagenum):
    items = []
    resp = music.mlog_socialsquare(cid, pagenum)
    mlogs = resp['data']['feeds']
    for video in mlogs:
        mid = video['id']
        if cid == '1002':
            path = plugin.url_for('play', meida_type='mv',
                                  song_id=0, mv_id=mid, sourceId=cid, dt=0)
        else:
            path = plugin.url_for('play', meida_type='mlog',
                                  song_id=0, mv_id=mid, sourceId=cid, dt=0)

        items.append({
            'label': video['resource']['mlogBaseData']['text'],
            'path': path,
            'is_playable': True,
            'icon': video['resource']['mlogBaseData']['coverUrl'],
            'thumbnail': video['resource']['mlogBaseData']['coverUrl'],
            'info': {
                'mediatype': 'video',
                'title': video['resource']['mlogBaseData']['text'],
                'duration': video['resource']['mlogBaseData']['duration']//1000
            },
            'info_type': 'video',
        })
    items.append({'label': tag('下一页', 'yellow'), 'path': plugin.url_for(
        'mlog', cid=cid, pagenum=int(pagenum)+1)})
    return items


# 热门MV
@plugin.route('/top_mvs/<offset>/')
def top_mvs(offset):
    offset = int(offset)
    result = music.top_mv(offset=offset, limit=limit)
    more = result['hasMore']
    mvs = result['data']
    items = get_mvs_items(mvs)
    if more:
        items.append({'label': tag('下一页', 'yellow'), 'path': plugin.url_for(
            'top_mvs', offset=str(offset+limit))})
    return items


# 新歌速递
@plugin.route('/new_songs/')
def new_songs():
    return get_songs_items(music.new_songs().get("data", []))


# 新碟上架
@plugin.route('/new_albums/<offset>/')
def new_albums(offset):
    offset = int(offset)
    result = music.new_albums(offset=offset, limit=limit)
    total = result.get('total', 0)
    albums = result.get('albums', [])
    items = get_albums_items(albums)
    if len(albums) + offset < total:
        items.append({'label': tag('下一页', 'yellow'), 'path': plugin.url_for(
            'new_albums', offset=str(offset+limit))})
    return items


# 排行榜
@plugin.route('/toplists/')
def toplists():
    items = get_playlists_items(music.toplists().get("list", []))
    return items


# 热门歌手
@plugin.route('/top_artists/')
def top_artists():
    return get_artists_items(music.top_artists().get("artists", []))


# 每日推荐
@plugin.route('/recommend_songs/')
def recommend_songs():
    return get_songs_items(music.recommend_playlist().get('data', {}).get('dailySongs', []))


# 历史日推
@plugin.route('/history_recommend_songs/<date>/')
def history_recommend_songs(date):
    return get_songs_items(music.history_recommend_detail(date).get('data', {}).get('songs', []))


def get_albums_items(albums):
    items = []
    for album in albums:
        if 'name' in album:
            name = album['name']
        elif 'albumName' in album:
            name = album['albumName']
        if 'size' in album:
            plot_info = '[COLOR pink]' + name + \
                '[/COLOR]  共' + str(album['size']) + '首歌\n'
        else:
            plot_info = '[COLOR pink]' + name + '[/COLOR]\n'
        if 'paidTime' in album and album['paidTime']:
            plot_info += '购买时间: ' + trans_time(album['paidTime']) + '\n'
        if 'type' in album and album['type']:
            plot_info += '类型: ' + album['type']
            if 'subType' in album and album['subType']:
                plot_info += ' - ' + album['subType'] + '\n'
            else:
                plot_info += '\n'
        if 'company' in album and album['company']:
            plot_info += '公司: ' + album['company'] + '\n'
        if 'id' in album:
            plot_info += '专辑id: ' + str(album['id'])+'\n'
            album_id = album['id']
        elif 'albumId' in album:
            plot_info += '专辑id: ' + str(album['albumId'])+'\n'
            album_id = album['albumId']
        if 'publishTime' in album and album['publishTime'] is not None:
            plot_info += '发行时间: '+trans_date(album['publishTime'])+'\n'
        if 'subTime' in album and album['subTime'] is not None:
            plot_info += '收藏时间: '+trans_date(album['subTime'])+'\n'
        if 'description' in album and album['description'] is not None:
            plot_info += album['description'] + '\n'
        if 'picUrl' in album:
            picUrl = album['picUrl']
        elif 'cover' in album:
            picUrl = album['cover']

        items.append({
            'label': album['artists'][0]['name'] + ' - ' + name,
            'path': plugin.url_for('album', id=album_id),
            'icon': picUrl,
            'thumbnail': picUrl,
            'info': {'plot': plot_info},
            'info_type': 'video',
        })
    return items


@plugin.route('/albums/<artist_id>/<offset>/')
def albums(artist_id, offset):
    offset = int(offset)
    result = music.artist_album(artist_id, offset=offset, limit=limit)
    more = result.get('more', False)
    albums = result.get('hotAlbums', [])
    items = get_albums_items(albums)
    if more:
        items.append({'label': tag('下一页', 'yellow'), 'path': plugin.url_for(
            'albums', artist_id=artist_id, offset=str(offset+limit))})
    return items


@plugin.route('/album/<id>/')
def album(id):
    result = music.album(id)
    return get_songs_items(result.get("songs", []), sourceId=id, picUrl=result.get('album', {}).get('picUrl', ''))


@plugin.route('/artist/<id>/')
def artist(id):
    items = [
        {'label': '热门50首', 'path': plugin.url_for('hot_songs', id=id)},
        {'label': '所有歌曲', 'path': plugin.url_for(
            'artist_songs', id=id, offset=0)},
        {'label': '专辑', 'path': plugin.url_for(
            'albums', artist_id=id, offset='0')},
        {'label': 'MV', 'path': plugin.url_for('artist_mvs', id=id, offset=0)},
    ]

    info = music.artist_info(id).get("artist", {})
    if 'accountId' in info:
        items.append({'label': '用户页', 'path': plugin.url_for(
            'user', id=info['accountId'])})

    if account['logined']:
        items.append(
            {'label': '相似歌手', 'path': plugin.url_for('similar_artist', id=id)})
    return items


@plugin.route('/similar_artist/<id>/')
def similar_artist(id):
    artists = music.similar_artist(id).get("artists", [])
    return get_artists_items(artists)


@plugin.route('/artist_mvs/<id>/<offset>/')
def artist_mvs(id, offset):
    offset = int(offset)
    result = music.artist_mvs(id, offset, limit)
    more = result.get('more', False)
    mvs = result.get("mvs", [])
    items = get_mvs_items(mvs)
    if more:
        items.append({'label': tag('下一页', 'yellow'), 'path': plugin.url_for(
            'albums', id=id, offset=str(offset+limit))})
    return items


@plugin.route('/hot_songs/<id>/')
def hot_songs(id):
    result = music.artists(id).get("hotSongs", [])
    ids = [a['id'] for a in result]
    resp = music.songs_detail(ids)
    datas = resp['songs']
    privileges = resp['privileges']
    return get_songs_items(datas, privileges=privileges)


@plugin.route('/artist_songs/<id>/<offset>/')
def artist_songs(id, offset):
    result = music.artist_songs(id, limit=limit, offset=offset)
    ids = [a['id'] for a in result.get('songs', [])]
    resp = music.songs_detail(ids)
    datas = resp['songs']
    privileges = resp['privileges']
    items = get_songs_items(datas, privileges=privileges)
    if result['more']:
        items.append({'label': '[COLOR yellow]下一页[/COLOR]', 'path': plugin.url_for(
            'artist_songs', id=id, offset=int(offset)+limit)})
    return items


# 我的收藏
@plugin.route('/sublist/')
def sublist():
    items = [
        {'label': '歌手', 'path': plugin.url_for('artist_sublist')},
        {'label': '专辑', 'path': plugin.url_for('album_sublist')},
        {'label': '视频', 'path': plugin.url_for('video_sublist')},
        {'label': '播单', 'path': plugin.url_for('dj_sublist', offset=0)},
        {'label': '我的数字专辑', 'path': plugin.url_for('digitalAlbum_purchased')},
        {'label': '已购单曲', 'path': plugin.url_for('song_purchased', offset=0)},
    ]
    return items


@plugin.route('/song_purchased/<offset>/')
def song_purchased(offset):
    result = music.single_purchased(offset=offset, limit=limit)
    ids = [a['songId'] for a in result.get('data', {}).get('list', [])]
    resp = music.songs_detail(ids)
    datas = resp['songs']
    privileges = resp['privileges']
    items = get_songs_items(datas, privileges=privileges)

    if result.get('data', {}).get('hasMore', False):
        items.append({'label': '[COLOR yellow]下一页[/COLOR]',
                     'path': plugin.url_for('song_purchased', offset=int(offset)+limit)})
    return items


@plugin.route('/dj_sublist/<offset>/')
def dj_sublist(offset):
    result = music.dj_sublist(offset=offset, limit=limit)
    items = get_djlists_items(result['djRadios'])
    if result['hasMore']:
        items.append({'label': '[COLOR yellow]下一页[/COLOR]',
                     'path': plugin.url_for('dj_sublist', offset=int(offset)+limit)})
    return items


def get_djlists_items(playlists):
    items = []
    for playlist in playlists:
        plot_info = '[COLOR pink]' + playlist['name'] + \
            '[/COLOR]  共' + str(playlist['programCount']) + '个声音\n'
        if 'lastProgramCreateTime' in playlist and playlist['lastProgramCreateTime'] is not None:
            plot_info += '更新时间: ' + \
                trans_time(playlist['lastProgramCreateTime']) + '\n'
        if 'subCount' in playlist and playlist['subCount'] is not None:
            plot_info += '收藏人数: '+trans_num(playlist['subCount'])+'\n'
        plot_info += '播单id: ' + str(playlist['id'])+'\n'
        if 'dj' in playlist and playlist['dj'] is not None:
            plot_info += '创建用户: ' + \
                playlist['dj']['nickname'] + '  id: ' + \
                str(playlist['dj']['userId']) + '\n'
        if 'createTime' in playlist and playlist['createTime'] is not None:
            plot_info += '创建时间: '+trans_time(playlist['createTime'])+'\n'
        if 'desc' in playlist and playlist['desc'] is not None:
            plot_info += playlist['desc'] + '\n'

        if 'coverImgUrl' in playlist and playlist['coverImgUrl'] is not None:
            img_url = playlist['coverImgUrl']
        elif 'picUrl' in playlist and playlist['picUrl'] is not None:
            img_url = playlist['picUrl']
        else:
            img_url = ''

        name = playlist['name']

        items.append({
            'label': name,
            'path': plugin.url_for('djlist', id=playlist['id']),
            'icon': img_url,
            'thumbnail': img_url,
            'info': {
                'plot': plot_info
            },
            'info_type': 'video',
        })
    return items


@plugin.route('/djlist/<id>/')
def djlist(id):
    resp = music.dj_program(id)
    return get_dj_items(resp.get('programs'), id)


def get_dj_items(songs, sourceId):
    items = []
    for play in songs:
        # xbmc.log('voice_test:%s'%play)
        ar_name = play['dj']['nickname']

        label = play['name']

        items.append({
            'label': label,
            'path': plugin.url_for('play', meida_type='dj', song_id=str(play['id']), mv_id=str(0), sourceId=str(sourceId), dt=str(play['duration']//1000)),
            'is_playable': True,
            'icon': play.get('coverUrl', None),
            'thumbnail': play.get('coverUrl', None),
            'fanart': play.get('coverUrl', None),
            'info': {
                'mediatype': 'music',
                'title': play['name'],
                'artist': ar_name,
                'album': play['radio']['name'],
                # 'tracknumber':play['no'],
                # 'discnumber':play['disc'],
                # 'duration': play['dt']//1000,
                # 'dbid':play['id'],
            },
            'info_type': 'music',
        })
    return items


@plugin.route('/digitalAlbum_purchased/')
def digitalAlbum_purchased():
    # items = []
    albums = music.digitalAlbum_purchased().get("paidAlbums", [])
    return get_albums_items(albums)


def get_mvs_items(mvs):
    items = []
    for mv in mvs:
        if 'artists' in mv:
            name = '&'.join([artist['name'] for artist in mv['artists']])
        elif 'artist' in mv:
            name = mv['artist']['name']
        elif 'artistName' in mv:
            name = mv['artistName']
        else:
            name = ''
        mv_url = music.mv_url(mv['id']).get("data", {})
        url = mv_url['url']
        if 'cover' in mv:
            cover = mv['cover']
        elif 'imgurl' in mv:
            cover = mv['imgurl']
        else:
            cover = None
        # top_mvs->mv['subed']收藏;
        items.append({
            'label': name + ' - ' + mv['name'],
            'path': url,
            'is_playable': True,
            'icon': cover,
            'thumbnail': cover,
            'info': {
                'mediatype': 'video',
                'title': mv['name'],
            },
            'info_type': 'video',
        })
    return items


def get_videos_items(videos):
    items = []
    for video in videos:
        type = video['type']  # MV:0 , video:1
        if type == 0:
            type = tag('[MV]')
            result = music.mv_url(video['vid']).get("data", {})
            url = result['url']
        else:
            type = ''
            result = music.video_url(video['vid']).get("urls", [])
            url = result[0]['url']
        ar_name = '&'.join([str(creator['userName'])
                           for creator in video['creator']])
        items.append({
            'label': type + ar_name + ' - ' + video['title'],
            'path': url,
            'is_playable': True,
            'icon': video['coverUrl'],
            'thumbnail': video['coverUrl'],
            # 'context_menu':context_menu,
            'info': {
                'mediatype': 'video',
                'title': video['title'],
                # 'duration':video['durationms']//1000
            },
            'info_type': 'video',
        })
    return items


@plugin.route('/playlist_contextmenu/<action>/<id>/')
def playlist_contextmenu(action, id):
    if action == 'subscribe':
        resp = music.playlist_subscribe(id)
        if resp['code'] == 200:
            title = '成功'
            msg = '收藏成功'
        elif resp['code'] == 401:
            title = '失败'
            msg = '不能收藏自己的歌单'
        elif resp['code'] == 501:
            title = '失败'
            msg = '已经收藏过该歌单了'
        else:
            title = '失败'
            msg = str(resp['code'])+': 未知错误'
        dialog = xbmcgui.Dialog()
        dialog.notification(title, msg, xbmcgui.NOTIFICATION_INFO, 800, False)
    elif action == 'unsubscribe':
        resp = music.playlist_unsubscribe(id)
        if resp['code'] == 200:
            title = '成功'
            msg = '取消收藏成功'
            dialog = xbmcgui.Dialog()
        dialog.notification(title, msg, xbmcgui.NOTIFICATION_INFO, 800, False)
    elif action == 'delete':
        resp = music.playlist_delete([id])
        if resp['code'] == 200:
            title = '成功'
            msg = '删除成功'
        else:
            title = '失败'
            msg = '删除失败'
        # xbmc.executebuiltin('Container.Refresh(%s)'%url)
        dialog = xbmcgui.Dialog()
        dialog.notification(title, msg, xbmcgui.NOTIFICATION_INFO, 800, False)


def get_playlists_items(playlists):
    items = []

    for playlist in playlists:
        context_menu = []
        plot_info = '[COLOR pink]' + playlist['name'] + \
            '[/COLOR]  共' + str(playlist['trackCount']) + '首歌\n'
        if 'updateFrequency' in playlist and playlist['updateFrequency'] is not None:
            plot_info += '更新频率: ' + playlist['updateFrequency'] + '\n'
        if 'updateTime' in playlist and playlist['updateTime'] is not None:
            plot_info += '更新时间: ' + trans_time(playlist['updateTime']) + '\n'

        if 'subscribed' in playlist and playlist['subscribed'] is not None:
            if playlist['subscribed']:
                plot_info += '收藏状态: 已收藏\n'
                item = ('取消收藏', 'RunPlugin(%s)' % plugin.url_for(
                    'playlist_contextmenu', action='unsubscribe', id=playlist['id']))
                context_menu.append(item)
            else:
                if 'creator' in playlist and playlist['creator'] is not None and str(playlist['creator']['userId']) != account['uid']:
                    plot_info += '收藏状态: 未收藏\n'
                    item = ('收藏', 'RunPlugin(%s)' % plugin.url_for(
                        'playlist_contextmenu', action='subscribe', id=playlist['id']))
                    context_menu.append(item)
        else:
            if 'creator' in playlist and playlist['creator'] is not None and str(playlist['creator']['userId']) != account['uid']:
                item = ('收藏', 'RunPlugin(%s)' % plugin.url_for(
                    'playlist_contextmenu', action='subscribe', id=playlist['id']))
                context_menu.append(item)

        if 'subscribedCount' in playlist and playlist['subscribedCount'] is not None:
            plot_info += '收藏人数: '+trans_num(playlist['subscribedCount'])+'\n'
        if 'playCount' in playlist and playlist['playCount'] is not None:
            plot_info += '播放次数: '+trans_num(playlist['playCount'])+'\n'
        if 'playcount' in playlist and playlist['playcount'] is not None:
            plot_info += '播放次数: '+trans_num(playlist['playcount'])+'\n'
        plot_info += '歌单id: ' + str(playlist['id'])+'\n'
        if 'creator' in playlist and playlist['creator'] is not None:
            plot_info += '创建用户: '+playlist['creator']['nickname'] + \
                '  id: ' + str(playlist['creator']['userId']) + '\n'
            creator_name = playlist['creator']['nickname']
            creator_id = playlist['creator']['userId']
        else:
            creator_name = '网易云音乐'
            creator_id = 1
        if 'createTime' in playlist and playlist['createTime'] is not None:
            plot_info += '创建时间: '+trans_time(playlist['createTime'])+'\n'
        if 'description' in playlist and playlist['description'] is not None:
            plot_info += playlist['description'] + '\n'

        if 'coverImgUrl' in playlist and playlist['coverImgUrl'] is not None:
            img_url = playlist['coverImgUrl']
        elif 'picUrl' in playlist and playlist['picUrl'] is not None:
            img_url = playlist['picUrl']
        else:
            img_url = ''

        name = playlist['name']
        if 'specialType' in playlist and playlist['specialType'] == 200:
            name += tag(' 视频')
            ptype = 'video'
        else:
            ptype = 'normal'
        if 'creator' in playlist and playlist['creator'] is not None and str(playlist['creator']['userId']) == account['uid']:
            item = ('删除歌单', 'RunPlugin(%s)' % plugin.url_for(
                'playlist_contextmenu', action='delete', id=playlist['id']))
            context_menu.append(item)

        items.append({
            'label': name,
            'path': plugin.url_for('playlist', ptype=ptype, id=playlist['id']),
            'icon': img_url,
            'thumbnail': img_url,
            'context_menu': context_menu,
            'info': {
                'plot': plot_info
            },
            'info_type': 'video',
        })
    return items


@plugin.route('/video_sublist/')
def video_sublist():
    return get_videos_items(music.video_sublist().get("data", []))


@plugin.route('/album_sublist/')
def album_sublist():
    return get_albums_items(music.album_sublist().get("data", []))


def get_artists_items(artists):
    items = []
    # xbmc.log(str(artists))
    for artist in artists:
        plot_info = '[COLOR pink]' + artist['name'] + '[/COLOR]'
        if 'musicSize' in artist and artist['musicSize']:
            plot_info += '  共' + str(artist['musicSize']) + '首歌\n'
        else:
            plot_info += '\n'

        if 'albumSize' in artist and artist['albumSize']:
            plot_info += '专辑数: ' + str(artist['albumSize']) + '\n'
        if 'mvSize' in artist and artist['mvSize']:
            plot_info += 'MV数: ' + str(artist['mvSize']) + '\n'
        plot_info += '歌手id: ' + str(artist['id'])+'\n'
        name = artist['name']
        if 'alias' in artist and artist['alias']:
            name += '('+artist['alias'][0]+')'
        elif 'trans' in artist and artist['trans']:
            name += '('+artist['trans']+')'

        items.append({
            'label': name,
            'path': plugin.url_for('artist', id=artist['id']),
            'icon': artist['picUrl'],
            'thumbnail': artist['picUrl'],
            'info': {'plot': plot_info},
            'info_type': 'video'
        })
    return items


def get_users_items(users):
    vip_level = ['壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖', '拾']
    items = []
    for user in users:
        plot_info = tag(user['nickname'], 'pink')
        if 'followed' in user:
            if user['followed'] == True:
                plot_info += '  [COLOR red]已关注[/COLOR]\n'
                context_menu = [('取消关注', 'RunPlugin(%s)' % plugin.url_for(
                    'follow_user', type='0', id=user['userId']))]
            else:
                plot_info += '\n'
                context_menu = [('关注该用户', 'RunPlugin(%s)' % plugin.url_for(
                    'follow_user', type='1', id=user['userId']))]
        else:
            plot_info += '\n'
        # userType: 0 普通用户 | 2 歌手 | 4 音乐人 | 10 官方账号 | 200 歌单达人 | 204 Mlog达人
        if user['vipType'] == 10:
            level_str = tag('音乐包', 'red')
            if user['userType'] == 4:
                plot_info += level_str + tag('  音乐人', 'red') + '\n'
            else:
                plot_info += level_str + '\n'
        elif user['vipType'] == 11:
            level = user['vipRights']['redVipLevel']
            level_str = tag('vip·' + vip_level[level], 'red')
            if user['userType'] == 4:
                plot_info += level_str + tag('  音乐人', 'red') + '\n'
            else:
                plot_info += level_str + '\n'
        else:
            level_str = ''
            if user['userType'] == 4:
                plot_info += tag('音乐人', 'red') + '\n'

        if 'description' in user and user['description'] != '':
            plot_info += user['description'] + '\n'
        if 'signature' in user and user['signature']:
            plot_info += '签名: ' + user['signature'] + '\n'
        plot_info += '用户id: ' + str(user['userId'])+'\n'

        items.append({
            'label': user['nickname']+' '+level_str,
            'path': plugin.url_for('user', id=user['userId']),
            'icon': user['avatarUrl'],
            'thumbnail': user['avatarUrl'],
            'context_menu': context_menu,
            'info': {'plot': plot_info},
            'info_type': 'video',
        })
    return items


@plugin.route('/follow_user/<type>/<id>/')
def follow_user(type, id):
    # result = music.user_follow(type, id)
    if type == '1':
        result = music.user_follow(id)
        if 'code' in result:
            if result['code'] == 200:
                xbmcgui.Dialog().notification('关注用户', '关注成功', xbmcgui.NOTIFICATION_INFO, 800, False)
            elif result['code'] == 201:
                xbmcgui.Dialog().notification('关注用户', '您已关注过该用户',
                                              xbmcgui.NOTIFICATION_INFO, 800, False)
            elif result['code'] == 400:
                xbmcgui.Dialog().notification('关注用户', '不能关注自己',
                                              xbmcgui.NOTIFICATION_INFO, 800, False)
            elif 'mas' in result:
                xbmcgui.Dialog().notification(
                    '关注用户', result['msg'], xbmcgui.NOTIFICATION_INFO, 800, False)
    else:
        result = music.user_delfollow(id)
        if 'code' in result:
            if result['code'] == 200:
                xbmcgui.Dialog().notification('取消关注用户', '取消关注成功',
                                              xbmcgui.NOTIFICATION_INFO, 800, False)
            elif result['code'] == 201:
                xbmcgui.Dialog().notification('取消关注用户', '您已不关注该用户了',
                                              xbmcgui.NOTIFICATION_INFO, 800, False)
            elif 'mas' in result:
                xbmcgui.Dialog().notification(
                    '取消关注用户', result['msg'], xbmcgui.NOTIFICATION_INFO, 800, False)


@plugin.route('/user/<id>/')
def user(id):
    items = [
        {'label': '歌单', 'path': plugin.url_for('user_playlists', uid=id)},
        {'label': '听歌排行', 'path': plugin.url_for('play_record', uid=id)},
        {'label': '关注列表', 'path': plugin.url_for(
            'user_getfollows', uid=id, offset='0')},
        {'label': '粉丝列表', 'path': plugin.url_for(
            'user_getfolloweds', uid=id, offset=0)},
    ]

    if account['uid'] == id:
        items.append(
            {'label': '每日推荐', 'path': plugin.url_for('recommend_songs')})
        items.append(
            {'label': '历史日推', 'path': plugin.url_for('history_recommend_dates')})

    info = music.user_detail(id)
    if 'artistId' in info.get('profile', {}):
        items.append({'label': '歌手页', 'path': plugin.url_for(
            'artist', id=info['profile']['artistId'])})
    return items


@plugin.route('/history_recommend_dates/')
def history_recommend_dates():
    dates = music.history_recommend_recent().get('data', {}).get('dates', [])
    items = []
    for date in dates:
        items.append({'label': date, 'path': plugin.url_for(
            'history_recommend_songs', date=date)})
    return items


@plugin.route('/play_record/<uid>/')
def play_record(uid):
    items = [
        {'label': '最近一周', 'path': plugin.url_for(
            'show_play_record', uid=uid, type='1')},
        {'label': '全部时间', 'path': plugin.url_for(
            'show_play_record', uid=uid, type='0')},
    ]
    return items


@plugin.route('/show_play_record/<uid>/<type>/')
def show_play_record(uid, type):
    result = music.play_record(uid, type)
    code = result.get('code', -1)
    if code == -2:
        xbmcgui.Dialog().notification('无权访问', '由于对方设置，你无法查看TA的听歌排行',
                                      xbmcgui.NOTIFICATION_INFO, 800, False)
    elif code == 200:
        if type == '1':
            songs = result.get('weekData', [])
        else:
            songs = result.get('allData', [])
        items = get_songs_items(songs)

        # 听歌次数
        # for i in range(len(items)):
        #     items[i]['label'] = items[i]['label'] + ' [COLOR red]' + str(songs[i]['playCount']) + '[/COLOR]'

        return items


@plugin.route('/user_getfolloweds/<uid>/<offset>/')
def user_getfolloweds(uid, offset):
    result = music.user_getfolloweds(userId=uid, offset=offset, limit=limit)
    more = result['more']
    followeds = result['followeds']
    items = get_users_items(followeds)
    if more:
        # time = followeds[-1]['time']
        items.append({'label': tag('下一页', 'yellow'), 'path': plugin.url_for(
            'user_getfolloweds', uid=uid, offset=int(offset)+limit)})
    return items


@plugin.route('/user_getfollows/<uid>/<offset>/')
def user_getfollows(uid, offset):
    offset = int(offset)
    result = music.user_getfollows(uid, offset=offset, limit=limit)
    more = result['more']
    follows = result['follow']
    items = get_users_items(follows)
    if more:
        items.append({'label': '[COLOR yellow]下一页[/COLOR]', 'path': plugin.url_for(
            'user_getfollows', uid=uid, offset=str(offset+limit))})
    return items


@plugin.route('/artist_sublist/')
def artist_sublist():
    return get_artists_items(music.artist_sublist().get("data", []))


@plugin.route('/search/')
def search():
    items = [
        {'label': '综合搜索', 'path': plugin.url_for('sea', type='1018')},
        {'label': '单曲搜索', 'path': plugin.url_for('sea', type='1')},
        {'label': '歌手搜索', 'path': plugin.url_for('sea', type='100')},
        {'label': '专辑搜索', 'path': plugin.url_for('sea', type='10')},
        {'label': '歌单搜索', 'path': plugin.url_for('sea', type='1000')},
        {'label': '云盘搜索', 'path': plugin.url_for('sea', type='-1')},
        {'label': 'M V搜索', 'path': plugin.url_for('sea', type='1004')},
        {'label': '视频搜索', 'path': plugin.url_for('sea', type='1014')},
        {'label': '歌词搜索', 'path': plugin.url_for('sea', type='1006')},
        {'label': '用户搜索', 'path': plugin.url_for('sea', type='1002')},
        {'label': '播客搜索', 'path': plugin.url_for('sea', type='1009')},
    ]
    return items


@plugin.route('/sea/<type>/')
def sea(type):
    items = []
    keyboard = xbmc.Keyboard('', '请输入搜索内容')
    xbmc.sleep(1500)
    keyboard.doModal()
    if (keyboard.isConfirmed()):
        keyword = keyboard.getText()
    else:
        return

    # 搜索云盘
    if type == '-1':
        datas = []
        kws = keyword.lower().split(' ')
        while '' in kws:
            kws.remove('')
        xbmc.log('kws='+str(kws))
        if len(kws) == 0:
            pass
        else:
            result = music.cloud_songlist(offset=0, limit=2000)
            playlist = result.get('data', [])
            if result.get('hasMore', False):
                result = music.cloud_songlist(
                    offset=2000, limit=result['count']-2000)
                playlist.extend(result.get('data', []))

            for song in playlist:
                # xbmc.log(str(song))
                if 'ar' in song['simpleSong'] and song['simpleSong']['ar'] is not None and song['simpleSong']['ar'][0]['name'] is not None:
                    artist = " ".join(
                        [a["name"] for a in song['simpleSong']["ar"] if a["name"] is not None])
                else:
                    artist = song['artist']
                if 'al' in song['simpleSong'] and song['simpleSong']['al'] is not None and song['simpleSong']['al']['name'] is not None:
                    album = song['simpleSong']['al']['name']
                else:
                    album = song['album']
                if 'alia' in song['simpleSong'] and song['simpleSong']['alia'] is not None:
                    alia = " ".join(
                        [a for a in song['simpleSong']["alia"] if a is not None])
                else:
                    alia = ''
                # filename = song['fileName']

                matched = True
                for kw in kws:
                    if kw != '':
                        if (kw in song['simpleSong']['name'].lower()) or (kw in artist.lower()) or (kw in album.lower()) or (kw in alia.lower()):
                            pass
                        else:
                            matched = False
                            break
                if matched:
                    datas.append(song)
        if len(datas) > 0:
            items = get_songs_items(datas)
            return items
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    result = music.search(keyword, stype=type).get("result", {})
    # 搜索单曲
    if type == '1':
        if 'songs' in result:
            sea_songs = result.get('songs', [])

            if xbmcplugin.getSetting(int(sys.argv[1]), 'hide_cover_songs') == 'true':
                filtered_songs = [
                    song for song in sea_songs if '翻自' not in song['name'] and 'cover' not in song['name'].lower()]
            else:
                filtered_songs = sea_songs

            ids = [a['id'] for a in filtered_songs]
            resp = music.songs_detail(ids)
            datas = resp['songs']
            privileges = resp['privileges']
            items = get_songs_items(datas, privileges=privileges)
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索歌词
    if type == '1006':
        if 'songs' in result:
            sea_songs = result.get('songs', [])
            ids = [a['id'] for a in sea_songs]
            resp = music.songs_detail(ids)
            datas = resp['songs']
            privileges = resp['privileges']

            for i in range(len(datas)):
                datas[i]['lyrics'] = sea_songs[i]['lyrics']

            if xbmcplugin.getSetting(int(sys.argv[1]), 'hide_cover_songs') == 'true':
                filtered_datas = []
                filtered_privileges = []
                for i in range(len(datas)):
                    if '翻自' not in datas[i]['name'] and 'cover' not in datas[i]['name'].lower():
                        filtered_datas.append(datas[i])
                        filtered_privileges.append(privileges[i])
            else:
                filtered_datas = datas
                filtered_privileges = privileges

            items = get_songs_items(
                filtered_datas, privileges=filtered_privileges, source='search_lyric')
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索专辑
    elif type == '10':
        if 'albums' in result:
            albums = result['albums']
            items.extend(get_albums_items(albums))
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索歌手
    elif type == '100':
        if 'artists' in result:
            artists = result['artists']
            items.extend(get_artists_items(artists))
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索用户
    elif type == '1002':
        if 'userprofiles' in result:
            users = result['userprofiles']
            items.extend(get_users_items(users))
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索歌单
    elif type == '1000':
        if 'playlists' in result:
            playlists = result['playlists']
            items.extend(get_playlists_items(playlists))
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索主播电台
    elif type == '1009':
        if 'djRadios' in result:
            playlists = result['djRadios']
            items.extend(get_djlists_items(playlists))
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索MV
    elif type == '1004':
        if 'mvs' in result:
            mvs = result['mvs']
            items.extend(get_mvs_items(mvs))
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 搜索视频
    elif type == '1014':
        if 'videos' in result:
            videos = result['videos']
            items.extend(get_videos_items(videos))
        else:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    # 综合搜索
    elif type == '1018':
        is_empty = True
        # 歌手
        if 'artist' in result:
            is_empty = False
            artist = result['artist']['artists'][0]
            item = get_artists_items([artist])[0]
            item['label'] = tag('[歌手]') + item['label']
            items.append(item)

        # 专辑
        if 'album' in result:
            is_empty = False
            album = result['album']['albums'][0]
            item = get_albums_items([album])[0]
            item['label'] = tag('[专辑]') + item['label']
            items.append(item)

        # 歌单
        if 'playList' in result:
            is_empty = False
            playList = result['playList']['playLists'][0]
            item = get_playlists_items([playList])[0]
            item['label'] = tag('[歌单]') + item['label']
            items.append(item)

        # MV & 视频
        if 'video' in result:
            is_empty = False
            # MV
            for video in result['video']['videos']:
                if video['type'] == 0:
                    mv_url = music.mv_url(video['vid']).get("data", {})
                    url = mv_url['url']
                    ar_name = '&'.join([str(creator['userName'])
                                       for creator in video['creator']])
                    name = tag('[M V]') + ar_name + '-' + video['title']
                    items.append({
                        'label': name,
                        'path': url,
                        'is_playable': True,
                        'icon': video['coverUrl'],
                        'thumbnail': video['coverUrl'],
                        'info': {
                            'mediatype': 'video',
                            'title': video['title'],
                            'duration': video['durationms']//1000
                        },
                        'info_type': 'video',
                    })
                    break
            # 视频
            for video in result['video']['videos']:
                if video['type'] == 1:
                    video_url = music.video_url(video['vid']).get("urls", [])
                    url = video_url[0]['url']
                    ar_name = '&'.join([str(creator['userName'])
                                       for creator in video['creator']])
                    name = tag('[视频]') + ar_name + '-' + video['title']
                    items.append({
                        'label': name,
                        'path': url,
                        'is_playable': True,
                        'icon': video['coverUrl'],
                        'thumbnail': video['coverUrl'],
                        'info': {
                            'mediatype': 'video',
                            'title': video['title'],
                            'duration': video['durationms']//1000
                        },
                        'info_type': 'video',
                    })
                    break
        # 单曲
        if 'song' in result:
            # is_empty = False
            # items.extend(get_songs_items([song['id'] for song in result['song']['songs']],getmv=False))
            sea_songs = result['song']['songs']
            if xbmcplugin.getSetting(int(sys.argv[1]), 'hide_cover_songs') == 'true':
                filtered_songs = [
                    song for song in sea_songs if '翻自' not in song['name'] and 'cover' not in song['name'].lower()]
            else:
                filtered_songs = sea_songs
            items.extend(get_songs_items(filtered_songs, getmv=False))
            if len(items) > 0:
                is_empty = False

        if is_empty:
            dialog = xbmcgui.Dialog()
            dialog.notification(
                '搜索', '无搜索结果', xbmcgui.NOTIFICATION_INFO, 800, False)
            return
    return items


@plugin.route('/personal_fm/')
def personal_fm():
    songs = []
    for i in range(10):
        songs.extend(music.personal_fm().get("data", []))
    return get_songs_items(songs)


@plugin.route('/recommend_playlists/')
def recommend_playlists():
    return get_playlists_items(music.recommend_resource().get("recommend", []))


@plugin.route('/user_playlists/<uid>/')
def user_playlists(uid):
    return get_playlists_items(music.user_playlist(uid).get("playlist", []))


@plugin.route('/playlist/<ptype>/<id>/')
def playlist(ptype, id):
    resp = music.playlist_detail(id)
    # return get_songs_items([song['id'] for song in songs],sourceId=id)
    if ptype == 'video':
        datas = resp.get('playlist', {}).get('videos', [])
        items = []
        for data in datas:

            label = data['mlogBaseData']['text']
            if 'song' in data['mlogExtVO']:
                artist = ", ".join([a["artistName"]
                                   for a in data['mlogExtVO']['song']['artists']])
                label += tag(' (' + artist + '-' +
                             data['mlogExtVO']['song']['name'] + ')', 'gray')
                context_menu = [
                    ('相关歌曲:%s' % (artist + '-' + data['mlogExtVO']['song']['name']), 'RunPlugin(%s)' % plugin.url_for('song_contextmenu', action='play_song', meida_type='song', song_id=str(
                        data['mlogExtVO']['song']['id']), mv_id=str(data['mlogBaseData']['id']), sourceId=str(id), dt=str(data['mlogExtVO']['song']['duration']//1000))),
                ]
            else:
                context_menu = []

            if data['mlogBaseData']['type'] == 2:
                # https://interface3.music.163.com/eapi/mlog/video/url
                meida_type = 'mlog'
            elif data['mlogBaseData']['type'] == 3:
                label = tag('[MV]') + label
                meida_type = 'mv'
            else:
                meida_type = ''

            items.append({
                'label': label,
                'path': plugin.url_for('play', meida_type=meida_type, song_id=str(data['mlogExtVO']['song']['id']), mv_id=str(data['mlogBaseData']['id']), sourceId=str(id), dt='0'),
                'is_playable': True,
                'icon': data['mlogBaseData']['coverUrl'],
                'thumbnail': data['mlogBaseData']['coverUrl'],
                'context_menu': context_menu,
                'info': {
                    'mediatype': 'video',
                    'title': data['mlogBaseData']['text'],
                },
                'info_type': 'video',
            })
        return items
    else:
        datas = resp.get('playlist', {}).get('tracks', [])
        privileges = resp.get('privileges', [])
        trackIds = resp.get('playlist', {}).get('trackIds', [])

        songs_number = len(trackIds)
        # 歌单中超过1000首歌
        if songs_number > len(datas):
            ids = [song['id'] for song in trackIds]
            resp2 = music.songs_detail(ids[songs_number:])
            datas.extend(resp2.get('songs', []))
            privileges.extend(resp2.get('privileges', []))
        return get_songs_items(datas, privileges=privileges, sourceId=id)


@plugin.route('/cloud/<offset>/')
def cloud(offset):
    offset = int(offset)
    result = music.cloud_songlist(offset=offset, limit=limit)
    more = result['hasMore']
    playlist = result['data']
    items = get_songs_items(playlist, offset=offset)
    if more:
        items.append({'label': tag('下一页', 'yellow'), 'path': plugin.url_for(
            'cloud', offset=str(offset+limit))})
    return items


if __name__ == '__main__':
    plugin.run()
