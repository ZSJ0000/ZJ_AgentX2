import json,os
DEFAULT_MANIFEST=json.load(open(os.path.join(os.path.dirname(os.path.dirname(__file__)),'platform_manifest.json'),encoding='utf-8'))
def load_manifest(path=None):
 try:
  with open(path or os.path.join(os.path.dirname(os.path.dirname(__file__)),'platform_manifest.json'),encoding='utf-8') as f:return json.load(f)
 except (IOError,ValueError):return dict(DEFAULT_MANIFEST)
def model_context(manifest=None):return 'Platform capability manifest (authoritative runtime rules):\n'+json.dumps(manifest or DEFAULT_MANIFEST,ensure_ascii=False,indent=2)
