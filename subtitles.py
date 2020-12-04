import os


class Subtitle:
    def __init__(self, start=None, end=None, text=None):
        self.start = start
        self.end = end
        self.text = text

    def __repr__(self):
        return F'{secs_to_strtime(self.start)} {secs_to_strtime(self.end)} {self.text}'



# Timestamp <-> String

def strtime_to_secs(str_time):
    str_time = str_time.replace(',', '.')
    parts = str_time.split(':')

    if not (1 <= len(parts) <= 3):
        raise ValueError

    secs = float(parts[-1])

    if len(parts) > 1:
        secs += float(parts[-2]) * 60
    if len(parts) > 2:
        secs += float(parts[-3]) * 60 * 60

    return secs


def secs_to_strtime(secs):
    hrs = int(secs // (60 * 60))
    secs -= hrs * 60 * 60
    mins = int(secs // 60)
    secs -= mins * 60
    return F'{hrs}:{mins:02d}:{secs:06.3f}'



# Subtitle parsing

def parse_file(path):
    extension_i = path.rfind('.')
    if extension_i < 0:
        raise ValueError('Unknown Format')
    extension = path[extension_i+1:]
    parser = parsers.get(extension)
    if parser is None:
        raise ValueError('Unknown Format')
    return parser(path)


def parse_file_srt(path):
    f = open(path, 'r', encoding='utf-8')

    lines = []
    for l in f:
        l = l.rstrip()
        lines.append(l)
        if l == '':
            if len(lines) >= 4:
                time_parts = lines[1].split(' --> ')
                if len(time_parts) == 2:
                    text = '\n'.join(lines[2:-1])
                    start = strtime_to_secs(time_parts[0])
                    end = strtime_to_secs(time_parts[1])
                    yield Subtitle(start, end, text)
            lines = []

    f.close()


def parse_file_ass(path):
    f = open(path, 'r', encoding='utf-8')

    in_events = False
    for l in f:
            l = l.rstrip()

            if l.startswith('[') and l.endswith(']'):
                in_events = l[1:-1] == 'Events'

            elif in_events and l.startswith('Dialogue: '):
                l_parts = l[len('Dialogue: '):].split(',')

                if len(l_parts) < 10:
                    continue

                text = ','.join(l_parts[9:])
                start = strtime_to_secs(l_parts[1])
                end = strtime_to_secs(l_parts[2])
                yield Subtitle(start, end, text)

    f.close()


parsers = {
    'srt': parse_file_srt,
    'ass': parse_file_ass,
}



def find_sub_for_path(path):
    extension_idx = path.rfind('.')

    if extension_idx < 0:
        return None

    path_no_extension = path[:extension_idx+1]

    for extension in parsers.keys():
        check_path = path_no_extension + extension
        if os.path.isfile(check_path):
            return check_path

    return None
