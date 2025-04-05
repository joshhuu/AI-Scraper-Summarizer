import re

# Read the HTML file
with open("joke.html", "r", encoding="utf-8") as file:
    content = file.read()

# Extract CSS
css_match = re.search(r"<style.*?>(.*?)</style>", content, re.DOTALL)
css_content = css_match.group(1).strip() if css_match else ""

# Extract JavaScript
js_match = re.search(r"<script.*?>(.*?)</script>", content, re.DOTALL)
js_content = js_match.group(1).strip() if js_match else ""

# Remove CSS and JS from HTML
clean_html = re.sub(r"<style.*?>.*?</style>", "", content, flags=re.DOTALL)
clean_html = re.sub(r"<script.*?>.*?</script>", "", clean_html, flags=re.DOTALL)

# Save HTML
with open("index_clean.html", "w", encoding="utf-8") as file:
    file.write(clean_html)

# Save CSS
if css_content:
    with open("style.css", "w", encoding="utf-8") as file:
        file.write(css_content)

# Save JavaScript
if js_content:
    with open("script.js", "w", encoding="utf-8") as file:
        file.write(js_content)

print("HTML, CSS, and JS split successfully!")
