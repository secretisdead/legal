from functools import wraps
import json
import time

from flask import Blueprint, g, redirect, render_template, request
from flask import after_this_request, url_for

legal = Blueprint(
	'legal',
	__name__,
	template_folder='templates',
)

def force_terms_agreement(**kwargs):
	return terms(agreement_form=True, **kwargs)

def initialize(config):
	g.legal = config

def terms_agreed():
	# ignore robots
	useragent = str(request.user_agent)
	for botname in [
			'APIs-Google',
			'Goooglebot',
			'Discordbot',
			'Twitterbot',
		]:
		if -1 != useragent.find(botname):
			return True
	if (
			g.legal['terms_agree']['name'] in request.cookies
			and request.cookies[g.legal['terms_agree']['name']]
		):
		return True
	return False

@legal.route('/terms')
def terms(agreement_form=False, **kwargs):
	if 'terms_agree' not in request.args:
		# try to submit form to whatever the underlying endpoint was
		if not kwargs:
			form_uri = request.url
		else:
			form_uri = url_for(request.endpoint, **kwargs)
		return render_template(
			'legal_terms.html',
			agreement_form=agreement_form,
			form_uri=form_uri,
		)
	@after_this_request
	def set_consent_cookie(response):
		opts = {
			'value': '1',
			'expires': time.time() + g.legal['terms_agree']['lifetime'],
			'secure': g.legal['terms_agree']['secure'],
		}
		if g.legal['terms_agree']['domain']:
			opts['domain'] = g.legal['terms_agree']['domain']
		if g.legal['terms_agree']['path']:
			opts['path'] = g.legal['terms_agree']['path']
		response.set_cookie(g.legal['terms_agree']['name'], **opts)
		return response
	# try to pass through to whatever the underlying endpoint was
	passed_kwargs = {}
	for key, value in request.args.items():
		if key != 'terms_agree':
			passed_kwargs[key] = value
	for key, value in kwargs.items():
		passed_kwargs[key] = value
	if not passed_kwargs:
		return redirect(request.url, code=303)
	return redirect(url_for(request.endpoint, **passed_kwargs), code=303)

@legal.route('/rules')
def rules():
	return render_template('legal_rules.html')

@legal.route('/privacy')
def privacy():
	return render_template('legal_privacy.html')

@legal.route('/revoke-cookie-consent')
def revoke_cookie_consent():
	@after_this_request
	def clear_cookies(response):
		for cookie_name in request.cookies:
			opts = {
				'value': '',
				'expires': time.time() - 1,
			}
			response.set_cookie(cookie_name, **opts)
		return response
	return render_template('legal_revoke_cookie_consent.html')

@legal.route('/takedown')
def takedown():
	return render_template('legal_takedown.html')
