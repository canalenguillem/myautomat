import hashlib

def generate_id_from_url(url):
    hasher = hashlib.md5()
    hasher.update(url.encode('utf-8'))
    return hasher.hexdigest()


def get_video_id(video_url=None, video_id=None):
    if video_id:
        return video_id
    elif video_url:
        return generate_id_from_url(video_url)
    else:
        return "unknown_id"  # Usar un ID predeterminado o lanzador de error

