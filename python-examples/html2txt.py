"""
	Insert a string containing HTML into a Tkinter Text widget.

	Author: Piers Lauder <piers@cs.su.oz.au> September 1998.

	Public functions:	Font2TkFont, HTML2Text, HTML2TextClean.
"""

__version__ = "1.18"
__author__ = "Piers Lauder <piers@cs.su.oz.au>"


import htmlentitydefs, htmllib, formatter, string, urlparse

try:
	import globals
except ImportError:
	class _X: pass
	globals = _X()
	globals.URLFGColour = 'blue'
	globals.OpenURLCmd = "netscape -remote 'openURL(%s, new-window)'"
	globals.AllowHREFURLQueries = 0
	globals.MaxURLShow = 60

try:
	from lib import readfile
	from logger import Debug
except ImportError:
	def Debug(l,s): pass
	def readfile(file):
		try:
			fd = open(file)
			html = fd.read()
			fd.close()
			return html
		except:
			return None



class TkTextWriter(formatter.NullWriter):

    """
	TkTextWriter class writes formatted text into Text widget.

	Instantiate as TkTextWriter(text, font, anchor)

		text   - Tk Text widget
		font   - base font for HTML
		anchor - function to handle anchor selections
			 will be called as anchor(href, base, text, cursor)
				href   - string from HREF attribute of anchor
				base   - string from HREF attribute of BASE
				text   - Text widget
				cursor - default cursor for text
		popup  - widget to display anchor value

	Errors cause default actions.
    """

    DefaultFontTuple = ('Helvetica', '10', 'normal', 'roman')

    # Map HTML Header tag sizes to (size, weight, slant) tuples.
    Hn2Points =	{
		'h1': ['18', 'bold', 'roman'],
		'h2': ['16', 'normal', 'roman'],
		'h3': ['14', 'normal', 'roman'],
		'h4': ['12', 'bold', 'roman'],
		'h5': ['10', 'bold', 'roman'],
		'h6':  ['8', 'bold', 'roman'],
		}

    # HTML Font tag sizes: range is 1 through 7, default is 3
    HTMLsize2points = [4,6,8,10,12,14,16,18]


    def __init__(self, text, basefont, doanchor, popup=None):

	self.text = text
	self.doanchor = doanchor
	self.popup = popup

	self.timer = None
	self.defcursor = text['cursor']

	self.tag_add = text.tag_add
	self.tag_bind = text.tag_bind
	self.tag_configure = text.tag_configure

	self.indent = None
	self._tags = {}
	self.font_stack = []
	self.align = None

	self.new_font_mark, self.new_font_tag = None, None

	self.width = int(text['width'])

	self.write = lambda d,i=text.insert: i('insert', d)

	try:
		basefont = Font2TkFont(basefont)
	except:
		basefont = Font2TkFont(self.DefaultFontTuple)
	try:
		self.basefont = Font2FontTuple(text, basefont)
	except:
		self.basefont = self.DefaultFontTuple
	self.font = self.basefont
	Debug(2, '''"self.basefont=%s"%`self.basefont`''')

	self.charpixelwidth = int(text.tk.call('font', 'measure', Font2TkFont(self.font), 'X'))
	Debug(2, '''"charpixelwidth=%s"%self.charpixelwidth''')

	size = max(int(self.basefont[1]), 7)
	self.HTMLsize2points = range(size-3*2, size+4*2+1, 2)
	Debug(2, '''"size=%s, HTMLsize2points=%s"%(size, `self.HTMLsize2points`)''')
	for i in range(7, 1, -1):
		self.Hn2Points['h%d'%(8-i)][0] = self.HTMLsize2points[i]
	# self.Hn2Points['h6'][0] = self.Hn2Points['h5'][0]
	Debug(2, '''"Hn2Points=%s"%`self.Hn2Points`''')

	self.configure = text.configure
	self.configure(font=Font2TkFont(self.basefont))

	Debug(1, '''"text font=%s, cursor=%s" % (text['font'], text['cursor'])''')

	self.reset()


    def reset(self):
	self.linebreak = 1
	self.atbreak = 0


    def _make_tag(self, name, **attrs):
	Debug(2, '''"_make_tag(%s, %s)" % (name, attrs)''')
	if self._tags.has_key(name):
		return name
	try:
		apply(self.tag_configure, (name,), attrs)
	except:
		pass
	self._tags[name] = 1
	return name


    def _make_hn_font(self, font):
	name, i, b, tt = font
	family, points, weight, slant = self.basefont
	if tt: family = 'Courier'
	heading = self.Hn2Points.get(name)
	if heading:
		points, weight, slant = heading
	else:
		if b: weight = 'bold'
		if i: slant = 'italic'
	return self._make_font(family, points, weight, slant)


    def _make_font(self, family, points, weight, slant):
	self.font = (family, str(points), weight, slant)
	name = string.join(filter(None, self.font), '_')
	return self._make_tag(name, font=Font2TkFont(self.font))


    def _htmlsize2font(self, size):
	if size[0] in ('+', '-'):
		rel, z = size[0], size[1:]
	else:
		rel, z = '', size

	try:	z = int(z)
	except:	return apply(self._make_font, self.font)

	if rel:
		points = int(self.font[1])
		for i in range(len(self.HTMLsize2points)):
			if self.HTMLsize2points[i] >= points:
				break
		z = eval('%s%s%s'%(i,rel,z))

	z = min(len(self.HTMLsize2points)-1, max(0, z))
	points = str(self.HTMLsize2points[z])
	return self._make_font(self.font[0], points, self.font[2], self.font[3])


    def start_body(self, attrs):	# BGCOLOR?
	Debug(1, '''"attrs=%s" % `attrs`''')


    def anchor_bgn(self, href, name, type, base):
	Debug(2, '''"anchor_bgn(%s, %s, %s, %s)" % (href, name, type, base)''')
	self.anchor = (href, base, name)
	self.anchor_mark = self.text.index("insert")


    def anchor_end(self):
	href, base, name = self.anchor
	if href:
		tag = "href_%s" % id(href or name)
		self._make_tag(tag, foreground=globals.URLFGColour, underline=1)
	else:
		tag = 'name_%s' % string.replace(name, ' ', '_')
		self._make_tag(tag)
	self.tag_add(tag, self.anchor_mark, "insert")
	if href:
		self.tag_bind(tag, "<ButtonPress>",
			lambda e,f=self.anchor_activate,u=href,b=base,t=tag: f(t,u,b))
		self.tag_bind(tag, "<Enter>",
			lambda e,f=self.anchor_enter,u=href,b=base,t=tag: f(t,u,b))	    
		self.tag_bind(tag, "<Leave>", self.anchor_leave)


    def anchor_enter(self, tag, href, base):
	self.configure(cursor = 'hand2')
	if self.popup is None:
		return
	self.unpost = 0
	if self.timer is not None:
		return
	self.timer = self.popup.after(globals.PostDelay,
		lambda f=self.showpopup,u=href,b=base,t=tag: f(t,u,b))


    def anchor_activate(self, tag, href, base):
#	apply(self.tag_add, ('sel',) + self.text.tag_ranges(tag)[:2])
	self.doanchor(href, base, self.text, self.defcursor)
	self.popup_leave()


    def anchor_leave(self, event):
	self.configure(cursor = self.defcursor)
	self.popup_leave()


    def popup_leave(self):
	if self.popup is None:
		return
	if self.timer is not None:
		self.unpost = 1	# Allow timer to expire to avoid Tkinter bug
	elif self.posted:
		self.posted = 0
		self.popup.unpost()


    def showpopup(self, tag, href, base):

	self.timer = None
	if self.unpost: return
	self.posted = 1
	url = urlparse.urljoin(base, href)

	# Truncate if too long
	if len(url) > globals.MaxURLShow:
		# parts = typ,loc,path,param,query,frag
		parts = list(urlparse.urlparse(url))
		max_part_len = globals.MaxURLShow/3
		max_part_half_len = max_part_len/2
		max_part_len = max_part_len + 3		# + 3 for elipsis
		for i in range(2, len(parts)):
			part = parts[i]
			if len(part) > max_part_len:
				parts[i] = part[:max_part_half_len] + '...' + part[-max_part_half_len:]
		url = urlparse.urlunparse(tuple(parts))

	self.popup.entryconfigure(0, label=url)
	self.popup.poston(texttag=tag)


    def new_alignment(self, align):
	Debug(2, '''"new_alignment(%s)" % align''')
	if self.align is not None:
		self.tag_add(self._make_tag(self.align, justify=self.align),
				self.align_mark, "insert")
	if align is not None:
		self.align_mark = self.text.index("insert")
	self.align = align


    def new_font(self, font):
	Debug(2, '''"new_font(%s)" % `font`''')
	mark, tag = self.new_font_mark, self.new_font_tag
	if font is not None:
		self.new_font_mark = self.text.index("insert")
		self.new_font_tag = self._make_hn_font(font)
	else:
		self.new_font_mark, self.new_font_tag = None, None
		self.font = self.basefont
	if mark is not None and mark != self.new_font_mark:
		self.tag_add(tag, mark, "insert")


    def new_margin(self, typ, level):
	Debug(2, '''"new_margin(%s, %s) @%s" % (typ, level, `self.indent`)''')
	if self.indent:
		t,l,m = self.indent
		p1 = p2 = 2 * self.charpixelwidth * l
		if t in ('blockquote',):
			g = self._make_tag('%s%s' % (t,l), lmargin1=p1, lmargin2=p1, rmargin=p1)
		elif t in ('dir', 'menu', 'ul', 'ol'):
			p2 = p1 + self.charpixelwidth
			g = self._make_tag('%s%s' % (t,l), lmargin1=p1, lmargin2=p2)
		else:
			g = self._make_tag('%s%s' % (t,l), lmargin1=p1, lmargin2=p1)
		self.tag_add(g, m, "insert")
	if level == 0:
		self.indent = None
		return
	self.indent = (typ, level, self.text.index("insert"))


    def send_line_break(self):
	if self.linebreak == 0:
		self.write('\n')
		self.linebreak = 1
	self.atbreak = 0


    def send_paragraph(self, blanklines):
	self.send_line_break()
	if blanklines:
		self.write('\n'*blanklines)


    def send_label_data(self, data):
	self.write(data + ' ')


    def send_hor_rule(self, attrs):
	Debug(2, '''"send_hor_rule(%s)" % attrs''')
	width = self.width*0.9
	for name,value in attrs:
		if name == 'width' and value[-1] == '%':
			width = width * int(value[:-1]) / 100.0
			
	self.write('_'*(int(width)))

	self.linebreak = 0
	self.atbreak = 1


    def send_flowing_data(self, data,
		whitespace=string.whitespace,
		join=string.join,
		split=string.split,
		replace=string.replace,
		NBSP=htmlentitydefs.entitydefs['nbsp']):
	if not data: return
	write = self.write
	if self.atbreak or data[0] in whitespace:
		write(' ')
	write(replace(join(split(data)), NBSP, ' '))
	self.linebreak = 0
	self.atbreak = data[-1] in whitespace


    def flush_softspace(self):
	if not self.atbreak: return
	self.write(' ')
	self.linebreak = 0
	self.atbreak = 0


    def send_literal_data(self, data):
	self.write(data)
	self.linebreak = data[-1] == '\n'
	self.atbreak = 0


    def start_font(self, attrs):
	Debug(2, '''"start_font(%s)" % attrs''')
	font = self.font
	tags = []
	for name,value in attrs:
		if name == 'color':
			tags.append(self._make_tag(value, foreground=value))
		elif name == 'size':
			tags.append(self._htmlsize2font(value))
		elif name == 'underline':
			tags.append(self._make_tag(name, underline=value))
	self.font_stack.append((tags, self.text.index("insert"), font))


    def end_font(self):
	Debug(2, '''"end_font()"''')
	tags, mark, self.font = self.font_stack[-1]
	del self.font_stack[-1]
	for tag in tags:
		self.tag_add(tag, mark, "insert")



class Formatter(formatter.AbstractFormatter):

    def anchor_bgn(self, href, name, type, base):
	self.anchor = href or name
	if not self.anchor: return
	self.flush_softspace()
	self.writer.anchor_bgn(href, name, type, base)


    def anchor_end(self):
	if not self.anchor: return
	self.writer.anchor_end()
	self.anchor = None


    def add_hor_rule(self, attrs):
	if not self.hard_break:
		self.writer.send_line_break()
	self.writer.send_hor_rule(attrs)
	self.nospace = 1
	self.hard_break = self.have_label = self.para_end = self.softspace = self.parskip = 0


    def flush_softspace(self):
	if self.softspace:
		self.hard_break = self.para_end = self.parskip = \
			  self.have_label = self.softspace = 0
		self.nospace = 1
		self.writer.send_flowing_data(' ')
	self.writer.flush_softspace()



class HTMLParser(htmllib.HTMLParser):

    def start_body(self, attrs):
	self.formatter.writer.start_body(attrs)


    def anchor_bgn(self, href, name, type):
	self.formatter.anchor_bgn(href, name, type, self.base)

    def anchor_end(self):
	self.formatter.anchor_end()


    def start_center(self, attrs):
	self.formatter.push_alignment('center')

    def end_center(self):
	self.formatter.pop_alignment()


    # <FONT>...</FONT> - this is cheating -
    # should probably be using formatter "styles"?

    def start_font(self, attrs):
	self.formatter.writer.start_font(attrs)

    def end_font(self):
	self.formatter.writer.end_font()


    def start_small(self, attrs):
	self.formatter.writer.start_font([('size', '-1')])

    def end_small(self):
	self.formatter.writer.end_font()


    def start_div(self, attrs):	# ALIGN= NOWRAP
	pass

    def end_div(self):
	self.formatter.add_line_break()


    def start_u(self, attrs):
	self.formatter.flush_softspace()
	self.formatter.writer.start_font([('underline', '1')])

    def end_u(self):
	self.formatter.writer.end_font()


    def do_hr(self, attrs):
	popa = 0
	for name,value in attrs:
		if name == 'align' and value in ('left', 'right', 'center'):
			self.formatter.push_alignment(value)
			popa = 1
	self.formatter.add_hor_rule(attrs)
	if popa: self.formatter.pop_alignment()



def DoAnchor(href, base, text, cursor):

	""" Default anchor selection handler """

	url = urlparse.urljoin(base, href)
	scheme, net, path = urlparse.urlparse(url)[:3]
	error = "%s\n- %s is not supported yet." % (url, scheme)
	if scheme == 'file':
		data = readfile(path)
		if data:
			text['cursor'] = cursor
			HTML2TextClean(text)
			HTML2Text(data, text)
			return
		error = "%s\n- could not read %s." % (url, path)
	elif scheme in ('http', 'https', 'ftp'):
		if not globals.AllowHREFURLQueries:
			url = urlparse.urlunparse((scheme, net, path) + ('',)*3)
		command = globals.OpenURLCmd % url
		Debug(1, 'command')
		text['cursor'] = 'watch'
		text.update_idletasks()
		import os; os.system(command)
		text['cursor'] = cursor
		return
	elif scheme == 'mailto':
		try:
			import Compose
			text['cursor'] = 'watch'
			text.update_idletasks()
			Compose.Compose()(path)
			text['cursor'] = cursor
			return
		except ImportError: pass
	elif not scheme and url[0] == '#':
		tag = 'name_%s' % string.replace(url[1:], ' ', '_')
		Debug(1, '''"See tag %s => %s" % (tag, `text.tag_ranges(tag)`)''')
		try:
			text.yview(text.tag_ranges(tag)[0])
		except IndexError:
			pass	# Hmmm. Tk bug?
		return

	Debug(1, '''"url=%s, scheme=%s, net=%s, path=%s" % (url, scheme, net, path)''')
	import TopLevel
	TopLevel.MessageTextBox('URL reference error')(error)



def HTML2Text(data, text, basefont=None, do_anchor=None, popup=None):

	"""
		Insert a string containing HTML into a Tkinter Text widget.

		Invoke as HTML2Text(data, text, basefont=None, do_anchor=None, popup=None)

			data	  - string containg HTML
			text	  - Tkinter Text widget
			basefont  - string containing Tk font description
					in format: "family points weight slant"
					the last 3 of which can be missing
			do_anchor - function to handle anchor selections
				    will be called as anchor(href, base, text, cursor)
					href - string from HREF attribute of anchor,
					base - string from HREF attribute of BASE,
					text - Text widget holding reference
					cursor - current cursor
			popup	  - widget to display anchor value
	"""

	if do_anchor is None:
		do_anchor = DoAnchor

	parser = HTMLParser(Formatter(TkTextWriter(text, basefont, do_anchor, popup)))

	restore_state = text['state']
	if restore_state != 'normal':
		text['state'] = 'normal'

	apply(text.tag_delete, text.tag_names())
	text.delete('1.0', 'end')

	parser.feed(data)	# This can generate `RuntimeError' exceptions on bad HTML
	parser.close()

	if restore_state != 'normal':
		text['state'] = restore_state



def HTML2TextClean(text, basefont=None):
	"""
		Undo effects of HTML2Text.

		Call as HTML2TextClean(text, basefont=None)
			text	  - Tkinter Text widget
			basefont  - Tk font description
	"""

	apply(text.tag_delete, text.tag_names())
	if basefont is not None:
		text['font'] = Font2TkFont(basefont)



def Font2TkFont(font):
	""" Turn font tuple into Tk font list. """
	ft = type(font)
	if ft is not type(()) and ft is not type([]):
		if ft is not type(''):
			raise ValueError("font must be string or tuple")
		return font
	return '{%s}' % string.join(map(str, filter(lambda x:x is not None, font)), '} {')


def Font2FontTuple(text, font):
	""" Turn font description to font tuple using Tk "font" command. """
	try:
		tkdesc = string.split(text.tk.call("font", "actual", font))
	except:
		import sys; exc = sys.exc_info()
		Debug(1, '''"tcl font error: %s - %s" % exc[:2]''')
		raise ValueError("font must be in X font name format")

	d = {'-family':0, '-size':1, '-weight':2, '-slant':3}

	res = [None]*len(d)

	for i in range(0, len(tkdesc), 2):
		index = d.get(tkdesc[i])
		if index is not None:
			res[index] = tkdesc[i+1]
		
	return tuple(res)



if __debug__:
    if __name__ == '__main__':

	html = readfile('test.html')
	if not html:
		html = '''
<HTML><BODY BGCOLOR="white">
<CENTER>
<H1>An H1 title</H1>
</CENTER>
<H3>An H3 heading</H3>
A short line containing three non-breaking-spaces here &gt;&nbsp;&nbsp;&nbsp;&lt;.
Check out <A HREF="#here">this local reference</A>
<H5>An H5 heading</H5>
<P>A few short lines of text containing an underlined <U>word</U>
that I hope are properly formatted,
with a reference to
<A HREF="http://www.cs.su.oz.au/~piers/">my homepage</A>.</P>
<H6>An H6 heading</H6>
<P>And now a <SMALL>&lt;BLOCKQUOTE&gt;</SMALL>:</P>
<BLOCKQUOTE>
<FONT COLOR="#808080"><B>facemail</B></FONT>
is a <SAMP>Python/Tkinter</SAMP> based program
for processing mail boxes.
<FONT COLOR="#808080"><B>facemail</B></FONT> displays a <B><I>face</I></B>
for each mail item,
most recent at the top-left, oldest at bottom-right.
The name and date are displayed below each face.
Pressing <SAMP>button-1</SAMP> on a face displays the associated message.
</BLOCKQUOTE>
<P>A new paragraph, and now we'll try indented text:</P>
<UL>
<LI><FONT COLOR="#800000">some indented text in red.</FONT>
Followed by some quite normal text to see what happens after a line break.
<UL>
<LI><B><FONT COLOR="#008000">Another</FONT></B> <I>nested</I> line.
</UL>
<B><I><FONT COLOR="#000080">Another</FONT></I></B> less <I>nested</I> line.
</UL>
<DIV><FONT SIZE=2 COLOR="#000080">A dark blue <SMALL>&lt;FONT SIZE=2&gt;</SMALL> line delimited by <SMALL>&lt;DIV&gt;</SMALL></FONT></DIV>
<HR WIDTH="100%" ALIGN="center">
<P><A NAME="here">And now</A>, nestled between two centred horizontal rules, a reference to <A HREF="file:help.html">another file</A>.</P>
<HR WIDTH="100%" ALIGN="center">
<P>The end.</P>
</BODY></HTML>'''

	try:
		from logger import DebugLevel
		DebugLevel(2)
	except ImportError: pass
	from TopLevel import Popup

	import Tkinter
	r = Tkinter.Tk()
	r.withdraw()
	t = Tkinter.Text(r, wrap='word', width=55, height=33)
	t.configure(insertofftime=0, insertontime=0, insertwidth=0)
	t.pack(expand=1, fill='both')
	popup = Popup(t)
	popup.add_command()
	HTML2Text(html, t, 'Helvetica 12', popup=popup)
	b = Tkinter.Button(r, text='Bye', command=r.quit)
	b.pack(fill='x')
	r.deiconify()
	r.mainloop()

# code highlighted using py2html.py version 0.8

