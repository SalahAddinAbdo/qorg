from __future__ import annotations
import hashlib, ipaddress
import frappe
from frappe import _
from frappe.utils import now_datetime

def client_ip():
    request=getattr(frappe.local,'request',None)
    if not request:return 'internal'
    remote=getattr(request,'remote_addr',None) or 'unknown'
    # Trust X-Forwarded-For only when Frappe/ProxyFix has already normalized access_route.
    route=getattr(request,'access_route',None) or []
    candidate=(route[0] if route else remote)
    try:return str(ipaddress.ip_address(candidate))
    except ValueError:return remote

def enforce_rate_limit(scope,limit):
    limit=max(1,int(limit or 1));identity=hashlib.sha256(client_ip().encode()).hexdigest()[:24]
    key=f'qorg:governance:{scope}:{identity}:{now_datetime().strftime("%Y%m%d%H")}'
    cache=frappe.cache();value=cache.incr(key)
    if value==1:cache.expire(key,3700)
    if value>limit:frappe.throw(_("Too many requests. Please try again later."),frappe.RateLimitExceededError)
    return value

def validate_captcha(token):
    settings=frappe.get_single('Accountability Settings')
    if not settings.require_captcha:return
    if not token:frappe.throw(_("CAPTCHA verification is required."))
    if not settings.captcha_verifier_method:frappe.throw(_("CAPTCHA verifier is not configured."),frappe.PermissionError)
    if not bool(frappe.get_attr(settings.captcha_verifier_method)(token, client_ip())):
        frappe.throw(_("CAPTCHA verification failed."),frappe.PermissionError)
