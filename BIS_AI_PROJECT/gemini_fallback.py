"""Bounded quota-aware fallback; never infer daily exhaustion from HTTP 429 alone."""
import json
import re
import time

TECHNICAL_MODELS = ('gemini-3.6-flash', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite')

def quota_info(exc):
    details = getattr(exc, 'response_json', None) or getattr(exc, 'details', None) or {}
    text = (str(exc) + ' ' + json.dumps(details, default=str)).lower()
    if any(word in text for word in ('spend cap', 'spend limit', 'spending limit', 'billing spend', 'insufficient credit', 'credit balance', 'budget exceeded')):
        return 'BILLING', None
    if any(word in text for word in ('perday', 'per_day', 'per day', 'daily', 'rpd')):
        return 'RPD', None
    delay = None
    response = getattr(exc, 'response', None)
    header = getattr(response, 'headers', {}).get('Retry-After') if response else None
    try: delay = float(header) if header else None
    except (TypeError, ValueError): pass
    match = re.search(r'(?:retrydelay["\' :]+|retry in\s+)([0-9.]+)s', text)
    if match: delay = float(match.group(1))
    if any(word in text for word in ('perminute', 'per_minute', 'per minute', 'rpm', 'tpm')) or delay is not None:
        return 'RATE', delay
    return 'UNKNOWN', None

def generate_with_fallback(client, models, *, contents, config, attempts):
    last = None
    for model in dict.fromkeys(models):
        for retry in range(2):
            try:
                response = client.models.generate_content(model=model, contents=contents, config=config)
                attempts.append({'model':model,'status':'SUCCESS'})
                return response, model
            except Exception as exc:
                try: code = int(getattr(exc, 'code', 0) or 0)
                except (TypeError, ValueError): code = 0
                row = {'model':model,'status':'FAILED','code':code}
                attempts.append(row)
                last = exc
                if code == 429:
                    kind, delay = quota_info(exc)
                    row['quota_kind'] = kind
                    if kind == 'BILLING': raise
                    if kind == 'RATE':
                        wait = max(4.0, delay if delay is not None else 4.0)
                        if retry == 0 and wait <= 15:
                            row['retry_seconds'] = wait
                            time.sleep(wait)
                            continue
                        # Long rate delays must not be bypassed by switching models.
                        raise
                    # Daily or unspecified quota: one attempt per remaining configured model.
                    break
                if code not in (503,504): raise
                break
    if last is None: raise ValueError('No model configured')
    raise last
