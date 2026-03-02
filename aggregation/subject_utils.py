from panoptes_client import Subject
from skimage import io


def get_subject_image(subject):
    """Fetch the subject image from Panoptes (Zooniverse database).

    :param subject: Zooniverse subject ID.
    :type subject: int
    :return: RGB image for the subject.
    :rtype: numpy.ndarray
    """
    # get the subject metadata from Panoptes
    subjecti = Subject(int(subject))
    try:
        frame0_url = subjecti.raw['locations'][0]['image/png']
    except KeyError:
        frame0_url = subjecti.raw['locations'][0]['image/jpeg']

    img = io.imread(frame0_url)

    return img
