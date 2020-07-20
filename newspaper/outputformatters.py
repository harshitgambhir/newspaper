# -*- coding: utf-8 -*-
"""
Output formatting to text via lxml xpath nodes abstracted in this file.
"""
__title__ = 'newspaper'
__author__ = 'Lucas Ou-Yang'
__license__ = 'MIT'
__copyright__ = 'Copyright 2014, Lucas Ou-Yang'

from html import unescape
import logging

from .text import innerTrim
import re

from functools  import reduce


log = logging.getLogger(__name__)


class OutputFormatter(object):

    def __init__(self, config):
        self.top_node = None
        self.config = config
        self.parser = self.config.get_parser()
        self.language = config.language
        self.stopwords_class = config.stopwords_class

    def update_language(self, meta_lang):
        '''Required to be called before the extraction process in some
        cases because the stopwords_class has to set incase the lang
        is not latin based
        '''
        if meta_lang:
            self.language = meta_lang
            self.stopwords_class = \
                self.config.get_stopwords_class(meta_lang)

    def get_top_node(self):
        return self.top_node

    def get_formatted(self, top_node, canonical_link, doc):
        """Returns the body text of an article, and also the body article
        html if specified. Returns in (text, html) form
        """
        self.top_node = top_node
        html, text = '', ''

        self.remove_negativescores_nodes()

        if self.config.keep_article_html:
            html = self.convert_to_html()

        self.links_to_text()
        self.add_newline_to_br()
        self.add_newline_to_li()
        self.replace_with_text()
        self.remove_empty_tags()
        self.remove_trailing_media_div()

        self.remove_h1_nodes()
        self.remove_ul_nodes()
        self.remove_ol_nodes()
        self.remove_unique_nodes(canonical_link)

        text = self.convert_to_text()
        firstp = self.get_firstp(canonical_link, doc)
        # print(self.parser.nodeToString(self.get_top_node()))

        return (text, firstp, html)

    def remove_h1_nodes(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='h1'):
            self.parser.remove(e)

    def remove_ul_nodes(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='ul'):
            self.parser.remove(e)

    def remove_ol_nodes(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='ol'):
            self.parser.remove(e)

    def remove_unique_nodes(self, canonical_link):
        if canonical_link.startswith("https://www.punjabkesari.in"):
            for e in self.top_node.xpath("//p[@itemprop='description']"):
                self.parser.remove(e)

    def convert_to_text(self):
        txts = []
        for node in list(self.get_top_node()):
            try:
                txt = self.parser.getText(node)
            except ValueError as err:  # lxml error
                log.info('%s ignoring lxml node error: %s', __title__, err)
                txt = None

            if txt:
                txt = unescape(txt)
                txt_lis = innerTrim(txt).split(r'\n')
                txt_lis = [n.strip(' ') for n in txt_lis]
                txts.extend(txt_lis)
        return '\n\n'.join(txts)

    def get_firstp(self, canonical_link, doc):
        txts = []
        txt = None
        try:
            if canonical_link.startswith("https://navbharattimes.indiatimes.com") or canonical_link.startswith("http://navbharattimes.indiatimes.com"):
                article_description = doc.xpath("//meta[@name='description']")
                if len(article_description) > 0:
                    article_description = [article_description[0]]
                    for e in article_description:
                        txt = e.attrib['content']
                        if(len(txt) > 10):
                            break
                else:
                    for e in self.parser.getElementsByTag(self.get_top_node(), tag='p'):
                        txt = self.parser.getText(e)
                        if(len(txt) > 10):
                            break
            elif canonical_link.startswith("https://khabar.ndtv.com") or canonical_link.startswith("http://khabar.ndtv.com"):
                article_description = doc.xpath("//span[@itemprop='description']")
                if len(article_description) > 0:
                    for e in article_description:
                        txt = e.attrib['content']
                        if(len(txt) > 10):
                            break
                else:
                    for e in self.parser.getElementsByTag(self.get_top_node(), tag='p'):
                        txt = self.parser.getText(e)
                        if(len(txt) > 10):
                            break
            elif canonical_link.startswith("https://zeenews.india.com") or canonical_link.startswith("http://zeenews.india.com"):
                article_description = doc.xpath("//meta[@name='description']")
                if len(article_description) > 0:
                    article_description = [article_description[0]]
                    for e in article_description:
                        txt = e.attrib['content']
                        if(len(txt) > 10):
                            break
            elif canonical_link.startswith("https://aajtak.intoday.in") or canonical_link.startswith("http://aajtak.intoday.in"):
                article_description = doc.xpath("//meta[@name='description']")
                if len(article_description) > 0:
                    article_description = [article_description[0]]
                    for e in article_description:
                        txt = e.attrib['content']
                        if(len(txt) > 10):
                            break
                else:
                    for e in self.parser.getElementsByTag(self.get_top_node(), tag='p'):
                        txt = self.parser.getText(e)
                        if(len(txt) > 10):
                            break
            elif canonical_link.startswith("https://www.indiatv.in") or canonical_link.startswith("http://www.indiatv.in"):
                article_description = doc.xpath("//meta[@property='og:description']")
                if len(article_description) > 0:
                    article_description = [article_description[0]]
                    for e in article_description:
                        txt = e.attrib['content']
                        if(len(txt) > 10):
                            break
                else:
                    for e in self.parser.getElementsByTag(self.get_top_node(), tag='p'):
                        txt = self.parser.getText(e)
                        if(len(txt) > 10):
                            break
            else:
                for e in self.parser.getElementsByTag(self.get_top_node(), tag='p'):
                    txt = self.parser.getText(e)
                    if(len(txt) > 10):
                        break

        except ValueError as err:  # lxml error
            log.info('%s ignoring lxml node error: %s', __title__, err)
            txt = None

        if txt:
            txt = unescape(txt)
            txt_lis = self.splitkeepsep(innerTrim(txt), '।')
            for txtx in txt_lis:
                if(len(txts) != 3):
                    new_text = re.sub(r'\(([^\)]+)\)', " ", txtx)
                    if(len(txts) == 0):
                        new_text = re.sub(r'^.*:', ' ', new_text)
                    txts.append(new_text)
        return ' '.join(txts)

    def splitkeepsep(self, s, sep):
        return reduce(lambda acc, elem: acc[:-1] + [acc[-1] + elem] if elem == sep else acc + [elem], re.split("(%s)" % re.escape(sep), s), [])

    def convert_to_html(self):
        cleaned_node = self.parser.clean_article_html(self.get_top_node())
        return self.parser.nodeToString(cleaned_node)

    def add_newline_to_br(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='br'):
            e.text = r'\n'

    def add_newline_to_li(self):
        for e in self.parser.getElementsByTag(self.top_node, tag='ul'):
            li_list = self.parser.getElementsByTag(e, tag='li')
            for li in li_list[:-1]:
                li.text = self.parser.getText(li) + r'\n'
                for c in self.parser.getChildren(li):
                    self.parser.remove(c)

    def links_to_text(self):
        """Cleans up and converts any nodes that should be considered
        text into text.
        """
        self.parser.stripTags(self.get_top_node(), 'a')

    def remove_negativescores_nodes(self):
        """If there are elements inside our top node that have a
        negative gravity score, let's give em the boot.
        """
        gravity_items = self.parser.css_select(
            self.top_node, "*[gravityScore]")
        for item in gravity_items:
            score = self.parser.getAttribute(item, 'gravityScore')
            score = float(score) if score else 0
            if score < 1:
                item.getparent().remove(item)

    def replace_with_text(self):
        """
        Replace common tags with just text so we don't have any crazy
        formatting issues so replace <br>, <i>, <strong>, etc....
        With whatever text is inside them.
        code : http://lxml.de/api/lxml.etree-module.html#strip_tags
        """
        self.parser.stripTags(
            self.get_top_node(), 'b', 'strong', 'i', 'br', 'sup')

    def remove_empty_tags(self):
        """It's common in top_node to exit tags that are filled with data
        within properties but not within the tags themselves, delete them
        """
        all_nodes = self.parser.getElementsByTags(
            self.get_top_node(), ['*'])
        all_nodes.reverse()
        for el in all_nodes:
            tag = self.parser.getTag(el)
            text = self.parser.getText(el)
            if (tag != 'br' or text != '\\r') \
                    and not text \
                    and len(self.parser.getElementsByTag(
                        el, tag='object')) == 0 \
                    and len(self.parser.getElementsByTag(
                        el, tag='embed')) == 0:
                if el.attrib.has_key('itemprop') and el.attrib.has_key('content') and el.attrib['itemprop'] == 'description':
                    continue
                self.parser.remove(el)

    def remove_trailing_media_div(self):
        """Punish the *last top level* node in the top_node if it's
        DOM depth is too deep. Many media non-content links are
        eliminated: "related", "loading gallery", etc. It skips removal if
        last top level node's class is one of NON_MEDIA_CLASSES.
        """

        NON_MEDIA_CLASSES = ('zn-body__read-all', )

        def get_depth(node, depth=1):
            """Computes depth of an lxml element via BFS, this would be
            in parser if it were used anywhere else besides this method
            """
            children = self.parser.getChildren(node)
            if not children:
                return depth
            max_depth = 0
            for c in children:
                e_depth = get_depth(c, depth + 1)
                if e_depth > max_depth:
                    max_depth = e_depth
            return max_depth

        top_level_nodes = self.parser.getChildren(self.get_top_node())
        if len(top_level_nodes) < 3:
            return

        last_node = top_level_nodes[-1]

        last_node_class = self.parser.getAttribute(last_node, 'class')
        if last_node_class in NON_MEDIA_CLASSES:
            return

        if get_depth(last_node) >= 2:
            self.parser.remove(last_node)
