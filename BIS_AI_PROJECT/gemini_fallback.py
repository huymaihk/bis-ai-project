"""Bounded, same-provider fallback for transient 503/504 only."""
def generate_with_fallback(client, models, *, contents, config, attempts):
    last = None
    for model in dict.fromkeys(models):
        try:
            response = client.models.generate_content(model=model, contents=contents, config=config)
            attempts.append({'model':model,'status':'SUCCESS'})
            return response, model
        except Exception as exc:
            try:
                code = int(getattr(exc, 'code', 0) or 0)
            except (TypeError, ValueError):
                code = 0
            attempts.append({'model':model,'status':'FAILED','code':code})
            if code not in (503, 504):
                raise
            last = exc
    if last is None:
        raise ValueError('No model configured')
    raise last
