"""
Browser localStorage + IndexedDB bridge for last team / nav.
Streamlit cannot read IndexedDB from Python; this injects JS that
persists preferences client-side for faster return visits.
"""
from __future__ import annotations
import json
import streamlit as st
import streamlit.components.v1 as components


def inject_client_store(team_key: str, last_page: str = "home") -> None:
    payload = json.dumps({"team_key": team_key, "last_page": last_page})
    components.html(
        f"""
<script>
(function() {{
  const data = {payload};
  try {{ localStorage.setItem('sosby_prefs', JSON.stringify(data)); }} catch (e) {{}}
  try {{
    if (!window.indexedDB) return;
    const req = indexedDB.open('sosby_db', 1);
    req.onupgradeneeded = function(e) {{
      const db = e.target.result;
      if (!db.objectStoreNames.contains('prefs')) db.createObjectStore('prefs');
    }};
    req.onsuccess = function(e) {{
      const db = e.target.result;
      try {{
        const tx = db.transaction('prefs', 'readwrite');
        tx.objectStore('prefs').put(data, 'main');
      }} catch (err) {{}}
    }};
  }} catch (e) {{}}
}})();
</script>
<p style="font-size:11px;opacity:.55;margin:0">Prefs saved in browser (localStorage / IndexedDB when available).</p>
""",
        height=28,
    )
