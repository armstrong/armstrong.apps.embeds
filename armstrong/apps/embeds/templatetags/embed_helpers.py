from django.template import Library, TemplateSyntaxError
from django.template.defaultfilters import stringfilter

from .. import logger

register = Library()


@register.filter
@stringfilter
def resize_iframe(value, new_width):
    if not value:
        return value

    try:
        from lxml.html import fromstring, tostring
    except ImportError as e:
        logger.error(
            "Cannot use template tag because lxml package is missing: %s" % e)
        return value

    new_width = int(new_width)
    if new_width < 0:
        raise TemplateSyntaxError("Can't set a negative size on an iframe")

    parsed = fromstring(value)

    for iframe in parsed.xpath('//iframe'):
        try:
            orig_width = int(iframe.attrib['width'])
        except (ValueError, KeyError):
            # don't set the width if the value isn't present or isn't a number
            continue

        if new_width < orig_width:
            scaler = new_width / float(iframe.attrib['width'])
            iframe.attrib['width'] = str(new_width)

            try:
                int(iframe.attrib['height'])
            except (ValueError, KeyError):
                # don't set height if the value isn't present or isn't a number
                pass
            else:
                new_height = float(iframe.attrib['height']) * scaler
                iframe.attrib['height'] = str(int(new_height))

    return tostring(parsed)
