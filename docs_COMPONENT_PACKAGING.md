# Streamlit custom component packaging (React)

## Why packaging matters
`components.html` cannot call `st.switch_page` from JS. A **declared component** can return values to Python on click.

## Scaffold
```bash
pip install streamlit-component-lib
# or
npx create-streamlit-component sosby_nav
cd sosby_nav/sosby_nav/frontend
npm install
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

`tailwind.config.js` content paths → `./src/**/*.{js,jsx,ts,tsx}`

## Frontend pattern
```jsx
import { Streamlit, withStreamlitConnection } from "streamlit-component-lib"

function Nav({ args }) {
  const go = (page) => Streamlit.setComponentValue({ page })
  return (
    <nav className="flex gap-2 p-3 bg-gradient-to-r from-amber-950 via-orange-500 to-amber-400 text-white rounded-2xl">
      <button onClick={() => go("home")}>Home</button>
      <button onClick={() => go("game_day")}>Game Day</button>
    </nav>
  )
}
export default withStreamlitConnection(Nav)
```

## Build & install
```bash
npm run build
# python package points path= to frontend/build
pip install -e .
```

## Python
```python
import streamlit.components.v1 as components
nav = components.declare_component("sosby_nav", path="sosby_nav/frontend/build")
val = nav(key="nav")
if val and val.get("page") == "game_day":
    st.switch_page("pages/1_Game_Day.py")
```

## Publish
Upload wheel to PyPI; add package name to `requirements.txt` for Streamlit Cloud.

Until then, use Navigate row + sidebar (already in SO!SB!Y!).
