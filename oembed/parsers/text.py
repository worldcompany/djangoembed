import re

from django.utils.safestring import mark_safe

import oembed
from oembed.constants import URL_RE, STANDALONE_URL_RE
from oembed.exceptions import OEmbedException
from oembed.parsers.base import BaseParser


class TextBlockParser(BaseParser):
    def parse_data(self, text, maxwidth, maxheight, template_dir, context,
                   urlize_all_links):
        """
        Parses a block of text indiscriminately
        """
        # create a dictionary of user urls -> rendered responses
        replacements = {}
        user_urls = set(re.findall(URL_RE, text))
        
        for user_url in user_urls:
            try:
                resource = oembed.site.embed(user_url, maxwidth=maxwidth, maxheight=maxheight)
            except OEmbedException:
                if urlize_all_links:
                    replacements[user_url] = '<a href="%(LINK)s">%(LINK)s</a>' % {'LINK': user_url}
            else:
                context['minwidth'] = min(maxwidth, resource.width)
                context['minheight'] = min(maxheight, resource.height)
                
                replacement = self.render_oembed(
                    resource, 
                    user_url, 
                    template_dir=template_dir, 
                    context=context
                )
                replacements[user_url] = replacement.strip()
        
        # go through the text recording URLs that can be replaced
        # taking note of their start & end indexes
        user_urls = re.finditer(URL_RE, text)
        matches = []
        for match in user_urls:
            if match.group() in replacements:
                matches.append([match.start(), match.end(), match.group()])
        
        # replace the URLs in order, offsetting the indices each go
        for indx, (start, end, user_url) in enumerate(matches):
            replacement = replacements[user_url]
            difference = len(replacement) - len(user_url)
            
            # insert the replacement between two slices of text surrounding the
            # original url
            text = text[:start] + replacement + text[end:]
            
            # iterate through the rest of the matches offsetting their indices
            # based on the difference between replacement/original
            for j in xrange(indx + 1, len(matches)):
                matches[j][0] += difference
                matches[j][1] += difference
        return mark_safe(text)
    
    def extract_urls(self, text):
        urls = set()
        url_list = []
        for url in re.findall(URL_RE, text):
            if url not in urls:
                urls.add(url)
                url_list.append(url)
        
        return url_list


class TextParser(TextBlockParser):
    def parse_data(self, text, maxwidth, maxheight, template_dir, context, 
                   urlize_all_links):
        """
        Parses a block of text rendering links that occur on their own line
        normally but rendering inline links using a special template dir
        """
        block_parser = TextBlockParser()
        
        lines = text.splitlines()
        parsed = []
        
        for line in lines:
            if STANDALONE_URL_RE.match(line):
                user_url = line.strip()
                try:
                    resource = oembed.site.embed(user_url, maxwidth=maxwidth, maxheight=maxheight)
                    context['minwidth'] = min(maxwidth, resource.width)
                    context['minheight'] = min(maxheight, resource.height)
                except OEmbedException:
                    if urlize_all_links:
                        line = '<a href="%(LINK)s">%(LINK)s</a>' % {'LINK': user_url}
                else:
                    context['minwidth'] = min(maxwidth, resource.width)
                    context['minheight'] = min(maxheight, resource.height)
                    
                    line = self.render_oembed(
                        resource, 
                        user_url, 
                        template_dir=template_dir, 
                        context=context)
            else:
                line = block_parser.parse(line, maxwidth, maxheight, 'inline',
                                          context, urlize_all_links)
            
            parsed.append(line)
        
        return mark_safe('\n'.join(parsed))
