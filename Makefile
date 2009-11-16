
project=jclic_browser
version=0.4

all:
	# none

glade:
	glade-2 $(project).glade

exec:
	python $(project).py 

clean:
	rm -f *~ *.pyc *.orig *.bak *-stamp
	find -name *.pyc | xargs rm -f
	find -name *~ | xargs rm -f
	if [ -d debian/jclic-browser ]; then rm -rf debian/jclic-browser; fi
	cd po && make clean

updatesql:
	sqlite ~/.$(project).db < utils/data.sql
	
newsqlite:
	sqlite ~/.$(project).db < db.sql

sqlite:
	sqlite ~/.$(project).db

install:
	#  Creating JClicBrowser directories in $(DESTDIR)/
	install -d $(DESTDIR)/usr/share/$(project)
	install -d $(DESTDIR)/usr/share/$(project)/utils
	install -d $(DESTDIR)/usr/share/locale/es/LC_MESSAGES/
	install -d $(DESTDIR)/usr/bin
	install -d -m 777 $(DESTDIR)/var/lib/$(project)/zips
	install -d -m 777 $(DESTDIR)/var/lib/$(project)/imgs
	install -d $(DESTDIR)/usr/lib/python2.5/site-packages/$(project)

	# Installing JClicBrowser in  $(DESTDIR)
	install -m 755 $(project).py $(DESTDIR)/usr/lib/python2.5/site-packages/$(project)
	install -m 755 JClicLib.py $(DESTDIR)/usr/lib/python2.5/site-packages/$(project)
	install -m 644 jclic_browser.glade $(DESTDIR)/usr/share/$(project)
	install -m 644 library.jclic $(DESTDIR)/usr/share/$(project)
	install -m 644 pixmaps/logo.png $(DESTDIR)/usr/share/$(project)


	install -m 644 downloader/jclic.db $(DESTDIR)/usr/share/$(project)
	gzip $(DESTDIR)/usr/share/$(project)/jclic.db

	install -m 755 utils/jclic.sh $(DESTDIR)/usr/share/$(project)/utils/
	install -m 755 utils/mostrar-infos.sh $(DESTDIR)/usr/share/$(project)/utils/
	install -m 755 utils/copy_library.sh $(DESTDIR)/usr/share/$(project)/utils/

	install -m 644 utils/urls.jclic $(DESTDIR)/usr/share/$(project)/utils/
	install -m 644 utils/urls.img $(DESTDIR)/usr/share/$(project)/utils/
	install -m 644 utils/data.sql $(DESTDIR)/usr/share/$(project)/utils/

	install -m 755 jclic-browser $(DESTDIR)/usr/bin/jclic-browser

	# locales
	cd po && make install DESTDIR=$(DESTDIR)

uninstall:
	#  Deleting JClicBrowser directories
	rm -rf /usr/share/$(project)
	rm -rf /usr/bin/jclic-browser

	#locales
	rm /usr/share/locale/es/LC_MESSAGES/jclic_browser.mo


targz: clean
	rm -rf ../tmp 2> /dev/null
	mkdir ../tmp
	cp -ra * ../tmp
	###################
	# Borrando svn... #
	###################
	rm -rf `find ../tmp/* -type d -name .svn`
	mv ../tmp ../jclic_browser-$(version)
	tar -czf ../jclic_browser-$(version).tar.gz ../jclic_browser-$(version)
	rm -rf ../jclic_browser-$(version)

